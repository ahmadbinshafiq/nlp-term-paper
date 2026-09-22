# Analysis of sweep `main`, primary auditor (qwen3.8:27b)

Main analysis: sweep tasks.


Faulty runs: 300 (removed as too long: 0). Answers parsed: 0.99.

## 1. Outcome label

**refuted: another interaction**

Interaction test: p = 0.0000 (glmer, task and run intercepts; fit warning left: False). Equivalence bound B = 0.20.

Predictions that cannot be tested because every format is at 95 percent or more in that class (ceiling): evidence.

Control 1 (sham records equal clean records): pass. Control 3 (structure-only guesser on the two tool faults: 7/100 = 0.07 [0.03, 0.14], against tool prior 0.226 + 0.10): pass. Control 4 (real exact score 0.839 against labels shuffled within fault type: mean 0.264, 97.5 percent point 0.308): pass.

| Class | Predicted format | Margin | 95% interval | 90% interval | Meets the rule |
|---|---|---|---|---|---|
| tool | log | -0.010 | [-0.060, +0.035] | [-0.050, +0.030] | no |
| state | diff | +0.095 | [+0.050, +0.145] | [+0.060, +0.135] | no |
| evidence | prov | +0.010 | [-0.030, +0.050] | [-0.025, +0.045] | no |

## 2. Exact step found, per fault class and format

| fault_class   |   log |   diff |   prov |
|:--------------|------:|-------:|-------:|
| evidence      |  0.97 |   0.95 |   0.97 |
| state         |  0.74 |   0.93 |   0.93 |
| tool          |  0.68 |   0.68 |   0.70 |

## 3. Exact step found, per fault type and format

| fault_type       |   log |   diff |   prov |
|:-----------------|------:|-------:|-------:|
| wrong_argument   |  0.88 |   0.84 |   0.92 |
| corrupted_output |  0.48 |   0.52 |   0.48 |
| dropped_note     |  0.48 |   0.86 |   0.86 |
| overwritten_note |  1.00 |   1.00 |   1.00 |
| wrong_source     |  1.00 |   1.00 |   1.00 |
| no_source        |  0.94 |   0.90 |   0.94 |

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

- `log`: false alarms 15/45 = 0.33 [0.21, 0.48]; said "no fault" on a faulty run 34/300 = 0.11 [0.08, 0.15]
- `diff`: false alarms 14/45 = 0.31 [0.20, 0.46]; said "no fault" on a faulty run 10/300 = 0.03 [0.02, 0.06]
- `prov`: false alarms 18/45 = 0.40 [0.27, 0.55]; said "no fault" on a faulty run 8/300 = 0.03 [0.01, 0.05]

## 6. Secondary

| format   |   within3 |   right_class |   pointer_ok |   tokens_in |   seconds |
|:---------|----------:|--------------:|-------------:|------------:|----------:|
| log      |      0.82 |          0.82 |         0.43 |     3773.80 |     47.24 |
| diff     |      0.89 |          0.88 |         0.54 |     4920.14 |     59.32 |
| prov     |      0.90 |          0.88 |         0.30 |     4854.51 |     60.51 |

Of the wrong step answers, the share that named a step AFTER the fault (the symptom, not the cause): 0.80.

Exact step by position of the fault (k_bin: 0 early, 1 middle, 2 late):

|   k_bin |   log |   diff |   prov |
|--------:|------:|-------:|-------:|
|    0.00 |  0.77 |   0.82 |   0.84 |
|    1.00 |  0.79 |   0.91 |   0.90 |
|    2.00 |  0.82 |   0.84 |   0.86 |

