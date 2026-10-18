# Front matter for Energy and Buildings

## Title

Source selection does not survive a wider population: a null result on 200 targets across 19 climates, and what replaces it

## Author

Evgenii Bogomazov-Pusser
Independent researcher, Rehovot, Israel
evgeniipusser88@gmail.com
ORCID 0009-0004-7834-1486

Corresponding author: as above. Sole author.

## Highlights

*Three to five bullets, at most 85 characters each including spaces.*

- Similarity of source to target does not predict transfer value over 8000 pairs
- Sources concord at +0.94: one is good or bad for every target, not for some
- Perfect per-target selection is worth 1% against one universally best source
- Enriching the policy from 5 to 26 parameters raises concordance to +0.978
- One policy searched against the population beats the median for 98% of targets

## Abstract

*238 words, limit 250.*

Choosing which building to transfer from is an open problem in transfer
learning for building thermal dynamics. We ask it under a wider population and
a different measure. The inherited object is a control policy rather than a
predictive model, and the outcome is degree-hours below the comfort norm during
a 72-hour loss of heating capacity placed at the coldest window of each
target's own year. Forty sources and two hundred targets are drawn from
measured weather for nineteen locations. The bench is a reduced three-capacity
model calibrated against BuilDa, agreeing with it to 2% on heat demand and
0.23 K on mean indoor temperature.

No similarity measure predicts the value of a transfer. Over 8000 ordered
pairs, the correlation of transfer gain with distance in ten building
parameters is +0.013, and with a physically motivated resilience trait −0.021;
permuting whole targets, which is the correct unit of resampling here, gives
p = 0.82 and p = 0.36. Choosing the nearest source by either measure is worse
than choosing at random.

The sources are not paired with the targets. Between-source correlation across
targets is +0.94. The target term holds 67% of the variance of the gain, the
source term 26%, their combination 6%, and a per-target oracle improves on one
universally best source by 1%. Enriching the policy from five parameters to
twenty-six raises concordance to +0.978.

What replaces selection is trial, and a single policy searched against the
population, which beats the median of individually learned policies for 98% of
unseen targets.

## Keywords

transfer learning; building thermal dynamics; source selection; control policy;
heat pump; negative result

## Graphical abstract

Figure s2_concordance.png, re-rendered at 531 × 1328 px (h × w). It carries the
whole argument in one picture: every source's outcome across the two hundred
targets, sources ordered by their mean, the spread between sources far larger
than the spread of any source across targets.

## CRediT author statement

Evgenii Bogomazov-Pusser: Conceptualization, Methodology, Software,
Validation, Formal analysis, Investigation, Data curation, Writing – original
draft, Writing – review and editing, Visualization.

## Declaration of competing interest

The author declares no competing financial interests or personal relationships
that could have appeared to influence the work reported in this paper.

## Declaration of generative AI and AI-assisted technologies

During the preparation of this work the author used Claude (Anthropic) to write
and debug the simulation code, to carry out the numerical experiments under the
author's protocol, and to draft and edit the manuscript text. The author
reviewed and edited the output and takes full responsibility for the content of
the publication. The research questions, the experimental protocol, the
decisions about what to measure and what to report, and the interpretation of
the results are the author's own.

## Funding

This research received no specific grant from any funding agency in the public,
commercial, or not-for-profit sectors.

## Data availability

The simulator, every experiment and control reported here, the computed result
files including the full 40 × 200 transfer matrix, and the scripts that draw
the figures are openly available at doi:10.5281/zenodo.23012010. Code is under
the MIT licence and result files under CC BY 4.0. The weather records are the
`.mos` set distributed with BuilDa and are not redistributed; the deposit
carries SHA-256 checksums for the nineteen files used.

## Note on a related correspondence

To be stated in the cover letter, not in the manuscript: an earlier version of
this work was sent to Dr Fabian Raisch (TU Munich / Hochschule München), whose
GenTL and BuilDa are cited here as [1] and [3], and he replied with comments
that shaped the present version. He is therefore the most natural referee for
this paper and also the least independent one. We leave the decision to the
editor and do not propose him ourselves.
