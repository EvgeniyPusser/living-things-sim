"""Сравнение двух языков записи опыта + мера дырки в фонде."""
import numpy as np, pandas as pd, sys
from life import make_houses
from life2 import weather_year, live_year, tune, WEEKS_YEAR
from language import to_words, from_words, WORDS

GEN, PER_GEN = 8, 20
START = np.full(24, 21.0)
COND = ["UA", "C", "solar", "Qmax", "T_mean", "T_amp", "start_h"]
SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 31

def prep(n, seed):
    h = make_houses(n, np.random.default_rng(seed))
    h["Qmax"] = 1.35*(h["UA"]+h["infil"])*(21.0-(h["T_mean"]-8-h["T_amp"]/2-14))
    return h

def occ_for(b, n):
    hh = np.arange(n) % 24; s = int(b["start_h"])
    return ((hh >= s) & (hh < s + 10)).astype(float)

records = []      # (условия, расписание в градусах, расписание в понятиях)
rows = []
for g in range(1, GEN + 1):
    houses = prep(PER_GEN, SEED*100 + g)
    fund = list(records)
    if fund:
        X = np.array([r[0] for r in fund]); mu, sd = X.mean(0), X.std(0) + 1e-9
        Zf = (X - mu) / sd
        med_deg = np.median(np.array([r[1] for r in fund]), axis=0)
        med_words = np.median(np.array([r[2] for r in fund]), axis=0)
    for i in range(PER_GEN):
        b = houses.iloc[i]; sh = int(b["start_h"])
        r = np.random.default_rng(SEED*1000 + g*50 + i)
        T, s = weather_year(b, r)
        occ = occ_for(b, len(T))
        cond = np.array([b[c] for c in COND], float)
        starts = {"default": START}
        gap = np.nan
        if fund:
            starts["degrees"] = med_deg                       # язык 1: как есть
            starts["words"] = from_words(med_words, sh)       # язык 2: общие понятия
            z = (cond - mu) / sd
            gap = float(np.sqrt(((Zf - z) ** 2).mean(axis=1)).min())   # дырка: до ближайшей записи
        res = {}
        for tag, st in starts.items():
            _, wk = live_year(b, st, T, s, occ, np.random.default_rng(SEED*7 + g*50 + i))
            res[tag] = wk.sum()
        row = dict(gen=g, obj=i, n=len(fund), gap=gap, **res)
        for tag in ("degrees", "words"):
            if tag in res: row["gain_" + tag] = (res["default"] - res[tag]) / res["default"] * 100
        rows.append(row)
        sch = tune(b, starts.get("words", START), T, s, occ,
                   np.random.default_rng(SEED*13 + g*50 + i))
        records.append((cond, sch, to_words(sch, sh)))
    d = pd.DataFrame(rows); dg = d[d.gen == g]
    if g > 1:
        print(f"поколение {g}: записей {dg.n.iloc[0]:3d} | градусы {dg.gain_degrees.median():+5.1f}% "
              f"| общие понятия {dg.gain_words.median():+5.1f}%", flush=True)
    d.to_csv(f"language_seed{SEED}.csv", index=False)

d = pd.DataFrame(rows).dropna(subset=["gap"])
print()
print("итог по всем поколениям:")
print("  градусы        медиана %+5.1f%%, помогло %2.0f%%" % (d.gain_degrees.median(), (d.gain_degrees>0).mean()*100))
print("  общие понятия  медиана %+5.1f%%, помогло %2.0f%%" % (d.gain_words.median(), (d.gain_words>0).mean()*100))
print()
print("зависимость от дырки (расстояние до ближайшей записи фонда):")
d["bucket"] = pd.qcut(d.gap, 4)
print(d.groupby("bucket", observed=True)[["gain_degrees", "gain_words"]].median().round(1).to_string())
