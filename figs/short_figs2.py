"""Ещё два рисунка к короткой статье: сверка с BuilDa и ход температуры в аварии."""
import numpy as np, pandas as pd, glob, os, re, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.linalg import expm
sys.path.insert(0, "/home/claude/crisis")
from weather import read_mos, load_all, WDIR
from sim3 import *
import sim3

S1, S2 = "#2a78d6", "#eb6834"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#8a8983"
SURF, GRID = "#fcfcfb", "#e5e4df"
plt.rcParams.update({
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
    "font.family": "DejaVu Sans", "font.size": 9,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2,
    "axes.titlesize": 10, "axes.titleweight": "normal", "axes.titlecolor": INK,
    "xtick.color": INK2, "ytick.color": INK2, "xtick.labelsize": 8, "ytick.labelsize": 8,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "legend.frameon": False, "legend.fontsize": 8,
})
def clean(ax, xg=False):
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    for s in ("left", "bottom"): ax.spines[s].set_color(GRID)
    ax.set_axisbelow(True)
    ax.grid(axis="x" if xg else "y")
    ax.grid(axis="y" if xg else "x", visible=False)

OUT = "/home/claude/figs/"

# ================================================================= Figure 0
# сверка приведённой модели с BuilDa: 8 подогнанных + 4 непросмотренных
H_IN_, RHO = 2.7, 1.2 * 1005
L, W, Hf = 9.4125, 8.0, 3.04
fAWin, URoof, UFloor = 0.14056, 0.402, 0.514
cw, cr, cf, ci = 192000.0, 81240.0, 483840.0, 145154.0
gW, fT, ach = 0.7, 0.9, 0.3
K_ENV, K_WIN = 0.65, 1.08
SUBc = 12

def ser(A, U):
    hin = H_IN_ * A
    Rt = 1 / max(U * A, 1e-9); Ri = 1 / hin
    return hin, 1 / max(Rt - Ri, Rt * 0.05)

def house(UExt, UWin, NF, corr):
    ke, kw = (K_ENV, K_WIN) if corr else (1.0, 1.0)
    H = Hf * NF; Awg = 2 * (L + W) * H
    Awf = Awg / 4 * fAWin; Awin = Awf * 4; Aw = Awg - Awin
    Ar = L * W * 1.63612217795485; Ag = L * W
    Ai = 1.238235294117647 * Awg; V = L * W * H; Af = L * W * NF
    h1, u1 = ser(Aw, UExt); h2, u2 = ser(Ar, URoof); h3, u3 = ser(Ag, UFloor)
    return dict(h_env=h1 + h2 + h3, ua_env=(u1 + u2 + u3) * ke,
                C_env=Aw * cw + Ar * cr + Ag * cf,
                h_int=H_IN_ * Ai, C_int=Ai * ci,
                ua_win=(Awin * UWin + V * ach * RHO / 3600) * kw,
                C_air=V * RHO + Af * 2230, Awf=Awf)

def run_ours(p, Qnom, T_out, Iv, hrs):
    dt = 3600.0 / SUBc
    Ca, Ce, Ci = p["C_air"], p["C_env"], p["C_int"]
    he, hi, uw, ue = p["h_env"], p["h_int"], p["ua_win"], p["ua_env"]
    A = np.array([[-(he + hi + uw) / Ca, he / Ca, hi / Ca],
                  [he / Ce, -(he + ue) / Ce, 0.0],
                  [hi / Ci, 0.0, -hi / Ci]])
    B = np.diag([1 / Ca, 1 / Ce, 1 / Ci])
    M = np.zeros((6, 6)); M[:3, :3] = A; M[:3, 3:] = B
    E = expm(M * dt); Ad, Bd = E[:3, :3], E[:3, 3:]
    Qs = p["Awf"] * gW * fT * Iv.sum(axis=1)
    hour = np.arange(hrs) % 24
    setp = np.where((hour >= 6) & (hour < 22), 22.0, 18.0)
    T = np.array([20.0, 19.0, 20.0]); Q = 0.0
    for k in range(hrs):
        for _ in range(SUBc):
            u = 1.0 if setp[k] - T[0] > 0 else 0.0
            Qh = u * Qnom
            T = Ad @ T + Bd @ np.array([Qh + 0.3 * Qs[k] + uw * T_out[k],
                                        ue * T_out[k], 0.7 * Qs[k]])
            Q += Qh * dt / 3.6e9
    return Q

def collect(rundir, city, lat, a, days, uwin_default=None):
    w = read_mos(f"{WDIR}/{city}")
    hrs = 24 * days
    T_out = w["T_out"][a:a + hrs]
    Iv = solar_vertical(lat, a + hrs, w["HDirNor"][:a + hrs],
                        w["HDifHor"][:a + hrs], w["HGloHor"][:a + hrs])[a:a + hrs]
    rows = []
    for d in sorted(glob.glob(rundir + "_#*")):
        tag = os.path.basename(d)
        UExt = float(re.search(r"Uex_([\d.]+)", tag).group(1))
        NF = float(re.search(r"NFlo_(\d)", tag).group(1))
        mw = re.search(r"Uwi_([\d.]+)", tag)
        UWin = float(mw.group(1)) if mw else uwin_default
        csv = glob.glob(d + "/*.csv")
        df = pd.read_csv([c for c in csv if os.path.basename(c).startswith("_#")][0])
        para = pd.read_csv([c for c in csv if "para_to_fmu" in c][0])
        Qnom = float(para[para.iloc[:, 0] == "heatingPower"].iloc[0, 1])
        Qref = df["Q_heating_MWh.y"].iloc[-1] - df["Q_heating_MWh.y"].iloc[0]
        q0 = run_ours(house(UExt, UWin, NF, False), Qnom, T_out, Iv, hrs)
        q1 = run_ours(house(UExt, UWin, NF, True), Qnom, T_out, Iv, hrs)
        rows.append((q0 / Qref, q1 / Qref))
    return np.array(rows)

runs = sorted(glob.glob("/home/claude/builda/output/*/"), key=os.path.getmtime)
fitd = [r for r in runs if glob.glob(r + "_#*Uwi*")][-1]
vald = [r for r in runs if glob.glob(r + "_#*") and not glob.glob(r + "_#*Uwi*")][-1]
fit = collect(fitd, "Munich.mos", 48.13, 0, 30)
val = collect(vald, "Berlin.mos", 52.47, 45 * 24, 30, uwin_default=2.0)

fig, ax = plt.subplots(figsize=(6.2, 3.2))
groups = [("fitted on these\n8 buildings, Munich, January", fit),
          ("held out: 4 buildings,\nBerlin, different month", val)]
x = 0
ticks, labs = [], []
for nm, arr in groups:
    for j, (u, c) in enumerate(arr):
        ax.plot([x, x], [u, c], color=GRID, lw=1.2, zorder=2)
        ax.plot(x, u, "o", ms=6, color=S2, mec=SURF, mew=1.2, zorder=4,
                label="before correction" if (x == 0) else None)
        ax.plot(x, c, "o", ms=6, color=S1, mec=SURF, mew=1.2, zorder=5,
                label="after correction" if (x == 0) else None)
        x += 1
    ticks.append(x - len(arr) / 2 - 0.5); labs.append(nm); x += 1.4
ax.axhline(1.0, color=INK2, lw=1.2, zorder=3)
ax.axhspan(0.95, 1.05, color=S1, alpha=0.07, zorder=1)
clean(ax)
ax.set_xticks(ticks); ax.set_xticklabels(labs)
ax.set_ylabel("heat demand, ours / BuilDa")
ax.legend(loc="upper right", ncols=2)
ax.set_title("The reduced model against BuilDa. Shaded band is ±5 %.")
fig.tight_layout(); fig.savefig(OUT + "s0_calibration.png", dpi=200); plt.close(fig)
print("s0_calibration: подогнанные", np.round(fit[:, 1], 3),
      " непросмотренные", np.round(val[:, 1], 3))

# ================================================================= Figure 5
# ход температуры в окне аварии у одного дома, четыре условия
YEAR, OCT1, HOR, WIN_H = 8760, 6552, 5112, 72
SEED, N_NEW, N_MOD = 501, 200, 40
rng = np.random.default_rng(SEED); rng_n = np.random.default_rng(SEED + 1000)
cities = load_all()
years = [(c["name"], c["lat"], c, y) for c in cities for y in range(c["hours"] // YEAR)]
half = len(years) // 2
def assign(n, pool, r):
    idx = r.permutation(len(pool)); return [pool[idx[i % len(pool)]] for i in range(n)]
_ = assign(N_MOD, years[:half], rng)
new_years = assign(N_NEW, years[half:], rng_n)
T = np.empty((N_NEW, HOR)); Iv = np.empty((N_NEW, HOR, 4))
for i, (nm, lat, c, y) in enumerate(new_years):
    a, b = y * YEAR, (y + 1) * YEAR
    T[i] = np.roll(c["T_out"][a:b], -OCT1)[:HOR]
    iv = solar_vertical(lat, YEAR, c["HDirNor"][a:b], c["HDifHor"][a:b], c["HGloHor"][a:b])
    Iv[i] = np.roll(iv, -OCT1, axis=0)[:HOR]
b = make_bodies(N_NEW, rng_n); size_heating(b, T)
net = thermal_network(b); Ad, Bd = discretise(net, 3600.0 / SUB)
occ = occupancy(b["start_h"], HOR)
kk = np.ones(WIN_H) / WIN_H
st = np.empty(N_NEW, int)
for i in range(N_NEW):
    mv = np.convolve(T[i], kk, mode="valid"); mv[:24 * 30] = 1e9
    st[i] = int(np.argmin(mv))
win = np.zeros((N_NEW, HOR)); sc = np.ones((N_NEW, HOR)); pre = np.zeros((N_NEW, HOR))
for i in range(N_NEW):
    win[i, st[i]:st[i] + WIN_H] = 1.0
    sc[i, st[i]:st[i] + WIN_H] = 0.5
    pre[i, :st[i]] = 1.0

each = np.load("/home/claude/crisis/w14_each_501.npy")
pop = np.load("/home/claude/crisis/w14_pop_501.npy")
fund = np.median(each, axis=0)
E = pd.read_csv("/home/claude/crisis/res14_501.csv")
# берём дом, чей результат ближе всего к медиане по условию «сам»
pick = int(np.argmin(np.abs(E.d_self.values - np.median(E.d_self.values))))

def trace(sched):
    """Температура воздуха в окне у одного дома."""
    one = {k: (v[pick:pick + 1] if isinstance(v, np.ndarray) and v.ndim == 1 else v)
           for k, v in b.items()}
    n1 = {k: v[pick:pick + 1] for k, v in net.items()}
    A1, B1 = Ad[pick:pick + 1], Bd[pick:pick + 1]
    T1 = T[pick:pick + 1]; I1 = Iv[pick:pick + 1]; o1 = occ[pick:pick + 1]
    s1 = sc[pick:pick + 1]; w1 = win[pick:pick + 1]
    r = live(one, n1, A1, B1, np.array([sched]), T1, I1, o1, s1, w1, w1)
    return r

# восстановим ход температуры: повторим цикл live вручную для одного дома
def trace_T(sched):
    dt = 3600.0 / SUB
    one_b = {k: (v[pick:pick + 1] if isinstance(v, np.ndarray) else v) for k, v in b.items()}
    n1 = {k: v[pick:pick + 1] for k, v in net.items()}
    A1, B1 = Ad[pick], Bd[pick]
    T_occ, T_away, lead, band, gain = sched
    hour = np.arange(HOR) % 24
    s = int(b["start_h"][pick])
    oc = ((hour >= s) & (hour < s + 10)).astype(float)
    nx = ((((hour + int(round(lead))) % 24) >= s) &
          (((hour + int(round(lead))) % 24) < s + 10)).astype(float)
    target = np.where((oc + nx) > 0, T_occ, T_away)
    rot = b["rot"][pick]
    wf = np.array([0.25 + 0.15 * np.cos(rot - g) for g in np.radians([0, 90, 180, -90])])
    wf /= wf.sum()
    Qs = b["A_win"][pick] * 0.7 * 0.9 * (Iv[pick] @ wf)
    x = np.array([COMFORT, COMFORT - 2.0, COMFORT - 0.5]); out = []
    a0 = max(0, st[pick] - 240)
    for k in range(a0, st[pick] + WIN_H):
        To = T[pick, k]
        Tsup = np.clip(20 + b["steep"][pick] * (20 - To), 25, 55)
        cop = np.clip(b["eta_hp"][pick] * (Tsup + 273.15) / max(Tsup - To, 8), 1.3, 5.5)
        qcap = b["Qmax"][pick] * sc[pick, k] * capacity_factor(np.array([To]))[0]
        for _ in range(SUB):
            u = np.clip(gain * (target[k] - x[0]) / max(band, 1e-6), 0, 1)
            w = np.array([u * qcap + 320 * oc[k] + 0.3 * Qs[k] + n1["ua_win"][0] * To,
                          n1["ua_env"][0] * To, 0.7 * Qs[k]])
            x = A1 @ x + B1 @ w
        if k >= st[pick]: out.append(x[0])
    return np.array(out)

conds = [("target-only, own adaptation", None, S2),
         ("median of the forty", fund, MUTED),
         ("searched against the population", pop, S1)]
s_self = None
# подстройка «сам» для этого дома: воспроизводим ту же процедуру
span = HI - LO
r0 = np.random.default_rng(5)
best = np.tile(DEFAULT, (N_NEW, 1))
bc = live(b, net, Ad, Bd, best, T, Iv, occ, sc, win, pre)["cost_obj"]
step = np.full(N_NEW, 0.25)
for _ in range(40):
    cand = np.clip(best + r0.normal(0, 1, best.shape) * step[:, None] * span, LO, HI)
    c = live(b, net, Ad, Bd, cand, T, Iv, occ, sc, win, pre)["cost_obj"]
    bt = c < bc; best[bt] = cand[bt]; bc = np.where(bt, c, bc)
    step = np.where(bt, step, np.maximum(step * 0.97, 0.02))
s_self = best[pick]

fig, axes = plt.subplots(2, 1, figsize=(6.6, 4.3), sharex=True,
                         gridspec_kw={"height_ratios": [2.4, 1]})
ax = axes[0]
for nm, sched, col in [("target-only, own adaptation", s_self, S2),
                       ("median of the forty", fund, MUTED),
                       ("searched against the population", pop, S1)]:
    y = trace_T(sched)
    ax.plot(np.arange(len(y)), y, color=col, lw=2, label=nm, zorder=4)
ax.axhline(COMFORT, color=INK2, lw=1.4, ls=(0, (5, 4)), zorder=3)
ax.annotate("norm 21 °C", xy=(WIN_H - 1, COMFORT), xytext=(WIN_H - 1, COMFORT + 0.45),
            ha="right", fontsize=8, color=INK2)
clean(ax)
ax.set_ylabel("indoor air, °C")
ax.legend(loc="lower left", ncols=1)
ax.set_title("One target, the 72 hours of its own event. Capacity halved throughout.")
ax2 = axes[1]
ax2.plot(np.arange(WIN_H), T[pick, st[pick]:st[pick] + WIN_H], color=MUTED, lw=1.8)
clean(ax2)
ax2.set_ylabel("outdoors, °C"); ax2.set_xlabel("hours from the start of the event")
ax2.set_xticks([0, 24, 48, 72])
fig.tight_layout(); fig.savefig(OUT + "s5_trace.png", dpi=200); plt.close(fig)
print("s5_trace: дом", pick, new_years[pick][0],
      "минимум снаружи", round(float(T[pick, st[pick]:st[pick] + WIN_H].min()), 1))
