"""Наследование расстановки датчиков, а не правила обнаружения.

Сеть имитируется один раз (50 сценариев, давления во всех узлах).
Расстановка задаётся ПРАВИЛОМ: веса на признаки узла (степень, удалённость
от источника, высота, спрос, диаметр труб). Правило не привязано к номерам
узлов, поэтому его можно отдать другой сети.
"""
import numpy as np, pandas as pd, wntr, warnings, networkx as nx
from sklearn.metrics import average_precision_score
warnings.filterwarnings("ignore")
from leaks import NETWORKS, run_scenario

FEATS = ["degree", "hops", "elev", "demand", "diam"]

def node_features(path):
    wn = wntr.network.WaterNetworkModel(path)
    G = wn.to_graph().to_undirected()
    sources = wn.reservoir_name_list + wn.tank_name_list
    hops = {}
    for s in sources:
        for n, d in nx.single_source_shortest_path_length(G, s).items():
            hops[n] = min(hops.get(n, 1e9), d)
    rows = {}
    for j in wn.junction_name_list:
        node = wn.get_node(j)
        dias = [wn.get_link(l).diameter for l in G.edges(j) and [] ] if False else \
               [wn.get_link(name).diameter for name in wn.pipe_name_list
                if wn.get_link(name).start_node_name == j or wn.get_link(name).end_node_name == j]
        rows[j] = dict(degree=G.degree(j), hops=hops.get(j, 0), elev=node.elevation,
                       demand=node.base_demand or 0.0,
                       diam=float(np.mean(dias)) if dias else 0.0)
    f = pd.DataFrame(rows).T[FEATS].astype(float)
    return (f - f.mean()) / (f.std(ddof=0) + 1e-9)          # внутри сети, чтобы сети были сравнимы

def simulate_network(name, n_normal=20, n_leak=25, seed=0):
    rng = np.random.default_rng(seed)
    path = NETWORKS[name]
    P, Y, H = [], [], []
    for i in range(n_normal + n_leak):
        p, y = run_scenario(path, rng, leak=(i >= n_normal))
        P.append(p); Y.append(y); H.append(p.index.to_numpy() % 24)
    return P, Y, H, node_features(path)

def normal_baseline(P, H, n_normal):
    cols = P[0].columns
    allP = np.vstack([p[cols].to_numpy() for p in P[:n_normal]])
    allH = np.concatenate(H[:n_normal])
    mu = np.vstack([allP[allH == h].mean(0) for h in range(24)])
    sd = np.vstack([allP[allH == h].std(0) + 1e-6 for h in range(24)])
    return mu, sd, list(cols)

def evaluate(sensors_idx, P, Y, H, mu, sd, idx_range, noise=1.0, seed=0):
    """Качество обнаружения при данной расстановке: средняя точность."""
    rng = np.random.default_rng(seed)
    s, y = [], []
    for i in idx_range:
        p = P[i].to_numpy()[:, sensors_idx] + rng.normal(0, noise, (len(P[i]), len(sensors_idx)))
        z = (p - mu[H[i]][:, sensors_idx]) / sd[H[i]][:, sensors_idx]
        s.append(-z.min(1))                      # чем сильнее провал давления, тем выше тревога
        y.append(Y[i])
    return average_precision_score(np.concatenate(y), np.concatenate(s))

def place(weights, feats, k):
    """Выбрать k узлов по правилу: сумма признаков с весами."""
    score = feats.to_numpy() @ np.asarray(weights)
    return list(np.argsort(-score)[:k])

def learn_weights(feats, P, Y, H, mu, sd, idx_range, k, n_try, rng, seed=0):
    best, best_ap = None, -1
    for _ in range(n_try):
        w = rng.normal(0, 1, len(FEATS))
        ap = evaluate(place(w, feats, k), P, Y, H, mu, sd, idx_range, seed=seed)
        if ap > best_ap:
            best, best_ap = w, ap
    return best, best_ap
