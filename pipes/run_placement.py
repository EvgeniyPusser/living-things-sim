"""Перенос ПРАВИЛА РАССТАНОВКИ датчиков между сетями."""
import numpy as np, pandas as pd, time
from placement import (NETWORKS, simulate_network, normal_baseline, evaluate,
                       place, learn_weights, FEATS)

K = 3                     # датчиков
N_NORMAL, N_LEAK = 20, 25
DONOR_LEAKS, NEW_LEAKS = 15, 2          # аварий у донора и у новичка
TRIES_DONOR, TRIES_NEW = 200, 30        # сколько вариантов расстановки успевает перебрать

store = {}
for i, name in enumerate(NETWORKS):
    t0 = time.time()
    P, Y, H, feats = simulate_network(name, N_NORMAL, N_LEAK, seed=20 + i)
    mu, sd, cols = normal_baseline(P, H, N_NORMAL)
    feats = feats.loc[[c for c in cols if c in feats.index]]
    keep = [cols.index(c) for c in feats.index]
    mu, sd = mu[:, keep], sd[:, keep]
    P = [p[feats.index] for p in P]
    store[name] = dict(P=P, Y=Y, H=H, feats=feats, mu=mu, sd=sd,
                       donor_idx=range(N_NORMAL, N_NORMAL + DONOR_LEAKS),
                       new_idx=range(N_NORMAL, N_NORMAL + NEW_LEAKS),
                       test_idx=list(range(10)) + list(range(N_NORMAL + DONOR_LEAKS, N_NORMAL + N_LEAK)))
    print(f"{name}: узлов {feats.shape[0]}, {time.time()-t0:5.1f}с", flush=True)

rng = np.random.default_rng(5)
W = {}
for n, d in store.items():
    W[n], ap = learn_weights(d["feats"], d["P"], d["Y"], d["H"], d["mu"], d["sd"],
                             d["donor_idx"], K, TRIES_DONOR, rng)
    print(f"{n}: своё правило расстановки выучено, качество на своей жизни {ap:.3f}", flush=True)

rows = []
for b, d in store.items():
    ev = lambda idxs: evaluate(idxs, d["P"], d["Y"], d["H"], d["mu"], d["sd"], d["test_idx"], seed=99)
    rnd = np.median([ev(list(rng.choice(len(d["feats"]), K, replace=False))) for _ in range(20)])
    w_new, _ = learn_weights(d["feats"], d["P"], d["Y"], d["H"], d["mu"], d["sd"],
                             d["new_idx"], K, TRIES_NEW, rng)
    own_short = ev(place(w_new, d["feats"], K))
    others = [a for a in NETWORKS if a != b]
    singles = [ev(place(W[a], d["feats"], K)) for a in others]
    # правило популяции: то, что в среднем лучше всего работает у всех остальных
    pool_w, pool_ap = None, -1
    for _ in range(TRIES_DONOR):
        w = rng.normal(0, 1, len(FEATS))
        m = np.mean([evaluate(place(w, store[a]["feats"], K), store[a]["P"], store[a]["Y"],
                              store[a]["H"], store[a]["mu"], store[a]["sd"],
                              store[a]["donor_idx"], seed=7) for a in others])
        if m > pool_ap: pool_w, pool_ap = w, m
    pool = ev(place(pool_w, d["feats"], K))
    # популяция как начальная точка: короткий поиск вокруг неё на опыте новичка
    best_w, best = pool_w, evaluate(place(pool_w, d["feats"], K), d["P"], d["Y"], d["H"],
                                    d["mu"], d["sd"], d["new_idx"], seed=99)
    for _ in range(TRIES_NEW):
        w = best_w + rng.normal(0, 0.4, len(FEATS))
        a = evaluate(place(w, d["feats"], K), d["P"], d["Y"], d["H"], d["mu"], d["sd"],
                     d["new_idx"], seed=99)
        if a > best: best_w, best = w, a
    pool_tuned = ev(place(best_w, d["feats"], K))
    rows.append(dict(network=b, random=rnd, own_short=own_short,
                     donor_median=np.median(singles), donor_best=max(singles),
                     pool=pool, pool_tuned=pool_tuned))
    print(f"{b}: случайно {rnd:.3f} | своё по 2 авариям {own_short:.3f} | чужое {np.median(singles):.3f} "
          f"| популяция {pool:.3f} | популяция+подстройка {pool_tuned:.3f}", flush=True)

d = pd.DataFrame(rows); d.to_csv("placement_transfer.csv", index=False)
print(); print(d.round(3).to_string(index=False)); print()
for c in ["own_short", "donor_median", "donor_best", "pool", "pool_tuned"]:
    g = (d[c] - d["random"]) / d["random"] * 100
    print("%-13s против случайной расстановки: медиана %+6.1f%%, лучше в %.0f%% сетей"
          % (c, g.median(), (g > 0).mean() * 100))
print()
for c in ["donor_median", "pool", "pool_tuned"]:
    g = (d[c] - d["own_short"]) / d["own_short"] * 100
    print("%-13s против своего правила по 2 авариям: медиана %+6.1f%%" % (c, g.median()))
