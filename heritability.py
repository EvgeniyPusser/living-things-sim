"""Наследуемость: предсказывает ли качество предка качество потомка.

Наклон прямой «насколько хорош предок → насколько выиграл потомок»
это и есть аналог коэффициента наследуемости из популяционной генетики.
Наклон около нуля означает: передаётся что угодно, только не качество.
"""
import numpy as np, pandas as pd, sys
from life import make_houses
from life2 import weather_year, live_year, year_cost, tune, WEEKS_YEAR

N_ANC, N_OFF = 12, 5          # предков и потомков на каждого
START = np.full(24, 21.0)
SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 41

def prep(n, seed):
    h = make_houses(n, np.random.default_rng(seed))
    h["Qmax"] = 1.35*(h["UA"]+h["infil"])*(21.0-(h["T_mean"]-8-h["T_amp"]/2-14))
    return h

def occ_for(b, n):
    hh = np.arange(n) % 24; s = int(b["start_h"])
    return ((hh >= s) & (hh < s + 10)).astype(float)

anc = prep(N_ANC, SEED)
records = []
for i in range(N_ANC):
    b = anc.iloc[i]
    T, s = weather_year(b, np.random.default_rng(SEED*10 + i))
    occ = occ_for(b, len(T))
    base = year_cost(b, START, T, s, occ)
    sch = tune(b, START, T, s, occ, np.random.default_rng(SEED*20 + i), tries=80)
    q = (base - year_cost(b, sch, T, s, occ)) / base * 100      # качество предка, %
    records.append((sch, q))
    print(f"предок {i:2d}: улучшил себя на {q:5.1f}%", flush=True)

pool = np.median(np.array([r[0] for r in records]), axis=0)
rows = []
off = prep(N_ANC * N_OFF, SEED + 777)
for k in range(len(off)):
    b = off.iloc[k]; i = k % N_ANC
    T, s = weather_year(b, np.random.default_rng(SEED*100 + k))
    occ = occ_for(b, len(T))
    _, w0 = live_year(b, START, T, s, occ, np.random.default_rng(SEED*3 + k))
    _, w1 = live_year(b, records[i][0], T, s, occ, np.random.default_rng(SEED*3 + k))
    _, w2 = live_year(b, pool, T, s, occ, np.random.default_rng(SEED*3 + k))
    rows.append(dict(anc=i, anc_quality=records[i][1],
                     gain_anc=(w0.sum()-w1.sum())/w0.sum()*100,
                     gain_pool=(w0.sum()-w2.sum())/w0.sum()*100))
d = pd.DataFrame(rows); d.to_csv(f"heritability_seed{SEED}.csv", index=False)
a, b0 = np.polyfit(d.anc_quality, d.gain_anc, 1)
print()
print("потомков: %d" % len(d))
print("качество предка:   среднее %.1f%%, разброс %.1f" % (d.anc_quality.mean(), d.anc_quality.std()))
print("выигрыш потомка от предка: медиана %+.1f%%, помог %.0f%%" % (d.gain_anc.median(), (d.gain_anc>0).mean()*100))
print("выигрыш потомка от фонда:  медиана %+.1f%%, помог %.0f%%" % (d.gain_pool.median(), (d.gain_pool>0).mean()*100))
print()
print("наследуемость качества: наклон %.3f, корреляция %.2f" % (a, d.anc_quality.corr(d.gain_anc)))
print("(наклон 1.0 значило бы: каждый процент, выигранный предком, переходит потомку)")
