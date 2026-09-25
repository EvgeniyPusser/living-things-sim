"""Готовим данные BDG2: одна площадка, здания с полными рядами."""
import pandas as pd, numpy as np

def load_site(site, min_cover=0.95, max_buildings=40, seed=0):
    meta = pd.read_csv("metadata.csv")
    meta = meta[meta.site_id == site]
    cols = ["timestamp"] + [c for c in pd.read_csv("electricity.csv", nrows=0).columns
                            if c.startswith(site + "_")]
    e = pd.read_csv("electricity.csv", usecols=cols, parse_dates=["timestamp"]).set_index("timestamp")
    cover = e.notna().mean()
    keep = cover[cover >= min_cover].index.tolist()
    # выбрасываем здания с почти постоянным или нулевым потреблением
    keep = [c for c in keep if e[c].std() > 0 and e[c].mean() > 1]
    rng = np.random.default_rng(seed)
    if len(keep) > max_buildings:
        keep = list(rng.choice(keep, max_buildings, replace=False))
    e = e[keep].interpolate(limit=6).dropna()

    w = pd.read_csv("weather.csv", parse_dates=["timestamp"])
    w = w[w.site_id == site].set_index("timestamp")[["airTemperature"]].sort_index()
    w = w[~w.index.duplicated()].reindex(e.index).interpolate(limit=12)
    return e, w, meta.set_index("building_id").loc[keep]

def features(index, temp):
    t = pd.DataFrame(index=index)
    t["hour"] = index.hour
    t["dow"] = index.dayofweek
    t["month"] = index.month
    t["is_weekend"] = (index.dayofweek >= 5).astype(int)
    t["temp"] = temp.values
    t["temp2"] = temp.values ** 2
    t["temp_lag24"] = pd.Series(temp.values, index=index).shift(24).bfill().values
    return t
