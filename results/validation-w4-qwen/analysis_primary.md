# Analysis of sweep `validation-w4-qwen`, primary auditor (qwen3.8:27b)

EXPLORATORY: development tasks.


Faulty runs: 30 (removed as too long: 0). Answers parsed: 0.98.

## 1. Outcome label

**null**

Interaction test: p = 0.9598 (glmer, task and run intercepts; fit warning left: False). Equivalence bound B = 0.20.

Predictions that cannot be tested because every format is at 95 percent or more in that class (ceiling): evidence.

Control 1 (sham records equal clean records): pass. Control 3 (structure-only guesser on the two tool faults: 0/10 = 0.00 [0.00, 0.28], against tool prior 0.223 + 0.10): pass. Control 4 (real exact score 0.844 against labels shuffled within fault type: mean 0.316, 97.5 percent point 0.489): pass.

| Class | Predicted format | Margin | 95% interval | 90% interval | Meets the rule |
|---|---|---|---|---|---|
| tool | log | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | no |
| state | diff | +0.100 | [+0.000, +0.200] | [+0.000, +0.200] | no |
| evidence | prov | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | no |

## 2. Exact step found, per fault class and format

| fault_class   |   log |   diff |   prov |
|:--------------|------:|-------:|-------:|
| evidence      |  1.00 |   1.00 |   1.00 |
| state         |  0.80 |   0.90 |   0.80 |
| tool          |  0.70 |   0.70 |   0.70 |

## 3. Exact step found, per fault type and format

| fault_type       |   log |   diff |   prov |
|:-----------------|------:|-------:|-------:|
| wrong_argument   |  1.00 |   1.00 |   1.00 |
| corrupted_output |  0.40 |   0.40 |   0.40 |
| dropped_note     |  0.60 |   0.80 |   0.60 |
| overwritten_note |  1.00 |   1.00 |   1.00 |
| wrong_source     |  1.00 |   1.00 |   1.00 |
| no_source        |  1.00 |   1.00 |   1.00 |

## 4. Baselines without a model (share of runs where the faulty step was named)

| fault_type       |   uniform chance |   tool prior |   most frequent step |   position-only |   structure-only |   rule auditor |
|:-----------------|-----------------:|-------------:|---------------------:|----------------:|-----------------:|---------------:|
| wrong_argument   |             0.08 |         0.00 |                 0.00 |            0.00 |             0.00 |           0.00 |
| corrupted_output |             0.06 |         0.00 |                 0.00 |            0.20 |             0.00 |           0.00 |
| dropped_note     |             0.09 |         0.31 |                 0.40 |            0.00 |             1.00 |           1.00 |
| overwritten_note |             0.09 |         0.31 |                 0.20 |            0.60 |             1.00 |           1.00 |
| wrong_source     |             0.09 |         0.29 |                 0.40 |            0.00 |             0.00 |           0.00 |
| no_source        |             0.12 |         0.43 |                 0.40 |            0.00 |             0.60 |           1.00 |

All faults together: uniform chance 0.089, tool prior 0.223, most frequent step 0.233, position-only 0.133, structure-only 0.433, rule auditor 0.500.

## 5. Controls: clean and sham runs

- `log`: false alarms 2/5 = 0.40 [0.12, 0.77]; said "no fault" on a faulty run 3/30 = 0.10 [0.03, 0.26]
- `diff`: false alarms 3/5 = 0.60 [0.23, 0.88]; said "no fault" on a faulty run 1/30 = 0.03 [0.01, 0.17]
- `prov`: false alarms 2/5 = 0.40 [0.12, 0.77]; said "no fault" on a faulty run 1/30 = 0.03 [0.01, 0.17]

## 6. Secondary

| format   |   within3 |   right_class |   pointer_ok |   tokens_in |   seconds |
|:---------|----------:|--------------:|-------------:|------------:|----------:|
| log      |      0.87 |          0.87 |         0.40 |     3860.77 |     50.34 |
| diff     |      0.90 |          0.93 |         0.53 |     5021.23 |     61.80 |
| prov     |      0.87 |          0.87 |         0.30 |     5004.10 |     62.13 |

Of the wrong step answers, the share that named a step AFTER the fault (the symptom, not the cause): 0.89.

Exact step by position of the fault (k_bin: 0 early, 1 middle, 2 late):

|   k_bin |   log |   diff |   prov |
|--------:|------:|-------:|-------:|
|    0.00 |  0.80 |   0.80 |   0.80 |
|    1.00 |  0.71 |   0.86 |   0.71 |
|    2.00 |  0.92 |   0.92 |   0.92 |

