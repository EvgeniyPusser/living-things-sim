# What is worth inheriting: a measurement platform for transferred operating experience in technical systems

Evgenii Bogomazov-Pusser · independent researcher · evgeniipusser88@gmail.com

Draft, September 2026. All figures reproduce from open code and public data.

## Abstract

A newly commissioned building, machine or network has no operating history of its own. The question here is not whether experience can be transferred between such objects. It can, and methods exist. The question is what is worth transferring, and how that can be measured instead of asserted.

We describe a measurement platform. An individual object lives once, without replay. Losses accumulate as they occur. A target object starts either from a generic default (target-only), from the record of one source applied without adaptation (single-source, zero-shot), from an aggregate over many sources which we call a fund (multi-source), or from that fund followed by its own short adaptation (fine-tuned). The protocol was applied in three domains — a synthetic population of buildings, measured electricity records of 40 real non-residential buildings, and six benchmark water distribution networks — and to five candidate inherited objects.

One section stands apart because its instrument is not the author's alone. A reduced three-capacity thermal model, driven by measured weather for nineteen locations and by an air-source heat pump whose capacity as well as its efficiency falls with outdoor temperature, was calibrated against BuilDa [15], the open Modelica generator released with the ThermBuild dataset [16], on eight buildings and then checked on four more in another city and another month: heat demand agrees to 2 %, mean indoor temperature to 0.2 K. On that instrument a crisis is located by the data — the coldest 72-hour window of the target's own year, with available heating capacity halved — and the deficit follows from standard sizing practice rather than from a chosen parameter. Measured inside that window and not over the year, the fund beats self-acquisition in every fifth of the population and for 89–94 % of targets across three populations; in the worst-affected fifth, degree-hours below the comfort norm fall from 116 to 46, and the lowest indoor temperature reached rises from 16.8 °C to 18.5 °C. The cost is stated as well: the fund spends 10–14 % more electricity over the season. What is inherited there is not economy but a reserve, and the reason a single object does not acquire that reserve is explicit — a reserve is paid for daily and repays once in several years, so an object optimising what it can observe is right to remove it, while a population that has met many different failures is right to keep it. Fine-tuning the fund on ordinary days destroys the effect, which inverts the ordering found elsewhere in the paper.

The paper is written as the chain of experiments in the order they were performed. It includes three defects of the instrument found after the experiments were finished, what each defect changed, and one reported figure that a controlled repetition did not support and which is withdrawn. Five results hold across domains. First, zero-shot transfer of a complete source representation is usually worse than what the target can obtain for itself, even from two weeks of its own history: negative transfer is the rule rather than the exception. Second, source selection by similarity of building characteristics does not work: no measure of similarity we tried predicts whether transfer helps; an apparent correlation of +0.21 in the first experiment turned out to be an artefact of the cost function and fell to +0.05 once the artefact was removed. Third, what transfers is the arrangement of observation, not the values: the rule for placing sensors transfers where the detection rule does not. Fourth, the quality a source achieved does not pass to its targets; across two populations the slope of target gain on source quality was −2.12 and −0.38, negative in sign and undetermined in size. Fifth, most of the negative transfer we measured is an artefact of feature representation rather than of transfer itself: a simple target-relative normalisation of the same records raises the share of objects helped from 81–84 % to 99 %.

A separate measurement bounds all of these. For each object we compute an oracle baseline — the best any schedule method could achieve, and find that four objects in five have almost nothing to gain while one in five has 11–41 %. What an object gains from the fund is closely related to how much it had to gain, with a correlation of +0.91, so the fund can be read as a ranking of which objects are worth attention — a question no object can answer about itself. We end with what the platform does not measure, including a measurement of its own range which shows that range to be narrow.

## 1. Introduction

Technical objects that adapt during their operating life are now common. Buildings whose controls follow occupancy. Networks whose monitoring adjusts to observed failures. Fleets whose maintenance is revised as evidence accumulates. Each object acquires, over years, information specific to it and expensive to obtain. When it is decommissioned or rebuilt, that information is lost, and the building that replaces it starts from generic settings.

We begin with buildings, because buildings are the best documented of these objects. Public hourly records exist for thousands of them. Benchmark networks ship with the simulation software. The same questions arise for machines, factories and vehicles, and the platform is not specific to buildings, but the material is here.

Transfer between buildings is an active field and not a new idea. Xu et al. [1] transfer the strategy part of a reinforcement-learning controller and retrain a building-specific physical part locally, obtaining stable control from the first day. A critical review of transfer learning in buildings [2] treats negative transfer as a recognised phenomenon, with its causes and mitigations an open subject, and identifies the selection of source buildings as an unsolved part of the problem. A dataset of 15 808 building models was released in 2025 specifically for transfer research in building control [3].

A recent line of work is closer still. Raisch et al. show that pretraining one model on 450 simulated buildings and fine-tuning it on thirty days of a target reduces prediction error by 42 % against fine-tuning single-source models [15, 17] — the same shape as the result we report for schedules, reached independently on a different inherited object and a different measure. The same group then shows that prediction accuracy is not a proxy for control performance, and that what makes pretraining pay is **excitation**: source data in which the control inputs were deliberately varied enough to reveal the system's response [18]. Excitation has to be bought, by perturbing a real building at the occupants' expense. The result of §8 can be read as a claim about that price: a population of buildings, each having met a different failure, supplies excitation that nobody paid for deliberately.

Two threads in that literature bear directly on what follows. Negative transfer — a source that leaves the target worse off than no source at all — is recognised but not solved. And source selection — deciding which building to transfer from — is open. Most of what we report is a measurement of those two.

The open question, though, is prior to method. Given an object with an operating history, what part of that history is worth preserving so another object can use it? The answer is usually assumed rather than measured. In evolutionary robotics the inherited object is fixed in advance — a genotype, with lifetime learning written back into it [14]. In building control it is a set of controller parameters or a forecasting model. In each case the question of what to inherit has been settled before the experiment begins. We treat it as an empirical question and supply an apparatus.

Two commitments shape the apparatus. An individual lives once. A building experiences each winter one time, cannot re-run it, and pays for mistakes in comfort and energy. Any protocol that lets the target replay its own life makes self-acquisition artificially cheap and inheritance artificially worthless. And the measured quantity is loss accumulated during the first life, not the quality of the final model, because the value of inherited experience is exactly the cost of acquiring it again.

The paper follows the experiments in order. Two of them rested on a wrong premise. Three defects of the instrument were found later. All are reported with the result that exposed them. This is not a stylistic choice. Each time the instrument reported that inheritance was worthless, the cause was the design rather than the phenomenon, and that is the strongest evidence available that the instrument measures something.

## 2. The platform

### 2.1 Elements

A measurement requires four elements from any candidate domain.

| Element | Meaning | Buildings | Water networks |
|---|---|---|---|
| Characteristics (body) | fixed properties of the individual | ten thermal and use parameters | the pipe graph, junctions, elevations |
| Life | a single pass through time, no replay | hourly simulation of one or more years | 45 scenarios of three days each |
| Loss | what is paid while living | energy cost plus discomfort | missed leaks and false alarms |
| Record | what an individual leaves behind | a setpoint schedule and its conditions | a placement rule or a detection rule |
Table 1. The four elements required of a domain.

### 2.2 Conditions compared

Every experiment compares the same starting conditions. Every figure is a percentage change in accumulated loss relative to the first of them.

- **target-only** — the target starts from a generic default and learns only from its own single life; the baseline all other conditions are measured against;
- **single-source, zero-shot** — the target starts from the record of one earlier individual and does not adapt it;
- **multi-source, zero-shot** — the target starts from an aggregate over many earlier records and does not adapt it. We call such an aggregate a **fund** and keep that word for it below;
- **multi-source, fine-tuned** — the same fund, followed by the target's own short adaptation.

Positive numbers mean the inherited start was better than the target-only baseline; negative numbers are instances of **negative transfer**, and they are the majority of what we report. The protocol declares before each run what counts as confirmation and what as refutation. Negative outcomes are reported as they came.

## 3. Step 1: transfer with replay, and a cost function that moved

Ten synthetic buildings differ in ten parameters: envelope loss, thermal capacity, effective glazing, heating power, infiltration, internal gains, occupancy hour, mean outdoor temperature, daily swing, orientation. Each simulates a season of 60 days at hourly resolution. Cost combines energy and degree-hours of discomfort during occupancy. A controller is either five parameters — occupied setpoint, unoccupied setpoint, preheating lead, deadband, gain — or a schedule of 24 hourly setpoints. A donor has 400 evaluations of a season, a target 40. Three populations give 270 ordered pairs per experiment.

| Condition | Five parameters | Twenty-four setpoints |
|---|---|---|
| inherited as is | −11.9 % (helped in 26 % of pairs) | −3.6 % (helped in 52 %) |
| inherited as starting point | +3.8 % (helped in 81 %) | +0.5 % (helped in 63 %) |
| correlation of gain with distance between building characteristics | +0.05 | ≈ 0 |
Table 2. Step 1, after the cost function was repaired. Transfer between simulated buildings under replay-based learning. 270 ordered pairs per column.

Source selection did not help. A linear rule predicting gain from per-parameter differences, fitted on two populations and tested on a third, gave +4.7 % against +4.1 % for a randomly chosen source. Choosing the nearest building by unweighted distance gave +3.5 %, worse than random. The best source in hindsight gave +5.4 %.

The numbers in the table are not the ones first obtained. The original cost function counted discomfort below the occupied setpoint, and the occupied setpoint was one of the five numbers the building was tuning. A building could lower its promise to the occupants from 21 °C to 18 °C and thereby move the threshold for the penalty from 20.5 °C to 16 °C. In one run this is exactly what it did, cutting cost from 3 078 to 1 915 mostly by deciding that 16 °C was acceptable. The building was not learning to heat more cheaply. It was moving the ruler by which it was measured.

The comfort threshold was fixed at 21 °C and Step 1 was re-run on the same three populations. The main result survived: an inherited setting used whole is harmful, and the same setting used as a starting point helps. One thing changed. The correlation of gain with distance between building characteristics fell from +0.21 to +0.05, that is to nothing. The only number in the original Step 1 that suggested similarity of characteristics might matter was produced by the moving threshold.

There is a second, larger problem with Step 1, and it is not fixable by patching. A target allowed 40 replays of the same season reaches most of what a source reached in 400, because in this setting a season can be re-lived at no cost. No building can do this. The design was discarded.

## 4. Step 2: one pass, losses accumulated

The protocol was rebuilt around a single life. Each building lives year after year in hourly simulation. Once a week it may try one modified schedule. The week is lived once, its cost is paid, and the modification is kept only if the week compared favourably with a regression of past weeks on mean outdoor temperature. Sources, having lived and kept a log, tune a schedule offline on their own record — the counterpart of an old building with years of data and a calibrated model. Targets begin from a generic 21 °C schedule, from a source's tuned schedule, or from the median of ten such schedules.

The experiment was run twice with one difference. In the first version the year is ordinary. In the second a rare condition may occur: a severe winter, a heat episode, or a heating plant at half capacity. Eight sources, ten targets, the same buildings and the same weather in both versions, the same tuning budget of sixty evaluations.

Because the integration step is a known weakness of this domain (§10), the whole experiment was run twice more, at one hour and at ten minutes, with everything else held identical. All four cells are reported.

| Year | Step | One source | Median over sources |
|---|---|---|---|
| ordinary | one hour | −0.4 % (helped 50 %) | +0.6 % (helped 80 %) |
| ordinary | ten minutes | −2.8 % (helped 20 %) | +0.1 % (helped 60 %) |
| rare conditions | one hour | −4.5 % (helped 0 %) | +0.2 % (helped 90 %) |
| rare conditions | ten minutes | −3.9 % (helped 0 %) | +0.4 % (helped 100 %) |
Table 3. One pass through time. Ten targets per cell, identical buildings and weather across cells; only the year type and the integration step differ.

Two things hold in every cell. An inherited schedule taken from a single source is harmful. A median over many sources is not.

Rare conditions sharpen the first of these and leave the second. A single source goes from helping half the targets in an ordinary year to helping none at all when rare conditions are present, at both step sizes. It survived its own rare event, not the target's. The fund, which contains all the cases, helps 90 % and 100 % of targets in the two rare cells.

The magnitudes are small: between +0.1 % and +0.6 % for the fund. An earlier version of this experiment, with a different tuning budget and a different set of buildings, reported +5.5 % for the fund in the rare condition. That figure did not survive the controlled repetition and is withdrawn. What survives is the direction and the share of objects helped, not the size of the gain.

Ten targets per cell. The ordering is consistent across four cells; the magnitudes are not established.

## 5. Step 3: measured buildings

The Building Data Genome Project 2 [4] provides hourly electricity for 1 636 non-residential buildings over 2016–2017, with weather and metadata. We use site "Rat": 40 buildings with at least 95 % coverage. Each building's load shape — consumption divided by its own mean — is predicted from hour, day of week, month, weekend, outdoor temperature and its lag. Models are gradient-boosted. 2016 trains, 2017 tests. A target is a building for which only the first 14 days of 2016 exist. 1 560 ordered pairs.

| Condition | Median change | Helped in |
|---|---|---|
| a source's full model, target has full history | −85 % | 7 % of pairs |
| a source's model, zero-shot, target has 14 days | −33 % | 17 % of pairs |
| a source's model fine-tuned on 14 days | −21 % | 28 % of pairs |
| best source in hindsight | +2.5 % | 52 % of buildings |
| model trained on all other buildings | −10.7 % | 40 % of buildings |
| that model refined on 14 days | +2.5 % | 62 % of buildings |
Table 4. Measured buildings. Change relative to the target's own model, 1 560 ordered pairs.

The ordering of Step 2 reappears on measured data, and it is sharper. A whole inherited representation loses 85 % of accuracy, against roughly 10 % in simulation. Population knowledge combined with the target's own short history is again the only condition that helps a majority.

Metadata similarity is again uninformative. Correlation of gain with difference in log floor area is −0.001. Correlation with difference in year of construction is −0.06. Buildings of the same declared use lose 82 % where buildings of a different use lose 86 %. A hospital and a school of the same size are no closer to each other than a hospital and a warehouse.

62 % is not "it works". It means the inherited start helps more often than it harms. For 38 % of buildings it remained harmful, and we found no property that separates them in advance.

## 6. Step 4: a domain whose building characteristics are a graph

Six benchmark water distribution networks — Net1, Net2, Net3, ky4, Anytown, CCWI17-Herman-Mahmoud, from 9 to 959 junctions — are simulated with EPANET [5] through WNTR [6]. Each receives 45 three-day scenarios, 25 containing a leak of random size at a random junction. Three pressure sensors observe the network. Performance is average precision of leak detection on held-out scenarios.

### 6.1 Transferring the detection rule

Detection features are permutation-invariant summaries of standardised pressure deviations, so a rule fitted on one network applies to another regardless of size.

| Network | Target-only, 1 failure | Single-source, zero-shot | Multi-source, fine-tuned |
|---|---|---|---|
| Net1 | 0.990 | 0.958 | 1.000 |
| Net2 | 0.986 | 0.902 | 0.993 |
| Net3 | 0.863 | 0.837 | 0.880 |
| ky4 | 0.959 | 0.886 | 0.959 |
| Anytown | 0.987 | 0.312 | 0.983 |
| Herman | 0.205 | 0.211 | 0.206 |
Table 5. Average precision of leak detection. Transferring the detection rule.

A single failure suffices. The target reaches 0.99 of 1.0 from one leak, and there is nothing left to inherit. Anytown shows the risk instead: a source's rule gives 0.312 where the network's own rule gives 0.987.

### 6.2 Transferring the rule of placement

The inherited object is moved one level up: not how to decide that a leak is present, but where to watch. A placement rule assigns weights to structural properties of a junction — degree, hops from the nearest source, elevation, base demand, mean adjacent diameter — standardised within each network, and selects the three highest-scoring junctions. No node identity crosses between networks.

| Network | Random | Target-only, 2 failures | Single-source | Multi-source |
|---|---|---|---|---|
| Anytown | 0.117 | 0.212 | 0.173 | 0.215 |
| Net3 | 0.931 | 0.967 | 0.939 | 1.000 |
| ky4 | 0.843 | 0.841 | 0.842 | 0.858 |
| Net1, Net2 | placement barely matters; all methods coincide | | | |
| Herman | 0.290 | 0.290 | 0.290 | 0.290 |
Table 6. Average precision of leak detection. Transferring the rule of placement.

In the networks where placement matters, the inherited rule equals or exceeds what the individual can acquire for itself. This is the first case in the series where inheritance was necessary rather than convenient. The difference from §6.1 is the number of failures required. A detection rule needs one. A placement rule needs dozens, because to judge whether a position is good one must see many different leaks. A new network does not have dozens and will not have them for years.

Herman stays at 0.290 under every placement. Three pressure sensors cannot see a leak in that network. This is a limit of the formulation, not of transfer.

A correction is recorded here. We first took the transferability of a placement rule to be new. It is not. Placement by topological rules and by centrality measures is established in water distribution research [7,8]. The contribution is narrower: not a new way to place sensors, but a measurement of what an inherited placement rule is worth to an object with no failures of its own.

## 7. Step 5: generations, conditions and rare events

Twenty objects per generation, ten generations, each object living one year and contributing one record. Rare conditions occur with fixed probability: severe winter 10 %, heat episode 8 %, heating plant at half capacity 7 %. Three funds are compared: the median of all records; a ridge regression from an object's conditions to a schedule; and the median of records from the same rare condition. The fund is frozen within a generation.

| Records in the fund | Median of records | Conditions → schedule | Same condition only |
|---|---|---|---|
| up to 20 | +0.8 % | +0.5 % | +1.7 % |
| 20–60 | +1.1 % | +2.3 % | +1.3 % |
| 60–100 | +1.6 % | +3.3 % | +1.9 % |
| 100–140 | +1.5 % | +4.4 % | +1.9 % |
| 140–200 | +2.2 % | +4.6 % | +2.5 % |
Table 7. Value of the fund as it accumulates. Ten generations, twenty objects each.

Quantity alone helps a little. The plain median improves from +0.8 % to +2.2 %. The conditional rule is worse than the median at twenty records, because the relations are not yet visible, then overtakes it and reaches +4.6 %. Relations between conditions and good settings must be paid for in records before they can be used.

The growth is not unbounded. Between 20 and 100 records the conditional rule adds almost three percentage points. Between 100 and 200 it adds 0.2. The curve flattens, and it flattens in the same place on two further populations. The first hundred records are worth more than the next hundred. For anyone planning to collect this material, that is the practical point: there is no need to wait for thousands of buildings, and no reason to expect a thousand to give ten times what a hundred gives.

| Condition of the target object | Median fund | Conditions → schedule | Same condition only | n |
|---|---|---|---|---|
| ordinary year | +1.4 % | +3.3 % | +1.9 % | 147 |
| severe winter | +0.8 % | +4.1 % | +1.1 % | 20 |
| heat episode | +1.6 % | +4.3 % | +1.8 % | 25 |
| heating at half capacity | −2.7 % | −14.8 % | −0.4 % | 8 |
Table 8. Rare conditions. Gains relative to a generic start.

The last row matters. Climate extremes are handled, because climate is part of the recorded conditions. A damaged object is not. Heating capacity is recorded as a nameplate value while the object runs at half power, so the conditional rule extrapolates confidently and wrongly and loses 15 %. Accumulation does not reduce this harm. It increases it, because a larger fund makes the rule more confident without making it correct. A record must carry the state of the object, not only its specification.

Eight cases. The sign is worth acting on. The number is not a result and should not be quoted as one.

## 8. A calibrated instrument, real weather, and a real crisis

Every experiment so far ran on a thermal model written by the author, driven by a sine-plus-noise weather series, with a single lumped capacity and a one-hour explicit step. Sections 7 and 11 suggested that inheritance matters where events are rare, but on such an instrument the rare events are the author's own invention, and the objection that the extremes were manufactured to produce the result is a fair one.

This section repeats the question on a rebuilt instrument, calibrated against a published independent simulator, with weather taken from measured records and with a crisis that the data rather than the author locates.

### 8.1 The instrument and its calibration

The thermal model now carries three capacities — air and furniture, envelope, internal partitions — connected by conductances derived from surface areas and U-values. Within each control interval the system is linear, so the state is advanced by the matrix exponential rather than by an explicit step: the integration-step artefact reported in §11 is removed by construction rather than reduced. Weather is read from `.mos` files for nineteen locations between Rome and Chicago. Solar gain is computed on four vertical facades from the true solar position at the file's latitude, with beam and diffuse components separate. Heating is supplied by an air-source heat pump whose coefficient of performance and whose **available capacity** both fall with outdoor temperature; nominal power is sized by the rule used in BuilDa's own code, following DIN 18599-2 including the 0.6 ground-coupling factor of DIN 4108-6, at a design temperature taken as the 0.4th percentile of the location's record.

BuilDa [15], the generator released with the ThermBuild dataset [16], is a Modelica multi-zone model solved by CVODE and validated against two instrumented twin houses. It is open, and we used it as the reference. Eight buildings spanning U-values of 0.2–0.665 W/m²K, window U-values of 1.0–3.2 W/m²K and two or three storeys were simulated for thirty days of January in Munich, in BuilDa and in the reduced model, with identical geometry, fabric, controller and weather. A single pair of correction factors on the envelope and window-plus-ventilation conductances was fitted to those eight. The factors were then applied unchanged to four buildings not in the fitting set, in a different city and a different month.

| | Fitting set: Munich, January | Held out: Berlin, days 45–75 |
|---|---|---|
| buildings | 8 | 4 |
| heat demand, ours / BuilDa, before correction | 1.20 (spread 0.089) | 1.23 (spread 0.008) |
| heat demand, ours / BuilDa, after correction | 1.016 (spread 0.054) | 1.020 (spread 0.012) |
| worst single building after correction | 12.1 % | 3.5 % |
| difference in mean indoor temperature | ≤ 0.20 K | ≤ 0.23 K |
Table 11. The reduced model against an independent Modelica model of the same buildings.

The reduced model runs a heating season in under a second for three hundred buildings at once, about four thousand times faster than the reference. The two are complementary: the fast model performs the hundreds of thousands of season evaluations a search protocol needs, and the reference model states what those evaluations are worth.

### 8.2 Two defects of the author's own cost function, found here

With a 0.5 K tolerance below the comfort norm, sources learned to hold the indoor temperature at exactly the edge of the tolerance. Penalty zero, energy minimal, reserve zero. This is an exploit of the measure rather than a skill: any disturbance immediately pushes such a building below the norm. The tolerance was removed and the penalty made proportional to the shortfall below 21 °C.

Second, the weighted sum of energy and discomfort used throughout this paper assigns one degree-hour the weight of eight kilowatt-hours. Percentages of that sum are therefore statements about comfort wearing the dress of money. In this section the two components are reported separately and no combined figure is quoted.

### 8.3 What a crisis is, declared before the runs

The heating season is taken as 1 October to 30 April, so that a newly commissioned building meets its first winter with an autumn behind it. Two conditions define the event, and both are located by the record rather than chosen:

- the 72-hour window whose mean outdoor temperature is the lowest in that building's own year, found by search over its weather file;
- within that window, available heating capacity halved.

Because nominal power is sized at the 0.4th percentile and heat-pump capacity falls with outdoor temperature, a building in its own coldest window can already deliver only 88–95 % of what it needs before the failure is applied. The deficit is a consequence of standard sizing practice and of a documented property of the equipment, not of a parameter set to produce it.

The primary measure is degree-hours below 21 °C **within the window**, reported in absolute units. The window is 1.4 % of the season and holds a third of the season's discomfort, which is why measuring over the year divides the effect away. Adaptation by the target is permitted only on hours preceding the window: a target allowed to adapt during the event would be living it twice.

### 8.4 Result

Three populations, twenty-four to forty sources and one hundred to three hundred targets, nineteen cities, thirty-two city-years. Targets and sources draw their years from disjoint halves of the pool, so a target's crisis is never a source's crisis.

| Fifth of targets, by how badly they fared alone | target-only | single-source | fund | fund, fine-tuned |
|---|---|---|---|---|
| worst fifth | 115.8 | 53.2 | 46.2 | 68.5 |
| second | 82.3 | 36.0 | 29.9 | 54.0 |
| middle | 60.1 | 29.0 | 22.8 | 45.0 |
| fourth | 41.8 | 18.0 | 13.4 | 36.5 |
| best fifth | 17.7 | 14.2 | 9.9 | 31.5 |
Table 12. Degree-hours below 21 °C during the 72-hour event. Three hundred targets, mean within each fifth.

The fund is better than target-only in every fifth, for 94 % of targets, and the two smaller populations give 92 % and 89 %. Hours spent below the norm within the event fall from 30 of 72 to 16, and the lowest indoor temperature reached rises from 16.8 °C to 18.5 °C, medians over targets.

| | seed 101, n=100 | seed 202, n=100 | seed 303, n=300 |
|---|---|---|---|
| worst fifth, target-only | 115.5 | 126.1 | 115.8 |
| worst fifth, fund | 40.4 | 67.6 | 46.2 |
| worst fifth, fund fine-tuned | 60.6 | 85.9 | 68.5 |
| targets helped by the fund | 92 % | 89 % | 94 % |
| season electricity, fund vs target-only | +9.9 % | +9.7 % | +13.7 % |
Table 13. The same experiment on three independent populations.

### 8.5 What the fund contains, and what it costs

The sources' learned schedules have a clear median. Against the generic default of 21 °C occupied, 18 °C setback, one hour of preheating, 0.5 K deadband and gain 0.35, the fund holds 23.4 °C occupied, applies **no setback at all**, narrows the deadband to 0.34 K and doubles the gain. Across forty sources the setback depth ranges from 8.6 K to zero; the median selects those that abandoned it.

Neither element of that posture is new to practice, and we claim no novelty for the rule itself. Compensating the supply temperature against outdoor temperature — the heating curve — is standard equipment in heat-pump controllers [19], and it is present in our own model as the parameter `heatingCurve_steepness` taken from BuilDa's configuration. Advice not to apply night setback to a heat pump in cold weather is routine installer guidance [20]. What the measurement contributes is not the rule but its provenance: the platform was told nothing about heat pumps, setbacks or installer practice, and the rule emerged as the median of forty objects that had each survived a different failure. A measuring instrument that independently reproduces an answer the field already holds is entitled to more confidence where the field holds no answer — which is the case for the second question below, how much reserve and at what price.

The cost of that posture is measurable and it is not small. Over the season the fund uses 2 987 kWh against 2 626 kWh for target-only, a 13.7 % increase, and accumulates 69 degree-hours of discomfort against 157.

This is the result the series has been missing. Inheritance here does not buy economy; it buys a reserve, at 10–14 % of the annual electricity bill. And the reason a single object does not acquire that reserve for itself is now explicit rather than assumed: a reserve is paid for every day and repays once in several years. An object optimising the loss it can observe is right to remove it. A population of objects, each having met a different failure, is right to keep it. What is inherited is not a setting but the population's verdict that an apparently wasteful behaviour is correct.

The fine-tuned condition, best in most earlier sections, is here the third of four. Fine-tuning takes place on ordinary days, and ordinary days reward exactly the removal of reserve: 46.2 degree-hours become 68.5. Adaptation to normal operation erases the property the fund was taken for. We report this as it came; it inverts the ordering of §5 and §6 and we have no account of it beyond the mechanism just stated.

## 9. Step 6: feature representation, or the language in which records are written

All transfers so far moved a schedule expressed in degrees. A schedule in degrees is meaningful only relative to a particular building. The same 18 °C night setpoint is a mild setback in one building and an unreachable target in another. In the vocabulary of the field this is a feature representation problem, and what follows is a simple form of domain adaptation: target-relative feature normalisation.

We re-expressed the identical records in four dimensionless quantities defined relative to the target object: the depth of setback below its own comfort temperature, the lead time before its own occupancy hour, any daytime reduction, and the duration of the reduced period. A schedule for any object is reconstructed from these four numbers. Nothing about the transfer method changes; only the space the records live in.

| Records in the fund | Degrees | Dimensionless |
|---|---|---|
| 20 | +1.6 % | +2.9 % |
| 40 | +2.8 % | +4.1 % |
| 80 | +3.6 % | +5.5 % |
| 120 | +4.1 % | +6.1 % |
| all objects, population 1 | +3.3 % (helped 84 %) | +4.6 % (helped 99 %) |
| all objects, population 2 | +2.8 % (helped 83 %) | +4.8 % (helped 99 %) |
Table 9. The same records transferred in two representations.

The median gain rises by about half. The decisive figure is the share of objects helped: 99 % against 83–84 %. Most of the harm previously attributed to inheritance was an effect of representation. A record written in quantities that refer to the target almost never damages it.

The same experiment measures the distance from each target to the nearest record in the fund. Gain falls as the distance grows, from +4.1 % to +1.8 % in degrees, and falls more gently in the dimensionless form, from +5.6 % to +3.6 %. A common language is needed exactly where no similar case exists.

### 9.1 A narrower statement, after §8

The claim "representation dominates" is too broad, and §8 shows where it fails. There the fund was carried in five parameters and re-expressed in quantities relative to the target — setback depth, preheating in units of the target's own time constant, controller authority per unit of its own installed power — and the gain over the raw form was 46.2 against 49.1 degree-hours, inside the noise.

Opening the earlier program explains the difference, and it is not subtle. In this section a record is **twenty-four hourly setpoints anchored to the source's own clock**. Sources differ in occupancy hour. Passing the twenty-four numbers unchanged shifts the whole schedule by the difference — the target heats while the building is empty and is cold when people arrive. The re-expression did not correct units; it corrected **alignment**, by re-anchoring the record to the target's own occupancy hour. In §8 the five parameters are already defined relative to each target's occupancy, so no misalignment exists to repair.

The statement that survives is therefore conditional: **re-expression helps exactly where the record is anchored in the source's frame of reference, and does nothing where it is already in the target's.** That is narrower than "representation dominates" and it is testable on any new domain by asking one question of the record — whose frame is it written in.

A second caution belongs here. The dimensionless quantities of §8 were chosen by the author: two of the five are near-forced, one depends on how thermal inertia is defined, one was invented, and one was left untransformed. A negative result from one hand-picked mapping is weak evidence that no mapping helps.

## 10. Step 7: is quality heritable?

Every experiment so far asked whether a fund helps. This one asks a different question. If a source tuned itself well, do its targets do better than the targets of a mediocre source?

Twelve sources tune themselves offline. Each contributes five targets. We measure the slope of target gain on source quality. A slope of 1.0 would mean that every percentage point won by the source passes to the target. Two independent populations.

| | Population 1 | Population 2 |
|---|---|---|
| source quality, mean | 5.1 % | 5.6 % |
| source quality, spread | 3.5 | 7.7 |
| target gain from one source | +0.4 % (helped 55 %) | −0.2 % (helped 43 %) |
| target gain from the fund | +3.6 % (helped 97 %) | +2.1 % (helped 98 %) |
| slope | −2.12 | −0.38 |
| correlation | −0.27 | −0.16 |
Table 10. Heritability of quality. Twelve sources, five targets each, two populations.

The slope is negative in both populations. Its size differs by a factor of five, and at sixty points neither correlation is distinguishable from zero. The statement that survives is that source quality does not predict target gain. The statement that does not survive is that a good source is harmful, which is what −2.12 alone appeared to say.

This explains why a fund works and a single source does not. If quality were heritable, finding the best source would be enough. One source helps roughly half of targets regardless of how good it is. A fund helps 97–98 %, and not because it contains good sources but because it contains many different cases.

For the general question, this is the working answer of the series: what is inherited is not what a parent acquired, but what many have survived.

## 11. What the instrument got wrong about itself

Three defects were found after the experiments were complete. Two were repaired. One is declared and stands.

**The building does not learn.** In the one-pass protocol a building tries a modified schedule about forty times a year and accepts two or three. Measured against an untouched 21 °C schedule across thirty buildings in three populations, a year of this gives a median of −0.2 %, and helps 13 % of buildings. The mechanism does not work.

This was not repaired, for two reasons. It is closer to a real building than a working mechanism would be: schedules in real buildings are set once at commissioning and stay, and savings from a re-commissioning visit decay to about 65 % after four years as operators adjust settings in response to complaints [9]. And it changes the reading of the earlier tables rather than invalidating them. The condition called "alone" was never a self-teaching building. It was an untouched schedule. That happens to be the right comparison, but the sentence "each building learns its own easily, therefore inheritance is not needed" must be withdrawn. The building learned nothing.

**The time step is too coarse.** The thermal integration advances one hour at a time with the heater at full or zero output. A building needing three degrees receives 6.31 in one hour, then shuts off and falls back:

```
18.00 → 24.31 → 18.22 → 24.48 → 18.35 → 24.58 → 18.43
```

The building never holds 21 °C. At a ten-minute step the same building settles at 20.52 °C and stays there, which confirms the oscillation as an artefact of the step size rather than a property of buildings.

We first declared this defect without measuring what it costs, which is not good enough. The experiment of §4 was therefore repeated at both step sizes with everything else held identical, and the four cells are in Table 3. The ordering of conditions is the same at both steps, in both the ordinary and the rare year. What the coarse step does change is magnitude: absolute costs are inflated, and one figure reported in an earlier version of §4 did not survive and has been withdrawn.

The defect therefore stands, with its effect on the comparisons now measured rather than assumed. The remaining experiments have not been repeated at ten minutes; on the evidence of §4 their orderings should hold and their magnitudes should not be relied on.

**The cost function moved.** Described in §3. Present only in Step 1, repaired, Step 1 re-run.

The three are of different kinds. The third was an error in the measuring device and produced a false positive, the correlation of +0.21. The second is a known approximation carried too far. The first was a wrong belief about the device, held by the author, and stated twice in earlier drafts.

## 12. How much is there to take at all

A separate measurement bounds everything above: an oracle baseline. For each building we searched for the cheapest schedule using 400 evaluations of its own year with full knowledge of that year in advance, and compared it with an untouched 21 °C schedule. No method that changes only the schedule can beat this number: not self-learning, not a fund, not an engineer.

| Measure | Across 30 buildings |
|---|---|
| median | +2.5 % |
| mean | +6.4 % |
| buildings above 5 % | 40 % |
| buildings above 10 % | 20 % |
| buildings above 15 % | 13 % |
Table 11. The upper bound on what any schedule method can deliver, measured per building.

The distribution matters more than the median. For four buildings in five there is almost nothing to take, and no method can help them. For one in five there is 11 % to 41 %, and the building took none of it. In the extreme case the available gain was 41 % and the building's own year of trials returned −3.2 %.

The schedule found for that building was checked on three other years of the same building and returned +44.5 %, +44.3 % and +45.7 % against +45.9 % on the year it was fitted. It is a property of the building, not of one year's weather.

Two things follow. Arguing about inheritance without this number is arguing about nothing, because for most buildings every condition is equivalent by construction. And the useful product of a fund may not be a better schedule at all. It may be the answer to which buildings have anything to gain — a question an individual building cannot answer about itself, since to know that 41 % is available one must have seen buildings where 2 % is available.

### 12.1 The fund as a way of finding those buildings

The second of these was tested directly. Fifteen sources in each of two populations contribute records; the median of those records is the fund. Twenty targets, none of them in the fund, each receive the fund and forty of their own evaluations. Their gain is compared with their own ceiling, measured separately.

| | Across 20 targets |
|---|---|
| ceiling | +4.1 % (present in 100 %) |
| fund, unchanged | −0.0 % (helped 45 %) |
| fund, refined | +0.6 % (helped 85 %) |
| correlation of fund gain with ceiling | +0.91 (rank +0.81) |

Table 12. What the fund takes of what is available, and how closely the two are related.

Two groups separate. In the nine targets whose ceiling exceeds 5 %, the ceiling has a median of 7.5 % and the fund with refinement returns 4.3 %. In the eleven below 5 %, the ceiling is 1.1 % and the fund returns 0.2 %. In the two largest cases the fund recovered 74 % and 53 % of what was available.

The correlation of +0.91 is the point. A building's gain from the fund tracks how much that building had to gain. So the fund can be read as a filter. Ranking the twenty targets by their gain and taking the first five captures 77 % of all the gain available in the population; five buildings chosen at random capture 30 %.

Twenty targets in two populations is a small sample and the correlation is measured within one synthetic domain. But the mechanism does not depend on the domain. A fund answers a question no individual can answer about itself, and the cheapest useful form of that answer is a ranking: which objects are worth visiting, and which are already close to their own limit.

The same measurement calibrates the platform against reality, and the result is not flattering. The median of 2.5 % is the whole range of the schedule game in this model. Measured re-commissioning of existing buildings gives a median of 16 % of whole-building energy across 643 buildings with a payback of 1.1 years [10]. Advanced controls retrofitted to 66 rooftop units gave 22–90 % of unit energy, averaging 57 % [11]. One campus programme reported 43 % in a single building from correcting its schedule alone [12]. Real waste sits in things this model does not contain: plant running in an empty building, a stuck economiser, a fan at full speed. The model has one zone and a setpoint.

The platform compares conditions of transfer honestly against each other. It understates by a large factor how much is available in a real building.

## 13. What the steps say together

- An inherited representation used unchanged is the worst of the conditions tested, in every domain.
- A single source is unreliable and cannot be chosen in advance by any obvious measure of similarity, including physical parameters, floor area, year and declared use.
- The quality a source achieved does not pass to its targets.
- What survives transfer is the arrangement of observation and regulation — where to watch, what to treat as a signal — rather than the values an individual arrived at.
- Inheritance from a single source becomes actively harmful where the event is rare: in an ordinary year such a source helps about half of targets, and when rare conditions are present it helps none, at both integration steps (§4). Where many events are needed before an object can judge at all, an inherited rule is the only source available (§6.2).
- Quantity of records converts into value only through relations between conditions and settings, and those relations must be paid for in records. The first hundred are worth more than the next hundred.
- A record must carry the state of the object, not only its nameplate, or accumulation amplifies harm.
- Representation matters where the record is anchored in the source's frame of reference: re-anchoring twenty-four hourly setpoints to the target's own occupancy hour raises the share helped from 83–84 % to 99 %. Where the record is already parameterised relative to the target, re-expression adds nothing (§9.1).
- Where an event is both rare and severe, the ordering is unambiguous and holds in every fifth of the population: fund, then single source, then the fund fine-tuned, then self-acquisition (§8). Self-acquisition is the worst of the four, by a factor of two in the worst-affected fifth.
- What inheritance buys there is a reserve, not economy, and it costs 10–14 % of the season's electricity. A reserve is paid for every day and repays once in several years, so an object optimising its own observable loss removes it correctly; only a population that has met many different failures keeps it correctly.
- Adaptation to ordinary operation destroys inherited crisis readiness. The fund fine-tuned on pre-event hours is worse than the fund untouched, in all three populations.
- What a fund gives an object is closely related to how much that object had to gain (correlation +0.91). A fund can therefore be used to rank objects by how much is available in them, which no object can determine about itself.

For the general question the results give one working answer, sharper than the one this series began with: what is worth inheriting is what an individual cannot rationally acquire for itself, because the lesson costs more than a single life can justify. Ordinary competence is not in that class — each object reaches it alone. Conduct during rare and expensive events is, and the form it takes is not a transferable setting but a population's verdict that an apparently wasteful behaviour is correct.

## 14. Limitations

- Three domains, two of them simulated. The measured domain contains no setpoints and no record of operator intervention, so the inherited object there is a predictive model rather than a policy.
- The synthetic domain of §8 is checked against an independent Modelica model to within 2 % of heat demand and 0.2 K of mean indoor temperature, on twelve buildings in two cities. Sections 3–7 and 9–12 run on the earlier uncalibrated model and carry the limitations listed below; §8 does not.
- The bodies of §8 are still generated by the author, from ranges taken from BuilDa's configuration. Calibration establishes that the physics agrees; it does not establish that the population is representative of a real stock.
- The crisis of §8 combines a real cold extreme with a failure whose severity — capacity halved for 72 hours — is a choice. The timing and the weather are taken from the record; the depth of the failure is not.
- The heat-pump capacity derating is a linear fit to typical published behaviour, not a manufacturer's curve for a specific unit.
- Thirty-two city-years across nineteen locations is a wide climate range but a small number of independent years; several targets in a population share a year and therefore a cold window.
- The range of the synthetic domain is narrow: a median of 2.5 % against 16 % measured in real re-commissioning. Orderings between conditions should be read; magnitudes should not be carried over to real buildings.
- The one-hour integration step produces a temperature oscillation of several degrees in every run of §§3–7 and 9–12; in §8 it is removed by exact integration within each control interval. Its effect was measured for §4, where the ordering of conditions is unchanged at ten minutes; the other experiments were not repeated at the finer step, so their magnitudes should not be relied on.
- Cost weights, the ranges of building parameters and the frequency of rare conditions are choices of the author. With different choices the magnitudes, though probably not the ordering, would change.
- The rare-condition result for a damaged object rests on eight cases and must be repeated.
- The heritability slope is negative in two populations but its magnitude differs fivefold; only the absence of a relation is established.
- The ranking result of §12.1 rests on twenty targets in one synthetic domain and has not been tested on measured data.
- The platform measures one function — inheritance — in a framework that names several others: retention, restoration, selection, mutation. Their protocols are defined and not yet run.
- Benchmark water networks are distribution systems, not the internal pipework of a single building. The mechanism carries over. The numbers do not.

## 15. Reproducibility

All results are produced by open code with fixed random seeds, and every table is written by the script that produces it. The calibration of §8.1 requires BuilDa [15], which is licensed GPL-3.0; our code drives its compiled FMU through an interface and contains none of its source, so it is distributed under its own terms. The measured data are public [4]. The water networks ship with WNTR [6]. Total computation is a few hours on an ordinary laptop.

The experiments were designed by the author. The code and the manuscript were prepared with AI assistance (Claude, Anthropic). The questions, the protocol, the choice of what to measure, the decision of what to report, and the interpretation of the results are the author's. No AI system is an author, and the author takes full responsibility for the content.

## 16. Where to begin

Three things would change the answers, in order of how much they would change them.

Data with setpoints and a log of interventions. The measured domain here has meter readings and nothing else, which is why the inherited object had to be a model rather than a policy. Sources exist: instrumented reference buildings, and thermostat data donated by householders, of which one programme covers more than 200 000 homes [13].

Everything re-run on the calibrated instrument of §8. Sections 3–7 and 9–12 stand on a model whose magnitudes are now known to have been wrong by tens of per cent; §8 shows the repair is affordable, and there is no reason left to leave the rest uncalibrated.

A curve rather than a sign. Section 8 shows that inheritance pays where the event is rare and severe, and §7 shows it does not pay in an ordinary year. Between those two lies a quantity: how rare and how expensive an event must be before a population's verdict is worth more than an individual's optimisation. Varying the frequency and the depth of the failure would produce that curve, and it would turn the claim of this paper from a direction into a number.

An object with a described structure of regulation — a set of observed quantities, rules of response, priorities — rather than a vector of numbers. Every experiment here transferred values. The results say values are the wrong thing to transfer. The next experiment should transfer the arrangement, and the first task is to describe an object that has one.

## References

[1] Xu, S., Wang, Y., Wang, Y., O'Neill, Z., Zhu, Q. One for Many: Transfer Learning for Building HVAC Control. Proc. 7th ACM Int. Conf. on Systems for Energy-Efficient Buildings, Cities, and Transportation (BuildSys '20), 2020. doi:10.1145/3408308.3427617; arXiv:2008.03625.

[2] Pinto, G., Wang, Z., Roy, A., Hong, T., Capozzoli, A. Transfer learning for smart buildings: a critical review of algorithms, applications, and future perspectives. Advances in Applied Energy 5, 100084 (2022). doi:10.1016/j.adapen.2022.100084.

[3] A HOT Dataset: 150 000 Buildings for HVAC Operations Transfer Research. Proc. 12th ACM Int. Conf. on Systems for Energy-Efficient Buildings, Cities, and Transportation (BuildSys '25), 2025. doi:10.1145/3736425.3770110.

[4] Miller, C., Kathirgamanathan, A., Picchetti, B. et al. The Building Data Genome Project 2, energy meter data from the ASHRAE Great Energy Predictor III competition. Scientific Data 7, 368 (2020). doi:10.1038/s41597-020-00712-x.

[5] Rossman, L. A. EPANET 2 Users Manual. U.S. Environmental Protection Agency, 2000.

[6] Klise, K. A., Bynum, M., Moriarty, D., Murray, R. A software framework for assessing the resilience of drinking water systems to disasters with an example earthquake case study. Environmental Modelling & Software 95, 420–431 (2017).

[7] A rule-based water quality sensor placement method for water supply systems using network topology. Water Resources Management, 2023. doi:10.1007/s11269-023-03685-9.

[8] Strategic sensor placement using centrality metrics and machine learning techniques for leak localization in water distribution networks. Water Supply 26 (2), 98 (2026). doi:10.2166/ws.2026.006.

[9] Evaluation of retrocommissioning persistence in large commercial buildings. National Conference on Building Commissioning, 2004. Lawrence Berkeley National Laboratory.

[10] Mills, E. Building commissioning: a golden opportunity for reducing energy costs and greenhouse gas emissions in the United States. Energy Efficiency 4, 145–173 (2011). doi:10.1007/s12053-011-9116-8.

[11] Wang, W., Katipamula, S., Ngo, H. et al. Advanced Rooftop Control (ARC) Retrofit: Field-Test Results. PNNL-22656, Pacific Northwest National Laboratory, 2013.

[12] Small Workplace Automation and Remote Monitoring (SWARM). University of California, Davis, Facilities Management.

[13] Donate Your Data. ecobee. Anonymised thermostat records from more than 200 000 homes, available to researchers on application.

[14] Luo, J., Miras, K., Tomczak, J., Eiben, A. E. Enhancing robot evolution through Lamarckian principles. Scientific Reports 13, 21109 (2023). doi:10.1038/s41598-023-48338-4.

[15] Raisch, F., Krug, T., Koch, F., Kollmannsberger, S., Lang, W. GenTL: A General Transfer Learning Model for Building Thermal Dynamics. Proc. 16th ACM Int. Conf. on Future and Sustainable Energy Systems (e-Energy '25), 2025. doi:10.1145/3679240.3734589; arXiv:2501.13703. Code: github.com/fabianraisch/BuilDa (GPL-3.0).

[16] Raisch, F. et al. Real-world and simulated thermal data from 960 residential multi-zone buildings in Central Europe. arXiv:2606.01994. Data: Fordatis, fordatis.fraunhofer.de/handle/fordatis/486 (CC-BY-SA 4.0).

[17] Raisch, F. et al. Adapting to change: transfer learning, continual learning and seasonal memory for building thermal models.

[18] Koch, F., Krug, T. et al. BuilDyn: Excitation-Driven Data Generation for Building Thermal Dynamics Modeling and Control. arXiv:2605.29849. Package: pypi.org/project/buildyn (MIT).

[19] Weather compensation control for heat pumps and boilers. Manufacturer and industry guidance, e.g. Danfoss electronic controllers; Energy Saving Trust, Heat Pump Installers Toolkit, "Weather compensation and other controls".

[20] Industry guidance on night setback with air-source heat pumps in cold weather, e.g. consumer advisories published by heat-pump installers, 2025–2026.
