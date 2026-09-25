"""Жизнь с редкими событиями и с записью условий.

Отличия от life.py:
  * погода может содержать редкое событие: суровая зима, жара, отказ отопления;
  * каждый объект возвращает не только расписание, но и свои условия —
    по ним потом ищутся связи.
"""
import numpy as np
from life import live_week, WEEKS_YEAR, LO, HI, COMFORT, BAND

HOURS_WEEK = 168

def weather_year(body, rng, rare=None):
    """Год по часам. rare: None, 'cold', 'heat'."""
    n = WEEKS_YEAR * HOURS_WEEK
    t = np.arange(n)
    day = 2 * np.pi * (t % 24) / 24
    season = 2 * np.pi * t / n
    T = (body["T_mean"] - 8 * np.sin(season) - body["T_amp"] / 2 * np.cos(day)
         + rng.normal(0, 1.5, n))
    for _ in range(rng.integers(2, 5)):                    # обычные похолодания
        s = int(rng.integers(0, n - 96)); T[s:s+96] -= rng.uniform(5, 10)
    if rare == "cold":                                     # суровая зима: весь сезон холоднее
        T -= 6.0
        s = int(rng.integers(n//3, 2*n//3)); T[s:s+336] -= 12.0
    if rare == "heat":
        T += 6.0
    sun = np.clip(np.sin(day - np.pi / 2 + body["orient"] * 0.15), 0, None) * 600
    sun *= rng.uniform(0.3, 1.0, n)
    return T, sun

def live_year(body, sched, T, sun, occ, rng, explore=0.8, broken=False):
    """Прожить год по неделям с осторожными пробами. broken: отопление вполсилы."""
    sched = np.clip(np.array(sched, float), LO, HI)
    b = dict(body)
    if broken:
        b["Qmax"] = body["Qmax"] * 0.5
    Tm = COMFORT
    hist_T, hist_c, weekly = [], [], []
    for w in range(WEEKS_YEAR):
        sl = slice(w * HOURS_WEEK, (w + 1) * HOURS_WEEK)
        Tw, sw, ow = T[sl], sun[sl], occ[sl]
        trying = rng.random() < explore and w > 2
        cand = sched.copy()
        if trying:
            idx = rng.integers(0, 24, rng.integers(1, 6))
            cand[idx] = np.clip(cand[idx] + rng.normal(0, 1.5, len(idx)), LO, HI)
        cost, Tm = live_week(b, cand if trying else sched, Tw, sw, ow, Tm)
        weekly.append(cost)
        if trying:
            if len(hist_T) >= 4:
                a, c0 = np.polyfit(hist_T, hist_c, 1)
                if cost < (a * Tw.mean() + c0) * 0.98:
                    sched = cand; hist_T, hist_c = [], []
        else:
            hist_T.append(Tw.mean()); hist_c.append(cost)
    return sched, np.array(weekly)

def year_cost(body, sched, T, sun, occ, broken=False):
    b = dict(body)
    if broken: b["Qmax"] = body["Qmax"] * 0.5
    tot, Tm = 0.0, COMFORT
    for w in range(WEEKS_YEAR):
        sl = slice(w * HOURS_WEEK, (w + 1) * HOURS_WEEK)
        c, Tm = live_week(b, sched, T[sl], sun[sl], occ[sl], Tm); tot += c
    return tot

def tune(body, start, T, sun, occ, rng, tries=60, broken=False):
    best = np.clip(np.array(start, float), LO, HI)
    bc = year_cost(body, best, T, sun, occ, broken)
    for _ in range(tries):
        c = best.copy(); idx = rng.integers(0, 24, rng.integers(1, 6))
        c[idx] = np.clip(c[idx] + rng.normal(0, 2.0, len(idx)), LO, HI)
        v = year_cost(body, c, T, sun, occ, broken)
        if v < bc: best, bc = c, v
    return best
