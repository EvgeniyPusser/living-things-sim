"""
Перенос выученного управления между домами.

Вопрос: при каком различии между домами перенос опыта перестаёт помогать?

Дом = 10 чисел (тело). Управление = 5 чисел (контроллер).
Дом "живёт" сезон по часам и подбирает свой контроллер (обучение за жизнь).
Потом контроллер дома A отдаётся дому B как начальная точка.
Сравниваем с обучением дома B с нуля при том же бюджете шагов.
"""
from __future__ import annotations
import numpy as np, pandas as pd, itertools

HOURS = 24 * 60          # сезон: 60 суток по часам
DT = 3600.0              # шаг, секунды

# ---------------------------------------------------------------- тело дома
BODY_NAMES = ["UA", "C", "solar", "Qmax", "infil", "occ_gain",
              "start_h", "T_mean", "T_amp", "orient"]

def make_houses(n: int, rng) -> pd.DataFrame:
    """n домов, у каждого 10 свойств."""
    return pd.DataFrame({
        "UA":       rng.uniform(80, 400, n),        # потери через оболочку, Вт/К
        "C":        rng.uniform(4e6, 40e6, n),      # теплоёмкость, Дж/К
        "solar":    rng.uniform(0.5, 6.0, n),       # площадь остекления × пропускание, м²
        "Qmax":     rng.uniform(3000, 15000, n),    # мощность отопления, Вт
        "infil":    rng.uniform(20, 200, n),        # инфильтрация, Вт/К
        "occ_gain": rng.uniform(100, 600, n),       # тепло от жильцов, Вт
        "start_h":  rng.integers(5, 10, n).astype(float),   # час прихода
        "T_mean":   rng.uniform(-5, 10, n),         # средняя наружная, °C
        "T_amp":    rng.uniform(3, 12, n),          # суточный размах, К
        "orient":   rng.uniform(0, 2 * np.pi, n),   # ориентация окон
    })

def weather(body, rng):
    """Наружная температура и солнце по часам."""
    t = np.arange(HOURS)
    day = 2 * np.pi * (t % 24) / 24
    season = 2 * np.pi * t / HOURS
    T_out = (body["T_mean"] - 4 * np.sin(season)
             - body["T_amp"] / 2 * np.cos(day)
             + rng.normal(0, 1.0, HOURS))
    sun = np.clip(np.sin(day - np.pi / 2 + body["orient"] * 0.15), 0, None) * 600
    sun *= rng.uniform(0.3, 1.0, HOURS)             # облачность
    return T_out, sun

def occupancy(body):
    h = np.arange(HOURS) % 24
    s = int(body["start_h"])
    return ((h >= s) & (h < s + 10)).astype(float)

# ------------------------------------------------------------- контроллер
CTRL_NAMES = ["T_occ", "T_away", "preheat_h", "band", "gain"]
DEFAULT = np.array([21.0, 18.0, 1.0, 0.5, 0.35])     # типовая настройка, ничего не знающая о доме
LO = np.array([18.0, 12.0, 0.0, 0.1, 0.02])
HI = np.array([24.0, 21.0, 5.0, 2.0, 1.00])

def simulate(body, ctrl, T_out, sun, occ):
    """Сезон по часам. Возвращает стоимость: энергия + штраф за холод."""
    T_occ, T_away, preheat, band, gain = ctrl
    lead = int(round(preheat))
    target_occ = np.roll(occ, -lead) if lead > 0 else occ   # прогрев заранее
    target = np.where((occ + target_occ) > 0, T_occ, T_away)

    UA = body["UA"] + body["infil"]
    T = target[0]
    energy = 0.0
    discomfort = 0.0
    for i in range(HOURS):
        err = target[i] - T
        u = np.clip(gain * err / max(band, 1e-6), 0.0, 1.0)      # доля мощности
        Q = u * body["Qmax"] + body["occ_gain"] * occ[i] + body["solar"] * sun[i]
        T = T + DT / body["C"] * (Q - UA * (T - T_out[i]))
        energy += u * body["Qmax"] * DT / 3.6e6                  # кВт·ч
        if occ[i] and T < T_occ - band:
            discomfort += (T_occ - band - T)                     # градусо-часы
    return energy * 0.25 + discomfort * 2.0                      # цена + вес комфорта

# ----------------------------------------------------------------- обучение
def learn(body, T_out, sun, occ, start, budget, rng, step0=0.25):
    """Простой локальный поиск: пробуем шаг в случайную сторону, оставляем лучшее.

    budget — сколько прогонов сезона разрешено. Это и есть 'жизнь' дома.
    """
    span = HI - LO
    best = np.clip(np.asarray(start, float), LO, HI)
    best_cost = simulate(body, best, T_out, sun, occ)
    step = step0
    for k in range(budget):
        cand = np.clip(best + rng.normal(0, step, 5) * span, LO, HI)
        c = simulate(body, cand, T_out, sun, occ)
        if c < best_cost:
            best, best_cost = cand, c
        else:
            step = max(step * 0.97, 0.02)
    return best, best_cost

# ------------------------------------------------------------- расстояние тел
def body_distance(houses: pd.DataFrame) -> np.ndarray:
    z = (houses - houses.mean()) / houses.std(ddof=0)
    z = z.to_numpy()
    n = len(z)
    d = np.zeros((n, n))
    for i, j in itertools.product(range(n), repeat=2):
        d[i, j] = np.sqrt(((z[i] - z[j]) ** 2).mean())
    return d
