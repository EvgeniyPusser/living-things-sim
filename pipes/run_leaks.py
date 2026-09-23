"""Перенос правила обнаружения утечки между сетями."""
import numpy as np, pandas as pd, lightgbm as lgb, itertools, time
from sklearn.metrics import average_precision_score
from leaks import NETWORKS, scenarios, baseline, featurize

N_NORMAL, N_LEAK = 25, 25
DONOR_LEAK, NEW_LEAK = 18, 1          # сколько аварий видел донор и сколько новичок
TEST_NORMAL, TEST_LEAK = 7, 7
PAR = dict(n_estimators=150, learning_rate=0.07, num_leaves=15, min_child_samples=30,
           verbose=-1, random_state=3)

data = {}
for i, name in enumerate(NETWORKS):
    t0 = time.time()
    s, sens = scenarios(name, N_NORMAL, N_LEAK, seed=10 + i)
    normal, leaky = s[:N_NORMAL], s[N_NORMAL:]
    mu, sd = baseline(normal[:10])                       # норма по обычной работе
    tr = normal[10:10+8] + leaky[:DONOR_LEAK]            # жизнь донора
    new = normal[10:10+8] + leaky[:NEW_LEAK]             # жизнь новичка
    te = normal[-TEST_NORMAL:] + leaky[-TEST_LEAK:]      # проверка
    data[name] = dict(donor=featurize(tr, mu, sd), new=featurize(new, mu, sd),
                      test=featurize(te, mu, sd))
    print(f"{name}: {time.time()-t0:5.1f}с, часов обучения донора {len(data[name]['donor'][1])}", flush=True)

donors = {n: lgb.LGBMClassifier(**PAR).fit(*d["donor"]) for n, d in data.items()}
rows = []
for b in NETWORKS:
    Xte, Yte = data[b]["test"]
    ap = lambda m: average_precision_score(Yte, m.predict_proba(Xte)[:, 1])
    scratch = ap(lgb.LGBMClassifier(**PAR).fit(*data[b]["new"]))
    others = [a for a in NETWORKS if a != b]
    Xp = np.vstack([data[a]["donor"][0] for a in others])
    Yp = np.concatenate([data[a]["donor"][1] for a in others])
    pool_m = lgb.LGBMClassifier(**PAR).fit(Xp, Yp)
    pool = ap(pool_m)
    pool_t = ap(lgb.LGBMClassifier(**PAR).fit(*data[b]["new"], init_model=pool_m.booster_))
    singles = {a: ap(donors[a]) for a in others}
    tuned = {a: ap(lgb.LGBMClassifier(**PAR).fit(*data[b]["new"], init_model=donors[a].booster_))
             for a in others}
    rows.append(dict(network=b, scratch=scratch,
                     donor_median=np.median(list(singles.values())),
                     donor_best=max(singles.values()), donor_worst=min(singles.values()),
                     tuned_median=np.median(list(tuned.values())),
                     pool=pool, pool_tuned=pool_t))
    print(f"{b}: своё {scratch:.3f} | чужое (медиана) {rows[-1]['donor_median']:.3f} | "
          f"популяция {pool:.3f} | популяция+подстройка {pool_t:.3f}", flush=True)

d = pd.DataFrame(rows); d.to_csv("leak_transfer.csv", index=False)
print()
print(d.round(3).to_string(index=False))
print()
for c in ["donor_median", "donor_best", "tuned_median", "pool", "pool_tuned"]:
    g = (d[c] - d.scratch) / d.scratch * 100
    print("%-13s против своего правила: медиана %+6.1f%%, лучше в %.0f%% сетей"
          % (c, g.median(), (g > 0).mean() * 100))
