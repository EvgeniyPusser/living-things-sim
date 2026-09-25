# CISBAT 2027 — тезисы

```
срок          15 ноября 2026
подача        conftool.com/cisbat2027/
тема          Operation → Predictive & adaptive control
рисунок       figs/fig1_ceiling.png
```

---

## Title

```
What is worth inheriting between buildings: a measurement of transferred operating experience, and how much there is to transfer at all
```

## Abstract (781 words)

```
CONTEXT

A newly commissioned building has no operating history of its own. An older
building has years of it, and when that building is refitted or replaced the
history is lost. Transfer learning between buildings is an active field, and
reviews of it treat negative transfer as a recognised phenomenon whose causes
are unsettled and whose source-selection problem is open. The question asked
here is prior to method: given a building with an operating history, which
part of that history is worth preserving so another building can use it, and
how much is available to be gained in the first place.

Two commitments shape the work. An individual lives once: a building
experiences each winter a single time and pays for its mistakes in comfort
and energy, so any protocol that lets the receiver replay its own year makes
self-acquisition artificially cheap and inheritance artificially worthless.
And the measured quantity is loss accumulated during the first year of
operation, not the quality of a final model, because the value of inherited
experience is the cost of acquiring it again.

METHOD

One protocol is applied across three domains: a synthetic population of
buildings differing in ten thermal and use parameters; measured hourly
electricity for 40 non-residential buildings from the Building Data Genome
Project 2; and six benchmark water distribution networks simulated in EPANET
through WNTR. Each domain supplies a body, a single pass through time, an
accumulated loss, and a record left behind.

Every experiment compares the same starting conditions for a newcomer:
starting alone from a generic default; starting from the record of one
predecessor; starting from a fund aggregated over many predecessors; and the
fund followed by the newcomer's own short adaptation. What counts as
confirmation and what as refutation is declared before each run, and negative
outcomes are reported as they came.

A separate measurement bounds all of these. For each building the cheapest
schedule is found by search with full knowledge of that building's own year.
No method that changes only the schedule can beat that number, so it is an
upper bound for self-learning, for inheritance and for a commissioning
engineer alike.

RESULTS

A complete inherited representation applied unchanged is the worst of the
conditions tested, in every domain. On measured buildings a donor's whole
load model loses a median of 85 % of accuracy and is worse than the
receiver's own model in 93 % of 1 560 ordered pairs. Combining population
knowledge with the receiver's own 14 days is the only condition that helps a
majority, and it helps 62 %.

Similarity between buildings does not predict whether transfer helps.
Correlation of gain with difference in log floor area is -0.001 and with
difference in year of construction -0.06; buildings of the same declared use
lose 82 % where buildings of a different use lose 86 %. In the synthetic
domain an apparent correlation of +0.21 with physical distance between bodies
proved to be an artefact of the authors' own cost function and fell to +0.05
once repaired.

The quality a predecessor achieved does not pass to its successors. Across
two populations the slope of successor gain on predecessor quality was -2.12
and -0.38: negative in sign, undetermined in size. One predecessor helps
roughly half of newcomers however good it is, while a fund over many helps
97-98 %.

Most of the harm attributed to inheritance is an effect of units. The same
records re-expressed in quantities defined relative to the receiving building
- depth of setback below its own comfort temperature, lead time before its
own occupancy hour - raise the share of buildings helped from 84 % to 99 %.

The bounding measurement is the one with the most direct consequence for
practice. Across 30 buildings the median available gain from any schedule
method is 2.5 %, but the distribution is extremely uneven: four buildings in
five have almost nothing to gain, while one in five has between 11 % and
41 % and has not taken it. What a building gains from the fund correlates at
+0.91 with how much that building had to gain, so the fund can be read as a
ranking. Selecting the five newcomers with the largest gain from the fund
captures 77 % of all the gain available in the population; five chosen at
random capture 30 %. No individual building can make this determination about
itself, because to know that 40 % is available one must have seen buildings
where 2 % is.

The paper also reports three defects found in the authors' own instrument
after the experiments were complete, and one previously reported figure that
a controlled repetition did not support and which is withdrawn. The
integration step was the most consequential: repeating the central experiment
at one hour and at ten minutes with everything else held identical leaves the
ordering of conditions unchanged and the magnitudes inflated.

Limitations are stated plainly. Two of three domains are simulated; the
measured domain contains no setpoints and no record of operator intervention,
so the inherited object there is a predictive model rather than a policy; and
the synthetic domain's median of 2.5 % is narrow against the 16 % median
measured in real re-commissioning, so the orderings should be read and the
magnitudes should not be carried over.
```

## References (up to 6)

```
[1] Xu, S. et al. One for Many: Transfer Learning for Building HVAC Control.
    Proc. BuildSys '20, 2020. doi:10.1145/3408308.3427617

[2] Pinto, G., Wang, Z., Roy, A., Hong, T., Capozzoli, A. Transfer learning
    for smart buildings: a critical review of algorithms, applications, and
    future perspectives. Advances in Applied Energy 5, 100084 (2022).
    doi:10.1016/j.adapen.2022.100084

[3] Miller, C. et al. The Building Data Genome Project 2. Scientific Data 7,
    368 (2020). doi:10.1038/s41597-020-00712-x

[4] Klise, K. A. et al. A software framework for assessing the resilience of
    drinking water systems to disasters. Environmental Modelling & Software
    95, 420-431 (2017).

[5] Mills, E. Building commissioning: a golden opportunity for reducing
    energy costs and greenhouse gas emissions in the United States. Energy
    Efficiency 4, 145-173 (2011). doi:10.1007/s12053-011-9116-8

[6] Luo, J., Miras, K., Tomczak, J., Eiben, A. E. Enhancing robot evolution
    through Lamarckian principles. Scientific Reports 13, 21109 (2023).
    doi:10.1038/s41598-023-48338-4
```

## Figure

```
figs/fig1_ceiling.png
```

Подпись к рисунку:

```
Upper bound on what any schedule method can deliver, measured per building
across 30 buildings. Four buildings in five have almost nothing available;
one in five has between 11 % and 41 %.
```

## Поле про языковую модель

Они спрашивают отдельно. Ответ:

```
Yes. The code and the manuscript were prepared with AI assistance (Claude,
Anthropic). The questions, the protocol, the choice of what to measure, the
decision of what to report and the interpretation of the results are the
author's. No AI system is an author.
```

## Автор

```
Evgenii Bogomazov-Pusser
Independent researcher
Rehovot, Israel
evgeniipusser88@gmail.com
```
