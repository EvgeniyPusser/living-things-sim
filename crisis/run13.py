"""Опыт 13. Отбор предка по стойкости тела против отбора по похожести.

Условия объявлены в УСЛОВИЯ.md до этого прогона.

Запуск:  python3 run13.py <зерно>
"""
from __future__ import annotations
import numpy as np, pandas as pd, sys, time
from weather import load_all
import sim3
from sim3 import (make_bodies, size_heating, thermal_network, discretise,
                  solar_vertical, occupancy, live, DEFAULT, LO, HI, SUB, COMFORT)

SEED  = int(sys.argv[1]) if len(sys.argv) > 1 else 501
N_ANC = 40
N_NEW = 200
LIFE  = 400
SHORT = 40
WIN_H = 72
YEAR  = 8760
OCT1  = 6552
HOR   = 5112

rng = np.random.default_rng(SEED)
t0 = time.time()

# ------------------------------------------------------------------ погода
cities = load_all()
years = []
for c in cities:
    for y in range(c["hours"] // YEAR):
        years.append((c["name"], c["lat"], c, y))
half = len(years) // 2
def assign(n, pool):
    idx = rng.permutation(len(pool))
    return [pool[idx[i % len(pool)]] for i in range(n)]
anc_years = assign(N_ANC, years[:half])
new_years = assign(N_NEW, years[half:])

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

def prepare(n, ylist):
    b = make_bodies(n, rng)
    T, Iv, nm = build_series(ylist)
    size_heating(b, T)
    net = thermal_network(b)
    Ad, Bd = discretise(net, 3600.0 / SUB)
    occ = occupancy(b["start_h"], HOR)
    return b, net, Ad, Bd, T, Iv, nm, occ

# ------------------------------------------- ПРИЗНАК: стандартная проба
def resilience(b, net, T_ext=-10.0, T0=21.0, hours=72):
    """Температура воздуха через 72 часа без отопления при −10 снаружи.

    Свойство ТЕЛА: расписание не участвует. Оболочка и перекрытия ставятся
    в установившееся состояние натопленного дома, как перед аварией.

    Почему не «часы до 19 °C»: воздуха в доме мало, он проваливается
    за первый час, и такая проба мерила бы воздух, а не дом. Через 72 часа
    видно уже поведение всей массы. Проверено: связь этого числа
    с постоянной времени здания (C_полная / UA) равна 0.97.
    """
    n = len(net["C_air"])
    Ad, Bd = discretise(net, 3600.0)
    fe = net["ua_env"] / (net["h_env"] + net["ua_env"])
    T = np.empty((n, 3))
    T[:, 0] = T0; T[:, 1] = T0 + (T_ext - T0) * fe; T[:, 2] = T0
    for k in range(hours):
        w = np.stack([net["ua_win"] * T_ext, net["ua_env"] * T_ext, np.zeros(n)], axis=1)
        T = np.einsum("nij,nj->ni", Ad, T) + np.einsum("nij,nj->ni", Bd, w)
    return T[:, 0]

# ------------------------------------------------------------------ окна
def cold_window(T_out):
    kk = np.ones(WIN_H) / WIN_H
    st = np.empty(len(T_out), int)
    for i in range(len(T_out)):
        mv = np.convolve(T_out[i], kk, mode="valid")
        mv[:24 * 30] = 1e9
        st[i] = int(np.argmin(mv))
    return st

def masks(T_out):
    n, H = T_out.shape
    st = cold_window(T_out)
    win = np.zeros((n, H)); pre = np.zeros((n, H)); sc = np.ones((n, H))
    for i in range(n):
        win[i, st[i]:st[i] + WIN_H] = 1.0
        pre[i, :st[i]] = 1.0
        sc[i, st[i]:st[i] + WIN_H] = 0.5       # беда на морозе, как в опыте 12
    return win, pre, sc, st

# ------------------------------------------------------------------ поиск
def learn(b, net, Ad, Bd, T, Iv, occ, start, budget, sc, win, obj, step0=0.25):
    span = HI - LO
    best = np.clip(np.array(start, float), LO, HI)
    bc = live(b, net, Ad, Bd, best, T, Iv, occ, sc, win, obj)["cost_obj"]
    step = np.full(len(bc), step0)
    for k in range(budget):
        cand = np.clip(best + rng.normal(0, 1, best.shape) * step[:, None] * span, LO, HI)
        c = live(b, net, Ad, Bd, cand, T, Iv, occ, sc, win, obj)["cost_obj"]
        better = c < bc
        best[better] = cand[better]
        bc = np.where(better, c, bc)
        step = np.where(better, step, np.maximum(step * 0.97, 0.02))
    return best

print(f"опыт 13, зерно {SEED}, городо-лет {len(years)}")

b_a, net_a, Ad_a, Bd_a, T_a, Iv_a, nm_a, occ_a = prepare(N_ANC, anc_years)
win_a, pre_a, sc_a, st_a = masks(T_a)
print("предки живут свой год...")
sched_anc = learn(b_a, net_a, Ad_a, Bd_a, T_a, Iv_a, occ_a,
                  np.tile(DEFAULT, (N_ANC, 1)), LIFE, sc_a, win_a, np.ones_like(win_a))
fund = np.median(sched_anc, axis=0)
print(f"  готово, {time.time()-t0:.0f} с")

b_n, net_n, Ad_n, Bd_n, T_n, Iv_n, nm_n, occ_n = prepare(N_NEW, new_years)
win_n, pre_n, sc_n, st_n = masks(T_n)

tau_a = resilience(b_a, net_a)
tau_n = resilience(b_n, net_n)
print(f"\nстойкость: температура через 72 ч без отопления при −10 снаружи:")
print(f"  предки:  от {tau_a.min():.1f} до {tau_a.max():.1f} °C, медиана {np.median(tau_a):.1f}")
print(f"  новички: от {tau_n.min():.1f} до {tau_n.max():.1f} °C, медиана {np.median(tau_n):.1f}")

# расстояние по десяти свойствам тела — старая мера
FEATS = ["UExt", "URoof", "UFloor", "UWin", "fAWin", "ach", "cap_wall",
         "cap_int", "A_floor", "Qmax"]
def zmat(b, ref):
    cols = []
    for f in FEATS:
        x = np.asarray(b[f], float); r = np.asarray(ref[f], float)
        cols.append((x - r.mean()) / (r.std() + 1e-9))
    return np.stack(cols, axis=1)
Za, Zn = zmat(b_a, b_a), zmat(b_n, b_a)
dist_body = np.sqrt(((Zn[:, None, :] - Za[None, :, :]) ** 2).mean(axis=2))   # [N_NEW, N_ANC]
dist_tau = np.abs(tau_n[:, None] - tau_a[None, :])

def evaluate(sched):
    return live(b_n, net_n, Ad_n, Bd_n, sched, T_n, Iv_n, occ_n, sc_n, win_n, pre_n)

print("\nусловие 0: сам, короткая подстройка...")
s0 = learn(b_n, net_n, Ad_n, Bd_n, T_n, Iv_n, occ_n,
           np.tile(DEFAULT, (N_NEW, 1)), SHORT, sc_n, win_n, pre_n)
r0 = evaluate(s0)

print("все пары предок-новичок...")
pair = np.empty((N_ANC, N_NEW))
for j in range(N_ANC):
    pair[j] = evaluate(np.tile(sched_anc[j], (N_NEW, 1)))["disc_win"]

pick_rand = rng.integers(0, N_ANC, N_NEW)
pick_body = dist_body.argmin(axis=1)
pick_tau  = dist_tau.argmin(axis=1)
d1 = pair[pick_rand, np.arange(N_NEW)]
d2 = pair[pick_body, np.arange(N_NEW)]
d3 = pair[pick_tau,  np.arange(N_NEW)]

print("условие 4: фонд...")
r4 = evaluate(np.tile(fund, (N_NEW, 1)))
d4 = r4["disc_win"]
d0 = r0["disc_win"]
best_pair = pair.min(axis=0)          # потолок: лучший возможный предок

print("\n" + "=" * 70)
print(f"ОПЫТ 13, зерно {SEED}. Градусо-часы ниже 21 °C в окне аварии.")
print("=" * 70)
print(f'{"":34s}{"медиана":>9s}{"среднее":>9s}{"худший":>9s}{"лучше «сам»":>13s}')
for nm, v in [("0 сам, своя подстройка", d0),
              ("1 случайный предок", d1),
              ("2 ближайший по свойствам тела", d2),
              ("3 ближайший по стойкости", d3),
              ("4 фонд по всем", d4),
              ("— лучший возможный предок", best_pair)]:
    sh = 100 * (v < d0 - 1e-6).mean()
    print(f"{nm:34s}{np.median(v):9.1f}{v.mean():9.1f}{v.max():9.1f}{sh:12.0f}%")

print("\nпрямые сравнения, доля новичков:")
def cmp(a, b, na, nb):
    print(f"  {na:28s} лучше {nb:26s} у {100*(a<b-1e-6).mean():3.0f}%")
cmp(d3, d1, "3 по стойкости", "1 случайного")
cmp(d3, d2, "3 по стойкости", "2 по свойствам тела")
cmp(d2, d1, "2 по свойствам тела", "1 случайного")
cmp(d3, d4, "3 по стойкости", "4 фонда")
cmp(d4, d1, "4 фонд", "1 случайного")

print("\nсвязь признака с пользой переноса:")
# ВНИМАНИЕ: dist_* имеют форму [новичок, предок], а pair — [предок, новичок].
# Разворачивать надо ОДИНАКОВО, иначе пары перемешиваются и связь
# получается от случайного сопоставления. Раньше здесь была эта ошибка.
gain = (d0[None, :] - pair).T            # -> [новичок, предок], как dist_*
for nm, dd in [("расстояние по свойствам тела", dist_body), ("разница стойкости", dist_tau)]:
    assert dd.shape == gain.shape, "оси не совпадают"
    r = np.corrcoef(dd.ravel(), gain.ravel())[0, 1]
    print(f"  {nm:30s} связь с выигрышем {r:+.3f}  ({dd.size} пар)")
print(f"  связь стойкости новичка с тем, сколько он потерял сам: "
      f"{np.corrcoef(tau_n, d0)[0,1]:+.3f}")

pd.DataFrame({"city": nm_n, "tau": tau_n, "d_alone": d0, "d_rand": d1,
              "d_body": d2, "d_tau": d3, "d_fund": d4, "d_best": best_pair,
              "Qmax_kW": b_n["Qmax"] / 1000, "A_floor": b_n["A_floor"]}
             ).to_csv(f"/home/claude/crisis/res13_{SEED}.csv", index=False)
np.save(f"/home/claude/crisis/pair13_{SEED}.npy", pair)
print(f"\nзаписано res13_{SEED}.csv, всего {time.time()-t0:.0f} с")
