"""Сети трубопроводов: обнаружение утечки и перенос правила между сетями.

Сеть = тело (граф труб). Правило обнаружения = то, что выучено за жизнь.
Вопрос тот же: можно ли отдать выученное правило другой сети.
"""
import numpy as np, pandas as pd, wntr, warnings
warnings.filterwarnings("ignore")

LIB = "/usr/local/lib/python3.11/dist-packages/wntr/library/networks/"
TEST = "/usr/local/lib/python3.11/dist-packages/wntr/tests/networks_for_testing/"
NETWORKS = {"Net1": LIB+"Net1.inp", "Net2": LIB+"Net2.inp", "Net3": LIB+"Net3.inp",
            "ky4": LIB+"ky4.inp", "Anytown": TEST+"Anytown.inp",
            "Herman": TEST+"CCWI17-HermanMahmoud.inp"}
DAYS, N_SENSORS = 3, 3

def run_scenario(path, rng, leak=False):
    wn = wntr.network.WaterNetworkModel(path)
    wn.options.time.duration = DAYS*24*3600
    wn.options.time.hydraulic_timestep = 3600
    wn.options.time.report_timestep = 3600
    wn.options.hydraulic.demand_model = "PDD"
    # случайный спрос этого сценария: сухая или мокрая неделя
    mult = rng.uniform(0.85, 1.15)
    for j in wn.junction_name_list:
        wn.get_node(j).demand_timeseries_list[0].base_value *= mult
    start = None
    if leak:
        cand = [j for j in wn.junction_name_list if wn.get_node(j).base_demand and wn.get_node(j).base_demand > 0]
        node = rng.choice(cand if cand else wn.junction_name_list)
        wn.get_node(node).emitter_coefficient = float(rng.uniform(1.0, 6.0))  # размер утечки
        start = int(rng.integers(12, DAYS*24 - 6))
    res = wntr.sim.EpanetSimulator(wn).run_sim()
    p = res.node["pressure"]
    p = p[[c for c in wn.junction_name_list if c in p.columns]]
    p.index = (p.index / 3600).astype(int)
    if leak and start is not None:
        # утечка включается не с начала: до start берём давления сценария без утечки
        wn2 = wntr.network.WaterNetworkModel(path)
        wn2.options.time.duration = DAYS*24*3600
        wn2.options.time.hydraulic_timestep = 3600
        wn2.options.time.report_timestep = 3600
        wn2.options.hydraulic.demand_model = "PDD"
        for j in wn2.junction_name_list:
            wn2.get_node(j).demand_timeseries_list[0].base_value *= mult
        p0 = wntr.sim.EpanetSimulator(wn2).run_sim().node["pressure"]
        p0 = p0[p.columns]; p0.index = p.index
        p = pd.concat([p0.loc[p.index < start], p.loc[p.index >= start]])
    label = np.zeros(len(p), dtype=int)
    if leak and start is not None:
        label[p.index >= start] = 1
    return p, label

def sensors(path, rng):
    wn = wntr.network.WaterNetworkModel(path)
    js = wn.junction_name_list
    k = min(N_SENSORS, len(js))
    return list(rng.choice(js, k, replace=False))

def scenarios(name, n_normal, n_leak, seed):
    """Сценарии одной сети: часть без утечки, часть с утечкой."""
    rng = np.random.default_rng(seed)
    path = NETWORKS[name]
    sens = sensors(path, np.random.default_rng(seed))
    out = []
    for i in range(n_normal + n_leak):
        p, y = run_scenario(path, rng, leak=(i >= n_normal))
        noise = rng.normal(0, 1.0, p[sens].shape)          # шум датчиков
        out.append((p[sens].to_numpy() + noise, y, p.index.to_numpy()))
    return out, sens

def baseline(scen_normal):
    """Норма по часам суток: среднее и разброс давления на каждом датчике."""
    H = np.concatenate([h % 24 for _, _, h in scen_normal])
    P = np.vstack([p for p, _, _ in scen_normal])
    mu = np.vstack([P[H == h].mean(axis=0) for h in range(24)])
    sd = np.vstack([P[H == h].std(axis=0) + 1e-6 for h in range(24)])
    return mu, sd

def featurize(scen, mu, sd):
    """Признаки, не зависящие от числа и имён узлов: сводка z-оценок за час."""
    X, Y = [], []
    for p, y, h in scen:
        hh = h % 24
        z = (p - mu[hh]) / sd[hh]
        X.append(np.column_stack([z.min(1), z.max(1), z.mean(1), z.std(1),
                                  (z < -2).sum(1), hh]))
        Y.append(y)
    return np.vstack(X), np.concatenate(Y)
