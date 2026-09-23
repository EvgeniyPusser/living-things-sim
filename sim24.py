"""Версия с почасовым расписанием уставок: контроллер = 24 числа."""
import numpy as np
from sim import HOURS, DT, make_houses, weather, occupancy, body_distance, BODY_NAMES

LO24, HI24 = 12.0, 24.0
DEFAULT24 = np.full(24, 20.0)          # типовое: одна уставка на все часы

def simulate24(body, sched, T_out, sun, occ, band=0.5, gain=0.5):
    UA = body["UA"] + body["infil"]
    hours = np.arange(HOURS) % 24
    target = sched[hours]
    T = target[0]
    energy = 0.0; disc = 0.0
    for i in range(HOURS):
        u = np.clip(gain * (target[i] - T) / band, 0.0, 1.0)
        Q = u * body["Qmax"] + body["occ_gain"] * occ[i] + body["solar"] * sun[i]
        T = T + DT / body["C"] * (Q - UA * (T - T_out[i]))
        energy += u * body["Qmax"] * DT / 3.6e6
        if occ[i] and T < 21.0 - band:     # комфорт требует 21 при людях, всегда
            disc += (21.0 - band - T)
    return energy * 0.25 + disc * 2.0

def learn24(body, T_out, sun, occ, start, budget, rng, step=1.5):
    best = np.clip(np.asarray(start, float), LO24, HI24)
    bc = simulate24(body, best, T_out, sun, occ)
    for k in range(budget):
        cand = best.copy()
        idx = rng.integers(0, 24, rng.integers(1, 5))      # меняем 1–4 часа
        cand[idx] += rng.normal(0, step, len(idx))
        cand = np.clip(cand, LO24, HI24)
        c = simulate24(body, cand, T_out, sun, occ)
        if c < bc:
            best, bc = cand, c
    return best, bc
