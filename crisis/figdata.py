"""Повторяет последовательность случайных чисел из run13 без счёта,
чтобы получить те же тела и те же расстояния для рисунков."""
import numpy as np, pandas as pd
from weather import load_all
from sim3 import *
SEED, N_ANC, N_NEW, LIFE, YEAR, OCT1, HOR = 501, 40, 200, 400, 8760, 6552, 5112
rng = np.random.default_rng(SEED)
cities = load_all()
years = [(c["name"], c["lat"], c, y) for c in cities for y in range(c["hours"]//YEAR)]
half = len(years)//2
def assign(n, pool):
    idx = rng.permutation(len(pool)); return [pool[idx[i%len(pool)]] for i in range(n)]
anc_years = assign(N_ANC, years[:half])
new_years = assign(N_NEW, years[half:])

def series(yl):
    n=len(yl); T=np.empty((n,HOR))
    for i,(nm,lat,c,y) in enumerate(yl):
        a,b=y*YEAR,(y+1)*YEAR; T[i]=np.roll(c["T_out"][a:b],-OCT1)[:HOR]
    return T

b_a = make_bodies(N_ANC, rng); T_a = series(anc_years); size_heating(b_a, T_a)
net_a = thermal_network(b_a)
# столько же обращений к rng, сколько съел поиск предков
for _ in range(LIFE):
    rng.normal(0, 1, (N_ANC, 5))
b_n = make_bodies(N_NEW, rng); T_n = series(new_years); size_heating(b_n, T_n)
net_n = thermal_network(b_n)

def resilience(b, net, T_ext=-10.0, T0=21.0, hours=72):
    n=len(net["C_air"]); Ad,Bd=discretise(net,3600.0)
    fe=net["ua_env"]/(net["h_env"]+net["ua_env"])
    T=np.empty((n,3)); T[:,0]=T0; T[:,1]=T0+(T_ext-T0)*fe; T[:,2]=T0
    for k in range(hours):
        w=np.stack([net["ua_win"]*T_ext, net["ua_env"]*T_ext, np.zeros(n)],axis=1)
        T=np.einsum("nij,nj->ni",Ad,T)+np.einsum("nij,nj->ni",Bd,w)
    return T[:,0]

tau_a, tau_n = resilience(b_a, net_a), resilience(b_n, net_n)
FEATS=["UExt","URoof","UFloor","UWin","fAWin","ach","cap_wall","cap_int","A_floor","Qmax"]
def zm(b, ref):
    return np.stack([ (np.asarray(b[f],float)-np.asarray(ref[f],float).mean())
                      /(np.asarray(ref[f],float).std()+1e-9) for f in FEATS], axis=1)
Za, Zn = zm(b_a,b_a), zm(b_n,b_a)
dist_body = np.sqrt(((Zn[:,None,:]-Za[None,:,:])**2).mean(axis=2))
dist_tau  = np.abs(tau_n[:,None]-tau_a[None,:])

d = pd.read_csv("res13_501.csv")
ok = np.allclose(tau_n, d.tau.values, atol=1e-6)
print("повтор совпал с записанным:", ok)
np.savez("figdata_501.npz", dist_body=dist_body, dist_tau=dist_tau,
         tau_a=tau_a, tau_n=tau_n)
print("сохранено figdata_501.npz")
