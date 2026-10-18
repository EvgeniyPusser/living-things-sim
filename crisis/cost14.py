"""Во что обошлось расписание прямого поиска за весь сезон."""
import numpy as np
from weather import load_all
from sim3 import *
YEAR, OCT1, HOR, WIN_H = 8760, 6552, 5112, 72
SEED, N_NEW, N_MOD = 501, 200, 40

rng = np.random.default_rng(SEED)
rng_n = np.random.default_rng(SEED + 1000)
cities = load_all()
years = [(c["name"], c["lat"], c, y) for c in cities for y in range(c["hours"] // YEAR)]
half = len(years) // 2
def assign(n, pool, r):
    idx = r.permutation(len(pool)); return [pool[idx[i % len(pool)]] for i in range(n)]
_ = assign(N_MOD, years[:half], rng)          # тот же порядок обращений к rng
new_years = assign(N_NEW, years[half:], rng_n)

T = np.empty((N_NEW, HOR)); Iv = np.empty((N_NEW, HOR, 4))
for i, (nm, lat, c, y) in enumerate(new_years):
    a, b = y*YEAR, (y+1)*YEAR
    T[i] = np.roll(c["T_out"][a:b], -OCT1)[:HOR]
    iv = solar_vertical(lat, YEAR, c["HDirNor"][a:b], c["HDifHor"][a:b], c["HGloHor"][a:b])
    Iv[i] = np.roll(iv, -OCT1, axis=0)[:HOR]
b = make_bodies(N_NEW, rng_n); size_heating(b, T)
net = thermal_network(b); Ad, Bd = discretise(net, 3600.0/SUB)
occ = occupancy(b["start_h"], HOR)

kk = np.ones(WIN_H)/WIN_H
st = np.empty(N_NEW, int)
for i in range(N_NEW):
    mv = np.convolve(T[i], kk, mode="valid"); mv[:24*30] = 1e9; st[i] = int(np.argmin(mv))
win = np.zeros((N_NEW, HOR)); sc = np.ones((N_NEW, HOR))
for i in range(N_NEW):
    win[i, st[i]:st[i]+WIN_H] = 1.0
    sc[i, st[i]:st[i]+WIN_H] = 0.5

pre = np.zeros((N_NEW, HOR))
for i in range(N_NEW): pre[i, :st[i]] = 1.0

def tune(budget=40, step0=0.25):
    r0 = np.random.default_rng(5)
    span = HI - LO
    best = np.tile(DEFAULT, (N_NEW,1))
    bc = live(b, net, Ad, Bd, best, T, Iv, occ, sc, win, pre)["cost_obj"]
    step = np.full(N_NEW, step0)
    for _ in range(budget):
        cand = np.clip(best + r0.normal(0,1,best.shape)*step[:,None]*span, LO, HI)
        c = live(b, net, Ad, Bd, cand, T, Iv, occ, sc, win, pre)["cost_obj"]
        bt = c < bc; best[bt] = cand[bt]; bc = np.where(bt, c, bc)
        step = np.where(bt, step, np.maximum(step*0.97, 0.02))
    return best
print("подстраиваю новичков...")
s_self = tune()

each = np.load(f"w14_each_{SEED}.npy"); pop = np.load(f"w14_pop_{SEED}.npy")
fund = np.median(each, axis=0)

print(f'{"":26s}{"электр., кВт·ч":>16s}{"холод за сезон":>16s}{"холод в окне":>14s}')
base = None
rows=[("типовое 21/18", np.tile(DEFAULT,(N_NEW,1))), ("сам подстроился", s_self),
      ("фонд: медиана сорока", np.tile(fund,(N_NEW,1))), ("прямой поиск", np.tile(pop,(N_NEW,1)))]
store={}
for nm, s in rows:
    r = live(b, net, Ad, Bd, s, T, Iv, occ, sc, win, win)
    store[nm]=r
    k, d, dw = np.median(r["kwh"]), np.median(r["disc"]), np.median(r["disc_win"])
    if nm=="сам подстроился": base=k
    print(f"{nm:26s}{k:12.0f}{d:14.0f}{dw:14.1f}")
print()
print("ОТСЧЁТ ОТ ДОМА, КОТОРЫЙ ПОДСТРОИЛСЯ САМ. Тариф 0.30 евро/кВт·ч, сезон 213 суток.")
r0 = store["сам подстроился"]
k0, d0 = np.median(r0["kwh"]), np.median(r0["disc"])
for nm in ["фонд: медиана сорока", "прямой поиск"]:
    r = store[nm]
    dk = np.median(r["kwh"]) - k0
    dd = d0 - np.median(r["disc"])
    dw = np.median(r0["disc_win"]) - np.median(r["disc_win"])
    print(f"  {nm}")
    print(f"     переплата           {dk:+6.0f} кВт·ч = {dk*0.30:+6.0f} евро за сезон")
    print(f"     холода меньше на    {dd:+6.0f} градусо-часов за сезон, из них {dw:.0f} в аварии")
    if dd>0:
        print(f"     цена одного сэкономленного градусо-часа: {dk*0.30/dd:.2f} евро")
