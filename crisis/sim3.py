"""Симулятор домов: три тепловые ёмкости, настоящая погода, теплонасос.

Отличия от прежнего sim.py, по пунктам разбора BuilDa:

1. Масса по слоям. Раньше был один узел с ёмкостью C. Теперь три:
   воздух+мебель, оболочка (стены+крыша+пол), внутренние стены.
   Стена отстаёт от воздуха — значит прогрев заранее наконец на что-то действует.

2. Погода настоящая, из файлов .mos, а не синус.

3. Солнце по четырём фасадам с настоящим положением солнца от широты,
   прямая и рассеянная радиация отдельно. Ориентация теперь работает.

4. Теплонасос: кривая нагрева и COP от наружной температуры.
   Платим за электричество, а не за тепло.

5. Интегрирование ТОЧНОЕ. Внутри шага система линейна, поэтому берём
   матричную экспоненту: T(k+1) = Ad·T(k) + Bd·w(k). Артефакта шага нет
   в принципе — это не приближение, а решение.

Всё считается сразу для всего населения: состояние — матрица [N,3].
"""
from __future__ import annotations
import numpy as np
from scipy.linalg import expm

# ------------------------------------------------------------------ константы
H_IN      = 2.7        # внутренний плёночный коэффициент, Вт/м²К
# Поправка приведённой модели, подобранная на 8 домах BuilDa в Мюнхене
# и проверенная на 4 других домах в Берлине в другой месяц (расхождение 3.5 %).
K_ENV     = 0.65       # проводимость оболочки наружу
K_WIN     = 1.08       # окна плюс вентиляция
RHO_CP    = 1.2 * 1005 # объёмная теплоёмкость воздуха, Дж/м³К
ALBEDO    = 0.2
COMFORT   = 21.0       # норма комфорта, НЕ настраиваемая домом
TOL       = 0.0        # допуска нет.
# Почему нет: с допуском 0.5 K предки научились садиться ровно на 20.5 —
# штрафа ноль, энергии минимум, запаса тоже ноль. Это дырка в мере, а не
# умение: любое возмущение сразу проваливает такой дом. Штраф теперь
# пропорционален отклонению ниже 21.0, без полки.

# Мощность теплонасоса падает с наружной температурой. Это не наша выдумка,
# а свойство воздушного теплонасоса: при 7 °C он выдаёт номинал, при −10 °C
# около 60 % от него. Именно поэтому мороз становится кризисом мощности.
HP_DERATE = True
def capacity_factor(T_out):
    return np.clip(1.0 - 0.0235 * (7.0 - T_out), 0.50, 1.15)
PRICE     = 0.25       # цена электричества, условных единиц за кВт·ч
W_DISC    = 2.0        # вес градусо-часа дискомфорта
SUB       = 4          # шагов управления в часе -> 15 минут

# ------------------------------------------------------------------ тела домов
BODY_NAMES = ["L", "W", "n_floors", "UExt", "URoof", "UFloor", "UWin",
              "fAWin", "ach", "steep", "eta_hp", "occ_gain", "start_h",
              "cap_wall", "cap_int", "Qmax", "rot"]

def make_bodies(n: int, rng) -> dict:
    """Население домов. Диапазоны взяты из конфигурации BuilDa."""
    b = {
        "L":        rng.uniform(5.0, 9.4, n),        # длина зоны, м
        "W":        rng.uniform(6.0, 10.0, n),       # ширина зоны, м
        "n_floors": rng.integers(1, 4, n).astype(float),
        "UExt":     rng.uniform(0.15, 0.70, n),      # стены, Вт/м²К
        "URoof":    rng.uniform(0.15, 0.55, n),
        "UFloor":   rng.uniform(0.25, 0.70, n),
        "UWin":     rng.uniform(0.9, 3.2, n),
        "fAWin":    rng.uniform(0.08, 0.25, n),      # доля окон в стене
        "ach":      rng.uniform(0.2, 0.8, n),        # воздухообмен, 1/ч
        "steep":    rng.uniform(0.3, 1.3, n),        # крутизна кривой нагрева
        "eta_hp":   rng.uniform(0.35, 0.55, n),      # доля от Карно
        "occ_gain": rng.uniform(150, 700, n),        # тепло от людей, Вт
        "start_h":  rng.integers(5, 10, n).astype(float),
        "cap_wall": rng.uniform(1.0e5, 2.6e5, n),    # Дж/м²К стены
        "cap_int":  rng.uniform(0.8e5, 2.0e5, n),    # Дж/м²К внутренних стен
        "rot":      rng.uniform(0, 2 * np.pi, n),    # поворот дома
        "Qmax":     np.zeros(n),                     # заполним ниже
    }
    # производные геометрии
    A_floor = b["L"] * b["W"] * b["n_floors"]
    H = 3.04 * b["n_floors"]
    A_wall_gross = 2 * (b["L"] + b["W"]) * H
    A_win = A_wall_gross * b["fAWin"]
    A_wall = A_wall_gross - A_win
    A_roof = b["L"] * b["W"] * 1.636
    A_grnd = b["L"] * b["W"]
    A_int = 1.238 * A_wall_gross
    V = b["L"] * b["W"] * H

    b.update(A_floor=A_floor, A_win=A_win, A_wall=A_wall, A_roof=A_roof,
             A_grnd=A_grnd, A_int=A_int, V=V)

    # Проводимость для расчёта мощности — по правилу самого BuilDa
    # (DIN 18599-2), включая понижающий множитель 0.6 для пола к грунту
    # по DIN 4108-6. Мощность задаётся отдельно, когда дому достанется город:
    # она считается от самого холодного часа ЕГО записи.
    b["UA_din"] = (A_wall * b["UExt"] + A_win * b["UWin"]
                   + A_grnd * b["UFloor"] * 0.6 + A_roof * b["URoof"]
                   + V * b["ach"] * RHO_CP / 3600.0)
    b["margin"] = rng.uniform(0.90, 1.30, n)   # как в жизни: кто с запасом, кто без
    return b

def design_temperature(T_record):
    """Расчётная наружная температура: 0.4-й процентиль записи.

    Так это и делают на практике (ASHRAE 99.6 %), и НЕ по абсолютному
    минимуму: по минимуму пятилетней записи мощность вышла бы в 26-44 кВт
    на жилой дом, чего не бывает. Проверка метода: для Мюнхена процентиль
    даёт −12.5 °C, в заголовке файла напечатано ASHRAE −14.2 °C.
    """
    return np.percentile(np.asarray(T_record, float), 0.4, axis=-1)

def size_heating(b: dict, T_record, derate=None):
    """Мощность: держать 21 °C при расчётной наружной температуре.

    Правило и слагаемые — как в Nominal_heating_power_calculator у BuilDa
    (DIN 18599-2). Если мощность падает на морозе, номинал поднимаем так,
    чтобы при расчётной температуре хватало. Запас margin — тот разброс,
    который есть в настоящем фонде.

    Следствие, которое мы НЕ подгоняли: в час, который холоднее расчётного,
    дому мощности не хватит. Так кризис возникает сам, из физики и из
    обычной практики выбора оборудования.
    """
    derate = HP_DERATE if derate is None else derate
    T_des = design_temperature(T_record)
    need = b["UA_din"] * (21.0 - T_des)
    if derate:
        need = need / capacity_factor(T_des)
    b["Qmax"] = need * b["margin"]
    b["T_design"] = T_des
    return b

def _series(A, U):
    """Одна поверхность как две последовательные проводимости.

    Полное U включает внутреннюю плёнку. Отделяем её:
    внутрь -> h_in*A,  наружу -> то, что осталось.
    """
    h_in = H_IN * A
    R_tot = 1.0 / np.maximum(U * A, 1e-9)
    R_in = 1.0 / h_in
    R_out = np.maximum(R_tot - R_in, R_tot * 0.05)
    return h_in, 1.0 / R_out

def thermal_network(b: dict) -> dict:
    """Собирает три ёмкости и проводимости между ними."""
    h_w1, ua_w = _series(b["A_wall"], b["UExt"])
    h_r1, ua_r = _series(b["A_roof"], b["URoof"])
    h_f1, ua_f = _series(b["A_grnd"], b["UFloor"])

    h_env  = h_w1 + h_r1 + h_f1                    # воздух <-> оболочка
    ua_env = (ua_w + ua_r + ua_f) * K_ENV          # оболочка <-> улица
    C_env  = b["A_wall"] * b["cap_wall"] + b["A_roof"] * b["cap_wall"] * 0.45 \
             + b["A_grnd"] * b["cap_wall"] * 1.2

    h_int = H_IN * b["A_int"]                # воздух <-> внутренние стены
    C_int = b["A_int"] * b["cap_int"]

    ua_win = (b["A_win"] * b["UWin"] + b["V"] * b["ach"] * RHO_CP / 3600.0) * K_WIN
    C_air = b["V"] * RHO_CP + b["A_floor"] * 2230.0   # воздух плюс мебель

    return dict(h_env=h_env, ua_env=ua_env, C_env=C_env,
                h_int=h_int, C_int=C_int, ua_win=ua_win, C_air=C_air)

def discretise(net: dict, dt: float):
    """Точный переход за шаг dt. Ad и Bd считаем через 6x6 экспоненту,
    чтобы не обращать A."""
    n = len(net["C_air"])
    Ad = np.empty((n, 3, 3)); Bd = np.empty((n, 3, 3))
    for i in range(n):
        Ca, Ce, Ci = net["C_air"][i], net["C_env"][i], net["C_int"][i]
        he, hi, uw, ue = net["h_env"][i], net["h_int"][i], net["ua_win"][i], net["ua_env"][i]
        A = np.array([
            [-(he + hi + uw) / Ca,  he / Ca,        hi / Ca],
            [ he / Ce,             -(he + ue) / Ce, 0.0    ],
            [ hi / Ci,              0.0,           -hi / Ci],
        ])
        B = np.diag([1.0 / Ca, 1.0 / Ce, 1.0 / Ci])
        M = np.zeros((6, 6)); M[:3, :3] = A; M[:3, 3:] = B
        E = expm(M * dt)
        Ad[i] = E[:3, :3]; Bd[i] = E[:3, 3:]
    return Ad, Bd

# ------------------------------------------------------------------- солнце
def solar_vertical(lat_deg: float, hours: int, HDirNor, HDifHor, HGloHor):
    """Радиация на четыре вертикальных фасада: юг, запад, север, восток.

    Возвращает [hours, 4] в Вт/м². Положение солнца настоящее, от широты.
    """
    t = np.arange(hours)
    n = (t // 24) % 365 + 1
    h = t % 24 + 0.5
    lat = np.radians(lat_deg)
    dec = np.radians(23.45) * np.sin(2 * np.pi * (284 + n) / 365.0)
    om = np.radians(15.0 * (h - 12.0))
    sin_alt = np.sin(lat) * np.sin(dec) + np.cos(lat) * np.cos(dec) * np.cos(om)
    alt = np.arcsin(np.clip(sin_alt, -1, 1))
    az = np.arctan2(np.sin(om), np.cos(om) * np.sin(lat) - np.tan(dec) * np.cos(lat))
    up = alt > 0.0
    out = np.zeros((hours, 4))
    face = np.radians([0.0, 90.0, 180.0, -90.0])   # юг, запад, север, восток
    for k, g in enumerate(face):
        cos_i = np.cos(alt) * np.cos(az - g)
        cos_i = np.where(up, np.clip(cos_i, 0, None), 0.0)
        out[:, k] = HDirNor * cos_i + HDifHor * 0.5 + HGloHor * ALBEDO * 0.5
    return out

# ------------------------------------------------------------------ занятость
def occupancy(start_h, hours: int):
    """[N, hours]: 1 когда дома. Десять часов подряд от своего часа."""
    h = (np.arange(hours) % 24)[None, :]
    s = np.asarray(start_h, float)[:, None]
    return ((h >= s) & (h < s + 10)).astype(float)

# ------------------------------------------------------------- расписание
SCHED_NAMES = ["T_occ", "T_away", "preheat_h", "band", "gain"]
DEFAULT = np.array([21.0, 18.0, 1.0, 0.5, 0.35])
LO      = np.array([18.0, 12.0, 0.0, 0.1, 0.02])
HI      = np.array([24.0, 21.0, 5.0, 2.0, 1.00])

def live(b, net, Ad, Bd, sched, T_out, Ivert, occ, qmax_scale=None,
         window=None, obj=None, T0=None):
    """Один проход по времени для всего населения сразу.

    b, net      тела и сеть, массивы длины N
    sched       [N,5] расписания
    T_out       [N, hours] наружная температура
    Ivert       [N, hours, 4] радиация по фасадам
    occ         [N, hours] занятость
    qmax_scale  [N, hours] множитель мощности; 0.5 = отказ вдвое
    window      [N, hours] окно события — по нему главная мера
    obj         [N, hours] что видно при подстройке. У новичка это ТОЛЬКО
                часы до события: подстраиваться на самом событии нельзя,
                иначе жизнь проживается дважды.

    Возвращает цену за весь период, цену в окне события, цену по obj,
    часы ниже нормы в окне и минимальную температуру в окне.
    """
    N, HRS = T_out.shape
    dt = 3600.0 / SUB
    T_occ, T_away, preheat, band, gain = (sched[:, i] for i in range(5))
    lead = np.round(preheat).astype(int)

    # цель: занят или скоро занят
    idx = np.arange(HRS)
    tgt_occ = np.zeros_like(occ)
    for i in range(N):
        tgt_occ[i] = occ[i][np.minimum(idx + lead[i], HRS - 1)]
    live_now = (occ + tgt_occ) > 0
    target = np.where(live_now, T_occ[:, None], T_away[:, None])

    # солнце через окна: доля окна по фасадам зависит от поворота дома
    rot = b["rot"]
    wf = np.stack([0.25 + 0.15 * np.cos(rot - g) for g in
                   np.radians([0.0, 90.0, 180.0, -90.0])], axis=1)   # [N,4]
    wf = wf / wf.sum(axis=1, keepdims=True)
    aper = (b["A_win"] * 0.7 * 0.9)[:, None]          # g * доля прозрачного
    Qsol = aper * np.einsum("nhk,nk->nh", Ivert, wf)  # [N, hours] Вт

    Ca, Ce, Ci = net["C_air"], net["C_env"], net["C_int"]
    uw, ue = net["ua_win"], net["ua_env"]

    T = np.zeros((N, 3))
    T[:, 0] = COMFORT if T0 is None else T0
    T[:, 1] = COMFORT - 2.0
    T[:, 2] = COMFORT - 0.5

    kwh_all = np.zeros(N); disc_all = np.zeros(N)
    kwh_win = np.zeros(N); disc_win = np.zeros(N)
    kwh_obj = np.zeros(N); disc_obj = np.zeros(N)
    hrs_cold = np.zeros(N); Tmin_win = np.full(N, 99.0)

    scale = np.ones((N, HRS)) if qmax_scale is None else qmax_scale
    Qmax = b["Qmax"]

    for k in range(HRS):
        To = T_out[:, k]
        # кривая нагрева и COP теплонасоса
        T_sup = np.clip(20.0 + b["steep"] * (20.0 - To), 25.0, 55.0)
        cop = np.clip(b["eta_hp"] * (T_sup + 273.15) /
                      np.maximum(T_sup - To, 8.0), 1.3, 5.5)
        qcap = Qmax * scale[:, k]
        if HP_DERATE:
            qcap = qcap * capacity_factor(To)
        e_h = 0.0
        for _ in range(SUB):
            u = np.clip(gain * (target[:, k] - T[:, 0]) / np.maximum(band, 1e-6), 0.0, 1.0)
            Qh = u * qcap
            q_air = Qh + b["occ_gain"] * occ[:, k] + 0.3 * Qsol[:, k] + uw * To
            q_env = ue * To
            q_int = 0.7 * Qsol[:, k]
            w = np.stack([q_air / 1.0, q_env, q_int], axis=1)
            # Bd уже содержит 1/C, поэтому подаём мощности как есть
            T = np.einsum("nij,nj->ni", Ad, T) + np.einsum("nij,nj->ni", Bd, w)
            e_h += Qh / cop * dt / 3.6e6          # кВт·ч электричества
        cold = np.where(occ[:, k] > 0, np.maximum(COMFORT - TOL - T[:, 0], 0.0), 0.0)
        kwh_all += e_h; disc_all += cold
        if window is not None:
            m = window[:, k]
            kwh_win += e_h * m; disc_win += cold * m
            hrs_cold += (cold > 0) * m
            Tmin_win = np.where(m > 0, np.minimum(Tmin_win, T[:, 0]), Tmin_win)
        if obj is not None:
            m = obj[:, k]
            kwh_obj += e_h * m; disc_obj += cold * m

    return dict(
        cost=kwh_all * PRICE + disc_all * W_DISC,
        cost_win=kwh_win * PRICE + disc_win * W_DISC,
        cost_obj=kwh_obj * PRICE + disc_obj * W_DISC,
        kwh=kwh_all, disc=disc_all,
        kwh_win=kwh_win, disc_win=disc_win,
        hrs_cold=hrs_cold, Tmin_win=Tmin_win,
    )
