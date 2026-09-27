"""Чтение настоящих метеофайлов .mos из BuilDa.

Формат: строки с 30 числами. Надёжны только те столбцы, которые сами авторы
помечают как взятые из PVGIS: C1 время, C2 температура, C9 глобальная,
C10 прямая нормальная, C11 рассеянная горизонтальная. Остальные они сами
называют ненадёжными, поэтому не берём.
"""
from __future__ import annotations
import numpy as np, os, re

WDIR = "/home/claude/builda/resources/weatherFiles"

def read_mos(path: str) -> dict:
    """Возвращает часовые ряды: t_sec, T_out (°C), HGloHor, HDirNor, HDifHor (Вт/м²)."""
    rows = []
    lat, lon = None, None
    with open(path, "r", errors="replace") as f:
        for line in f:
            s = line.strip()
            if s.startswith("#LOCATION"):
                p = s.split(",")
                try:
                    lat, lon = float(p[6]), float(p[7])
                except (IndexError, ValueError):
                    pass
            if not s or s.startswith("#") or s.startswith("double"):
                continue
            parts = s.split()
            if len(parts) < 11:
                continue
            try:
                rows.append([float(x) for x in parts[:11]])
            except ValueError:
                continue
    a = np.array(rows)
    return {
        "name": os.path.basename(path).replace(".mos", ""),
        "lat": lat, "lon": lon,
        "t":       a[:, 0],
        "T_out":   a[:, 1],
        "HGloHor": a[:, 8],
        "HDirNor": a[:, 9],
        "HDifHor": a[:, 10],
        "hours":   len(a),
    }

# Заголовки пятилетних файлов скопированы с мюнхенского — сами авторы пишут,
# что информация в заголовке ненадёжна. Широту задаём сами по названию города.
LAT_FIX = {"Munich": 48.13, "Bratislava": 48.15, "Amsterdam": 52.37}

# Амстердам исключён: за пять лет минимум −1.7 °C, для настоящей записи
# это невозможно. Файл подозрителен, на нём ничего не строим.
LONG = [
    f"{WDIR}/5years/Munich.mos",
    f"{WDIR}/5years/Bratislava.mos",
    f"{WDIR}/2years/Berlin_2years.mos",
    f"{WDIR}/2years/London_2years.mos",
    f"{WDIR}/2years/Prague_2years.mos",
    f"{WDIR}/2years/Zurich_2years.mos",
    f"{WDIR}/2years/Belgrade_2years.mos",
    # однолетние: ещё полтора десятка климатов, уже лежат на диске
    f"{WDIR}/Vienna.mos",
    f"{WDIR}/Warsaw.mos",
    f"{WDIR}/Paris.mos",
    f"{WDIR}/Rome.mos",
    f"{WDIR}/Copenhagen.mos",
    f"{WDIR}/Stockholm.mos",
    f"{WDIR}/Dublin.mos",
    f"{WDIR}/Brussels.mos",
    f"{WDIR}/Budapest.mos",
    f"{WDIR}/Amsterdam.mos",
    f"{WDIR}/Muhldorf.mos",
    f"{WDIR}/USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.mos",
]

# широты для файлов, где заголовок скопирован или отсутствует
LAT_CITY = {
    "Munich": 48.13, "Bratislava": 48.15, "Amsterdam": 52.37, "Vienna": 48.21,
    "Warsaw": 52.23, "Paris": 48.85, "Rome": 41.90, "Copenhagen": 55.68,
    "Stockholm": 59.33, "Dublin": 53.35, "Brussels": 50.85, "Budapest": 47.50,
    "Muhldorf": 48.25, "Berlin_2years": 52.52, "London_2years": 51.51,
    "Prague_2years": 50.08, "Zurich_2years": 47.37, "Belgrade_2years": 44.79,
}

def load_all(paths=None) -> list:
    out = []
    for p in (paths or LONG):
        w = read_mos(p)
        if w["name"] in LAT_CITY:
            w["lat"] = LAT_CITY[w["name"]]
        elif w["lat"] is None:
            continue
        out.append(w)
    return out

if __name__ == "__main__":
    for w in load_all():
        T = w["T_out"]
        yrs = w["hours"] / 8760
        print(f'{w["name"]:22s} часов {w["hours"]:6d}  лет {yrs:.1f}  '
              f'T от {T.min():6.1f} до {T.max():5.1f}  средняя {T.mean():5.1f}  '
              f'солнце макс {w["HGloHor"].max():5.0f}')
