"""Честное сравнение шага. Всё одинаковое, кроме DT.

Один и тот же набор домов, одна и та же погода, один и тот же бюджет отладки.
Вопрос: меняется ли ПОРЯДОК условий при переходе с часа на 10 минут.
"""
import sys, numpy as np, pandas as pd
from sim import make_houses
from life import WEEKS_YEAR, LO, HI, COMFORT, BAND
from life2 import weather_year

HOURS_WEEK = 168
OCC = np.r_[np.zeros(7), np.ones(11), np.zeros(6)].astype(bool)

def live_week(body, sched, T_out, sun, occ, T0, sub):
    """sub = шагов в часе. 1 -> час, 6 -> 10 минут."""
    UA = body["UA"] + body["infil"]
    dt = 3600.0 / sub
    hours = np.arange(len(T_out)) % 24
    target = sched[hours]
    T = T0; energy = 0.0; disc = 0.0
    for i in range(len(T_out)):
        for _ in range(sub):
            u = np.clip(0.5 * (target[i] - T) / BAND, 0.0, 1.0)
            Q = u*body["Qmax"] + body["occ_gain"]*occ[i] + body["solar"]*sun[i]
            T = T + dt/body["C"] * (Q - UA*(T - T_out[i]))
            energy += u*body["Qmax"]*dt/3.6e6
            if occ[i] and T < COMFORT - BAND:
                d = COMFORT - BAND - T
                disc += (d if d < 3 else d*4) / sub
    return energy*0.25 + disc*2.0, T

def year_cost(body, sched, T, sun, occ, sub, broken=False):
    b = dict(body)
    if broken: b["Qmax"] = body["Qmax"]*0.5
    tot, Tm = 0.0, COMFORT
    for w in range(WEEKS_YEAR):
        sl = slice(w*HOURS_WEEK, (w+1)*HOURS_WEEK)
        c, Tm = live_week(b, sched, T[sl], sun[sl], occ[sl], Tm, sub); tot += c
    return tot

def tune(body, start, T, sun, occ, sub, rng, tries, broken=False):
    best = np.clip(np.array(start, float), LO, HI)
    bc = year_cost(body, best, T, sun, occ, sub, broken)
    for _ in range(tries):
        c = best.copy(); idx = rng.integers(0,24,rng.integers(1,6))
        c[idx] = np.clip(c[idx] + rng.normal(0,2.0,len(idx)), LO, HI)
        v = year_cost(body, c, T, sun, occ, sub, broken)
        if v < bc: best, bc = c, v
    return best

N_ANC, N_NEW, TRIES = 8, 10, 60
rows = []
for mode in ["ordinary", "rare"]:
    # ОДИН набор домов и погоды на оба шага
    rng0 = np.random.default_rng(77)
    houses = make_houses(N_ANC + N_NEW, rng0).to_dict("records")
    cases = []
    for b in houses:
        rare = None if mode == "ordinary" else ["cold","heat"][rng0.integers(0,2)]
        brk  = (mode == "rare") and (rng0.random() < 0.15)
        T, sun = weather_year(b, np.random.default_rng(int(rng0.integers(1,10**6))), rare=rare)
        occ = np.tile(OCC, 7*WEEKS_YEAR)[:len(T)]
        cases.append((b, T, sun, occ, rare or "none", brk))

    for sub, name in [(1, "1 час"), (6, "10 мин")]:
        r = np.random.default_rng(777)                      # одно зерно отладки
        fund = [tune(b, np.full(24,21.0), T, s, o, sub, r, TRIES, brk)
                for (b,T,s,o,_,brk) in cases[:N_ANC]]
        fund_s = np.median(np.array(fund), axis=0)
        anc    = fund[0]
        for k,(b,T,s,o,rare,brk) in enumerate(cases[N_ANC:]):
            a = year_cost(b, np.full(24,21.0), T, s, o, sub, brk)
            p = year_cost(b, anc,    T, s, o, sub, brk)
            f = year_cost(b, fund_s, T, s, o, sub, brk)
            rows.append(dict(mode=mode, step=name, house=k, rare=rare, broken=brk,
                             alone=a, anc=p, fund=f))
            print(mode, name, k, round(a,1), round(p,1), round(f,1), flush=True)

d = pd.DataFrame(rows)
d["g_anc"]  = (d.alone-d.anc )/d.alone*100
d["g_fund"] = (d.alone-d.fund)/d.alone*100
d.to_csv("step_compare.csv", index=False)
print()
print("%-10s %-8s %18s %18s" % ("год","шаг","предок","фонд"))
for mode in ["ordinary","rare"]:
    for name in ["1 час","10 мин"]:
        x = d[(d["mode"]==mode)&(d.step==name)]
        print("%-10s %-8s %+8.1f%% (помог %3.0f%%) %+8.1f%% (помог %3.0f%%)" % (
            mode, name, x.g_anc.median(), (x.g_anc>0).mean()*100,
            x.g_fund.median(), (x.g_fund>0).mean()*100))
