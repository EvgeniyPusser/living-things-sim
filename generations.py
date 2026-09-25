"""Поколения: растёт ли ценность фонда, когда в него добавляют новые поколения.

Поколение 1: объекты начинают с типовых настроек, живут два года,
             в конце подбирают расписание на своей модели (по своему журналу)
             и кладут его в фонд.
Поколение k: новые объекты (другие тела, другая погода) начинают с фонда
             поколения k-1, живут, дополняют фонд.

Мерим потери первого года в каждом поколении.
"""
import numpy as np, pandas as pd, sys
from life import make_houses, weather_years, live, live_week, WEEKS_YEAR

GEN, PER_GEN, YEARS = 6, 8, 2
START = np.full(24, 21.0)
SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 3

def occ_for(b, n):
    h = np.arange(n) % 24; s = int(b["start_h"])
    return ((h >= s) & (h < s + 10)).astype(float)

def year_cost(b, sch, T, s, occ):
    tot, Tm = 0.0, 21.0
    for w in range(WEEKS_YEAR):
        sl = slice(w*168, (w+1)*168)
        c, Tm = live_week(b, sch, T[sl], s[sl], occ[sl], Tm); tot += c
    return tot

def tune_on_own_log(b, start, T, s, occ, rng, tries=80):
    """Подбор на собственной модели по прожитому году: то, что объект может
    сделать к концу жизни, имея свой журнал."""
    best, bc = np.clip(np.array(start, float), 12, 24), year_cost(b, start, T, s, occ)
    for _ in range(tries):
        c = best.copy(); idx = rng.integers(0, 24, rng.integers(1, 6))
        c[idx] = np.clip(c[idx] + rng.normal(0, 2.0, len(idx)), 12, 24)
        v = year_cost(b, c, T, s, occ)
        if v < bc: best, bc = c, v
    return best

rows, fund = [], []
rng = np.random.default_rng(SEED)
for g in range(1, GEN + 1):
    houses = make_houses(PER_GEN, np.random.default_rng(SEED * 100 + g))
    houses["Qmax"] = 1.35*(houses["UA"]+houses["infil"])*(21.0-(houses["T_mean"]-8-houses["T_amp"]/2-14))
    start = START if not fund else np.median(np.vstack(fund), axis=0)
    y1s = []
    for i in range(PER_GEN):
        b = houses.iloc[i]
        T, s = weather_years(b, YEARS, np.random.default_rng(SEED*1000 + g*50 + i))
        occ = occ_for(b, len(T))
        _, wk = live(b, T, s, occ, start, YEARS, np.random.default_rng(SEED*2000 + g*50 + i))
        y1 = wk[:WEEKS_YEAR].sum(); y1s.append(y1)
        # то же тело с типовых настроек — точка отсчёта этого поколения
        _, wk0 = live(b, T, s, occ, START, YEARS, np.random.default_rng(SEED*2000 + g*50 + i))
        base = wk0[:WEEKS_YEAR].sum()
        rows.append(dict(gen=g, house=i, y1_fund=y1, y1_default=base,
                         gain=(base - y1) / base * 100))
        # прожив жизнь, объект подбирает расписание на своём журнале и кладёт в фонд
        fund.append(tune_on_own_log(b, start, T[:WEEKS_YEAR*168], s[:WEEKS_YEAR*168],
                                    occ[:WEEKS_YEAR*168], np.random.default_rng(SEED*3000+g*50+i)))
    d = pd.DataFrame(rows); dg = d[d.gen == g]
    print(f"поколение {g}: в фонде {len(fund)-PER_GEN:3d} записей до, "
          f"выигрыш первого года медиана {dg.gain.median():+5.1f}%, "
          f"помогло {(dg.gain>0).mean()*100:3.0f}% объектов", flush=True)

d = pd.DataFrame(rows); d.to_csv(f"generations_seed{SEED}.csv", index=False)
print()
print(d.groupby("gen").gain.agg(["median", "mean", lambda x: (x > 0).mean()*100]).round(1)
      .rename(columns={"<lambda_0>": "помогло %"}).to_string())
