"""Жизнь дома по неделям, без повторов.

Каждая неделя проживается один раз. Потери накапливаются: что потеряно,
то потеряно. Раз в неделю дом может попробовать одно изменение расписания
и по итогу недели решить, оставить его или откатить.
"""
import numpy as np, pandas as pd
from sim import make_houses, occupancy

HOURS_WEEK = 168
WEEKS_YEAR = 52
LO, HI = 12.0, 24.0
DEFAULT = np.full(24, 20.0)
COMFORT, BAND = 21.0, 0.5

def weather_years(body, years, rng):
    """Погода на несколько лет: сезон, суточный ход, шум. Годы разные."""
    n = years * WEEKS_YEAR * HOURS_WEEK
    t = np.arange(n)
    day = 2 * np.pi * (t % 24) / 24
    season = 2 * np.pi * t / (WEEKS_YEAR * HOURS_WEEK)
    T = (body["T_mean"] - 8 * np.sin(season) - body["T_amp"] / 2 * np.cos(day)
         + rng.normal(0, 1.5, n))
    # редкие холодные волны: в среднем одна-две за зиму
    for _ in range(rng.integers(2, 5) * years):
        s = int(rng.integers(0, n - 96))
        T[s:s+96] -= rng.uniform(6, 14)
    sun = np.clip(np.sin(day - np.pi / 2 + body["orient"] * 0.15), 0, None) * 600
    sun *= rng.uniform(0.3, 1.0, n)
    return T, sun

def live_week(body, sched, T_out, sun, occ, T0):
    """Прожить неделю. Возвращает потери и конечную температуру."""
    UA = body["UA"] + body["infil"]
    hours = np.arange(len(T_out)) % 24
    target = sched[hours]
    T = T0; energy = 0.0; disc = 0.0
    for i in range(len(T_out)):
        u = np.clip(0.5 * (target[i] - T) / BAND, 0.0, 1.0)
        Q = u * body["Qmax"] + body["occ_gain"] * occ[i] + body["solar"] * sun[i]
        T = T + 3600.0 / body["C"] * (Q - UA * (T - T_out[i]))
        energy += u * body["Qmax"] / 1000.0
        if occ[i] and T < COMFORT - BAND:
            d = COMFORT - BAND - T
            disc += d if d < 3 else d * 4          # сильный холод стоит непропорционально дорого
    return energy * 0.25 + disc * 2.0, T

def live(body, T_out, sun, occ, start_sched, years, rng, explore=0.8):
    """Жизнь: неделя за неделей, с осторожными пробами."""
    sched = np.clip(np.array(start_sched, float), LO, HI)
    T = COMFORT
    hist_T, hist_cost = [], []        # недели, прожитые с текущим расписанием
    weekly = []
    n_weeks = years * WEEKS_YEAR
    for w in range(n_weeks):
        sl = slice(w * HOURS_WEEK, (w + 1) * HOURS_WEEK)
        Tw, sw, ow = T_out[sl], sun[sl], occ[sl]
        mean_T = Tw.mean()
        trying = rng.random() < explore and w > 2
        cand = sched.copy()
        if trying:
            idx = rng.integers(0, 24, rng.integers(1, 6))
            cand[idx] = np.clip(cand[idx] + rng.normal(0, 1.5, len(idx)), LO, HI)
        cost, T = live_week(body, cand if trying else sched, Tw, sw, ow, T)
        weekly.append(cost)
        if trying:
            # чего ждали от старого расписания при такой погоде
            if len(hist_T) >= 4:
                a, b = np.polyfit(hist_T, hist_cost, 1)
                expect = a * mean_T + b
                if cost < expect * 0.98:
                    sched = cand
                    hist_T, hist_cost = [], []      # прошлое относилось к другому расписанию
        else:
            hist_T.append(mean_T); hist_cost.append(cost)
    return sched, np.array(weekly)
