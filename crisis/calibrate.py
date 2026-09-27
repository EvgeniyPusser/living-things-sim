"""Сверка нашего быстрого симулятора с BuilDa на одном и том же доме.

BuilDa посчитал 5 суток января в Мюнхене и напечатал:
    Q_heating_MWh.y   = 0.9384 МВт·ч
    thermalZone.TAir  = 291.78 K = 18.63 °C в конце

Здесь собираем ТОТ ЖЕ дом по числам из config_example_singleFamilyHouse.json,
тот же двухпозиционный регулятор 22/18 с ночным снижением с 22:00 до 6:00,
ту же погоду, и смотрим, насколько разойдётся.

Условие, объявленное до счёта: если расход разойдётся больше чем вдвое,
симулятор непригоден.
"""
import numpy as np
from scipy.linalg import expm
from weather import read_mos, WDIR
from sim3 import H_IN, RHO_CP, ALBEDO, solar_vertical, _series

# ---- дом из конфигурации BuilDa
L, W, Hf, NF = 9.4125, 8.0, 3.04, 3.0
fAWin = 0.14056
UExt, URoof, UFloor, UWin = 0.665, 0.402, 0.514, 3.2
cap_wall, cap_roof, cap_floor, cap_int = 192000.0, 81240.0, 483840.0, 145154.0
gWin, fATrans, ach = 0.7, 0.9, 0.3
Qnom = 17338.855570898402          # взято из para_to_fmu.csv самого BuilDa

H = Hf * NF
A_wall_gross = 2 * (L + W) * H
A_win_face = A_wall_gross / 4.0 * fAWin      # по каждому из четырёх фасадов
A_win = A_win_face * 4
A_wall = A_wall_gross - A_win
A_roof = L * W * 1.63612217795485
A_grnd = L * W
A_int = 1.238235294117647 * A_wall_gross
V = L * W * H
A_floor = L * W * NF

h_w1, ua_w = _series(A_wall, UExt)
h_r1, ua_r = _series(A_roof, URoof)
h_f1, ua_f = _series(A_grnd, UFloor)
h_env, ua_env = h_w1 + h_r1 + h_f1, ua_w + ua_r + ua_f
C_env = A_wall * cap_wall + A_roof * cap_roof + A_grnd * cap_floor
h_int, C_int = H_IN * A_int, A_int * cap_int
ua_win = A_win * UWin + V * ach * RHO_CP / 3600.0
C_air = V * RHO_CP + A_floor * 2230.0

print("дом, собранный по числам BuilDa")
print(f"  площадь пола        {A_floor:8.1f} м2")
print(f"  стены без окон      {A_wall:8.1f} м2")
print(f"  окна                {A_win:8.1f} м2")
print(f"  объём               {V:8.1f} м3")
print(f"  UA через окна+вент  {ua_win:8.1f} Вт/К")
print(f"  UA оболочки наружу  {ua_env:8.1f} Вт/К")
print(f"  ёмкость воздуха     {C_air/1e6:8.2f} МДж/К")
print(f"  ёмкость оболочки    {C_env/1e6:8.2f} МДж/К")
print(f"  ёмкость внутр.стен  {C_int/1e6:8.2f} МДж/К")
print(f"  мощность отопления  {Qnom/1000:8.2f} кВт")

# ---- точный переход за шаг
SUB = 40                      # 90 секунд, как у BuilDa
dt = 3600.0 / SUB
A = np.array([
    [-(h_env + h_int + ua_win) / C_air, h_env / C_air, h_int / C_air],
    [ h_env / C_env, -(h_env + ua_env) / C_env, 0.0],
    [ h_int / C_int, 0.0, -h_int / C_int],
])
B = np.diag([1 / C_air, 1 / C_env, 1 / C_int])
M = np.zeros((6, 6)); M[:3, :3] = A; M[:3, 3:] = B
E = expm(M * dt)
Ad, Bd = E[:3, :3], E[:3, 3:]

# ---- погода: тот же файл, те же первые 5 суток
w = read_mos(f"{WDIR}/Munich.mos")
HRS = 24 * 5
T_out = w["T_out"][:HRS]
Iv = solar_vertical(48.13, HRS, w["HDirNor"][:HRS], w["HDifHor"][:HRS], w["HGloHor"][:HRS])
aper = A_win_face * gWin * fATrans
Qsol = aper * Iv.sum(axis=1)

print(f"\nпогода: наружная от {T_out.min():.1f} до {T_out.max():.1f} °C, "
      f"солнце в сумме по фасадам до {Qsol.max():.0f} Вт")

# ---- двухпозиционный регулятор с ночным снижением, как у них
hour = np.arange(HRS) % 24
setp = np.where((hour >= 6) & (hour < 22), 22.0, 18.0)

T = np.array([20.0, 18.0, 19.5])     # как в их первой строке: 293.15 K = 20 °C
u = 0.0
Q_MWh = 0.0
trace = []
for k in range(HRS):
    for _ in range(SUB):
        e = setp[k] - T[0]
        u = 1.0 if e > 0 else 0.0
        Qh = u * Qnom
        q_air = Qh + 0.3 * Qsol[k] + ua_win * T_out[k]
        q_env = ua_env * T_out[k]
        q_int = 0.7 * Qsol[k]
        T = Ad @ T + Bd @ np.array([q_air, q_env, q_int])
        Q_MWh += Qh * dt / 3.6e9
    trace.append(T[0])

print("\n--- сверка ---")
print(f"BuilDa  тепло за 5 суток   0.9384 МВт·ч")
print(f"наш     тепло за 5 суток   {Q_MWh:.4f} МВт·ч")
print(f"отношение наш/BuilDa       {Q_MWh/0.9384:.2f}")
print(f"BuilDa  температура в конце 18.63 °C")
print(f"наш     температура в конце {trace[-1]:.2f} °C")
tr = np.array(trace)
print(f"наш     в комнате от {tr.min():.2f} до {tr.max():.2f} °C")
