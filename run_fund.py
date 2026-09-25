"""Три источника ценности накопления: количество, связи, редкие случаи."""
import numpy as np, pandas as pd, sys
from sklearn.linear_model import Ridge
from life import make_houses
from life2 import weather_year, live_year, year_cost, tune, WEEKS_YEAR

GEN, PER_GEN = 10, 20
P_RARE = {"cold": 0.10, "heat": 0.08, "broken": 0.07}      # редкие случаи
START = np.full(24, 21.0)
COND = ["UA", "C", "solar", "Qmax", "T_mean", "T_amp", "start_h"]
SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 21
rng = np.random.default_rng(SEED)

def prep(n, seed):
    h = make_houses(n, np.random.default_rng(seed))
    h["Qmax"] = 1.35*(h["UA"]+h["infil"])*(21.0-(h["T_mean"]-8-h["T_amp"]/2-14))
    return h

def occ_for(b, n):
    hh = np.arange(n) % 24; s = int(b["start_h"])
    return ((hh >= s) & (hh < s + 10)).astype(float)

def draw_rare(r):
    x = r.random()
    if x < P_RARE["cold"]: return "cold", False
    if x < P_RARE["cold"] + P_RARE["heat"]: return "heat", False
    if x < sum(P_RARE.values()): return None, True      # отказ отопления
    return None, False

records = []          # (условия, расписание, было ли редкое событие)
rows = []
for g in range(1, GEN + 1):
    houses = prep(PER_GEN, SEED*100 + g)
    fund = list(records)            # фонд заморожен на время поколения
    if fund:
        X = np.array([r[0] for r in fund]); Y = np.array([r[1] for r in fund])
        mu, sd = X.mean(0), X.std(0) + 1e-9
        model = Ridge(alpha=1.0).fit((X - mu)/sd, Y)      # связи: условия → расписание
        med = np.median(Y, axis=0)
    for i in range(PER_GEN):
        b = houses.iloc[i]
        r = np.random.default_rng(SEED*1000 + g*50 + i)
        rare, broken = draw_rare(r)
        T, s = weather_year(b, r, rare=rare)
        occ = occ_for(b, len(T))
        cond = np.array([b[c] for c in COND], float)
        starts = {"default": START}
        if fund:
            starts["median"] = med
            starts["model"] = np.clip(model.predict(((cond - mu)/sd)[None, :])[0], 12, 24)
            # только записи из похожих условий (по редкому событию и по климату)
            same = [rec for rec in fund if rec[2] == (rare or ("broken" if broken else None))]
            starts["same_case"] = np.median(np.array([rec[1] for rec in same]), axis=0) if len(same) >= 3 else med
        res = {}
        for tag, st in starts.items():
            _, wk = live_year(b, st, T, s, occ, np.random.default_rng(SEED*7 + g*50 + i), broken=broken)
            res[tag] = wk.sum()
        row = dict(gen=g, obj=i, n_records=len(fund), rare=rare or ("broken" if broken else "none"))
        for tag in starts: row[tag] = res[tag]
        for tag in ("median", "model", "same_case"):
            if tag in res: row["gain_" + tag] = (res["default"] - res[tag]) / res["default"] * 100
        rows.append(row)
        # объект прожил год и кладёт в фонд расписание, подобранное по своему журналу
        sch = tune(b, starts.get("median", START), T, s, occ,
                   np.random.default_rng(SEED*13 + g*50 + i), broken=broken)
        records.append((cond, sch, rare or ("broken" if broken else None)))
    d = pd.DataFrame(rows); dg = d[d.gen == g]
    msg = f"поколение {g:2d}: записей до {dg.n_records.iloc[0]:3d}"
    for tag in ("median", "model", "same_case"):
        if "gain_" + tag in dg: msg += f" | {tag} {dg['gain_'+tag].median():+5.1f}%"
    print(msg, flush=True)
    d.to_csv(f"fund_seed{SEED}.csv", index=False)

d = pd.DataFrame(rows)
print()
print("выигрыш по размеру фонда:")
d["bucket"] = pd.cut(d.n_records, [0, 20, 60, 100, 140, 200])
print(d.groupby("bucket", observed=True)[["gain_median", "gain_model", "gain_same_case"]].median().round(1).to_string())
print()
print("обычный год против года с редким событием:")
print(d.groupby(d.rare != "none")[["gain_median", "gain_model", "gain_same_case"]].median().round(1).to_string())
print()
print("по видам событий:")
print(d.groupby("rare")[["gain_median", "gain_model", "gain_same_case"]].agg(["median", "size"]).round(1).to_string())
