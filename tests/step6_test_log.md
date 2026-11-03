# Step 6 Test Log: Test Data Prediction

- Tester transcript: transcripts/29_2026-11-03_tester_step6.md

## Tests written (tester)

One row per test function. Row counts follow AGENTS.md (2014-2018: 9,000 per file, so 18,000 per year; 2019-2021: 1,500 per file, so 3,000 per year), not ASSIGNMENT.md. Entry point tested: main.run_step6 (PLAN.md), plus evaluate.per_year_table.

| Test | What it checks (from the assignment or plan) |
| --- | --- |
| test_one_row_per_test_year_per_classifier | 15 rows: logreg, random_forest, sgd x 2017-2021, no duplicate (model, year) pairs |
| test_all_metric_values_between_0_and_1 | accuracy, precision, recall, f1 all in [0,1], no NaN |
| test_per_year_n_sums_to_total_test_rows | per-year n adds up to the number of 2017-2021 rows for each classifier; each year's n = rows in that year |
| test_no_training_year_in_per_year_table | no 2014-2016 year in any returned table with a year column |
| test_step6_writes_expected_files | results/step6_by_year.csv has columns classifier, year, n, accuracy, precision, recall, f1 and 15 rows |
| test_step6_only_predicts_with_given_models | stub models raise on fit/partial_fit and Preprocessor.fit is patched to raise; run_step6 still works (predict only) |
| test_step6_does_not_refit_passed_models | a fitted LogisticRegression keeps identical coef_/intercept_ after run_step6 |
| test_per_year_metrics_hand_checked_two_years | hand-computed two-year example (2017: acc 0.6, P/R/F1 2/3; 2018: acc 0.75, P/R/F1 0 with zero_division) |
| test_per_year_metrics_match_sklearn | per-year metrics equal scikit-learn (pos_label=1) on the same rows |
| test_run_step6_matches_sklearn_on_same_rows | end to end: run_step6 per-year f1/accuracy equal sklearn on each model's own predictions |
| test_year_outside_test_range_is_rejected | years 2013, 2016, 2022 in the test rows raise ValueError |
| test_single_class_test_year_does_not_crash | all-malware 2019 and all-benign 2021: 15 rows, no NaN, metrics in [0,1]; 2021 precision/recall/F1 = 0 |
| test_missing_test_year_is_not_invented | data without 2019: step raises, or table has exactly 2017, 2018, 2020, 2021 and no fake 2019 row |
| test_real_data_each_test_year_has_expected_rows | real data (skipped if absent): 18,000 rows for 2017-2018, 3,000 for 2019-2021; per-year n and metric range with a stub model (no retraining) |

## Failures and decisions (student)

One row per failing test. Decision is "Accepted" (the test is right; the builder fixes the code) or "Rejected" (the test is wrong; the tester fixes the test). Add the commit with the fix.

| Test | Cause | Decision | Fixed in commit |
| --- | --- | --- | --- |
| test_step6_only_predicts_with_given_models | The test stub asserted that predict always sees all 600 test rows, but run_step6 also predicts on the smaller no-duplicate subset (552 rows), so it failed with 552 == 600. The code is right and the test setup was wrong; the tester fixed the stub and Run 2 passed. | Rejected | dc006ad |

## Runs (added by `python harness.py test N`; do not edit)

### Run 1: FAILED

- Time: 2026-11-03T05:38:08+02:00
- Commit: 6195a68
- Result: 1 failed, 13 passed, 1 warning in 16.46s
- Files: test_step6_per_year.py

```
... (208 earlier lines omitted)
______________________ test_step6_writes_expected_files _______________________
---------------------------- Captured stdout call -----------------------------
Step 6 (per test year; malware = positive class):
   classifier  year   n  accuracy  precision  recall     f1
       logreg  2017 120    0.9917     1.0000  0.9833 0.9916
       logreg  2018 120    1.0000     1.0000  1.0000 1.0000
       logreg  2019 120    1.0000     1.0000  1.0000 1.0000
       logreg  2020 120    0.9833     0.9667  1.0000 0.9831
       logreg  2021 120    0.9833     0.9630  1.0000 0.9811
random_forest  2017 120    0.9833     0.9677  1.0000 0.9836
random_forest  2018 120    0.9833     0.9677  1.0000 0.9836
random_forest  2019 120    1.0000     1.0000  1.0000 1.0000
random_forest  2020 120    0.9833     0.9828  0.9828 0.9828
random_forest  2021 120    0.9833     0.9808  0.9808 0.9808
          sgd  2017 120    0.9917     1.0000  0.9833 0.9916
          sgd  2018 120    1.0000     1.0000  1.0000 1.0000
          sgd  2019 120    1.0000     1.0000  1.0000 1.0000
          sgd  2020 120    0.9833     0.9667  1.0000 0.9831
          sgd  2021 120    0.9833     0.9630  1.0000 0.9811
 year   n  n_malware  n_benign  malware_share  baseline_accuracy
 2017 120         60        60         0.5000             0.5000
 2018 120         60        60         0.5000             0.5000
 2019 120         55        65         0.4583             0.5417
 2020 120         58        62         0.4833             0.5167
 2021 120         52        68         0.4333             0.5667
        model  first_year  last_year  f1_first  f1_last  f1_drop  f1_slope_per_year
       logreg        2017       2021    0.9916   0.9811   0.0105            -0.0038
random_forest        2017       2021    0.9836   0.9808   0.0028            -0.0007
          sgd        2017       2021    0.9916   0.9811   0.0105            -0.0038
___________________ test_step6_does_not_refit_passed_models ___________________
---------------------------- Captured stdout call -----------------------------
Step 6 (per test year; malware = positive class):
classifier  year   n  accuracy  precision  recall     f1
    logreg  2017 120    0.9917     1.0000  0.9833 0.9916
    logreg  2018 120    1.0000     1.0000  1.0000 1.0000
    logreg  2019 120    1.0000     1.0000  1.0000 1.0000
    logreg  2020 120    0.9833     0.9667  1.0000 0.9831
    logreg  2021 120    0.9833     0.9630  1.0000 0.9811
 year   n  n_malware  n_benign  malware_share  baseline_accuracy
 2017 120         60        60         0.5000             0.5000
 2018 120         60        60         0.5000             0.5000
 2019 120         55        65         0.4583             0.5417
 2020 120         58        62         0.4833             0.5167
 2021 120         52        68         0.4333             0.5667
 model  first_year  last_year  f1_first  f1_last  f1_drop  f1_slope_per_year
logreg        2017       2021    0.9916   0.9811   0.0105            -0.0038
_________________ test_run_step6_matches_sklearn_on_same_rows _________________
---------------------------- Captured stdout call -----------------------------
Step 6 (per test year; malware = positive class):
   classifier  year   n  accuracy  precision  recall     f1
       logreg  2017 120    0.9917     1.0000  0.9833 0.9916
       logreg  2018 120    1.0000     1.0000  1.0000 1.0000
       logreg  2019 120    1.0000     1.0000  1.0000 1.0000
       logreg  2020 120    0.9833     0.9667  1.0000 0.9831
       logreg  2021 120    0.9833     0.9630  1.0000 0.9811
random_forest  2017 120    0.9833     0.9677  1.0000 0.9836
random_forest  2018 120    0.9833     0.9677  1.0000 0.9836
random_forest  2019 120    1.0000     1.0000  1.0000 1.0000
random_forest  2020 120    0.9833     0.9828  0.9828 0.9828
random_forest  2021 120    0.9833     0.9808  0.9808 0.9808
          sgd  2017 120    0.9917     1.0000  0.9833 0.9916
          sgd  2018 120    1.0000     1.0000  1.0000 1.0000
          sgd  2019 120    1.0000     1.0000  1.0000 1.0000
          sgd  2020 120    0.9833     0.9667  1.0000 0.9831
          sgd  2021 120    0.9833     0.9630  1.0000 0.9811
 year   n  n_malware  n_benign  malware_share  baseline_accuracy
 2017 120         60        60         0.5000             0.5000
 2018 120         60        60         0.5000             0.5000
 2019 120         55        65         0.4583             0.5417
 2020 120         58        62         0.4833             0.5167
 2021 120         52        68         0.4333             0.5667
        model  first_year  last_year  f1_first  f1_last  f1_drop  f1_slope_per_year
       logreg        2017       2021    0.9916   0.9811   0.0105            -0.0038
random_forest        2017       2021    0.9836   0.9808   0.0028            -0.0007
          sgd        2017       2021    0.9916   0.9811   0.0105            -0.0038
_________________ test_single_class_test_year_does_not_crash __________________
---------------------------- Captured stdout call -----------------------------
Step 6 (per test year; malware = positive class):
   classifier  year   n  accuracy  precision  recall     f1
       logreg  2017 120    0.9917     1.0000  0.9833 0.9916
       logreg  2018 120    1.0000     1.0000  1.0000 1.0000
       logreg  2019 120    0.4583     1.0000  0.4583 0.6286
       logreg  2020 120    0.9833     0.9667  1.0000 0.9831
       logreg  2021 120    0.5500     0.0000  0.0000 0.0000
random_forest  2017 120    0.9833     0.9677  1.0000 0.9836
random_forest  2018 120    0.9833     0.9677  1.0000 0.9836
random_forest  2019 120    0.4583     1.0000  0.4583 0.6286
random_forest  2020 120    0.9833     0.9828  0.9828 0.9828
random_forest  2021 120    0.5667     0.0000  0.0000 0.0000
          sgd  2017 120    0.9917     1.0000  0.9833 0.9916
          sgd  2018 120    1.0000     1.0000  1.0000 1.0000
          sgd  2019 120    0.4583     1.0000  0.4583 0.6286
          sgd  2020 120    0.9833     0.9667  1.0000 0.9831
          sgd  2021 120    0.5500     0.0000  0.0000 0.0000
 year   n  n_malware  n_benign  malware_share  baseline_accuracy
 2017 120         60        60         0.5000             0.5000
 2018 120         60        60         0.5000             0.5000
 2019 120        120         0         1.0000             1.0000
 2020 120         58        62         0.4833             0.5167
 2021 120          0       120         0.0000             1.0000
        model  first_year  last_year  f1_first  f1_last  f1_drop  f1_slope_per_year
       logreg        2017       2021    0.9916      0.0   0.9916            -0.2000
random_forest        2017       2021    0.9836      0.0   0.9836            -0.1968
          sgd        2017       2021    0.9916      0.0   0.9916            -0.2000
=========================== short test summary info ===========================
PASSED tests/test_step6_per_year.py::test_one_row_per_test_year_per_classifier
PASSED tests/test_step6_per_year.py::test_all_metric_values_between_0_and_1
PASSED tests/test_step6_per_year.py::test_per_year_n_sums_to_total_test_rows
PASSED tests/test_step6_per_year.py::test_no_training_year_in_per_year_table
PASSED tests/test_step6_per_year.py::test_step6_writes_expected_files
PASSED tests/test_step6_per_year.py::test_step6_does_not_refit_passed_models
PASSED tests/test_step6_per_year.py::test_per_year_metrics_hand_checked_two_years
PASSED tests/test_step6_per_year.py::test_per_year_metrics_match_sklearn
PASSED tests/test_step6_per_year.py::test_run_step6_matches_sklearn_on_same_rows
PASSED tests/test_step6_per_year.py::test_year_outside_test_range_is_rejected
PASSED tests/test_step6_per_year.py::test_single_class_test_year_does_not_crash
PASSED tests/test_step6_per_year.py::test_missing_test_year_is_not_invented
PASSED tests/test_step6_per_year.py::test_real_data_each_test_year_has_expected_rows
FAILED tests/test_step6_per_year.py::test_step6_only_predicts_with_given_models
================== 1 failed, 13 passed, 1 warning in 16.46s ===================
```

### Run 2: PASSED

- Time: 2026-11-03T05:38:48+02:00
- Commit: 6195a68
- Result: 14 passed, 1 warning in 18.46s
- Files: test_step6_per_year.py

```
... (178 earlier lines omitted)
_________________ test_step6_only_predicts_with_given_models __________________
---------------------------- Captured stdout call -----------------------------
Step 6 (per test year; malware = positive class):
   classifier  year   n  accuracy  precision  recall     f1
       logreg  2017 120    0.8583     0.7945  0.9667 0.8722
       logreg  2018 120    0.8583     0.8209  0.9167 0.8661
       logreg  2019 120    0.8500     0.7681  0.9636 0.8548
       logreg  2020 120    0.7917     0.7200  0.9310 0.8120
       logreg  2021 120    0.7833     0.7031  0.8654 0.7759
random_forest  2017 120    0.8583     0.7945  0.9667 0.8722
random_forest  2018 120    0.8583     0.8209  0.9167 0.8661
random_forest  2019 120    0.8500     0.7681  0.9636 0.8548
random_forest  2020 120    0.7917     0.7200  0.9310 0.8120
random_forest  2021 120    0.7833     0.7031  0.8654 0.7759
          sgd  2017 120    0.8583     0.7945  0.9667 0.8722
          sgd  2018 120    0.8583     0.8209  0.9167 0.8661
          sgd  2019 120    0.8500     0.7681  0.9636 0.8548
          sgd  2020 120    0.7917     0.7200  0.9310 0.8120
          sgd  2021 120    0.7833     0.7031  0.8654 0.7759
 year   n  n_malware  n_benign  malware_share  baseline_accuracy
 2017 120         60        60         0.5000             0.5000
 2018 120         60        60         0.5000             0.5000
 2019 120         55        65         0.4583             0.5417
 2020 120         58        62         0.4833             0.5167
 2021 120         52        68         0.4333             0.5667
        model  first_year  last_year  f1_first  f1_last  f1_drop  f1_slope_per_year
       logreg        2017       2021    0.8722   0.7759   0.0963            -0.0247
random_forest        2017       2021    0.8722   0.7759   0.0963            -0.0247
          sgd        2017       2021    0.8722   0.7759   0.0963            -0.0247
___________________ test_step6_does_not_refit_passed_models ___________________
---------------------------- Captured stdout call -----------------------------
Step 6 (per test year; malware = positive class):
classifier  year   n  accuracy  precision  recall     f1
    logreg  2017 120    0.9917     1.0000  0.9833 0.9916
    logreg  2018 120    1.0000     1.0000  1.0000 1.0000
    logreg  2019 120    1.0000     1.0000  1.0000 1.0000
    logreg  2020 120    0.9833     0.9667  1.0000 0.9831
    logreg  2021 120    0.9833     0.9630  1.0000 0.9811
 year   n  n_malware  n_benign  malware_share  baseline_accuracy
 2017 120         60        60         0.5000             0.5000
 2018 120         60        60         0.5000             0.5000
 2019 120         55        65         0.4583             0.5417
 2020 120         58        62         0.4833             0.5167
 2021 120         52        68         0.4333             0.5667
 model  first_year  last_year  f1_first  f1_last  f1_drop  f1_slope_per_year
logreg        2017       2021    0.9916   0.9811   0.0105            -0.0038
_________________ test_run_step6_matches_sklearn_on_same_rows _________________
---------------------------- Captured stdout call -----------------------------
Step 6 (per test year; malware = positive class):
   classifier  year   n  accuracy  precision  recall     f1
       logreg  2017 120    0.9917     1.0000  0.9833 0.9916
       logreg  2018 120    1.0000     1.0000  1.0000 1.0000
       logreg  2019 120    1.0000     1.0000  1.0000 1.0000
       logreg  2020 120    0.9833     0.9667  1.0000 0.9831
       logreg  2021 120    0.9833     0.9630  1.0000 0.9811
random_forest  2017 120    0.9833     0.9677  1.0000 0.9836
random_forest  2018 120    0.9833     0.9677  1.0000 0.9836
random_forest  2019 120    1.0000     1.0000  1.0000 1.0000
random_forest  2020 120    0.9833     0.9828  0.9828 0.9828
random_forest  2021 120    0.9833     0.9808  0.9808 0.9808
          sgd  2017 120    0.9917     1.0000  0.9833 0.9916
          sgd  2018 120    1.0000     1.0000  1.0000 1.0000
          sgd  2019 120    1.0000     1.0000  1.0000 1.0000
          sgd  2020 120    0.9833     0.9667  1.0000 0.9831
          sgd  2021 120    0.9833     0.9630  1.0000 0.9811
 year   n  n_malware  n_benign  malware_share  baseline_accuracy
 2017 120         60        60         0.5000             0.5000
 2018 120         60        60         0.5000             0.5000
 2019 120         55        65         0.4583             0.5417
 2020 120         58        62         0.4833             0.5167
 2021 120         52        68         0.4333             0.5667
        model  first_year  last_year  f1_first  f1_last  f1_drop  f1_slope_per_year
       logreg        2017       2021    0.9916   0.9811   0.0105            -0.0038
random_forest        2017       2021    0.9836   0.9808   0.0028            -0.0007
          sgd        2017       2021    0.9916   0.9811   0.0105            -0.0038
_________________ test_single_class_test_year_does_not_crash __________________
---------------------------- Captured stdout call -----------------------------
Step 6 (per test year; malware = positive class):
   classifier  year   n  accuracy  precision  recall     f1
       logreg  2017 120    0.9917     1.0000  0.9833 0.9916
       logreg  2018 120    1.0000     1.0000  1.0000 1.0000
       logreg  2019 120    0.4583     1.0000  0.4583 0.6286
       logreg  2020 120    0.9833     0.9667  1.0000 0.9831
       logreg  2021 120    0.5500     0.0000  0.0000 0.0000
random_forest  2017 120    0.9833     0.9677  1.0000 0.9836
random_forest  2018 120    0.9833     0.9677  1.0000 0.9836
random_forest  2019 120    0.4583     1.0000  0.4583 0.6286
random_forest  2020 120    0.9833     0.9828  0.9828 0.9828
random_forest  2021 120    0.5667     0.0000  0.0000 0.0000
          sgd  2017 120    0.9917     1.0000  0.9833 0.9916
          sgd  2018 120    1.0000     1.0000  1.0000 1.0000
          sgd  2019 120    0.4583     1.0000  0.4583 0.6286
          sgd  2020 120    0.9833     0.9667  1.0000 0.9831
          sgd  2021 120    0.5500     0.0000  0.0000 0.0000
 year   n  n_malware  n_benign  malware_share  baseline_accuracy
 2017 120         60        60         0.5000             0.5000
 2018 120         60        60         0.5000             0.5000
 2019 120        120         0         1.0000             1.0000
 2020 120         58        62         0.4833             0.5167
 2021 120          0       120         0.0000             1.0000
        model  first_year  last_year  f1_first  f1_last  f1_drop  f1_slope_per_year
       logreg        2017       2021    0.9916      0.0   0.9916            -0.2000
random_forest        2017       2021    0.9836      0.0   0.9836            -0.1968
          sgd        2017       2021    0.9916      0.0   0.9916            -0.2000
=========================== short test summary info ===========================
PASSED tests/test_step6_per_year.py::test_one_row_per_test_year_per_classifier
PASSED tests/test_step6_per_year.py::test_all_metric_values_between_0_and_1
PASSED tests/test_step6_per_year.py::test_per_year_n_sums_to_total_test_rows
PASSED tests/test_step6_per_year.py::test_no_training_year_in_per_year_table
PASSED tests/test_step6_per_year.py::test_step6_writes_expected_files
PASSED tests/test_step6_per_year.py::test_step6_only_predicts_with_given_models
PASSED tests/test_step6_per_year.py::test_step6_does_not_refit_passed_models
PASSED tests/test_step6_per_year.py::test_per_year_metrics_hand_checked_two_years
PASSED tests/test_step6_per_year.py::test_per_year_metrics_match_sklearn
PASSED tests/test_step6_per_year.py::test_run_step6_matches_sklearn_on_same_rows
PASSED tests/test_step6_per_year.py::test_year_outside_test_range_is_rejected
PASSED tests/test_step6_per_year.py::test_single_class_test_year_does_not_crash
PASSED tests/test_step6_per_year.py::test_missing_test_year_is_not_invented
PASSED tests/test_step6_per_year.py::test_real_data_each_test_year_has_expected_rows
======================= 14 passed, 1 warning in 18.46s ========================
```

### Run 3: PASSED

- Time: 2026-11-03T05:57:04+02:00
- Commit: 6d6f625
- Result: 14 passed, 1 warning in 9.34s
- Files: test_step6_per_year.py

```
... (411 earlier lines omitted)
       logreg  2021 120    0.9833     0.9630  1.0000 0.9811
random_forest  2017 120    0.9833     0.9677  1.0000 0.9836
random_forest  2018 120    0.9833     0.9677  1.0000 0.9836
random_forest  2019 120    1.0000     1.0000  1.0000 1.0000
random_forest  2020 120    0.9833     0.9828  0.9828 0.9828
random_forest  2021 120    0.9833     0.9808  0.9808 0.9808
          sgd  2017 120    0.9917     1.0000  0.9833 0.9916
          sgd  2018 120    1.0000     1.0000  1.0000 1.0000
          sgd  2019 120    1.0000     1.0000  1.0000 1.0000
          sgd  2020 120    0.9833     0.9667  1.0000 0.9831
          sgd  2021 120    0.9833     0.9630  1.0000 0.9811
 year   n  n_malware  n_benign  malware_share  baseline_accuracy
 2017 120         60        60         0.5000             0.5000
 2018 120         60        60         0.5000             0.5000
 2019 120         55        65         0.4583             0.5417
 2020 120         58        62         0.4833             0.5167
 2021 120         52        68         0.4333             0.5667
        model  first_year  last_year  f1_first  f1_last  f1_drop  f1_slope_per_year
       logreg        2017       2021    0.9916   0.9811   0.0105            -0.0038
random_forest        2017       2021    0.9836   0.9808   0.0028            -0.0007
          sgd        2017       2021    0.9916   0.9811   0.0105            -0.0038
Confusion counts and predicted-malware share by year:
   classifier  year  tn  fp  fn  tp  predicted_malware_share
       logreg  2017  60   0   1  59                   0.4917
       logreg  2018  60   0   0  60                   0.5000
       logreg  2019  65   0   0  55                   0.4583
       logreg  2020  60   2   0  58                   0.5000
       logreg  2021  66   2   0  52                   0.4500
random_forest  2017  58   2   0  60                   0.5167
random_forest  2018  58   2   0  60                   0.5167
random_forest  2019  65   0   0  55                   0.4583
random_forest  2020  61   1   1  57                   0.4833
random_forest  2021  67   1   1  51                   0.4333
          sgd  2017  60   0   1  59                   0.4917
          sgd  2018  60   0   0  60                   0.5000
          sgd  2019  65   0   0  55                   0.4583
          sgd  2020  60   2   0  58                   0.5000
          sgd  2021  66   2   0  52                   0.4500
Clip share and mean |z| by year (before clipping):
 side  year   n  clip_share  mean_abs_z
train  2014 120         0.0      0.8534
train  2015 120         0.0      0.8484
train  2016 120         0.0      0.8373
 test  2017 120         0.0      0.8685
 test  2018 120         0.0      0.8521
 test  2019 120         0.0      0.8009
 test  2020 120         0.0      0.8540
 test  2021 120         0.0      0.8310
_________________ test_single_class_test_year_does_not_crash __________________
---------------------------- Captured stdout call -----------------------------
Step 6 (per test year; malware = positive class):
   classifier  year   n  accuracy  precision  recall     f1
       logreg  2017 120    0.9917     1.0000  0.9833 0.9916
       logreg  2018 120    1.0000     1.0000  1.0000 1.0000
       logreg  2019 120    0.4583     1.0000  0.4583 0.6286
       logreg  2020 120    0.9833     0.9667  1.0000 0.9831
       logreg  2021 120    0.5500     0.0000  0.0000 0.0000
random_forest  2017 120    0.9833     0.9677  1.0000 0.9836
random_forest  2018 120    0.9833     0.9677  1.0000 0.9836
random_forest  2019 120    0.4583     1.0000  0.4583 0.6286
random_forest  2020 120    0.9833     0.9828  0.9828 0.9828
random_forest  2021 120    0.5667     0.0000  0.0000 0.0000
          sgd  2017 120    0.9917     1.0000  0.9833 0.9916
          sgd  2018 120    1.0000     1.0000  1.0000 1.0000
          sgd  2019 120    0.4583     1.0000  0.4583 0.6286
          sgd  2020 120    0.9833     0.9667  1.0000 0.9831
          sgd  2021 120    0.5500     0.0000  0.0000 0.0000
 year   n  n_malware  n_benign  malware_share  baseline_accuracy
 2017 120         60        60         0.5000             0.5000
 2018 120         60        60         0.5000             0.5000
 2019 120        120         0         1.0000             1.0000
 2020 120         58        62         0.4833             0.5167
 2021 120          0       120         0.0000             1.0000
        model  first_year  last_year  f1_first  f1_last  f1_drop  f1_slope_per_year
       logreg        2017       2021    0.9916      0.0   0.9916            -0.2000
random_forest        2017       2021    0.9836      0.0   0.9836            -0.1968
          sgd        2017       2021    0.9916      0.0   0.9916            -0.2000
Confusion counts and predicted-malware share by year:
   classifier  year  tn  fp  fn  tp  predicted_malware_share
       logreg  2017  60   0   1  59                   0.4917
       logreg  2018  60   0   0  60                   0.5000
       logreg  2019   0   0  65  55                   0.4583
       logreg  2020  60   2   0  58                   0.5000
       logreg  2021  66  54   0   0                   0.4500
random_forest  2017  58   2   0  60                   0.5167
random_forest  2018  58   2   0  60                   0.5167
random_forest  2019   0   0  65  55                   0.4583
random_forest  2020  61   1   1  57                   0.4833
random_forest  2021  68  52   0   0                   0.4333
          sgd  2017  60   0   1  59                   0.4917
          sgd  2018  60   0   0  60                   0.5000
          sgd  2019   0   0  65  55                   0.4583
          sgd  2020  60   2   0  58                   0.5000
          sgd  2021  66  54   0   0                   0.4500
Clip share and mean |z| by year (before clipping):
 side  year   n  clip_share  mean_abs_z
train  2014 120         0.0      0.8534
train  2015 120         0.0      0.8484
train  2016 120         0.0      0.8373
 test  2017 120         0.0      0.8685
 test  2018 120         0.0      0.8521
 test  2019 120         0.0      0.8009
 test  2020 120         0.0      0.8540
 test  2021 120         0.0      0.8310
=========================== short test summary info ===========================
PASSED tests/test_step6_per_year.py::test_one_row_per_test_year_per_classifier
PASSED tests/test_step6_per_year.py::test_all_metric_values_between_0_and_1
PASSED tests/test_step6_per_year.py::test_per_year_n_sums_to_total_test_rows
PASSED tests/test_step6_per_year.py::test_no_training_year_in_per_year_table
PASSED tests/test_step6_per_year.py::test_step6_writes_expected_files
PASSED tests/test_step6_per_year.py::test_step6_only_predicts_with_given_models
PASSED tests/test_step6_per_year.py::test_step6_does_not_refit_passed_models
PASSED tests/test_step6_per_year.py::test_per_year_metrics_hand_checked_two_years
PASSED tests/test_step6_per_year.py::test_per_year_metrics_match_sklearn
PASSED tests/test_step6_per_year.py::test_run_step6_matches_sklearn_on_same_rows
PASSED tests/test_step6_per_year.py::test_year_outside_test_range_is_rejected
PASSED tests/test_step6_per_year.py::test_single_class_test_year_does_not_crash
PASSED tests/test_step6_per_year.py::test_missing_test_year_is_not_invented
PASSED tests/test_step6_per_year.py::test_real_data_each_test_year_has_expected_rows
======================== 14 passed, 1 warning in 9.34s ========================
```
