"""sim.py с одной поправкой: планка комфорта прибита к 21 градусу.
В оригинале штраф считался от T_occ, который дом сам подбирает, —
дом снижал T_occ и тем убирал штраф. Здесь T_occ влияет только на нагрев."""
import numpy as np
from sim import HOURS, DT, make_houses, weather, occupancy, body_distance, \
                BODY_NAMES, CTRL_NAMES, DEFAULT, LO, HI

COMFORT = 21.0        # обещание людям. постоянное, дом его менять не может

def simulate(body, ctrl, T_out, sun, occ):
    T_occ, T_away, preheat, band, gain = ctrl
    lead = int(round(preheat))
    target_occ = np.roll(occ, -lead) if lead > 0 else occ
    target = np.where((occ + target_occ) > 0, T_occ, T_away)
    UA = body["UA"] + body["infil"]
    T = target[0]; energy = 0.0; discomfort = 0.0
    for i in range(HOURS):
        u = np.clip(gain * (target[i] - T) / max(band, 1e-6), 0.0, 1.0)
        Q = u * body["Qmax"] + body["occ_gain"] * occ[i] + body["solar"] * sun[i]
        T = T + DT / body["C"] * (Q - UA * (T - T_out[i]))
        energy += u * body["Qmax"] * DT / 3.6e6
        if occ[i] and T < COMFORT - band:          # ← прибито
            discomfort += (COMFORT - band - T)
    return energy * 0.25 + discomfort * 2.0

def learn(body, T_out, sun, occ, start, budget, rng, step0=0.25):
    span = HI - LO
    best = np.clip(np.asarray(start, float), LO, HI)
    best_cost = simulate(body, best, T_out, sun, occ)
    step = step0
    for k in range(budget):
        cand = np.clip(best + rng.normal(0, step, 5) * span, LO, HI)
        c = simulate(body, cand, T_out, sun, occ)
        if c < best_cost: best, best_cost = cand, c
        else: step = max(step * 0.97, 0.02)
    return best, best_cost
