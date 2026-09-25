# Подача на Preprints.org — что в какое поле

Файл для загрузки: **What_is_worth_inheriting_v2.pdf** (последний, с расширенным раскрытием про ИИ).

Аккаунт заводите сами: `preprints.org` → Submit → нужен логин MDPI. Я паролей не касаюсь.

---

## Перед подачей: ORCID

Если у вас его нет — заведите на `orcid.org`. Бесплатно, минут пять.
Это номер, который навсегда связывает статьи с вами, а не с однофамильцем.
Площадки на него смотрят, и в письмах он выглядит солиднее, чем ничего.

---

## Title

```
What is worth inheriting: a measurement platform for transferred operating experience in technical systems
```

## Authors

```
First name     Evgenii
Last name      Bogomazov-Pusser
Email          evgeniipusser88@gmail.com
Affiliation    Independent researcher
Country        Israel
ORCID          (вставить, если завели)
Corresponding  да, галочка
```

## Abstract

A newly commissioned building, machine or network has no operating history of its own. The question here is not whether experience can be transferred between such objects. It can, and methods exist. The question is what is worth transferring, and how that can be measured instead of asserted.

We describe a measurement platform. An individual object lives once, without replay. Losses accumulate as they occur. The object starts either from a generic default, from the record of one predecessor, or from a fund aggregated over many predecessors. The protocol was applied in three domains — a synthetic population of buildings, measured electricity records of 40 real non-residential buildings, and six benchmark water distribution networks — and to five candidate inherited objects.

The paper is written as the chain of experiments in the order they were performed. It includes three defects of the instrument found after the experiments were finished, and what each defect changed. Five results hold across domains. First, a complete inherited representation applied unchanged is usually worse than what the receiver can obtain for itself, even from two weeks of its own history. Second, similarity of bodies does not predict whether transfer helps; an apparent correlation of +0.21 in the first experiment turned out to be an artefact of the cost function and fell to +0.05 once the artefact was removed. Third, what transfers is the arrangement of observation, not the values: the rule for placing sensors transfers where the detection rule does not. Fourth, the quality a predecessor achieved does not pass to its successors. Fifth, most of the harm attributed to inheritance is an artefact of the units in which records are written; the same records expressed in quantities defined relative to the receiver raise the share of objects helped from 81–84 % to 99 %. A separate measurement shows that four objects in five have almost nothing to gain, while what an object gains from the fund correlates at +0.91 with how much it had to gain — so a fund can be read as a ranking of which objects are worth attention.

## Keywords

```
transfer learning; operating experience; buildings; water distribution networks; negative transfer; sensor placement; measurement protocol; negative results
```

## Subject

```
Engineering → Civil Engineering
```
Если такого нет в списке — берите ближайшее из Engineering:
Control and Systems Engineering, либо Energy and Fuel Technology.

## Funding

```
This research received no external funding.
```

## Conflicts of Interest

```
The author declares no conflict of interest.
```

## Data Availability Statement

```
The measured building data are the public Building Data Genome Project 2 dataset
(doi:10.1038/s41597-020-00712-x). The water distribution networks are the benchmark
networks distributed with WNTR. All code and result files are available from the author
on request.
```

Когда положите код на Zenodo — эту строку заменим на DOI кода.

## Declaration об использовании ИИ

Оно уже стоит в самой статье, в разделе Reproducibility:

> The experiments were designed by the author. The code and the manuscript were prepared with AI assistance (Claude, Anthropic). The questions, the protocol, the choice of what to measure, the decision of what to report, and the interpretation of the results are the author's. No AI system is an author, and the author takes full responsibility for the content.

Если форма отдельно спросит про ИИ — вставьте этот же абзац.

---

## После подачи

Проверка у редакторов занимает около суток. Придёт DOI.

Дальше письма: Эйбену, Капоццоли, Миллеру. Тексты готовы в `Письмо-рассылка.md`,
адреса:

```
a.e.eiben@vu.nl
alfonso.capozzoli@polito.it
clayton@nus.edu.sg   (может быть устаревшим, он перешёл в SMU)
```

Ни одно письмо не уйдёт без вашего «да» на конкретный текст и конкретный адрес.

---

## Что в статье остаётся недоделанным

Всё это написано в самой статье, в разделе Limitations. Прячем ничего не стали.

```
шаг в 1 час       даёт колебание температуры в несколько градусов.
                  объявлен, не исправлен
сломанное отопление   8 случаев
опыты §4 и §5     10 домов, одно зерно
§11.1             20 новичков, один выдуманный домен
диапазон стенда   медиана 2.5% против 16% в настоящей перенастройке зданий
```
