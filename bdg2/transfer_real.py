"""Перенос модели потребления между настоящими зданиями (BDG2).

Обучаем на 2016, проверяем на 2017. Модель здания A применяем к зданию B.
Потребление нормировано на среднее самого здания за 2016: переносится форма
отклика (на погоду, час, день недели), а не масштаб.
"""
import numpy as np, pandas as pd, sys, itertools
import lightgbm as lgb
from prep import load_site, features

SITE = sys.argv[1] if len(sys.argv) > 1 else "Rat"
e, w, meta = load_site(SITE)
X = features(e.index, w["airTemperature"])
train = e.index.year == 2016
test = e.index.year == 2017
print(f"{SITE}: {e.shape[1]} зданий, обучение {train.sum()} ч, проверка {test.sum()} ч", flush=True)

PAR = dict(n_estimators=200, learning_rate=0.06, num_leaves=31,
           min_child_samples=40, verbose=-1, random_state=1)

models, scale, own_err = {}, {}, {}
for b in e.columns:
    y = e[b]
    s = y[train].mean(); scale[b] = s
    m = lgb.LGBMRegressor(**PAR).fit(X[train], (y[train] / s))
    models[b] = m
    own_err[b] = np.abs(m.predict(X[test]) - (y[test] / s).values).mean()
print("свои модели готовы", flush=True)

rows = []
Xte = X[test]
pred_cache = {b: models[b].predict(Xte) for b in e.columns}
for a, b in itertools.permutations(e.columns, 2):
    yb = (e[b][test] / scale[b]).values
    err = np.abs(pred_cache[a] - yb).mean()
    rows.append(dict(donor=a, receiver=b, err_transfer=err, err_own=own_err[b],
                     loss_pct=(err - own_err[b]) / own_err[b] * 100))
d = pd.DataFrame(rows)

# различия между зданиями по метаданным
md = meta.copy()
md["log_sqm"] = np.log10(md["sqm"].astype(float))
md["year"] = md["yearbuilt"].fillna(md["yearbuilt"].median())
for col in ["log_sqm", "year"]:
    z = (md[col] - md[col].mean()) / md[col].std()
    d["d_" + col] = [abs(z[r.donor] - z[r.receiver]) for r in d.itertuples()]
d["same_use"] = [int(md.primaryspaceusage[r.donor] == md.primaryspaceusage[r.receiver])
                 for r in d.itertuples()]
d.to_csv(f"real_transfer_{SITE}.csv", index=False)

print(d.loss_pct.describe().round(1).to_string())
print("\nдоля пар, где чужая модель хуже своей: %.0f%%" % ((d.loss_pct > 0).mean() * 100))
print("медианная потеря: %.1f%%" % d.loss_pct.median())
print("\nсвязь потери с различием:")
print(d[["d_log_sqm", "d_year", "same_use"]].corrwith(d.loss_pct).round(3).to_string())
print("\nтот же тип использования против разного:")
print(d.groupby("same_use").loss_pct.median().round(1).to_string())
