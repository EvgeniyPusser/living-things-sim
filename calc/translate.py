"""Собирает английскую версию страницы из русской. Один список замен."""
import re, os, json

PAIRS = [
 # заголовок и введение
 ("Тепловой стенд: что даёт унаследованный опыт в аварии",
  "Thermal bench: what inherited experience is worth in a failure"),
 ("<title>Тепловой стенд</title>", "<title>Thermal bench</title>"),
 ('lang="ru"', 'lang="en"'),
 ("Модель дома с тремя тепловыми ёмкостями считается здесь же, в браузере, на настоящих",
  "A three-capacity thermal model of a house runs here, in the browser, on measured"),
 ("метеоданных шести городов. Сравниваются два дома-близнеца: один подобрал расписание сам за первую зиму,",
  "weather for six cities. Two identical houses are compared: one tuned its own schedule over its first winter,"),
 ("второй начал с расписания, собранного по сорока домам, каждый из которых пережил свою аварию.",
  "the other started from a schedule pooled over forty houses, each of which had survived a failure of its own."),
 ("тёмный / светлый", "dark / light"),
 # панель управления
 ("Дом и погода", "House and weather"),
 ("Город", "City"),
 ("Стены, U —", "Walls, U —"),
 ("Вт/м²К", "W/m²K"),
 ("Тепловая масса —", "Thermal mass —"),
 ("Запас мощности —", "Power margin —"),
 ("Авария: отопление вполсилы, 72 часа", "Failure: heating at half power, 72 hours"),
 # графики
 ("Температура в доме во время самого холодного окна года",
  "Indoor temperature during the coldest window of the year"),
 ("Температура в доме за 72 часа аварии", "Indoor temperature over the 72 hours of the failure"),
 ("Наружная температура за те же 72 часа", "Outdoor temperature over the same 72 hours"),
 ("дом подбирал сам", "house tuned itself"),
 ("дом начал с фонда", "house started from the fund"),
 ("норма 21 °C", "norm 21 °C"),
 ("на улице, °C", "outdoors, °C"),
 ("${d===0?'начало':d+' сут'}", "${d===0?'start':'day '+d}"),
 ("начало", "start"),
 ("${d===0?'начало':d+' сут'}", "${d===0?'start':'day '+d}"),
 ("""<span><i class="sw" style="background:var(--s2)"></i>сам</span>""",
  """<span><i class="sw" style="background:var(--s2)"></i>alone</span>"""),
 ("хуже всех", "worst"),
 ("лучше всех", "best"),
 # плитки
 ("сам · самая низкая", "alone · lowest"),
 ("сам · часов холоднее 19 °C", "alone · hours below 19 °C"),
 ("сам · электричество", "alone · electricity"),
 ("фонд · самая низкая", "fund · lowest"),
 ("фонд · часов холоднее 19 °C", "fund · hours below 19 °C"),
 ("фонд · электричество", "fund · electricity"),
 ("°C в комнате", "°C indoors"),
 ("из 72", "of 72"),
 ("кВт·ч за 72 ч", "kWh over 72 h"),
 # население
 ("Население: 40 домов этого города, часов холоднее 19 °C за трое суток аварии",
  "Population: 40 houses in this city, hours below 19 \u00b0C during the three-day failure"),
 ("Часы холоднее 19 градусов по 40 домам", "Hours below 19 degrees across 40 houses"),
 ("с фондом", "with the fund"),
 # таблица расписаний
 ("Два расписания, которые сравниваются", "The two schedules being compared"),
 ("Что задаёт", "What it sets"),
 ("дом сам", "house alone"),
 ("фонд по 40 домам", "fund over 40 houses"),
 ("держать днём, °C", "hold during occupancy, °C"),
 ("ночью снижать до, °C", "night setback to, °C"),
 ("греть заранее, ч", "preheating lead, h"),
 ("зона нечувствительности, °C", "deadband, °C"),
 ("коэффициент регулятора", "controller gain"),
 ("Левая колонка подобрана прямо сейчас, на этой странице: дом сделал 40 попыток",
  "The left column was tuned just now, on this page: the house made 40 attempts"),
 ("на обычных днях до аварии. Правая — медиана расписаний сорока домов,",
  "on ordinary days before the failure. The right is the median of the schedules of forty houses,"),
 ("каждый из которых прожил свою зиму со своей аварией. Они сошлись на том, что ночное снижение",
  "each of which lived its own winter with its own failure. They converged on abandoning the night"),
 ("надо отменить, держать выше нормы и реагировать резче.",
  "setback, holding above the norm and reacting more sharply."),
 # что внутри
 ("Что внутри", "What is inside"),
 ("Модель", "Model"),
 ("Данные", "Data"),
 ("Проверка", "Validation"),
 ("три тепловые ёмкости: воздух с мебелью, оболочка, внутренние стены",
  "three thermal capacities: air with furniture, envelope, internal partitions"),
 ("теплонасос: и КПД, и доступная мощность падают с морозом",
  "heat pump: both efficiency and available capacity fall with outdoor temperature"),
 ("солнце по четырём фасадам от настоящего положения солнца",
  "solar gain on four facades from the true solar position"),
 ("шаг управления 15 минут, физика решается точно внутри шага",
  "15-minute control step; the physics is solved exactly within each step"),
 ("метеофайлы шести городов, 75 суток зимы, часовой шаг",
  "weather files for six cities, 75 winter days, hourly"),
 ("прямая и рассеянная радиация отдельно", "beam and diffuse radiation kept separate"),
 ("мощность отопления выбирается по DIN 18599-2", "heating power sized by DIN 18599-2"),
 ("та же модель сверена с BuilDa — открытым Modelica-генератором",
  "the same model is calibrated against BuilDa, the open Modelica generator by"),
 ("Fraunhofer, проверенным на\n      двух настоящих домах в Хольцкирхене",
  "Fraunhofer, itself validated on two\n      instrumented houses in Holzkirchen"),
 ("проверенным на", "validated on"),
 ("двух настоящих домах в Хольцкирхене", "two instrumented houses in Holzkirchen"),
 ("расхождение по расходу тепла 2 %, по средней", "agreement within 2 % on heat demand and 0.2 K on mean"),
 ("температуре 0.2 К,", "indoor temperature,"),
 ("на 12 домах в двух городах", "across 12 buildings in two cities"),
 # строки в скриптах
 ("`<b>час ${i}</b><br>`", "`<b>hour ${i}</b><br>`"),
 ("`<b>дом ${(+el.dataset.i)+1}</b><br>`", "`<b>house ${(+el.dataset.i)+1}</b><br>`"),
 ("сам: <b>", "alone: <b>"),
 ("фонд: <b>", "fund: <b>"),
 ("{n:'сам'", "{n:'alone'"),
 ("{n:'фонд'", "{n:'fund'"),
 ("{n:'улица'", "{n:'outdoors'"),
 ("самое холодное 72-часовое окно начинается на ${Math.floor(from/24)+1}-е сутки января;",
  "the coldest 72-hour window starts on day ${Math.floor(from/24)+1} of January;"),
 ("средняя наружная в нём ${wmean.toFixed(1)} °C, минимум ${wmin.toFixed(1)} °C.",
  "mean outdoor temperature in it ${wmean.toFixed(1)} °C, minimum ${wmin.toFixed(1)} °C."),
 ("Окно ищется по метеофайлу, а не задаётся.",
  "The window is found in the weather file, not prescribed."),
 ("Фонд лучше у ${better} домов из 40. В среднем ${mA.toFixed(1)} часа холода против ${mB.toFixed(1)}.",
  "The fund is better for ${better} of 40 houses. On average ${mA.toFixed(1)} hours below 19 °C against ${mB.toFixed(1)}."),
 ("Каждый дом здесь считается заново, с этой погодой и своими стенами.",
  "Every house here is computed afresh, with this weather and its own fabric."),
 # комментарии в коде
 ("/* ---------- модель ---------- */", "/* ---------- model ---------- */"),
 ("/* ---------- отрисовка ---------- */", "/* ---------- drawing ---------- */"),
 ("/* ---------- сборка ---------- */", "/* ---------- assembly ---------- */"),
 ("/* расписания: 5 чисел */", "/* schedules: five numbers */"),
 ("/* дом подбирает расписание сам, на ОБЫЧНЫХ днях до аварии.\n   Ровно как в опыте: подстраиваться на самой аварии нельзя. */",
  "/* the house tunes its schedule itself, on ORDINARY days before the failure.\n   Exactly as in the experiment: adapting during the event itself is not allowed. */"),
 ("// A*dt, затем exp через ряд с масштабированием", "// A*dt, then exp by scaling and squaring"),
 ("// Bd = A^{-1}(Ad - I) B, считаем численно через ряд: Bd ≈ dt*(I + Adt/2 + ...)*B",
  "// Bd = A^{-1}(Ad - I) B, by series: Bd = dt*(I + Adt/2 + ...)*B"),
 ("// разогрев массы перед окном", "// warm the mass before the window"),
 ("// население: 60 домов, разброс параметров", "// population: houses with scattered parameters"),
 ("/* точный переход за шаг: матричная экспонента 3x3 через масштабирование и возведение */",
  "/* exact step: 3x3 matrix exponential by scaling and squaring */"),
]

CITIES = {"Мюнхен":"Munich","Варшава":"Warsaw","Стокгольм":"Stockholm",
          "Вена":"Vienna","Лондон":"London","Чикаго":"Chicago"}

src = open('/home/claude/calc/stend.html', encoding='utf-8').read()
i = src.index('const WX = '); j = src.index('\n', i)
head, data, tail = src[:i], src[i:j], src[j:]

for ru, en in PAIRS:
    head = head.replace(ru, en)
    tail = tail.replace(ru, en)

for ru, en in CITIES.items():
    data = data.replace(f'"{ru}"', f'"{en}"')
    tail = tail.replace(f"sel.value='{ru}'", f"sel.value='{en}'")

out = head + data + tail
left = re.findall(r'[А-Яа-яЁё][А-Яа-яЁё \-,\.]{2,}', out)
open('/home/claude/calc/bench.html','w',encoding='utf-8').write(out)
print('готово,', round(os.path.getsize('/home/claude/calc/bench.html')/1024), 'КБ')
if left:
    print('ОСТАЛОСЬ ПО-РУССКИ:', len(left))
    for x in sorted(set(left))[:20]: print('  ', repr(x))
else:
    print('русского текста не осталось')
