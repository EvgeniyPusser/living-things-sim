"""Один проход жизни: чему новичок может научиться сам и что даёт наследство.

Предок: прожил годы, накопил журнал, подобрал расписание на своей модели
        (300 прогонов года по собственной погоде — то, что можно делать на двойнике).
Новичок: живёт один раз. Учится только недельными пробами, без повторов.
"""
import numpy as np, pandas as pd, sys
from life import make_houses, weather_years, live, live_week, WEEKS_YEAR

N, SEED = 10, int(sys.argv[1]) if len(sys.argv) > 1 else 11
START = np.full(24, 21.0)
rng = np.random.default_rng(SEED)
houses = make_houses(N, rng)
houses["Qmax"] = 1.35 * (houses["UA"] + houses["infil"]) * (21.0 - (houses["T_mean"] - 8 - houses["T_amp"]/2 - 14))

def occ_for(b, n):
    h = np.arange(n) % 24; s = int(b["start_h"])
    return ((h >= s) & (h < s + 10)).astype(float)

def year_cost(b, sch, T, s, occ):
    tot, Tm = 0.0, 21.0
    for w in range(WEEKS_YEAR):
        sl = slice(w*168, (w+1)*168)
        c, Tm = live_week(b, sch, T[sl], s[sl], occ[sl], Tm); tot += c
    return tot

# 1. Предки: подбор на собственной модели по своей прожитой погоде
learned = []
for i in range(N):
    b = houses.iloc[i]
    T, s = weather_years(b, 1, np.random.default_rng(SEED*10 + i)); occ = occ_for(b, len(T))
    best, bc = START.copy(), year_cost(b, START, T, s, occ)
    r = np.random.default_rng(SEED*20 + i)
    for _ in range(300):
        c = best.copy(); idx = r.integers(0, 24, r.integers(1, 6))
        c[idx] = np.clip(c[idx] + r.normal(0, 2.0, len(idx)), 12, 24)
        v = year_cost(b, c, T, s, occ)
        if v < bc: best, bc = c, v
    learned.append(best)
    print(f"предок {i}: подбор на модели дал {(1-bc/year_cost(b,START,T,s,occ))*100:4.1f}% экономии", flush=True)
pool = np.median(learned, axis=0)

# 2. Новички: другая погода, один проход, только недельные пробы
rows = []
for j in range(N):
    b = houses.iloc[j]
    T, s = weather_years(b, 2, np.random.default_rng(SEED*30 + j)); occ = occ_for(b, len(T))
    def run(start, seed):
        _, wk = live(b, T, s, occ, start, 2, np.random.default_rng(seed))
        return wk[:WEEKS_YEAR].sum(), wk[WEEKS_YEAR:].sum()
    a1, a2 = run(START, SEED*40 + j)
    n1, n2 = run(learned[(j+3) % N], SEED*40 + j)
    p1, p2 = run(pool, SEED*40 + j)
    rows.append(dict(house=j, alone_y1=a1, alone_y2=a2, ancestor_y1=n1, ancestor_y2=n2,
                     pool_y1=p1, pool_y2=p2))
    print(f"дом {j}: один {a1:8.0f}/{a2:8.0f}  предок {n1:8.0f}/{n2:8.0f}  фонд {p1:8.0f}/{p2:8.0f}", flush=True)

d = pd.DataFrame(rows); d.to_csv(f"life2_seed{SEED}.csv", index=False)
print()
for tag in ["ancestor", "pool"]:
    for y in ["y1", "y2"]:
        g = (d["alone_"+y] - d[tag+"_"+y]) / d["alone_"+y] * 100
        print("%-9s %s: экономия против одиночки, медиана %+5.1f%%, помогло %2.0f%% домов"
              % (tag, y, g.median(), (g > 0).mean()*100))
ta, tp = d.alone_y1+d.alone_y2, d.pool_y1+d.pool_y2
print("\nза два года: фонд против одиночки, медиана %+.1f%%" % (((ta-tp)/ta*100).median()))
