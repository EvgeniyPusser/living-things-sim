"""То же, что life.py, но шаг 10 минут вместо часа.
Проверка: меняется ли ПОРЯДОК условий, если убрать качели температуры."""
import numpy as np
from life import WEEKS_YEAR, LO, HI, COMFORT, BAND
from life2 import weather_year

HOURS_WEEK = 168
SUB = 6                      # шагов в часе
DT  = 3600.0 / SUB           # 600 секунд

def live_week10(body, sched, T_out, sun, occ, T0):
    UA = body["UA"] + body["infil"]
    hours = np.arange(len(T_out)) % 24
    target = sched[hours]
    T = T0; energy = 0.0; disc = 0.0
    for i in range(len(T_out)):
        for _ in range(SUB):
            u = np.clip(0.5 * (target[i] - T) / BAND, 0.0, 1.0)
            Q = u*body["Qmax"] + body["occ_gain"]*occ[i] + body["solar"]*sun[i]
            T = T + DT/body["C"] * (Q - UA*(T - T_out[i]))
            energy += u*body["Qmax"]*DT/3.6e6
            if occ[i] and T < COMFORT - BAND:
                d = COMFORT - BAND - T
                disc += (d if d < 3 else d*4) / SUB
    return energy*0.25 + disc*2.0, T

def year_cost10(body, sched, T, sun, occ, broken=False):
    b = dict(body)
    if broken: b["Qmax"] = body["Qmax"]*0.5
    tot, Tm = 0.0, COMFORT
    for w in range(WEEKS_YEAR):
        sl = slice(w*HOURS_WEEK, (w+1)*HOURS_WEEK)
        c, Tm = live_week10(b, sched, T[sl], sun[sl], occ[sl], Tm); tot += c
    return tot

def tune10(body, start, T, sun, occ, rng, tries=60, broken=False):
    best = np.clip(np.array(start, float), LO, HI)
    bc = year_cost10(body, best, T, sun, occ, broken)
    for _ in range(tries):
        c = best.copy(); idx = rng.integers(0,24,rng.integers(1,6))
        c[idx] = np.clip(c[idx] + rng.normal(0,2.0,len(idx)), LO, HI)
        v = year_cost10(body, c, T, sun, occ, broken)
        if v < bc: best, bc = c, v
    return best
