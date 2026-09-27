"""Проверка поправки на домах, городе и месяце, на которых её НЕ подбирали.

Подбирали: Мюнхен, январь, UExt 0.2 и 0.665, UWin 1.0 и 3.2.
Проверяем:  Берлин, с 45 по 75 сутки, UExt 0.35 и 0.50, UWin 2.0.
"""
import numpy as np, pandas as pd, glob, os, re, sys
from scipy.linalg import expm
from weather import read_mos, WDIR
from sim3 import H_IN, RHO_CP, solar_vertical, _series

K_ENV, K_WIN = 0.65, 1.08          # поправка, найденная в fit.py

RUN = sorted(glob.glob("/home/claude/builda/output/*/"), key=os.path.getmtime)[-1]
START_DAY, DAYS = 45, 30
SUB = 12
dt = 3600.0 / SUB
HRS = 24 * DAYS
a, b_ = START_DAY * 24, START_DAY * 24 + HRS

w = read_mos(f"{WDIR}/Berlin.mos")
LAT = w["lat"] or 52.56
T_out = w["T_out"][a:b_]
Iv_full = solar_vertical(LAT, b_, w["HDirNor"][:b_], w["HDifHor"][:b_], w["HGloHor"][:b_])
Iv = Iv_full[a:b_]

hour = (np.arange(a, b_) % 24)
setp = np.where((hour >= 6) & (hour < 22), 22.0, 18.0)

L, W, Hf = 9.4125, 8.0, 3.04
fAWin = 0.14056
URoof, UFloor = 0.402, 0.514
cap_wall, cap_roof, cap_floor, cap_int = 192000.0, 81240.0, 483840.0, 145154.0
gWin, fATrans, ach = 0.7, 0.9, 0.3


def our_house(UExt, UWin, NF, k_env=K_ENV, k_win=K_WIN):
    H = Hf * NF
    Awg = 2 * (L + W) * H
    Awin_face = Awg / 4.0 * fAWin
    Awin = Awin_face * 4
    Aw, Ar, Ag = Awg - Awin, L * W * 1.63612217795485, L * W
    Ai, V, Af = 1.238235294117647 * Awg, L * W * H, L * W * NF
    h1, uw_ = _series(Aw, UExt)
    h2, ur_ = _series(Ar, URoof)
    h3, uf_ = _series(Ag, UFloor)
    return dict(h_env=h1 + h2 + h3, ua_env=(uw_ + ur_ + uf_) * k_env,
                C_env=Aw * cap_wall + Ar * cap_roof + Ag * cap_floor,
                h_int=H_IN * Ai, C_int=Ai * cap_int,
                ua_win=(Awin * UWin + V * ach * RHO_CP / 3600.0) * k_win,
                C_air=V * RHO_CP + Af * 2230.0, Awin_face=Awin_face)


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


print(f"Берлин, широта {LAT}, сутки {START_DAY}–{START_DAY+DAYS}")
print(f"наружная от {T_out.min():.1f} до {T_out.max():.1f}, средняя {T_out.mean():.1f} °C\n")

rows = []
for d in sorted(glob.glob(RUN + "_#*")):
    tag = os.path.basename(d)
    UExt = float(re.search(r"Uex_([\d.]+)", tag).group(1))
    NF = float(re.search(r"NFlo_(\d)", tag).group(1))
    mw = re.search(r"Uwi_([\d.]+)", tag)
    UWin = float(mw.group(1)) if mw else 2.0      # в этом наборе UWin не варьировался
    csv = glob.glob(d + "/*.csv")
    df = pd.read_csv([c for c in csv if os.path.basename(c).startswith("_#")][0])
    para = pd.read_csv([c for c in csv if "para_to_fmu" in c][0])
    Qnom = float(para[para.iloc[:, 0] == "heatingPower"].iloc[0, 1])
    Qref = df["Q_heating_MWh.y"].iloc[-1] - df["Q_heating_MWh.y"].iloc[0]
    Tref = (df["thermalZone.TAir"] - 273.15).mean()
    Q1, tr1 = run_ours(our_house(UExt, UWin, NF, 1.0, 1.0), Qnom)
    Q2, tr2 = run_ours(our_house(UExt, UWin, NF), Qnom)
    rows.append((tag, Q1 / Qref, Q2 / Qref, tr2.mean() - Tref))
    print(f"  {tag:30s} без поправки {Q1/Qref:5.2f}   с поправкой {Q2/Qref:5.2f}"
          f"   разница средней T {tr2.mean()-Tref:+5.2f} K")

r = np.array([x[2] for x in rows])
print(f"\nс поправкой: среднее {r.mean():.3f}, разброс {r.std():.3f}, "
      f"худший дом {abs(r-1).max()*100:.1f} %")
