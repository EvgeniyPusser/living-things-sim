"""Наследование от одного донора против наследования от всей популяции.

Для каждого здания-новичка (ему известны только первые 14 дней):
  scratch     своя модель по 14 дням
  best_donor  лучшая из чужих моделей (задним числом, верхняя граница)
  median_donor медиана по всем 39 чужим моделям
  pool        модель, обученная на нормированных данных ВСЕХ других зданий
  pool_tuned  та же модель, дообученная на 14 днях новичка
"""
import numpy as np, pandas as pd, sys, lightgbm as lgb
from prep import load_site, features

SITE = sys.argv[1] if len(sys.argv) > 1 else "Rat"
DAYS = int(sys.argv[2]) if len(sys.argv) > 2 else 14
e, w, meta = load_site(SITE)
X = features(e.index, w["airTemperature"])
tr, te = e.index.year == 2016, e.index.year == 2017
short = tr & (e.index < e.index[tr][0] + pd.Timedelta(days=DAYS))
FULL = dict(n_estimators=200, learning_rate=0.06, num_leaves=31, min_child_samples=40, verbose=-1, random_state=1)
SHORT = dict(n_estimators=120, learning_rate=0.06, num_leaves=15, min_child_samples=20, verbose=-1, random_state=1)
scale = {b: e[b][tr].mean() for b in e.columns}
donors = {b: lgb.LGBMRegressor(**FULL).fit(X[tr], e[b][tr] / scale[b]) for b in e.columns}
Xte, Xsh = X[te], X[short]
rows = []
for b in e.columns:
    others = [a for a in e.columns if a != b]
    yte = (e[b][te] / scale[b]).values
    s_short = e[b][short].mean(); k = s_short / scale[b]
    err = lambda p: float(np.abs(p - yte).mean())
    scratch = err(lgb.LGBMRegressor(**SHORT).fit(Xsh, e[b][short] / s_short).predict(Xte) * k)
    P = np.vstack([donors[a].predict(Xte) for a in others])
    single = [err(p * k) for p in P]
    med = err(np.median(P, axis=0) * k)
    # общая модель по всем остальным зданиям
    Xp = pd.concat([X[tr]] * len(others), ignore_index=True)
    yp = np.concatenate([(e[a][tr] / scale[a]).values for a in others])
    pool_m = lgb.LGBMRegressor(**FULL).fit(Xp, yp)
    pool = err(pool_m.predict(Xte) * k)
    pool_t = err(lgb.LGBMRegressor(**SHORT).fit(Xsh, e[b][short] / s_short,
                 init_model=pool_m.booster_).predict(Xte) * k)
    rows.append(dict(building=b, scratch=scratch, best_donor=min(single),
                     median_donor=med, pool=pool, pool_tuned=pool_t))
    print(".", end="", flush=True)
d = pd.DataFrame(rows); d.to_csv(f"pool_{SITE}_{DAYS}d.csv", index=False)
print()
for c in ["best_donor", "median_donor", "pool", "pool_tuned"]:
    g = (d.scratch - d[c]) / d.scratch * 100
    print("%-13s выигрыш против своей короткой модели: медиана %+5.1f%%, помог в %2.0f%% зданий"
          % (c, g.median(), (g > 0).mean() * 100))
