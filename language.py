"""Общий язык записей: градусы против безразмерных понятий.

Запись расписания можно передать двумя способами.

1. КАК ЕСТЬ: 24 числа в градусах.
2. В ОБЩИХ ПОНЯТИЯХ (безразмерно, относительно самого объекта):
     setback  — насколько ниже комфорта держим, когда людей нет
     lead     — за сколько часов до прихода начинаем греть
     day_off  — насколько ниже комфорта держим днём при людях (обычно 0)
     night_h  — сколько часов в сутки держим пониженную уставку
   Из этих четырёх чисел расписание собирается заново под ЛЮБОЙ объект,
   потому что они привязаны к его собственному комфорту и его расписанию людей.
"""
import numpy as np
from life import COMFORT, LO, HI

WORDS = ["setback", "lead", "day_off", "night_h"]

def to_words(sched, start_h):
    """Перевести расписание в общие понятия."""
    s = np.asarray(sched, float)
    occ = np.zeros(24, bool); occ[start_h:start_h+10] = True
    day = s[occ].mean() if occ.any() else COMFORT
    night = s[~occ].mean() if (~occ).any() else COMFORT
    setback = max(COMFORT - night, 0.0)
    day_off = max(COMFORT - day, 0.0)
    # за сколько часов до прихода уставка уже поднята выше ночного уровня
    lead = 0
    for k in range(1, 6):
        h = (start_h - k) % 24
        if s[h] > night + 0.5: lead = k
        else: break
    night_h = int((~occ).sum() - 0)
    return np.array([setback, lead, day_off, night_h], float)

def from_words(w, start_h):
    """Собрать расписание объекта из общих понятий."""
    setback, lead, day_off, _ = w
    s = np.full(24, COMFORT - max(day_off, 0.0))
    occ = np.zeros(24, bool); occ[start_h:start_h+10] = True
    s[~occ] = COMFORT - max(setback, 0.0)
    for k in range(1, int(round(lead)) + 1):
        s[(start_h - k) % 24] = COMFORT - max(day_off, 0.0)
    return np.clip(s, LO, HI)
