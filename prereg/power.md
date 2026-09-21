# Power: what this study can detect (simulation)

Made by `analysis/simulate.py`, `analysis/primary.R` and `analysis/power.py`. 200 simulated data sets per setting, 50 tasks, 6 faulty runs per task, 3 formats. Accuracy per class as on the validation runs with Qwen (tool 0.70, state 0.85, evidence 0.95); task SD 0.5 and run SD 1.0 on the logit scale. Bootstrap: 500 resamples here (2,000 in the real analysis).

## The interaction test

| Setting | Share of data sets with a significant interaction |
|---|---|
| no effect | 0.05 |
| no effect, but tasks differ in which format suits them | 0.04 |
| true margins 10 points | 0.94 |
| true margins 15 points | 0.99 |
| true margins 20 points | 1.00 |

The first two rows are false-positive rates and should be near 0.05.

Mean half-width of a 95 percent interval of one margin: 8.1 points.

## Chance of each outcome label, with equivalence bound B = 10 points

| Setting | confirmed | partly confirmed | another interaction | one format dominates | null | underpowered |
|---|---|---|---|---|---|---|
| no effect | 0.00 | 0.00 | 0.05 | 0.01 | 0.10 | 0.84 |
| no effect, but tasks differ in which format suits them | 0.00 | 0.00 | 0.04 | 0.01 | 0.09 | 0.86 |
| true margins 10 points | 0.05 | 0.77 | 0.13 | 0.00 | 0.00 | 0.06 |
| true margins 15 points | 0.37 | 0.61 | 0.01 | 0.00 | 0.00 | 0.01 |
| true margins 20 points | 0.69 | 0.30 | 0.00 | 0.00 | 0.00 | 0.00 |

## Chance of each outcome label, with equivalence bound B = 15 points

| Setting | confirmed | partly confirmed | another interaction | one format dominates | null | underpowered |
|---|---|---|---|---|---|---|
| no effect | 0.00 | 0.00 | 0.05 | 0.01 | 0.71 | 0.23 |
| no effect, but tasks differ in which format suits them | 0.00 | 0.00 | 0.04 | 0.01 | 0.62 | 0.32 |
| true margins 10 points | 0.05 | 0.77 | 0.13 | 0.00 | 0.04 | 0.02 |
| true margins 15 points | 0.37 | 0.61 | 0.01 | 0.00 | 0.01 | 0.00 |
| true margins 20 points | 0.69 | 0.30 | 0.00 | 0.00 | 0.00 | 0.00 |

## Chance of each outcome label, with equivalence bound B = 20 points

| Setting | confirmed | partly confirmed | another interaction | one format dominates | null | underpowered |
|---|---|---|---|---|---|---|
| no effect | 0.00 | 0.00 | 0.05 | 0.01 | 0.93 | 0.01 |
| no effect, but tasks differ in which format suits them | 0.00 | 0.00 | 0.04 | 0.01 | 0.92 | 0.03 |
| true margins 10 points | 0.05 | 0.77 | 0.13 | 0.00 | 0.06 | 0.00 |
| true margins 15 points | 0.37 | 0.61 | 0.01 | 0.00 | 0.01 | 0.00 |
| true margins 20 points | 0.69 | 0.30 | 0.00 | 0.00 | 0.00 | 0.00 |

## The bound B (rule of the pre-registration, section 5)

B = 20 points. With true margins of 0, the label "null" comes out in 0.93 of the data sets.
