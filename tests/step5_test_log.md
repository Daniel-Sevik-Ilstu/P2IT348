# Step 5 Test Log: Evaluate Classifier Performance

- Tester transcript: transcripts/25_2026-11-03_tester_step5.md

## Tests written (tester)

One row per test function. Row counts follow AGENTS.md (2014-2018: 9,000 per file; 2019-2021: 1,500), not ASSIGNMENT.md. Entry point tested: main.run_step5.

| Test | What it checks (from the assignment or plan) |
| --- | --- |
| test_metrics_hand_checked | TP=3, FP=1, FN=2, TN=4 gives accuracy 0.7, precision 0.75, recall 0.6, F1 2/3 (by hand) |
| test_metrics_match_sklearn | compute_metrics equals scikit-learn with pos_label=1 |
| test_metrics_have_expected_keys_and_range | keys accuracy/precision/recall/f1; all values in [0,1] |
| test_malware_is_positive_class | swapping labels changes precision/recall (label 1 is positive) |
| test_confusion_counts_add_up | confusion counts = (3,1,2,4) and sum to number of rows |
| test_all_benign_predictions_do_not_crash | one-class predictions: recall/precision/F1 = 0, no exception (zero_division) |
| test_all_malware_predictions | predict-all-malware gives recall 1, precision 0.5, values in [0,1] |
| test_no_positive_in_truth_and_prediction_no_crash | no malware in truth or prediction: zeros, no crash |
| test_unequal_lengths_raise | y_true/y_pred of different length raises ValueError |
| test_empty_input_raises_or_is_rejected | empty input raises rather than returning silent numbers |
| test_evaluate_model_uses_given_rows_and_predictions | evaluate_model predicts once on exactly the given X_test |
| test_pooled_table_columns_and_n_test | pooled table columns model,accuracy,precision,recall,f1,n_test; one row per model; n_test correct |
| test_assert_test_years_only_accepts_test_years | 2017-2021 accepted |
| test_assert_test_years_only_rejects_training_years | 2014/2015/2016 rejected (3 params) |
| test_assert_test_years_only_rejects_mixed_train_and_test | test rows mixed with training years raise |
| test_per_year_table_rows_and_counts | one row per model per year; n sums to total; weighted accuracy equals pooled; hand-checked 2017 row |
| test_per_year_table_rejects_training_years | per-year table refuses training years |
| test_sensitivity_tables_exclude_flagged_rows | excludes exactly dup_mask rows; n + n_excluded = full count; model sees only kept rows |
| test_sensitivity_tables_wrong_mask_length_raises | mask length mismatch raises |
| test_save_table_writes_csv_and_md | writes .csv and .md with 4-decimal rounding (RESULTS_DIR redirected to tmp_path) |
| test_run_step5_evaluates_only_test_years | main.run_step5 on synthetic 2014-2021 data: pooled n_test = number of 2017-2021 rows only; 3 models; metrics in [0,1] |
| test_run_step5_rejects_test_rows_mixed_with_training_years | run_step5 given a split with a 2015 row among test years raises ValueError |
| test_real_data_loaded_test_year_passes_and_train_year_fails | real data (skipped if absent): 2019 passes guard, training year fails; 2019 has 3,000 rows (AGENTS.md figure, not ASSIGNMENT.md's) |

## Failures and decisions (student)

One row per failing test. Decision is "Accepted" (the test is right; the builder fixes the code) or "Rejected" (the test is wrong; the tester fixes the test). Add the commit with the fix.

| Test | Cause | Decision | Fixed in commit |
| --- | --- | --- | --- |

## Runs (added by `python harness.py test N`; do not edit)

### Run 1: PASSED

- Time: 2026-11-03T04:34:22+02:00
- Commit: f339624
- Result: 25 passed, 1 warning in 3.45s
- Files: test_step5_evaluate.py

```
============================= test session starts =============================
platform win32 -- Python 3.11.4, pytest-9.2.0, pluggy-1.7.0 -- C:\Program Files\Python311\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\thema\OneDrive\Desktop\Project2\project2-harness2\project2-harness2
configfile: pytest.ini
plugins: anyio-4.8.0, dash-2.18.1
collecting ... collected 25 items

tests/test_step5_evaluate.py::test_metrics_hand_checked PASSED           [  4%]
tests/test_step5_evaluate.py::test_metrics_match_sklearn PASSED          [  8%]
tests/test_step5_evaluate.py::test_metrics_have_expected_keys_and_range PASSED [ 12%]
tests/test_step5_evaluate.py::test_malware_is_positive_class PASSED      [ 16%]
tests/test_step5_evaluate.py::test_confusion_counts_add_up PASSED        [ 20%]
tests/test_step5_evaluate.py::test_all_benign_predictions_do_not_crash PASSED [ 24%]
tests/test_step5_evaluate.py::test_all_malware_predictions PASSED        [ 28%]
tests/test_step5_evaluate.py::test_no_positive_in_truth_and_prediction_no_crash PASSED [ 32%]
tests/test_step5_evaluate.py::test_unequal_lengths_raise PASSED          [ 36%]
tests/test_step5_evaluate.py::test_empty_input_raises_or_is_rejected PASSED [ 40%]
tests/test_step5_evaluate.py::test_evaluate_model_uses_given_rows_and_predictions PASSED [ 44%]
tests/test_step5_evaluate.py::test_pooled_table_columns_and_n_test PASSED [ 48%]
tests/test_step5_evaluate.py::test_assert_test_years_only_accepts_test_years PASSED [ 52%]
tests/test_step5_evaluate.py::test_assert_test_years_only_rejects_training_years[2014] PASSED [ 56%]
tests/test_step5_evaluate.py::test_assert_test_years_only_rejects_training_years[2015] PASSED [ 60%]
tests/test_step5_evaluate.py::test_assert_test_years_only_rejects_training_years[2016] PASSED [ 64%]
tests/test_step5_evaluate.py::test_assert_test_years_only_rejects_mixed_train_and_test PASSED [ 68%]
tests/test_step5_evaluate.py::test_per_year_table_rows_and_counts PASSED [ 72%]
tests/test_step5_evaluate.py::test_per_year_table_rejects_training_years PASSED [ 76%]
tests/test_step5_evaluate.py::test_sensitivity_tables_exclude_flagged_rows PASSED [ 80%]
tests/test_step5_evaluate.py::test_sensitivity_tables_wrong_mask_length_raises PASSED [ 84%]
tests/test_step5_evaluate.py::test_save_table_writes_csv_and_md PASSED   [ 88%]
tests/test_step5_evaluate.py::test_run_step5_evaluates_only_test_years PASSED [ 92%]
tests/test_step5_evaluate.py::test_run_step5_rejects_test_rows_mixed_with_training_years PASSED [ 96%]
tests/test_step5_evaluate.py::test_real_data_loaded_test_year_passes_and_train_year_fails PASSED [100%]

============================== warnings summary ===============================
..\..\..\..\..\AppData\Roaming\Python\Python311\site-packages\dash\testing\plugin.py:92
  C:\Users\thema\AppData\Roaming\Python\Python311\site-packages\dash\testing\plugin.py:92: PytestRemovedIn10Warning: The hookimpl pytest_addhooks uses old-style configuration options (marks or attributes).
  Please use the pytest.hookimpl(tryfirst=True) decorator instead
   to configure the hooks.
   See https://docs.pytest.org/en/latest/deprecations.html#configuring-hook-specs-impls-using-markers
    @pytest.mark.tryfirst

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=================================== PASSES ====================================
__________________ test_run_step5_evaluates_only_test_years ___________________
---------------------------- Captured stdout call -----------------------------
Step 5 (pooled test years, n=750; majority-class accuracy 0.5253):
        model  accuracy  precision  recall     f1  n_test
       logreg    0.9867     0.9887  0.9831 0.9859     750
random_forest    0.9867     0.9887  0.9831 0.9859     750
          sgd    0.9760     0.9774  0.9719 0.9746     750
Sensitivity (no exact training duplicate; 66 test rows excluded):
        model  accuracy  precision  recall     f1  n_test  n_excluded
       logreg    0.9854     0.9886  0.9831 0.9858     684          66
random_forest    0.9854     0.9886  0.9831 0.9858     684          66
          sgd    0.9737     0.9773  0.9718 0.9745     684          66
        model  tn  fp  fn  tp
       logreg 390   4   6 350
random_forest 390   4   6 350
          sgd 386   8  10 346
=========================== short test summary info ===========================
PASSED tests/test_step5_evaluate.py::test_metrics_hand_checked
PASSED tests/test_step5_evaluate.py::test_metrics_match_sklearn
PASSED tests/test_step5_evaluate.py::test_metrics_have_expected_keys_and_range
PASSED tests/test_step5_evaluate.py::test_malware_is_positive_class
PASSED tests/test_step5_evaluate.py::test_confusion_counts_add_up
PASSED tests/test_step5_evaluate.py::test_all_benign_predictions_do_not_crash
PASSED tests/test_step5_evaluate.py::test_all_malware_predictions
PASSED tests/test_step5_evaluate.py::test_no_positive_in_truth_and_prediction_no_crash
PASSED tests/test_step5_evaluate.py::test_unequal_lengths_raise
PASSED tests/test_step5_evaluate.py::test_empty_input_raises_or_is_rejected
PASSED tests/test_step5_evaluate.py::test_evaluate_model_uses_given_rows_and_predictions
PASSED tests/test_step5_evaluate.py::test_pooled_table_columns_and_n_test
PASSED tests/test_step5_evaluate.py::test_assert_test_years_only_accepts_test_years
PASSED tests/test_step5_evaluate.py::test_assert_test_years_only_rejects_training_years[2014]
PASSED tests/test_step5_evaluate.py::test_assert_test_years_only_rejects_training_years[2015]
PASSED tests/test_step5_evaluate.py::test_assert_test_years_only_rejects_training_years[2016]
PASSED tests/test_step5_evaluate.py::test_assert_test_years_only_rejects_mixed_train_and_test
PASSED tests/test_step5_evaluate.py::test_per_year_table_rows_and_counts
PASSED tests/test_step5_evaluate.py::test_per_year_table_rejects_training_years
PASSED tests/test_step5_evaluate.py::test_sensitivity_tables_exclude_flagged_rows
PASSED tests/test_step5_evaluate.py::test_sensitivity_tables_wrong_mask_length_raises
PASSED tests/test_step5_evaluate.py::test_save_table_writes_csv_and_md
PASSED tests/test_step5_evaluate.py::test_run_step5_evaluates_only_test_years
PASSED tests/test_step5_evaluate.py::test_run_step5_rejects_test_rows_mixed_with_training_years
PASSED tests/test_step5_evaluate.py::test_real_data_loaded_test_year_passes_and_train_year_fails
======================== 25 passed, 1 warning in 3.45s ========================
```

### Run 2: PASSED

- Time: 2026-11-03T04:39:57+02:00
- Commit: 2472742
- Result: 25 passed, 1 warning in 3.26s
- Files: test_step5_evaluate.py

```
============================= test session starts =============================
platform win32 -- Python 3.11.4, pytest-9.2.0, pluggy-1.7.0 -- C:\Program Files\Python311\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\thema\OneDrive\Desktop\Project2\project2-harness2\project2-harness2
configfile: pytest.ini
plugins: anyio-4.8.0, dash-2.18.1
collecting ... collected 25 items

tests/test_step5_evaluate.py::test_metrics_hand_checked PASSED           [  4%]
tests/test_step5_evaluate.py::test_metrics_match_sklearn PASSED          [  8%]
tests/test_step5_evaluate.py::test_metrics_have_expected_keys_and_range PASSED [ 12%]
tests/test_step5_evaluate.py::test_malware_is_positive_class PASSED      [ 16%]
tests/test_step5_evaluate.py::test_confusion_counts_add_up PASSED        [ 20%]
tests/test_step5_evaluate.py::test_all_benign_predictions_do_not_crash PASSED [ 24%]
tests/test_step5_evaluate.py::test_all_malware_predictions PASSED        [ 28%]
tests/test_step5_evaluate.py::test_no_positive_in_truth_and_prediction_no_crash PASSED [ 32%]
tests/test_step5_evaluate.py::test_unequal_lengths_raise PASSED          [ 36%]
tests/test_step5_evaluate.py::test_empty_input_raises_or_is_rejected PASSED [ 40%]
tests/test_step5_evaluate.py::test_evaluate_model_uses_given_rows_and_predictions PASSED [ 44%]
tests/test_step5_evaluate.py::test_pooled_table_columns_and_n_test PASSED [ 48%]
tests/test_step5_evaluate.py::test_assert_test_years_only_accepts_test_years PASSED [ 52%]
tests/test_step5_evaluate.py::test_assert_test_years_only_rejects_training_years[2014] PASSED [ 56%]
tests/test_step5_evaluate.py::test_assert_test_years_only_rejects_training_years[2015] PASSED [ 60%]
tests/test_step5_evaluate.py::test_assert_test_years_only_rejects_training_years[2016] PASSED [ 64%]
tests/test_step5_evaluate.py::test_assert_test_years_only_rejects_mixed_train_and_test PASSED [ 68%]
tests/test_step5_evaluate.py::test_per_year_table_rows_and_counts PASSED [ 72%]
tests/test_step5_evaluate.py::test_per_year_table_rejects_training_years PASSED [ 76%]
tests/test_step5_evaluate.py::test_sensitivity_tables_exclude_flagged_rows PASSED [ 80%]
tests/test_step5_evaluate.py::test_sensitivity_tables_wrong_mask_length_raises PASSED [ 84%]
tests/test_step5_evaluate.py::test_save_table_writes_csv_and_md PASSED   [ 88%]
tests/test_step5_evaluate.py::test_run_step5_evaluates_only_test_years PASSED [ 92%]
tests/test_step5_evaluate.py::test_run_step5_rejects_test_rows_mixed_with_training_years PASSED [ 96%]
tests/test_step5_evaluate.py::test_real_data_loaded_test_year_passes_and_train_year_fails PASSED [100%]

============================== warnings summary ===============================
..\..\..\..\..\AppData\Roaming\Python\Python311\site-packages\dash\testing\plugin.py:92
  C:\Users\thema\AppData\Roaming\Python\Python311\site-packages\dash\testing\plugin.py:92: PytestRemovedIn10Warning: The hookimpl pytest_addhooks uses old-style configuration options (marks or attributes).
  Please use the pytest.hookimpl(tryfirst=True) decorator instead
   to configure the hooks.
   See https://docs.pytest.org/en/latest/deprecations.html#configuring-hook-specs-impls-using-markers
    @pytest.mark.tryfirst

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=================================== PASSES ====================================
__________________ test_run_step5_evaluates_only_test_years ___________________
---------------------------- Captured stdout call -----------------------------
Step 5 (pooled test years, n=750; majority-class accuracy 0.5253):
        model  accuracy  precision  recall     f1  n_test  baseline_accuracy
       logreg    0.9867     0.9887  0.9831 0.9859     750             0.5253
random_forest    0.9867     0.9887  0.9831 0.9859     750             0.5253
          sgd    0.9760     0.9774  0.9719 0.9746     750             0.5253
Sensitivity (no exact training duplicate; 66 test rows excluded; majority-class accuracy of subset 0.5175):
        model  accuracy  precision  recall     f1  n_test  n_excluded  n_malware  n_benign  n_excluded_malware  n_excluded_benign
       logreg    0.9854     0.9886  0.9831 0.9858     684          66        354       330                   2                 64
random_forest    0.9854     0.9886  0.9831 0.9858     684          66        354       330                   2                 64
          sgd    0.9737     0.9773  0.9718 0.9745     684          66        354       330                   2                 64
        model  tn  fp  fn  tp
       logreg 390   4   6 350
random_forest 390   4   6 350
          sgd 386   8  10 346
=========================== short test summary info ===========================
PASSED tests/test_step5_evaluate.py::test_metrics_hand_checked
PASSED tests/test_step5_evaluate.py::test_metrics_match_sklearn
PASSED tests/test_step5_evaluate.py::test_metrics_have_expected_keys_and_range
PASSED tests/test_step5_evaluate.py::test_malware_is_positive_class
PASSED tests/test_step5_evaluate.py::test_confusion_counts_add_up
PASSED tests/test_step5_evaluate.py::test_all_benign_predictions_do_not_crash
PASSED tests/test_step5_evaluate.py::test_all_malware_predictions
PASSED tests/test_step5_evaluate.py::test_no_positive_in_truth_and_prediction_no_crash
PASSED tests/test_step5_evaluate.py::test_unequal_lengths_raise
PASSED tests/test_step5_evaluate.py::test_empty_input_raises_or_is_rejected
PASSED tests/test_step5_evaluate.py::test_evaluate_model_uses_given_rows_and_predictions
PASSED tests/test_step5_evaluate.py::test_pooled_table_columns_and_n_test
PASSED tests/test_step5_evaluate.py::test_assert_test_years_only_accepts_test_years
PASSED tests/test_step5_evaluate.py::test_assert_test_years_only_rejects_training_years[2014]
PASSED tests/test_step5_evaluate.py::test_assert_test_years_only_rejects_training_years[2015]
PASSED tests/test_step5_evaluate.py::test_assert_test_years_only_rejects_training_years[2016]
PASSED tests/test_step5_evaluate.py::test_assert_test_years_only_rejects_mixed_train_and_test
PASSED tests/test_step5_evaluate.py::test_per_year_table_rows_and_counts
PASSED tests/test_step5_evaluate.py::test_per_year_table_rejects_training_years
PASSED tests/test_step5_evaluate.py::test_sensitivity_tables_exclude_flagged_rows
PASSED tests/test_step5_evaluate.py::test_sensitivity_tables_wrong_mask_length_raises
PASSED tests/test_step5_evaluate.py::test_save_table_writes_csv_and_md
PASSED tests/test_step5_evaluate.py::test_run_step5_evaluates_only_test_years
PASSED tests/test_step5_evaluate.py::test_run_step5_rejects_test_rows_mixed_with_training_years
PASSED tests/test_step5_evaluate.py::test_real_data_loaded_test_year_passes_and_train_year_fails
======================== 25 passed, 1 warning in 3.26s ========================
```
