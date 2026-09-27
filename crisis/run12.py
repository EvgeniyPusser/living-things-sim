"""Опыт 12. Наследование поведения в кризисе, настоящая погода, большая выборка.

Условия объявлены в УСЛОВИЯ.md до этого прогона.

Запуск:  python3 run12.py <вид> <зерно>
   вид = cold | fail | calm
"""
from __future__ import annotations
import numpy as np, pandas as pd, sys, time
from weather import load_all
import sim3
from sim3 import (make_bodies, size_heating, thermal_network, discretise,
                 solar_vertical, occupancy, live, DEFAULT, LO, HI, SUB,
                 COMFORT, capacity_factor)

MODE = sys.argv[1] if len(sys.argv) > 1 else "cold"
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 101
if len(sys.argv) > 3 and sys.argv[3] == "noderate":
    sim3.HP_DERATE = False
TAG = f"{MODE}_{SEED}" + ("" if sim3.HP_DERATE else "_noderate")

N_ANC = 40          # предшественники
N_NEW = 300         # новички
LIFE  = 400         # бюджет поиска на всю жизнь предка
SHORT = 40          # короткая подстройка новичка
WIN_H = 72          # длина окна события, часов
YEAR  = 8760
# Считаем отопительный сезон, а не календарный год: дом сдают осенью
# и он встречает первую зиму. Ряд сдвигаем так, чтобы час 0 = 1 октября.
OCT1  = 6552
HOR   = 5112        # 1 октября .. 30 апреля, 213 суток

rng = np.random.default_rng(SEED)
t0 = time.time()

# ------------------------------------------------------------------ погода
cities = load_all()
years = []            # (имя города, широта, срез года)
for c in cities:
    ny = c["hours"] // YEAR
    for y in range(ny):
        years.append((c["name"], c["lat"], c, y))
print(f"городо-лет доступно: {len(years)}")

def assign(n, pool, rng):
    """Каждому объекту свой год. Разные объекты — по возможности разные годы."""
    idx = rng.permutation(len(pool))
    return [pool[idx[i % len(pool)]] for i in range(n)]

# предки и новички берут годы из РАЗНЫХ половин списка,
# чтобы кризис новичка не был кризисом предка
half = len(years) // 2
pool_anc = years[:half]
pool_new = years[half:]
anc_years = assign(N_ANC, pool_anc, rng)
new_years = assign(N_NEW, pool_new, rng)

def build_series(ylist):
    n = len(ylist)
    T = np.empty((n, HOR)); Iv = np.empty((n, HOR, 4))
    names = []
    for i, (nm, lat, c, y) in enumerate(ylist):
        a, b = y * YEAR, (y + 1) * YEAR
        rot = lambda x: np.roll(x[a:b], -OCT1)[:HOR]
        T[i] = rot(c["T_out"])
        iv = solar_vertical(lat, YEAR, c["HDirNor"][a:b],
                            c["HDifHor"][a:b], c["HGloHor"][a:b])
        Iv[i] = np.roll(iv, -OCT1, axis=0)[:HOR]
        names.append(f"{nm}#{y}")
    return T, Iv, names

def prepare(n, ylist, rng):
    """Тела, мощность по своей записи, сеть, точный переход, погода, занятость."""
    b = make_bodies(n, rng)
    T, Iv, nm = build_series(ylist)
    size_heating(b, T)
    net = thermal_network(b)
    Ad, Bd = discretise(net, 3600.0 / SUB)
    occ = occupancy(b["start_h"], HOR)
    return b, net, Ad, Bd, T, Iv, nm, occ

# ------------------------------------------------------------------ события
def cold_window(T_out):
    """Самое холодное окно из WIN_H часов. Находится в данных."""
    k = np.ones(WIN_H) / WIN_H
    n = T_out.shape[0]
    start = np.empty(n, int)
    for i in range(n):
        mv = np.convolve(T_out[i], k, mode="valid")
        mv[:24 * 30] = 1e9          # первый месяц дому на обживание
        start[i] = int(np.argmin(mv))
    return start

def fail_window(n, rng):
    """Отказ вдвое: случайный час сезона, не в первый месяц и не в конце.

    Первый месяц оставляем дому, чтобы у него было на чём подстроиться.
    """
    return rng.integers(24 * 30, HOR - WIN_H, n)

def calm_window(T_out):
    """Обычное зимнее окно: серединное по холоду, не самое холодное.

    Это контроль. Если в нём условия так же расходятся, как в кризисе,
    значит расходятся они не из-за кризиса.
    """
    k = np.ones(WIN_H) / WIN_H
    n = T_out.shape[0]
    st = np.empty(n, int)
    for i in range(n):
        mv = np.convolve(T_out[i], k, mode="valid")
        cand = np.arange(24 * 30, len(mv))
        st[i] = int(cand[np.argsort(mv[cand])[len(cand) // 2]])
    return st

def make_masks(T_out, mode, rng):
    n, H = T_out.shape
    if mode == "cold":
        st = cold_window(T_out)
    elif mode == "fail":
        st = fail_window(n, rng)
    elif mode == "both":
        st = cold_window(T_out)      # отказ ИМЕННО в самый мороз
    else:
        st = calm_window(T_out)
    win = np.zeros((n, H)); pre = np.zeros((n, H)); scale = np.ones((n, H))
    for i in range(n):
        win[i, st[i]:st[i] + WIN_H] = 1.0
        pre[i, :st[i]] = 1.0
        if mode in ("fail", "both"):
            scale[i, st[i]:st[i] + WIN_H] = 0.5
    return win, pre, scale, st


# ------------------------------------------------- величины от получателя
def ua_eff(net):
    """Сквозная проводимость дома наружу, Вт/К."""
    return 1.0 / (1.0 / net["h_env"] + 1.0 / net["ua_env"]) + net["ua_win"]

def tau_hours(net):
    """Тепловая инерция быстрой части дома, часы."""
    return (net["C_air"] + net["C_int"]) / ua_eff(net) / 3600.0

def to_z(sched, b, net):
    """Сырое расписание -> величины, отсчитанные от самого дома."""
    T_occ, T_away, pre, band, gain = (sched[:, i] for i in range(5))
    U, tau = ua_eff(net), tau_hours(net)
    return np.stack([T_occ - COMFORT,
                     T_occ - T_away,
                     pre / tau,
                     band,
                     gain * b["Qmax"] / (U * np.maximum(band, 1e-6))], axis=1)

def from_z(z, b, net):
    """Обратно: величины получателя -> сырое расписание ЭТОГО дома."""
    U, tau = ua_eff(net), tau_hours(net)
    T_occ = COMFORT + z[:, 0]
    T_away = T_occ - z[:, 1]
    band = z[:, 3]
    gain = z[:, 4] * U * np.maximum(band, 1e-6) / b["Qmax"]
    pre = z[:, 2] * tau
    return np.clip(np.stack([T_occ, T_away, pre, band, gain], axis=1), LO, HI)

# ------------------------------------------------------------------ поиск
def learn(b, net, Ad, Bd, T_out, Iv, occ, start, budget, rng,
          scale=None, win=None, obj=None, step0=0.25):
    """Локальный поиск. Все дома учатся одновременно, каждый свой.

    Целевая функция — cost_obj: только те часы, которые дому видны.
    """
    span = HI - LO
    best = np.clip(np.array(start, float), LO, HI)
    r = live(b, net, Ad, Bd, best, T_out, Iv, occ, scale, win, obj)
    bc = r["cost_obj"]
    step = np.full(len(bc), step0)
    for k in range(budget):
        cand = np.clip(best + rng.normal(0, 1, best.shape) * step[:, None] * span, LO, HI)
        r = live(b, net, Ad, Bd, cand, T_out, Iv, occ, scale, win, obj)
        c = r["cost_obj"]
        better = c < bc
        best[better] = cand[better]
        bc = np.where(better, c, bc)
        step = np.where(better, step, np.maximum(step * 0.97, 0.02))
    return best, bc

# ------------------------------------------------------------------ предки
print(f"\nвид события: {MODE}, зерно {SEED}, "
      f"падение мощности на морозе: {'да' if sim3.HP_DERATE else 'нет'}")
b_anc, net_anc, Ad_a, Bd_a, T_a, Iv_a, nm_a, occ_a = prepare(N_ANC, anc_years, rng)
win_a, pre_a, sc_a, st_a = make_masks(T_a, MODE, rng)
full_a = np.ones_like(win_a)

print("предки живут свой год (весь год виден, кризис свой)...")
sched_anc, cost_anc = learn(b_anc, net_anc, Ad_a, Bd_a, T_a, Iv_a, occ_a,
                            np.tile(DEFAULT, (N_ANC, 1)), LIFE, rng,
                            sc_a, win_a, full_a)
print(f"  готово, {time.time()-t0:.0f} с")

fund = np.median(sched_anc, axis=0)
print("фонд (медиана по предкам):",
      ", ".join(f"{v:.2f}" for v in fund))
print("типовые настройки:      ",
      ", ".join(f"{v:.2f}" for v in DEFAULT))

# ------------------------------------------------------------------ новички
b_new, net_new, Ad_n, Bd_n, T_n, Iv_n, nm_n, occ_n = prepare(N_NEW, new_years, rng)
win_n, pre_n, sc_n, st_n = make_masks(T_n, MODE, rng)

if MODE == "cold":
    Tw = np.array([T_n[i, st_n[i]:st_n[i]+WIN_H].mean() for i in range(N_NEW)])
    print(f"\nокно у новичков: средняя наружная от {Tw.min():.1f} до {Tw.max():.1f} °C")

def evaluate(sched):
    """Прожить весь год с этим расписанием и вернуть все меры."""
    return live(b_new, net_new, Ad_n, Bd_n, sched, T_n, Iv_n, occ_n,
                sc_n, win_n, pre_n)

print("\nусловие 1: сам, короткая подстройка на доступных часах...")
s1, _ = learn(b_new, net_new, Ad_n, Bd_n, T_n, Iv_n, occ_n,
              np.tile(DEFAULT, (N_NEW, 1)), SHORT, rng, sc_n, win_n, pre_n)
r1 = evaluate(s1)

print("условие 3: фонд как есть...")
s3 = np.tile(fund, (N_NEW, 1))
r3 = evaluate(s3)

print("условие 4: фонд плюс своя подстройка...")
s4, _ = learn(b_new, net_new, Ad_n, Bd_n, T_n, Iv_n, occ_n,
              s3.copy(), SHORT, rng, sc_n, win_n, pre_n)
r4 = evaluate(s4)

# проверка пересчёта: вперёд и обратно на том же доме должно вернуть то же
z_anc = to_z(sched_anc, b_anc, net_anc)
back = from_z(z_anc, b_anc, net_anc)
err = np.abs(back - sched_anc).max()
print(f"\nпроверка пересчёта величин: худшее расхождение {err:.2e}")
assert err < 1e-6, "пересчёт величин неверен, дальше идти нельзя"

fund_z = np.median(z_anc, axis=0)
print("фонд в величинах получателя:", ", ".join(f"{v:.3f}" for v in fund_z))
print("  z1 выше нормы, z2 глубина снижения, z3 прогрев/инерция, "
      "z4 зона, z5 власть регулятора")

print("условие 5: фонд в своих величинах...")
s5 = from_z(np.tile(fund_z, (N_NEW, 1)), b_new, net_new)
r5 = evaluate(s5)

print("условие 6: фонд в своих величинах плюс своё...")
s6, _ = learn(b_new, net_new, Ad_n, Bd_n, T_n, Iv_n, occ_n,
              s5.copy(), SHORT, rng, sc_n, win_n, pre_n)
r6 = evaluate(s6)

print(f"условие 2: каждый из {N_ANC} предков каждому новичку...")
pair_disc, pair_all = [], []
for j in range(N_ANC):
    r = evaluate(np.tile(sched_anc[j], (N_NEW, 1)))
    pair_disc.append(r["disc_win"]); pair_all.append(r["cost"])
pair_disc = np.array(pair_disc); pair_all = np.array(pair_all)   # [N_ANC, N_NEW]

# ------------------------------------------------------------------ итог
# Главная мера — АБСОЛЮТНЫЕ градусо-часы ниже 21 °C внутри окна события.
# Проценты от почти нулевого основания дают бессмысленные числа, поэтому
# проценты считаем только там, где основание не мало.
print("\n" + "=" * 72)
print(f"ВИД {MODE}, зерно {SEED}, падение мощности: "
      f"{'учтено' if sim3.HP_DERATE else 'НЕ учтено'}")
print("=" * 72)

d1, d3, d4 = r1["disc_win"], r3["disc_win"], r4["disc_win"]
d2 = np.median(pair_disc, axis=0)
print("\nГЛАВНОЕ: градусо-часы ниже 21 °C ВНУТРИ окна события")
print(f'{"":24s}{"медиана":>9s}{"среднее":>9s}{"худший дом":>12s}{"домов без холода":>18s}')
d5, d6 = r5["disc_win"], r6["disc_win"]
for nm, v in [("1 сам", d1), ("2 один предок", d2), ("3 фонд сырой", d3),
              ("4 фонд сырой+своё", d4), ("5 фонд свои величины", d5),
              ("6 фонд свои вел.+своё", d6)]:
    print(f"{nm:24s}{np.median(v):9.1f}{v.mean():9.1f}{v.max():12.1f}"
          f"{100*(v<=0.01).mean():17.0f}%")

print("\nсравнение с условием 1 (сам), по градусо-часам в окне:")
for nm, v in [("2 один предок", d2), ("3 фонд сырой", d3), ("4 фонд сырой+своё", d4),
              ("5 фонд свои вел.", d5), ("6 фонд свои вел.+своё", d6)]:
    better = (v < d1 - 1e-6).mean() * 100
    same = (np.abs(v - d1) <= 1e-6).mean() * 100
    worse = (v > d1 + 1e-6).mean() * 100
    print(f"  {nm:16s} лучше {better:3.0f}%   так же {same:3.0f}%   хуже {worse:3.0f}%")

print("\nпо ВСЕМ парам предок-новичок в окне:")
pb = (pair_disc < d1[None, :] - 1e-6)
print(f"  пар {pair_disc.size}, предок помог в {100*pb.mean():.0f} %")
print(f"  новичков, которым помог хотя бы один предок: {100*pb.any(axis=0).mean():.0f} %")
print(f"  новичков, которым помогло большинство предков: "
      f"{100*(pb.mean(axis=0) > 0.5).mean():.0f} %")

# ---- по пятым частям: медиана прячет то, что важно
print("\nПО ПЯТЫМ ЧАСТЯМ. 100 домов разложены по тому, как сильно замёрзли,")
print("когда справлялись сами. Первая часть — кому было хуже всех.")
q = np.argsort(-d1)
parts = np.array_split(q, 5)
names = ["1 хуже всех", "2", "3 середина", "4", "5 лучше всех"]
print(f'{"":14s}{"сам":>9s}{"предок":>9s}{"фонд":>9s}{"фонд+св":>9s}{"свои вел":>10s}')
for nm, ix in zip(names, parts):
    print(f"{nm:14s}{d1[ix].mean():9.1f}{d2[ix].mean():9.1f}{d3[ix].mean():9.1f}"
          f"{d4[ix].mean():9.1f}{d5[ix].mean():10.1f}")
print("\n  числа — градусо-часы ниже 21 °C за 72 часа беды, среднее по части")

print("\nсколько ЧАСОВ из 72 в доме было холоднее 21 °C, среднее по части:")
h1, h3, h5 = r1["hrs_cold"], r3["hrs_cold"], r5["hrs_cold"]
print(f'{"":14s}{"сам":>9s}{"фонд":>9s}{"свои вел":>10s}{"самая низкая T, сам":>22s}')
for nm, ix in zip(names, parts):
    print(f"{nm:14s}{h1[ix].mean():9.1f}{h3[ix].mean():9.1f}{h5[ix].mean():10.1f}"
          f"{r1['Tmin_win'][ix].mean():22.1f}")

print("\nэлектричество в окне события, кВт·ч (медиана):")
for nm, r in [("1 сам", r1), ("3 фонд сырой", r3), ("4 фонд+своё", r4),
              ("5 фонд свои вел.", r5), ("6 свои вел.+своё", r6)]:
    print(f"  {nm:18s}{np.median(r['kwh_win']):8.1f}   "
          f"самая низкая T в окне {np.median(r['Tmin_win']):5.1f} °C   "
          f"часов ниже нормы {np.median(r['hrs_cold']):5.1f}")

print("\nза весь год, для сравнения (цена: электричество + дискомфорт):")
base_all = r1["cost"]
for nm, v in [("2 один предок", np.median(pair_all, axis=0)),
              ("3 фонд сырой", r3["cost"]), ("4 фонд сырой+своё", r4["cost"]),
              ("5 фонд свои вел.", r5["cost"]), ("6 свои вел.+своё", r6["cost"])]:
    g = (base_all - v) / base_all * 100
    print(f"  {nm:16s} медиана {np.median(g):+6.1f}%   помогло {100*(g>0).mean():3.0f}%")

print("\nразбавление: доля годовых градусо-часов, набранная в окне")
share = np.where(r1["disc"] > 0, d1 / np.maximum(r1["disc"], 1e-9), np.nan)
print(f"  окно = {WIN_H} ч из {HOR} = {100*WIN_H/HOR:.1f} % времени")
print(f"  а дискомфорта в нём (медиана по новичкам): {100*np.nanmedian(share):.1f} %")

out = pd.DataFrame({
    "city": nm_n, "win_start": st_n, "Qmax_kW": b_new["Qmax"] / 1000,
    "margin": b_new["margin"], "A_floor": b_new["A_floor"],
    "disc_win_alone": d1, "disc_win_anc_med": d2,
    "disc_win_fund": d3, "disc_win_fund_tuned": d4,
    "disc_win_fundz": d5, "disc_win_fundz_tuned": d6,
    "kwh_win_alone": r1["kwh_win"], "kwh_win_fund": r3["kwh_win"],
    "kwh_win_fund_tuned": r4["kwh_win"],
    "cost_all_alone": base_all, "cost_all_fund": r3["cost"],
    "cost_all_fund_tuned": r4["cost"],
    "cost_all_fundz": r5["cost"], "cost_all_fundz_tuned": r6["cost"],
    "Tmin_alone": r1["Tmin_win"], "Tmin_fund": r3["Tmin_win"],
    "Tmin_fund_tuned": r4["Tmin_win"], "Tmin_fundz": r5["Tmin_win"],
    # по-человечески: сколько часов было холоднее нормы внутри окна
    "hrs_alone": r1["hrs_cold"], "hrs_fund": r3["hrs_cold"],
    "hrs_fund_tuned": r4["hrs_cold"], "hrs_fundz": r5["hrs_cold"],
    "hrs_fundz_tuned": r6["hrs_cold"],
    "disc_all_alone": r1["disc"], "disc_all_fund": r3["disc"],
    "disc_all_fundz": r5["disc"],
    "hrs_win": WIN_H,
})
out.to_csv(f"/home/claude/crisis/res12_{TAG}.csv", index=False)
np.save(f"/home/claude/crisis/pairs_{TAG}.npy", pair_disc)
np.save(f"/home/claude/crisis/sched_anc_{TAG}.npy", sched_anc)
print(f"\nзаписано res12_{TAG}.csv, всего {time.time()-t0:.0f} с")
