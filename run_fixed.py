"""Опыт: помогает ли перенос контроллера и до какого различия домов."""
import numpy as np, pandas as pd, itertools, sys
from sim_fixed import (make_houses, weather, occupancy, simulate, learn,
                 body_distance, DEFAULT, CTRL_NAMES, BODY_NAMES)

N_HOUSES = 10
LIFE_BUDGET = 400      # полная жизнь: дом учится сам
SHORT_BUDGET = 40      # короткая жизнь нового дома: успеть немного
SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 7

rng = np.random.default_rng(SEED)
houses = make_houses(N_HOUSES, rng)
env = []
for i in range(N_HOUSES):
    b = houses.iloc[i]
    r = np.random.default_rng(SEED * 100 + i)
    T_out, sun = weather(b, r)
    env.append((b, T_out, sun, occupancy(b)))

# 1. каждый дом прожил жизнь и выучил свой контроллер
learned, own_cost = [], []
for i, (b, T_out, sun, occ) in enumerate(env):
    c, cost = learn(b, T_out, sun, occ, DEFAULT, LIFE_BUDGET, np.random.default_rng(SEED + i))
    learned.append(c); own_cost.append(cost)
    print(f"дом {i}: своё обучение → {cost:8.1f}", flush=True)

D = body_distance(houses)
rows = []
for j, (b, T_out, sun, occ) in enumerate(env):
    r = np.random.default_rng(SEED * 1000 + j)
    # с нуля: типовая настройка + короткая жизнь
    scratch_ctrl, scratch = learn(b, T_out, sun, occ, DEFAULT, SHORT_BUDGET, r)
    base_default = simulate(b, DEFAULT, T_out, sun, occ)
    for i in range(N_HOUSES):
        if i == j:
            continue
        # (1) чужой контроллер как есть
        as_is = simulate(b, learned[i], T_out, sun, occ)
        # (2) чужой контроллер как начальная точка + та же короткая жизнь
        _, tuned = learn(b, T_out, sun, occ, learned[i], SHORT_BUDGET,
                         np.random.default_rng(SEED * 1000 + j * 10 + i))
        rows.append(dict(donor=i, receiver=j, distance=D[i, j],
                         scratch=scratch, as_is=as_is, tuned=tuned,
                         default=base_default, own=own_cost[j],
                         gain_as_is=(scratch - as_is) / scratch * 100,
                         gain_tuned=(scratch - tuned) / scratch * 100))
    print(f"дом {j}: с нуля {scratch:8.1f}  (типовая настройка {base_default:8.1f})", flush=True)

df = pd.DataFrame(rows)
df.to_csv(f"transferFIX_seed{SEED}.csv", index=False)
print(df[["distance","gain_as_is","gain_tuned"]].describe().round(2))
