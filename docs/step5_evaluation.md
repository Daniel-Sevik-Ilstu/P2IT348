# Step 5 Report: Evaluation

Written by the builder agent. All numbers below were produced by `python -m src.main --step 5` (about 23 s when run alone, which trains the models; in the full pipeline Step 5 reuses the Step 4 models) and are saved in `results/`.

## What was done

- `src/evaluate.py` holds the metric code: `compute_metrics` (accuracy, precision, recall, F1 with `pos_label=1`, `zero_division=0`), `confusion_counts`, `evaluate_model`, `pooled_table`, `assert_test_years_only`, `sensitivity_tables`, `save_table`. (`per_year_table` is also there because `sensitivity_tables` returns the per-year table too; it is Step 6 and not reported here.)
- The three Step 4 classifiers (fit on 2014-2016 only) are reused from `run_step4` when the whole pipeline runs and trained by `run_step5` only for `--step 5` alone. `pooled_table` and `confusion_table` raise `ValueError` if `X_test` and `y_test` differ in length. The entry point is `main.run_step5` (PLAN.md updated). The classifiers are evaluated on the **pooled held-out test years 2017-2021 only**: 45,000 rows (22,500 malware, 22,500 goodware). `assert_test_years_only` raises if any other year is passed. No metric is computed on training rows.
- Malware (label 1) is the positive class.
- 2017 and 2018 make up 80% of the pooled test set (36,000 of 45,000 rows; each is six times the size of 2019, 2020 or 2021), so the pooled numbers are dominated by the early test years. The per-year view is Step 6.

## Main table (all 45,000 test rows)

Files: `results/step5_metrics.csv|md`.

| Classifier | Accuracy | Precision | Recall | F1 | n_test | baseline_accuracy |
|---|---|---|---|---|---|---|
| logreg | 0.8600 | 0.8196 | 0.9232 | 0.8683 | 45000 | 0.5 |
| random_forest | 0.8658 | 0.8228 | 0.9324 | 0.8742 | 45000 | 0.5 |
| sgd | 0.8358 | 0.8063 | 0.8841 | 0.8434 | 45000 | 0.5 |

## Sensitivity: test rows with no exact training duplicate

Files: `results/step5_pooled_no_dup.csv|md`. Test rows whose exact feature vector also occurs in 2014-2016 (`train_duplicate_mask`, Step 1) are removed. This **removes 7,743 of 45,000 test rows (17.2%)**, leaving 37,257. The main table above keeps all rows.

| Classifier | Accuracy | Precision | Recall | F1 | n_test | n_excluded | n_malware | n_benign | n_excluded_malware | n_excluded_benign |
|---|---|---|---|---|---|---|---|---|---|---|
| logreg | 0.8480 | 0.7695 | 0.9318 | 0.8429 | 37257 | 7743 | 16300 | 20957 | 6200 | 1543 |
| random_forest | 0.8544 | 0.7735 | 0.9434 | 0.8501 | 37257 | 7743 | 16300 | 20957 | 6200 | 1543 |
| sgd | 0.8475 | 0.7636 | 0.9433 | 0.8440 | 37257 | 7743 | 16300 | 20957 | 6200 | 1543 |

**Class mix (review #3).** The filter removes 6,200 malware rows (27.6% of the 22,500 malware test rows) but only 1,543 goodware rows (6.9%). The subset is therefore 43.8% malware and 56.2% goodware, and its majority-class (always goodware) accuracy is **0.5625**, not 0.5. Accuracy gains over the baseline are 28.5-29.2 points here (vs. 33.6-36.6 on the full set). Precision falls partly because malware is now the minority: with the same false-positive rate, a smaller malware share gives lower precision, so the precision drop (about 0.05) is not only evidence that the models relied on duplicates. Recall is not affected by the base rate and rises slightly (0.9232 to 0.9318 for logreg). I did not compute a base-rate-adjusted precision.

Accuracy drops by about 1.1-1.2 points and F1 by about 2.4-2.5 points for logreg and random forest (accuracy 0.8600 to 0.8480, 0.8658 to 0.8544; F1 0.8683 to 0.8429, 0.8742 to 0.8501), so the duplicates help a little but do not explain the result. SGD's accuracy goes up (0.8358 to 0.8475) and its F1 goes up (0.8434 to 0.8440). Precision falls in all three (about 0.04-0.05) and recall rises. The removed rows are not a random sample (they are mostly 2017 rows, see Step 1: 5,972 of 18,000), so the filtered set also has a different year mix, which I did not break down further.

## Confusion matrices (pooled, all 45,000 test rows)

Files: `results/step5_confusion.csv|md`. Rows are the true class, columns the predicted class; malware = positive.

| Classifier | TN (goodware ok) | FP (goodware flagged) | FN (malware missed) | TP (malware caught) |
|---|---|---|---|---|
| logreg | 17927 | 4573 | 1729 | 20771 |
| random_forest | 17983 | 4517 | 1521 | 20979 |
| sgd | 17721 | 4779 | 2608 | 19892 |

## Baseline

The test set is exactly balanced (50% malware), so always predicting one class gives accuracy 0.5000 (saved as the `baseline_accuracy` column in `results/step5_metrics.csv`); logreg (0.8600), random forest (0.8658) and SGD (0.8358) beat that by 33.6-36.6 points, so all three learn real signal even on drifted years.

## Which metric matters most

Recall on malware matters most here: a missed malware app (false negative) is installed and can do harm, while a false alarm on goodware costs a review or a blocked install. Recall is 0.9232 (logreg), 0.9324 (random forest) and 0.8841 (SGD), i.e. 1,729, 1,521 and 2,608 of 22,500 malware apps are missed. Precision is lower (0.81-0.82): about one flagged app in five is goodware. Since the classes are balanced, accuracy is not misleading, but it hides this asymmetry; F1 balances precision and recall but treats both errors alike. All of these pooled numbers are dominated by 2017-2018 and may hide a decline in later years; Step 6 reports it per year.

## Caveats

- The classifiers were trained once with the default settings from Step 4 (no tuning), so differences of about one point between logreg and random forest are small and come from a single fit with `random_state=42`; I did not measure the run-to-run spread.
- Duplicate rows and 107 feature vectors with conflicting labels (Step 1) are kept in the main table, as planned.
- `PLAN.md` names the pooled file `results/step5_pooled_metrics.*`; I used `results/step5_metrics.*` as the lead engineer asked.
