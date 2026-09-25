import numpy as np, pandas as pd, sys
from sim import make_houses, weather, occupancy, body_distance
from sim24 import simulate24, learn24, DEFAULT24

N = 10; LIFE = 3000; SHORT = 20
SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 7
rng = np.random.default_rng(SEED)
houses = make_houses(N, rng)
env = []
for i in range(N):
    b = houses.iloc[i]; r = np.random.default_rng(SEED*100+i)
    T, s = weather(b, r); env.append((b, T, s, occupancy(b)))

learned, own = [], []
for i, (b, T, s, o) in enumerate(env):
    c, cost = learn24(b, T, s, o, DEFAULT24, LIFE, np.random.default_rng(SEED+i))
    learned.append(c); own.append(cost)
    print(f"дом {i}: полная жизнь {cost:9.1f}", flush=True)

D = body_distance(houses); rows = []
for j, (b, T, s, o) in enumerate(env):
    scratch_c, scratch = learn24(b, T, s, o, DEFAULT24, SHORT, np.random.default_rng(SEED*7+j))
    for i in range(N):
        if i == j: continue
        as_is = simulate24(b, learned[i], T, s, o)
        _, tuned = learn24(b, T, s, o, learned[i], SHORT, np.random.default_rng(SEED*13+j*10+i))
        rows.append(dict(donor=i, receiver=j, distance=D[i, j], scratch=scratch,
                         as_is=as_is, tuned=tuned, own=own[j],
                         gain_as_is=(scratch-as_is)/scratch*100,
                         gain_tuned=(scratch-tuned)/scratch*100))
    print(f"дом {j}: с нуля {scratch:9.1f}   (полная жизнь {own[j]:9.1f})", flush=True)

df = pd.DataFrame(rows); df.to_csv(f"transfer24_seed{SEED}.csv", index=False)
print(df[["gain_as_is","gain_tuned"]].mean().round(2).to_string())
print("корреляция с различием тел: as_is %.3f  tuned %.3f" %
      (df.distance.corr(df.gain_as_is), df.distance.corr(df.gain_tuned)))
