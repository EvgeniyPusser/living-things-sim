"""Новое здание: мало собственной истории. Стоит ли брать чужую модель?

Донор: здание с полным 2016 годом.
Новичок: то же здание, но ему доступны только первые N дней 2016.
Три условия, проверка на всём 2017:
  scratch  — своя модель по N дням
  as_is    — модель донора без изменений
  tuned    — модель донора, дообученная на N днях новичка (init_model)
"""
import numpy as np, pandas as pd, sys, itertools, lightgbm as lgb
from prep import load_site, features

SITE = sys.argv[1] if len(sys.argv) > 1 else "Rat"
DAYS = int(sys.argv[2]) if len(sys.argv) > 2 else 14

e, w, meta = load_site(SITE)
X = features(e.index, w["airTemperature"])
tr = e.index.year == 2016
te = e.index.year == 2017
start = e.index[tr][0]
short = tr & (e.index < start + pd.Timedelta(days=DAYS))
print(f"{SITE}: {e.shape[1]} зданий; новичку дано {short.sum()} часов ({DAYS} дней)", flush=True)

FULL = dict(n_estimators=200, learning_rate=0.06, num_leaves=31, min_child_samples=40,
            verbose=-1, random_state=1)
SHORT = dict(n_estimators=120, learning_rate=0.06, num_leaves=15, min_child_samples=20,
             verbose=-1, random_state=1)

scale = {b: e[b][tr].mean() for b in e.columns}
donor = {b: lgb.LGBMRegressor(**FULL).fit(X[tr], e[b][tr] / scale[b]) for b in e.columns}
print("доноры обучены", flush=True)

res = []
for b in e.columns:
    yte = (e[b][te] / scale[b]).values
    s_short = e[b][short].mean()                      # масштаб по тому, что известно
    m_scratch = lgb.LGBMRegressor(**SHORT).fit(X[short], e[b][short] / s_short)
    err_scratch = np.abs(m_scratch.predict(X[te]) * s_short / scale[b] - yte).mean()
    for a in e.columns:
        if a == b: continue
        # чужая модель, приведённая к масштабу новичка по его коротким данным
        k = s_short / scale[b]
        err_as_is = np.abs(donor[a].predict(X[te]) * k - yte).mean()
        booster = donor[a].booster_
        m_tuned = lgb.LGBMRegressor(**SHORT).fit(X[short], e[b][short] / s_short,
                                                 init_model=booster)
        err_tuned = np.abs(m_tuned.predict(X[te]) * k - yte).mean()
        res.append(dict(donor=a, receiver=b, err_scratch=err_scratch,
                        err_as_is=err_as_is, err_tuned=err_tuned,
                        gain_as_is=(err_scratch - err_as_is) / err_scratch * 100,
                        gain_tuned=(err_scratch - err_tuned) / err_scratch * 100))
    print(".", end="", flush=True)

d = pd.DataFrame(res)
md = meta.copy(); md["log_sqm"] = np.log10(md["sqm"].astype(float))
z = (md["log_sqm"] - md["log_sqm"].mean()) / md["log_sqm"].std()
d["d_log_sqm"] = [abs(z[r.donor] - z[r.receiver]) for r in d.itertuples()]
d["same_use"] = [int(md.primaryspaceusage[r.donor] == md.primaryspaceusage[r.receiver]) for r in d.itertuples()]
d.to_csv(f"newcomer_{SITE}_{DAYS}d.csv", index=False)
print()
print(d[["gain_as_is","gain_tuned"]].describe().round(1).loc[["mean","50%","min","max"]].to_string())
print("как есть помог в %.0f%% пар; дообучение помогло в %.0f%%" %
      ((d.gain_as_is>0).mean()*100, (d.gain_tuned>0).mean()*100))
print("связь выигрыша с различием площадей: %.3f" % d.d_log_sqm.corr(d.gain_tuned))
print(d.groupby("same_use")[["gain_as_is","gain_tuned"]].median().round(1).to_string())
