"""Первый год без повторов: свой опыт против унаследованного."""
import numpy as np, pandas as pd, sys
from life import (make_houses, occupancy, weather_years, live, DEFAULT, WEEKS_YEAR, HOURS_WEEK)

N, YEARS_ANC, YEARS_NEW = 10, 3, 2
START = None  # задаётся ниже
SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 11
import numpy as _np
START = _np.full(24, 21.0)   # комфортно, но расточительно: учиться = найти ночное снижение
rng = np.random.default_rng(SEED)
houses = make_houses(N, rng)
# мощности хватает, чтобы держать комфорт в самый холодный час: иначе расписание ни при чём
houses["Qmax"] = 1.35 * (houses["UA"] + houses["infil"]) * (21.0 - (houses["T_mean"] - 8 - houses["T_amp"]/2 - 14))

def occ_for(body, n):
    h = np.arange(n) % 24
    s = int(body["start_h"])
    return ((h >= s) & (h < s + 10)).astype(float)

# 1. предки: живут три года сами, каждый в своей погоде
learned = []
for i in range(N):
    b = houses.iloc[i]
    T, s = weather_years(b, YEARS_ANC, np.random.default_rng(SEED * 10 + i))
    sch, wk = live(b, T, s, occ_for(b, len(T)), START, YEARS_ANC,
                   np.random.default_rng(SEED * 20 + i))
    learned.append(sch)
    print(f"предок {i}: годы {wk[:52].sum():8.0f} {wk[52:104].sum():8.0f} {wk[104:].sum():8.0f}", flush=True)
pool = np.mean(learned, axis=0)

# 2. новички: те же дома, но другая погода и только два года жизни
rows = []
for j in range(N):
    b = houses.iloc[j]
    T, s = weather_years(b, YEARS_NEW, np.random.default_rng(SEED * 30 + j))
    occ = occ_for(b, len(T))
    def run(start, tag, seed):
        _, wk = live(b, T, s, occ, start, YEARS_NEW, np.random.default_rng(seed))
        return {tag + "_y1": wk[:WEEKS_YEAR].sum(), tag + "_y2": wk[WEEKS_YEAR:].sum()}
    r = dict(house=j)
    r.update(run(START, "alone", SEED * 40 + j))
    anc = learned[(j + 3) % N]                      # предок — другой дом
    r.update(run(anc, "ancestor", SEED * 40 + j))   # та же погода и те же пробы
    r.update(run(pool, "pool", SEED * 40 + j))
    rows.append(r)
    print(f"дом {j}: один {r['alone_y1']:8.0f}/{r['alone_y2']:8.0f}  "
          f"предок {r['ancestor_y1']:8.0f}/{r['ancestor_y2']:8.0f}  "
          f"фонд {r['pool_y1']:8.0f}/{r['pool_y2']:8.0f}", flush=True)

d = pd.DataFrame(rows); d.to_csv(f"life_seed{SEED}.csv", index=False)
print()
for tag in ["ancestor", "pool"]:
    for y in ["y1", "y2"]:
        g = (d["alone_" + y] - d[tag + "_" + y]) / d["alone_" + y] * 100
        print("%-9s %s: экономия против одиночки, медиана %+5.1f%%, помогло %2.0f%% домов"
              % (tag, y, g.median(), (g > 0).mean() * 100))
tot_a = (d.alone_y1 + d.alone_y2); tot_p = (d.pool_y1 + d.pool_y2)
print("\nза два года вместе: фонд против одиночки, медиана %+.1f%%" %
      (((tot_a - tot_p) / tot_a * 100).median()))
