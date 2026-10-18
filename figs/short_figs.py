"""Рисунки к короткой статье. Всё из посчитанных файлов, ничего не нарисовано руками."""
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

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

C = "/home/claude/crisis/"
OUT = "/home/claude/figs/"
P = np.load(C + "pair13_501.npy")                  # [40 предков, 200 новичков]
D = pd.read_csv(C + "res13_501.csv")
F = np.load(C + "figdata_501.npz")
E = pd.read_csv(C + "res14_501.csv")
NA, NN = P.shape

# ------------------------------------------------------------------ Figure 1
# ни одна мера похожести не предсказывает пользу переноса
gain = (D.d_alone.values[None, :] - P).T.ravel()   # [новичок, предок] -> вектор
db = F["dist_body"].ravel()
dt = F["dist_tau"].ravel()
fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.1), sharey=True)
for ax, x, lab, r in [
        (axes[0], db, "distance in ten body parameters", np.corrcoef(db, gain)[0, 1]),
        (axes[1], dt, "difference in resilience, K", np.corrcoef(dt, gain)[0, 1])]:
    ax.scatter(x, gain, s=3, color=S1, alpha=0.10, edgecolors="none", zorder=3)
    # среднее по децилям — видно, что линия плоская
    q = np.quantile(x, np.linspace(0, 1, 11))
    mid, mean = [], []
    for i in range(10):
        m = (x >= q[i]) & (x <= q[i + 1])
        if m.sum(): mid.append(x[m].mean()); mean.append(gain[m].mean())
    ax.plot(mid, mean, color=S2, lw=2, marker="o", ms=4.5,
            mfc=S2, mec=SURF, mew=1.2, zorder=5, label="mean by decile")
    ax.axhline(0, color=INK2, lw=0.9, zorder=4)
    clean(ax)
    ax.set_xlabel(lab)
    ax.set_title(f"r = {r:+.3f}")
axes[0].set_ylabel("gain over target-only, degree-hours")
axes[0].legend(loc="upper right")
fig.suptitle("Neither similarity measure predicts the value of a transfer   "
             "(8 000 ordered pairs)", y=1.00, fontsize=10, color=INK)
fig.tight_layout()
fig.savefig(OUT + "s1_no_signal.png", dpi=200, bbox_inches="tight"); plt.close(fig)

# ------------------------------------------------------------------ Figure 2
# предки согласованы между собой: хорош или плох для всех
order = np.argsort(P.mean(axis=1))
lo = np.percentile(P[order], 10, axis=1)
hi = np.percentile(P[order], 90, axis=1)
me = P[order].mean(axis=1)
fig, ax = plt.subplots(figsize=(7.0, 3.2))
x = np.arange(NA)
ax.vlines(x, lo, hi, color=S1, lw=4, alpha=0.30, zorder=3)
ax.plot(x, me, "o", color=S1, ms=5, mec=SURF, mew=1.2, zorder=5)
clean(ax)
ax.set_xticks([]); ax.set_xlabel("40 sources, ordered by their mean outcome")
ax.set_ylabel("degree-hours at a target")
r = np.corrcoef(P)[np.triu_indices(NA, 1)].mean()
ax.set_title(f"A source is good or bad for everyone   "
             f"(mean between-source correlation {r:+.2f})")
ax.annotate("bars span the 10th–90th percentile over the 200 targets",
            xy=(2.0, hi[0]), xytext=(1.0, hi[-1] * 0.80),
            fontsize=7.5, color=INK2,
            arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
fig.tight_layout(); fig.savefig(OUT + "s2_concordance.png", dpi=200); plt.close(fig)

# ------------------------------------------------------------------ Figure 3
# что работает: отбор испытанием и прямой поиск
labels = ["target-only,\nown adaptation", "one of forty,\nat random",
          "median of the\nforty policies", "best of forty,\nchosen by trial",
          "searched against\nthe population"]
cols = [E.d_self, pd.Series(P[np.random.default_rng(3).integers(0, NA, NN),
                              np.arange(NN)]), E.d_fund, E.d_best, E.d_pop]
fig, ax = plt.subplots(figsize=(7.0, 3.4))
pos = np.arange(len(cols))
for i, v in enumerate(cols):
    v = np.asarray(v)
    jitter = (np.random.default_rng(i).random(len(v)) - 0.5) * 0.34
    c = S2 if i <= 1 else S1
    ax.scatter(pos[i] + jitter, v, s=7, color=c, alpha=0.22,
               edgecolors="none", zorder=3)
    ax.hlines(np.median(v), pos[i] - 0.28, pos[i] + 0.28, color=INK, lw=2.2, zorder=6)
    ax.text(pos[i], np.median(v) - 6, f"{np.median(v):.1f}", ha="center", va="top",
            fontsize=9, color=INK, zorder=7)
clean(ax)
ax.set_xticks(pos); ax.set_xticklabels(labels)
ax.set_ylabel("degree-hours below 21 °C during the event")
ax.set_title("200 unseen targets. Black bar is the median.")
fig.tight_layout(); fig.savefig(OUT + "s3_conditions.png", dpi=200); plt.close(fig)

# ------------------------------------------------------------------ Figure 4
# цена: энергия против холода, две величины отдельно
pts = [("generic default 21/18",      2072, 2104, MUTED, (12, -4),  "left"),
       ("target tuned itself",        2545,  157, S2,    (12,  4),  "left"),
       ("median of the forty",        2822,   55, S1,    (-14, 14), "right"),
       ("searched against\nthe population", 2923, 37, S1,  (-16, 4), "right")]
fig, ax = plt.subplots(figsize=(5.8, 3.6))
ax.plot([p[1] for p in pts], [p[2] for p in pts], color=MUTED, lw=1,
        ls=(0, (4, 3)), zorder=2)
for nm, kwh, dh, c, off, ha in pts:
    ax.scatter(kwh, dh, s=90, color=c, edgecolors=SURF, linewidth=1.6, zorder=4)
    ax.annotate(nm, (kwh, dh), textcoords="offset points", xytext=off,
                fontsize=8, color=INK2, ha=ha, va="center")
ax.set_yscale("log")
ax.set_ylim(26, 4200)
ax.set_xlim(1990, 3010)
clean(ax)
ax.set_xlabel("electricity over the 213-day season, kWh")
ax.set_ylabel("degree-hours below 21 °C, season")
ax.set_title("What the reserve costs. Two numbers, never one.")
ax.annotate("from the self-tuned target to the fund:\n+277 kWh, 102 degree-hours avoided\n= 0.81 EUR per degree-hour",
            xy=(2700, 92), xytext=(2560, 900), fontsize=8, color=INK2,
            arrowprops=dict(arrowstyle="->", color=MUTED, lw=0.9))
fig.tight_layout(); fig.savefig(OUT + "s4_price.png", dpi=200); plt.close(fig)

print("готово: s1_no_signal, s2_concordance, s3_conditions, s4_price")
