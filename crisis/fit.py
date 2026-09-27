"""Подгонка нашего быстрого дома к честному дому BuilDa.

Восемь домов BuilDa прожили 30 суток января в Мюнхене. Мы собираем те же
восемь у себя и ищем ОДИН поправочный множитель на проводимость оболочки.
Один множитель на все восемь — если он подходит всем, это не подгонка
под один случай, а поправка приведённой модели.
"""
import numpy as np, pandas as pd, glob, os, re
from scipy.linalg import expm
from weather import read_mos, WDIR
from sim3 import H_IN, RHO_CP, ALBEDO, solar_vertical, _series

RUN = sorted(glob.glob("/home/claude/builda/output/*/"), key=os.path.getmtime)[-1]
DAYS = 30
SUB = 12                     # 5 минут: интегрирование точное, дробить незачем
dt = 3600.0 / SUB
HRS = 24 * DAYS

w = read_mos(f"{WDIR}/Munich.mos")
T_out = w["T_out"][:HRS]
Iv = solar_vertical(48.13, HRS, w["HDirNor"][:HRS], w["HDifHor"][:HRS], w["HGloHor"][:HRS])

hour = np.arange(HRS) % 24
setp = np.where((hour >= 6) & (hour < 22), 22.0, 18.0)

# постоянные из конфигурации
L, W, Hf = 9.4125, 8.0, 3.04
fAWin = 0.14056
URoof, UFloor = 0.402, 0.514
cap_wall, cap_roof, cap_floor, cap_int = 192000.0, 81240.0, 483840.0, 145154.0
gWin, fATrans, ach = 0.7, 0.9, 0.3


def our_house(UExt, UWin, NF, k_env, k_win):
    H = Hf * NF
    Awg = 2 * (L + W) * H
    Awin_face = Awg / 4.0 * fAWin
    Awin = Awin_face * 4
    Aw = Awg - Awin
    Ar = L * W * 1.63612217795485
    Ag = L * W
    Ai = 1.238235294117647 * Awg
    V = L * W * H
    Af = L * W * NF

    h1, uw_ = _series(Aw, UExt)
    h2, ur_ = _series(Ar, URoof)
    h3, uf_ = _series(Ag, UFloor)
    h_env = h1 + h2 + h3
    ua_env = (uw_ + ur_ + uf_) * k_env
    C_env = Aw * cap_wall + Ar * cap_roof + Ag * cap_floor
    h_int = H_IN * Ai
    C_int = Ai * cap_int
    ua_win = (Awin * UWin + V * ach * RHO_CP / 3600.0) * k_win
    C_air = V * RHO_CP + Af * 2230.0
    return dict(h_env=h_env, ua_env=ua_env, C_env=C_env, h_int=h_int,
                C_int=C_int, ua_win=ua_win, C_air=C_air,
                Awin_face=Awin_face)


def run_ours(p, Qnom):
    Ca, Ce, Ci = p["C_air"], p["C_env"], p["C_int"]
    he, hi, uw, ue = p["h_env"], p["h_int"], p["ua_win"], p["ua_env"]
    A = np.array([[-(he + hi + uw) / Ca, he / Ca, hi / Ca],
                  [he / Ce, -(he + ue) / Ce, 0.0],
                  [hi / Ci, 0.0, -hi / Ci]])
    B = np.diag([1 / Ca, 1 / Ce, 1 / Ci])
    M = np.zeros((6, 6)); M[:3, :3] = A; M[:3, 3:] = B
    E = expm(M * dt); Ad, Bd = E[:3, :3], E[:3, 3:]
    Qsol = p["Awin_face"] * gWin * fATrans * Iv.sum(axis=1)

    T = np.array([20.0, 19.0, 20.0]); Q = 0.0; tr = []
    for k in range(HRS):
        for _ in range(SUB):
            u = 1.0 if setp[k] - T[0] > 0 else 0.0
            Qh = u * Qnom
            T = Ad @ T + Bd @ np.array([Qh + 0.3 * Qsol[k] + uw * T_out[k],
                                        ue * T_out[k], 0.7 * Qsol[k]])
            Q += Qh * dt / 3.6e9
        tr.append(T[0])
    return Q, np.array(tr)


cases = []
for d in sorted(glob.glob(RUN + "_#*")):
    tag = os.path.basename(d)
    m = re.match(r"_#Uex_([\d.]+)#Uwi_([\d.]+)#NFlo_(\d)", tag)
    UExt, UWin, NF = float(m.group(1)), float(m.group(2)), float(m.group(3))
    csv = glob.glob(d + "/*.csv")
    main = [c for c in csv if os.path.basename(c).startswith("_#")]
    df = pd.read_csv(main[0])
    para = pd.read_csv([c for c in csv if "para_to_fmu" in c][0])
    Qnom = float(para[para.iloc[:, 0] == "heatingPower"].iloc[0, 1])
    cases.append(dict(tag=tag, UExt=UExt, UWin=UWin, NF=NF, Qnom=Qnom,
                      Q_ref=df["Q_heating_MWh.y"].iloc[-1],
                      T_ref=(df["thermalZone.TAir"] - 273.15).mean()))

print(f"домов: {len(cases)}, {DAYS} суток каждый\n")


def err(k_env, k_win):
    rs = []
    for c in cases:
        p = our_house(c["UExt"], c["UWin"], c["NF"], k_env, k_win)
        Q, tr = run_ours(p, c["Qnom"])
        rs.append((Q / c["Q_ref"], tr.mean() - c["T_ref"]))
    return np.array(rs)


print("без поправки:")
r = err(1.0, 1.0)
for c, (rat, dT) in zip(cases, r):
    print(f'  {c["tag"]:34s} наш/их {rat:5.2f}   разница средней T {dT:+5.2f} K')
print(f"  среднее отношение {r[:,0].mean():.3f}, разброс {r[:,0].std():.3f}")

def search(env_grid, win_grid):
    best = None
    for k_env in env_grid:
        for k_win in win_grid:
            r = err(k_env, k_win)
            score = np.abs(r[:, 0] - 1).mean() + 0.1 * np.abs(r[:, 1]).mean()
            if best is None or score < best[0]:
                best = (score, k_env, k_win, r)
    return best

best = search(np.arange(0.55, 1.01, 0.10), np.arange(0.70, 1.11, 0.10))
_, e0, w0, _ = best
best = search(np.arange(e0 - 0.08, e0 + 0.081, 0.02),
              np.arange(w0 - 0.08, w0 + 0.081, 0.02))

score, k_env, k_win, r = best
print(f"\nлучшая поправка: оболочка ×{k_env:.2f}, окна+вентиляция ×{k_win:.2f}")
for c, (rat, dT) in zip(cases, r):
    print(f'  {c["tag"]:34s} наш/их {rat:5.2f}   разница средней T {dT:+5.2f} K')
print(f"  среднее отношение {r[:,0].mean():.3f}, разброс {r[:,0].std():.3f}")
print(f"  худший дом: {np.abs(r[:,0]-1).max()*100:.1f} % расхождения")
