"""Опыт 14. Одно расписание, найденное сразу для всего модельного населения.

Сравнение четырёх способов получить расписание для новичка:
  фонд          медиана сорока решений «каждый для себя»
  лучший из 40  те же сорок, выбран лучший по испытанию
  прямой поиск  одно расписание, искомое сразу для всего населения
  сам           новичок подбирает себе сам, за свою первую зиму

Поиск и испытание идут на СОРОКА МОДЕЛЬНЫХ домах.
Проверка — на ДВУХСТАХ новичках, которых поиск не видел.

Запуск:  python3 run14.py <зерно>
"""
from __future__ import annotations
import numpy as np, pandas as pd, sys, time
from weather import load_all
import sim3
from sim3 import (make_bodies, size_heating, thermal_network, discretise,
                  solar_vertical, occupancy, live, DEFAULT, LO, HI, SUB)

SEED  = int(sys.argv[1]) if len(sys.argv) > 1 else 501
STAGE = sys.argv[2] if len(sys.argv) > 2 else "all"
N_MOD = 40
N_NEW = 200
LIFE  = 400
POP   = 400        # бюджет прямого поиска, тот же
SHORT = 40
WIN_H = 72
YEAR  = 8760
OCT1  = 6552
HOR   = 5112

rng = np.random.default_rng(SEED)          # модельное население
rng_n = np.random.default_rng(SEED + 1000)  # новички, независимо
t0 = time.time()

cities = load_all()
years = []
for c in cities:
    for y in range(c["hours"] // YEAR):
        years.append((c["name"], c["lat"], c, y))
half = len(years) // 2
def assign(n, pool, r=None):
    r = r or rng
    idx = r.permutation(len(pool))
    return [pool[idx[i % len(pool)]] for i in range(n)]

def build_series(ylist):
    n = len(ylist)
    T = np.empty((n, HOR)); Iv = np.empty((n, HOR, 4)); names = []
    for i, (nm, lat, c, y) in enumerate(ylist):
        a, b = y * YEAR, (y + 1) * YEAR
        T[i] = np.roll(c["T_out"][a:b], -OCT1)[:HOR]
        iv = solar_vertical(lat, YEAR, c["HDirNor"][a:b], c["HDifHor"][a:b], c["HGloHor"][a:b])
        Iv[i] = np.roll(iv, -OCT1, axis=0)[:HOR]
        names.append(f"{nm}#{y}")
    return T, Iv, names

def prepare(n, ylist, r=None):
    b = make_bodies(n, r or rng)
    T, Iv, nm = build_series(ylist)
    size_heating(b, T)
    net = thermal_network(b)
    Ad, Bd = discretise(net, 3600.0 / SUB)
    occ = occupancy(b["start_h"], HOR)
    return b, net, Ad, Bd, T, Iv, nm, occ

def masks(T_out):
    n, H = T_out.shape
    kk = np.ones(WIN_H) / WIN_H
    st = np.empty(n, int)
    for i in range(n):
        mv = np.convolve(T_out[i], kk, mode="valid"); mv[:24 * 30] = 1e9
        st[i] = int(np.argmin(mv))
    win = np.zeros((n, H)); pre = np.zeros((n, H)); sc = np.ones((n, H))
    for i in range(n):
        win[i, st[i]:st[i] + WIN_H] = 1.0
        pre[i, :st[i]] = 1.0
        sc[i, st[i]:st[i] + WIN_H] = 0.5
    return win, pre, sc, st

def learn_each(b, net, Ad, Bd, T, Iv, occ, start, budget, sc, win, obj, step0=0.25):
    """Каждый объект ищет себе сам."""
    span = HI - LO
    best = np.clip(np.array(start, float), LO, HI)
    bc = live(b, net, Ad, Bd, best, T, Iv, occ, sc, win, obj)["cost_obj"]
    step = np.full(len(bc), step0)
    for _ in range(budget):
        cand = np.clip(best + np.random.default_rng(_ + 7777).normal(0, 1, best.shape) * step[:, None] * span, LO, HI)
        c = live(b, net, Ad, Bd, cand, T, Iv, occ, sc, win, obj)["cost_obj"]
        bt = c < bc
        best[bt] = cand[bt]; bc = np.where(bt, c, bc)
        step = np.where(bt, step, np.maximum(step * 0.97, 0.02))
    return best

def learn_population(b, net, Ad, Bd, T, Iv, occ, budget, sc, win, step0=0.25):
    """ОДНО расписание, ищется сразу для всего населения.

    Цель — средние градусо-часы ниже нормы в окне события по всему
    населению. Здесь населению разрешено видеть свои аварии: это и есть
    то, за что население платит и что потом отдаёт новичку.
    """
    n = len(T)
    span = HI - LO
    best = DEFAULT.copy()
    def score(s):
        r = live(b, net, Ad, Bd, np.tile(s, (n, 1)), T, Iv, occ, sc, win, win)
        return r["disc_win"].mean()
    bc = score(best); step = step0
    trace = [bc]
    for _ in range(budget):
        cand = np.clip(best + rng.normal(0, 1, 5) * step * span, LO, HI)
        c = score(cand)
        if c < bc: best, bc = cand, c
        else: step = max(step * 0.97, 0.02)
        trace.append(bc)
    return best, bc, np.array(trace)

print(f"опыт 14, зерно {SEED}")
mod_years = assign(N_MOD, years[:half])
new_years = assign(N_NEW, years[half:], rng_n)

b_m, net_m, Ad_m, Bd_m, T_m, Iv_m, nm_m, occ_m = prepare(N_MOD, mod_years)
win_m, pre_m, sc_m, st_m = masks(T_m)

if STAGE == "b":
    sched_each = np.load(f"/home/claude/crisis/w14_each_{SEED}.npy")
    sched_pop  = np.load(f"/home/claude/crisis/w14_pop_{SEED}.npy")
    fund = np.median(sched_each, axis=0)
    print("расписания шага A прочитаны")
else:
    print("модельное население: каждый ищет себе сам...")
    sched_each = learn_each(b_m, net_m, Ad_m, Bd_m, T_m, Iv_m, occ_m,
                            np.tile(DEFAULT, (N_MOD, 1)), LIFE, sc_m, win_m, np.ones_like(win_m))
    fund = np.median(sched_each, axis=0)
    print(f"  {time.time()-t0:.0f} с")
    print("модельное население: одно расписание сразу для всех...")
    sched_pop, pop_cost, trace = learn_population(b_m, net_m, Ad_m, Bd_m, T_m, Iv_m, occ_m,
                                                  POP, sc_m, win_m)
    print(f"  {time.time()-t0:.0f} с; на модельном населении {trace[0]:.1f} -> {pop_cost:.1f}")

np.save(f"/home/claude/crisis/w14_each_{SEED}.npy", sched_each)
np.save(f"/home/claude/crisis/w14_pop_{SEED}.npy", sched_pop)
if STAGE == "a":
    print(f"шаг A готов, {time.time()-t0:.0f} с. Дальше: python3 run14.py {SEED} b")
    sys.exit(0)

b_n, net_n, Ad_n, Bd_n, T_n, Iv_n, nm_n, occ_n = prepare(N_NEW, new_years, rng_n)
win_n, pre_n, sc_n, st_n = masks(T_n)
ev = lambda s: live(b_n, net_n, Ad_n, Bd_n, s, T_n, Iv_n, occ_n, sc_n, win_n, pre_n)

print("новички: сам, короткая подстройка...")
s_self = learn_each(b_n, net_n, Ad_n, Bd_n, T_n, Iv_n, occ_n,
                    np.tile(DEFAULT, (N_NEW, 1)), SHORT, sc_n, win_n, pre_n)
d_self = ev(s_self)["disc_win"]

print("новички: все сорок расписаний по очереди...")
pair = np.empty((N_MOD, N_NEW))
for j in range(N_MOD):
    pair[j] = ev(np.tile(sched_each[j], (N_NEW, 1)))["disc_win"]

d_fund = ev(np.tile(fund, (N_NEW, 1)))["disc_win"]
d_pop  = ev(np.tile(sched_pop, (N_NEW, 1)))["disc_win"]

# лучший из сорока — отобранный ПО МОДЕЛЬНОМУ НАСЕЛЕНИЮ, не по новичкам
r_mod = live(b_m, net_m, Ad_m, Bd_m, sched_each, T_m, Iv_m, occ_m, sc_m, win_m, win_m)
# каждое расписание испытываем на всём модельном населении
trial = np.empty(N_MOD)
for j in range(N_MOD):
    trial[j] = live(b_m, net_m, Ad_m, Bd_m, np.tile(sched_each[j], (N_MOD, 1)),
                    T_m, Iv_m, occ_m, sc_m, win_m, win_m)["disc_win"].mean()
pick = int(trial.argmin())
d_best = pair[pick]
d_ceil = pair.min(axis=0)

print("\n" + "=" * 70)
print(f"ОПЫТ 14, зерно {SEED}. Градусо-часы ниже 21 °C в окне аварии, {N_NEW} новичков.")
print("=" * 70)
print(f'{"":38s}{"медиана":>9s}{"среднее":>9s}{"худший":>9s}{"лучше «сам»":>13s}')
rows = [("сам, своя подстройка", d_self),
        ("случайное из сорока", pair[rng.integers(0, N_MOD, N_NEW), np.arange(N_NEW)]),
        ("фонд: медиана сорока", d_fund),
        (f"лучшее из сорока по испытанию (№{pick})", d_best),
        ("прямой поиск для всего населения", d_pop),
        ("— лучший возможный из сорока", d_ceil)]
for nm, v in rows:
    print(f"{nm:38s}{np.median(v):9.1f}{v.mean():9.1f}{v.max():9.1f}"
          f"{100*(v<d_self-1e-6).mean():12.0f}%")

print("\nпрямой поиск против остальных, доля новичков:")
for nm, v in [("фонда", d_fund), ("лучшего из сорока", d_best), ("«сам»", d_self)]:
    print(f"  лучше {nm:22s} у {100*(d_pop<v-1e-6).mean():3.0f}%")

print("\nчто нашёл прямой поиск, против типовых настроек:")
names = ["держать днём", "ночью до", "греть заранее", "зона", "коэффициент"]
for i, n in enumerate(names):
    print(f"  {n:16s} {DEFAULT[i]:6.2f} -> {sched_pop[i]:6.2f}   (фонд {fund[i]:6.2f})")

pd.DataFrame({"city": nm_n, "d_self": d_self, "d_fund": d_fund,
              "d_best": d_best, "d_pop": d_pop, "d_ceil": d_ceil}
             ).to_csv(f"/home/claude/crisis/res14_{SEED}.csv", index=False)
np.save(f"/home/claude/crisis/sched_pop_{SEED}.npy", sched_pop)
print(f"\nзаписано res14_{SEED}.csv, всего {time.time()-t0:.0f} с")
