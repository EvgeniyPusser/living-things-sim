"""Опыт §4 на шаге 10 минут: обычный год против года с редкими событиями."""
import numpy as np, pandas as pd
from sim import make_houses
from life import WEEKS_YEAR
from life2 import weather_year
from life10 import year_cost10, tune10

OCC = np.r_[np.zeros(7), np.ones(11), np.zeros(6)].astype(bool)
rows=[]
for mode in ["ordinary","rare"]:
    rng = np.random.default_rng(11)
    houses = make_houses(24, rng).to_dict("records")
    # 5 предков отлаживаются у себя -> фонд
    fund=[]
    for b in houses[:10]:
        rare = None if mode=="ordinary" else ["cold","heat",None][rng.integers(0,3)]
        T,sun = weather_year(b, rng, rare=rare)
        occ = np.tile(OCC,7*WEEKS_YEAR)[:len(T)]
        fund.append(tune10(b, np.full(24,21.0), T, sun, occ, rng, tries=100))
    fund_s = np.median(np.array(fund),axis=0)
    anc    = fund[0]                          # один предок
    for i,b in enumerate(houses[10:22]):
        rare = None if mode=="ordinary" else ["cold","heat",None][rng.integers(0,3)]
        brk  = (mode=="rare") and rng.random()<0.2
        T,sun = weather_year(b, rng, rare=rare)
        occ = np.tile(OCC,7*WEEKS_YEAR)[:len(T)]
        a = year_cost10(b, np.full(24,21.0), T, sun, occ, brk)
        p = year_cost10(b, anc,    T, sun, occ, brk)
        f = year_cost10(b, fund_s, T, sun, occ, brk)
        rows.append(dict(mode=mode,house=i,rare=rare or "none",broken=brk,alone=a,anc=p,fund=f))
        print(mode,i,round(a,1),round(p,1),round(f,1),flush=True)
d=pd.DataFrame(rows)
d["g_anc"]=(d.alone-d.anc)/d.alone*100
d["g_fund"]=(d.alone-d.fund)/d.alone*100
d.to_csv("life10.csv",index=False)
print()
for m in ["ordinary","rare"]:
    x=d[d["mode"]==m]
    print("%-9s предок %+.1f%% (помог %.0f%%)   фонд %+.1f%% (помог %.0f%%)"%(
        m,x.g_anc.median(),(x.g_anc>0).mean()*100,x.g_fund.median(),(x.g_fund>0).mean()*100))
