# Analysis of sweep `main`, second auditor (glm-4.7-flash:q8_0)

Main analysis: sweep tasks.
Second auditor: description only. Its label and p-value are shown for completeness and are not a test (pre-registration, section 8).

Faulty runs: 300 (removed as too long: 0). Answers parsed: 0.97.

## 1. Outcome label

**refuted: another interaction**

Interaction test: p = 0.0009 (glmer, task and run intercepts; fit warning left: False). Equivalence bound B = 0.20.

Predictions that cannot be tested because every format is at 95 percent or more in that class (ceiling): none.

Control 1 (sham records equal clean records): pass. Control 3 (structure-only guesser on the two tool faults: 7/100 = 0.07 [0.03, 0.14], against tool prior 0.226 + 0.10): pass. Control 4 (real exact score 0.536 against labels shuffled within fault type: mean 0.213, 97.5 percent point 0.247): pass.

| Class | Predicted format | Margin | 95% interval | 90% interval | Meets the rule |
|---|---|---|---|---|---|
| tool | log | -0.095 | [-0.155, -0.040] | [-0.145, -0.050] | no |
| state | diff | +0.010 | [-0.065, +0.085] | [-0.055, +0.070] | no |
| evidence | prov | +0.060 | [+0.000, +0.120] | [+0.010, +0.110] | no |

## 2. Exact step found, per fault class and format

| fault_class   |   log |   diff |   prov |
|:--------------|------:|-------:|-------:|
| evidence      |  0.93 |   0.83 |   0.94 |
| state         |  0.62 |   0.61 |   0.58 |
| tool          |  0.04 |   0.11 |   0.16 |

## 3. Exact step found, per fault type and format

| fault_type       |   log |   diff |   prov |
|:-----------------|------:|-------:|-------:|
| wrong_argument   |  0.08 |   0.16 |   0.28 |
| corrupted_output |  0.00 |   0.06 |   0.04 |
| dropped_note     |  0.32 |   0.26 |   0.38 |
| overwritten_note |  0.92 |   0.96 |   0.78 |
| wrong_source     |  1.00 |   0.96 |   0.96 |
| no_source        |  0.86 |   0.70 |   0.92 |

## 4. Baselines without a model (share of runs where the faulty step was named)

| fault_type       |   uniform chance |   tool prior |   most frequent step |   position-only |   structure-only |   rule auditor |
|:-----------------|-----------------:|-------------:|---------------------:|----------------:|-----------------:|---------------:|
| wrong_argument   |             0.08 |         0.00 |                 0.00 |            0.00 |             0.02 |           0.00 |
| corrupted_output |             0.07 |         0.00 |                 0.00 |            0.00 |             0.12 |           0.00 |
| dropped_note     |             0.10 |         0.34 |                 0.32 |            0.38 |             0.86 |           1.00 |
| overwritten_note |             0.10 |         0.34 |                 0.44 |            0.64 |             0.78 |           1.00 |
| wrong_source     |             0.10 |         0.34 |                 0.46 |            0.56 |             0.00 |           0.00 |
| no_source        |             0.10 |         0.34 |                 0.32 |            0.38 |             0.82 |           1.00 |

All faults together: uniform chance 0.092, tool prior 0.226, most frequent step 0.257, position-only 0.327, structure-only 0.433, rule auditor 0.500.

## 5. Controls: clean and sham runs

- `log`: false alarms 39/45 = 0.87 [0.74, 0.94]; said "no fault" on a faulty run 13/300 = 0.04 [0.03, 0.07]
- `diff`: false alarms 32/45 = 0.71 [0.57, 0.82]; said "no fault" on a faulty run 25/300 = 0.08 [0.06, 0.12]
- `prov`: false alarms 35/45 = 0.78 [0.64, 0.87]; said "no fault" on a faulty run 27/300 = 0.09 [0.06, 0.13]

## 6. Secondary

| format   |   within3 |   right_class |   pointer_ok |   tokens_in |   seconds |
|:---------|----------:|--------------:|-------------:|------------:|----------:|
| log      |      0.68 |          0.45 |         0.65 |     3558.57 |     10.91 |
| diff     |      0.61 |          0.51 |         0.78 |     4663.92 |     13.27 |
| prov     |      0.64 |          0.49 |         0.49 |     4565.58 |     14.04 |

Of the wrong step answers, the share that named a step AFTER the fault (the symptom, not the cause): 0.85.

Exact step by position of the fault (k_bin: 0 early, 1 middle, 2 late):

|   k_bin |   log |   diff |   prov |
|--------:|------:|-------:|-------:|
|    0.00 |  0.44 |   0.37 |   0.45 |
|    1.00 |  0.57 |   0.51 |   0.61 |
|    2.00 |  0.57 |   0.63 |   0.61 |

