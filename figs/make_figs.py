"""Рисунки к статье. Все данные — из посчитанных файлов, ничего не выдумано."""
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# палитра из справочника dataviz, светлый режим
S1, S2, S3 = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#8a8983"
SURF, GRID = "#fcfcfb", "#e5e4df"

plt.rcParams.update({
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
    "font.family": "DejaVu Sans", "font.size": 9,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "axes.titlesize": 10,
    "axes.titleweight": "normal", "axes.titlecolor": INK,
    "xtick.color": INK2, "ytick.color": INK2,
    "xtick.labelsize": 8, "ytick.labelsize": 8,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "legend.frameon": False, "legend.fontsize": 8,
})

def clean(ax, xgrid=False):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.set_axisbelow(True)
    ax.grid(axis="x" if xgrid else "y")
    if not xgrid: ax.grid(axis="x", visible=False)
    else: ax.grid(axis="y", visible=False)

OUT = "/home/claude/figs/"

# ---------------------------------------------------------------- Figure 1
# распределение потолка: сколько вообще можно взять расписанием
d = pd.read_csv("/home/claude/houses/baseline_selflearn.csv").sort_values("best_gain")
fig, ax = plt.subplots(figsize=(6.4, 3.0))
x = np.arange(len(d))
ax.bar(x, d.best_gain, color=S1, width=0.72, zorder=3)
clean(ax)
ax.set_xticks([]); ax.set_xlabel("30 buildings, ordered by how much is available")
ax.set_ylabel("upper bound on any schedule method, %")
ax.axhline(d.best_gain.median(), color=MUTED, lw=1, ls=(0, (4, 3)), zorder=2)
ax.annotate(f"median {d.best_gain.median():.1f} %", xy=(1.5, d.best_gain.median()),
            xytext=(1.5, d.best_gain.median() + 3.5), color=INK2, fontsize=8)
top = d.iloc[-1]
ax.annotate(f"{top.best_gain:.0f} %", xy=(len(d) - 1, top.best_gain),
            xytext=(len(d) - 5.5, top.best_gain - 1.5), color=INK, fontsize=8)
ax.set_title("Most buildings have nothing to gain; one in five has a great deal")
fig.tight_layout(); fig.savefig(OUT + "fig1_ceiling.png", dpi=200); plt.close(fig)

# ---------------------------------------------------------------- Figure 2
# выигрыш от фонда против потолка
c = pd.read_csv("/home/claude/houses/ceiling.csv")
r = c.g_fund_tuned.corr(c.g_ceiling)
fig, ax = plt.subplots(figsize=(4.6, 3.6))
ax.scatter(c.g_ceiling, c.g_fund_tuned, s=42, color=S1,
           edgecolor=SURF, linewidth=1.6, zorder=3)
lim = max(c.g_ceiling.max(), c.g_fund_tuned.max()) * 1.08
ax.plot([0, lim], [0, lim], color=MUTED, lw=1, ls=(0, (4, 3)), zorder=2)
ax.annotate("everything available\nis taken", xy=(lim * 0.62, lim * 0.62),
            xytext=(lim * 0.30, lim * 0.80), color=MUTED, fontsize=7.5)
clean(ax)
ax.set_xlabel("available to any method, %")
ax.set_ylabel("taken by the fund, %")
ax.set_title(f"What the fund gains tracks what was there  (r = {r:+.2f})")
fig.tight_layout(); fig.savefig(OUT + "fig2_fund_vs_ceiling.png", dpi=200); plt.close(fig)

# ---------------------------------------------------------------- Figure 3
# шаг сетки: порядок условий не меняется
s = pd.read_csv("/home/claude/houses/step_compare.csv")
cells, anc, fund = [], [], []
for mode, mlab in [("ordinary", "ordinary year"), ("rare", "rare conditions")]:
    for step, slab in [("1 час", "1 h"), ("10 мин", "10 min")]:
        x = s[(s["mode"] == mode) & (s.step == step)]
        cells.append(f"{mlab}\n{slab}")
        anc.append(x.g_anc.median()); fund.append(x.g_fund.median())
fig, ax = plt.subplots(figsize=(6.4, 3.4))
i = np.arange(len(cells)); w = 0.36
ax.bar(i - w/2 - 0.01, anc,  w, label="one predecessor", color=S2, zorder=3)
ax.bar(i + w/2 + 0.01, fund, w, label="median over predecessors", color=S1, zorder=3)
for k in i:
    ax.text(k - w/2 - 0.01, anc[k] - 0.18, f"{anc[k]:+.1f}", ha="center", va="top",
            fontsize=7.5, color=INK2)
    ax.text(k + w/2 + 0.01, fund[k] + 0.12, f"{fund[k]:+.1f}", ha="center", va="bottom",
            fontsize=7.5, color=INK2)
ax.axhline(0, color=INK2, lw=0.9, zorder=4)
clean(ax)
ax.set_ylim(min(anc) - 1.3, max(fund) + 0.7)
ax.set_xticks(i); ax.set_xticklabels(cells)
ax.set_ylabel("change against starting alone, %")
ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.02), ncols=2)
ax.set_title("The integration step changes magnitudes, not the ordering", pad=26)
fig.tight_layout(); fig.savefig(OUT + "fig3_step.png", dpi=200); plt.close(fig)

# ---------------------------------------------------------------- Figure 4
# мутация: распределение последствий
m = pd.read_csv("/home/claude/houses/mutation.csv")
fig, ax = plt.subplots(figsize=(6.4, 3.0))
v = m.delta.clip(-3, 3)
bins = np.linspace(-3, 3, 61)
n, edges = np.histogram(v, bins=bins)
mid = (edges[:-1] + edges[1:]) / 2
cols = [S1 if x > 0 else MUTED for x in mid]
ax.bar(mid, n, width=(edges[1]-edges[0]) * 0.9, color=cols, zorder=3)
ax.axvline(0, color=INK2, lw=0.9, zorder=4)
clean(ax)
ax.set_xlabel("effect of one random change on the year's cost, %  (clipped at ±3)")
ax.set_ylabel("number of trials")
ax.set_title("Mutation: 2 400 random changes to a schedule in 16 buildings")
worse = (m.delta < 0).mean() * 100
better = (m.delta > 0).mean() * 100
big = (m.delta > 1).sum()
ax.text(0.985, 0.92, f"harmful {worse:.0f} %\nbeneficial {better:.0f} %\nabove +1 %: {big} of {len(m)}",
        transform=ax.transAxes, ha="right", va="top", fontsize=8, color=INK2)
nclip = (m.delta <= -3).sum()
ax.annotate(f"{nclip} trials worse than \u22123 %,\npiled into this bar",
            xy=(-2.95, n[0]), xytext=(-2.55, n[0] * 0.80),
            color=INK2, fontsize=7.5,
            arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
fig.tight_layout(); fig.savefig(OUT + "fig4_mutation.png", dpi=200); plt.close(fig)

# ---------------------------------------------------------------- Figure 5
# дефект шага, видно глазами
import sys; sys.path.insert(0, "/home/claude/houses")
from sim import make_houses
rng = np.random.default_rng(12)
b = make_houses(10, rng).to_dict("records")[0]
UA = b["UA"] + b["infil"]
def trace(sub, hours=12):
    dt = 3600.0 / sub; T = 18.0; ts = [0.0]; Ts = [T]
    for i in range(hours):
        for k in range(sub):
            u = np.clip(0.5 * (21.0 - T) / 0.5, 0, 1)
            Q = u * b["Qmax"] + b["occ_gain"]
            T = T + dt / b["C"] * (Q - UA * (T - (-5.0)))
            ts.append(i + (k + 1) / sub); Ts.append(T)
    return np.array(ts), np.array(Ts)
fig, ax = plt.subplots(figsize=(6.4, 3.0))
t1, T1 = trace(1); t6, T6 = trace(6)
ax.plot(t1, T1, color=S2, lw=2, label="one-hour step", zorder=3)
ax.plot(t6, T6, color=S1, lw=2, label="ten-minute step", zorder=4)
ax.axhline(21.0, color=MUTED, lw=1, ls=(0, (4, 3)), zorder=2)
ax.annotate("target 21 °C", xy=(0.3, 21.0), xytext=(0.3, 21.35), color=MUTED, fontsize=8)
clean(ax)
ax.set_xlabel("hours"); ax.set_ylabel("indoor temperature, °C")
ax.legend(loc="lower right", ncols=2)
ax.set_title("The oscillation is an artefact of the step size")
fig.tight_layout(); fig.savefig(OUT + "fig5_step_defect.png", dpi=200); plt.close(fig)

# ---------------------------------------------------------------- Figure 6
# язык записи: доля объектов, которым помогло
fig, ax = plt.subplots(figsize=(4.6, 2.8))
labs = ["degrees", "relative to\nthe receiver"]
vals = [83.5, 99.0]
ax.barh(labs, vals, color=[MUTED, S1], height=0.5, zorder=3)
for y, v in enumerate(vals):
    ax.text(v - 1.6, y, f"{v:.0f} %", ha="right", va="center", fontsize=9, color=SURF)
clean(ax, xgrid=True)
ax.set_xlim(0, 100); ax.set_xlabel("share of objects the fund helped, %")
ax.set_title("The same records, two ways of writing them")
fig.tight_layout(); fig.savefig(OUT + "fig6_language.png", dpi=200); plt.close(fig)

print("готово")
