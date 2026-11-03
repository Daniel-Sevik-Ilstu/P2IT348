# Step 5 Report: Evaluation

Written by the builder agent. All numbers below were produced by `python -m src.main --step 5` (about 23 s including the three model fits) and are saved in `results/`.

## What was done

- `src/evaluate.py` holds the metric code: `compute_metrics` (accuracy, precision, recall, F1 with `pos_label=1`, `zero_division=0`), `confusion_counts`, `evaluate_model`, `pooled_table`, `assert_test_years_only`, `sensitivity_tables`, `save_table`. (`per_year_table` is also there because `sensitivity_tables` returns the per-year table too; it is Step 6 and not reported here.)
- The three Step 4 classifiers (fit on 2014-2016 only, via `train_all_from_split`) are evaluated on the **pooled held-out test years 2017-2021 only**: 45,000 rows (22,500 malware, 22,500 goodware). `assert_test_years_only` raises if any other year is passed. No metric is computed on training rows.
- Malware (label 1) is the positive class.
- Because pooled metrics weight 2017-2018 (18,000 rows each) six times more than 2019-2021 (3,000 each), the pooled numbers are dominated by the early test years. The per-year view is Step 6.

## Main table (all 45,000 test rows)

Files: `results/step5_metrics.csv|md`.

| Classifier | Accuracy | Precision | Recall | F1 | n_test |
|---|---|---|---|---|---|
| logreg | 0.8600 | 0.8196 | 0.9232 | 0.8683 | 45000 |
| random_forest | 0.8658 | 0.8228 | 0.9324 | 0.8742 | 45000 |
| sgd | 0.8358 | 0.8063 | 0.8841 | 0.8434 | 45000 |

## Sensitivity: test rows with no exact training duplicate

Files: `results/step5_pooled_no_dup.csv|md`. Test rows whose exact feature vector also occurs in 2014-2016 (`train_duplicate_mask`, Step 1) are removed. This **removes 7,743 of 45,000 test rows (17.2%)**, leaving 37,257. The main table above keeps all rows.

| Classifier | Accuracy | Precision | Recall | F1 | n_test | n_excluded |
|---|---|---|---|---|---|---|
| logreg | 0.8480 | 0.7695 | 0.9318 | 0.8429 | 37257 | 7743 |
| random_forest | 0.8544 | 0.7735 | 0.9434 | 0.8501 | 37257 | 7743 |
| sgd | 0.8475 | 0.7636 | 0.9433 | 0.8440 | 37257 | 7743 |

Accuracy and F1 drop by about 0.5-1.4 points for logreg and random forest (accuracy 0.8600 to 0.8480, 0.8658 to 0.8544), so the duplicates help a little but do not explain the result. SGD changes the least in accuracy (0.8358 to 0.8475, slightly higher). Precision falls in all three (about 0.04-0.05) and recall rises. The removed rows are not a random sample (they are mostly 2017 rows, see Step 1: 5,972 of 18,000), so the filtered set has a different class mix and year mix; I did not break this down further.

## Confusion matrices (pooled, all 45,000 test rows)

Files: `results/step5_confusion.csv|md`. Rows are the true class, columns the predicted class; malware = positive.

| Classifier | TN (goodware ok) | FP (goodware flagged) | FN (malware missed) | TP (malware caught) |
|---|---|---|---|---|
| logreg | 17927 | 4573 | 1729 | 20771 |
| random_forest | 17983 | 4517 | 1521 | 20979 |
| sgd | 17721 | 4779 | 2608 | 19892 |

## Baseline

The test set is exactly balanced (50% malware), so always predicting one class gives accuracy 0.5000; logreg (0.8600), random forest (0.8658) and SGD (0.8358) beat that by 33.6-36.6 points, so all three learn real signal even on drifted years.

## Which metric matters most

Recall on malware matters most here: a missed malware app (false negative) is installed and can do harm, while a false alarm on goodware costs a review or a blocked install. Recall is 0.9232 (logreg), 0.9324 (random forest) and 0.8841 (SGD), i.e. 1,729, 1,521 and 2,608 of 22,500 malware apps are missed. Precision is lower (0.81-0.82): about one flagged app in five is goodware. Since the classes are balanced, accuracy is not misleading, but it hides this asymmetry; F1 balances precision and recall but treats both errors alike. All of these pooled numbers are dominated by 2017-2018 and may hide a decline in later years; Step 6 reports it per year.

## Caveats

- The classifiers were trained once with the default settings from Step 4 (no tuning), so differences of about one point between logreg and random forest are small and come from a single fit with `random_state=42`; I did not measure the run-to-run spread.
- Duplicate rows and 107 feature vectors with conflicting labels (Step 1) are kept in the main table, as planned.
- `PLAN.md` names the pooled file `results/step5_pooled_metrics.*`; I used `results/step5_metrics.*` as the lead engineer asked.
