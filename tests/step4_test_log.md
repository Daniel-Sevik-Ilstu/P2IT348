# Step 4 Test Log: Apply Machine Learning Classifiers

- Tester transcript: transcripts/20_2026-11-03_tester_step4.md

- Source followed for row counts: AGENTS.md (2014-2018 = 9,000 rows per file, 2019-2021 = 1,500), not ASSIGNMENT.md. Tests use small synthetic data, so this only matters for the real-data test.
- One-class y_train, empty training set and mismatched lengths are not stated in PLAN.md; tests follow the AGENTS.md "fail loudly" rule and expect ValueError.

## Tests written (tester)

One row per test function.

| Test | What it checks (from the assignment or plan) |
| --- | --- |
| test_model_names_has_logreg_random_forest_sgd | MODEL_NAMES lists logreg, random_forest, sgd |
| test_build_model_returns_expected_classes | build_model builds the right sklearn classes by name |
| test_build_model_random_state_is_42 | Every model has random_state == 42 (parametrized) |
| test_logreg_is_balanced_and_has_larger_max_iter_than_default | LogisticRegression class_weight balanced, max_iter above the default 100 |
| test_random_forest_has_200_trees | RandomForest n_estimators == 200 |
| test_sgd_has_no_balanced_class_weight_and_log_loss | SGD has no class_weight='balanced' (partial_fit rejects it), log_loss |
| test_build_model_returns_new_unfitted_objects | build_model returns fresh unfitted objects |
| test_build_model_unknown_name_raises_value_error | Unknown/mis-cased/empty model name raises ValueError (parametrized) |
| test_each_model_fits_and_predicts_well_on_separable_data | Each model fits and predicts with accuracy > 0.9 on separable synthetic data |
| test_predictions_use_only_labels_0_and_1 | Predictions (incl. on unseen shifted data) are only 0 or 1 |
| test_train_all_returns_all_named_models_fitted | train_all returns a fitted model per MODEL_NAMES entry |
| test_same_random_state_gives_identical_results_twice | Two trainings on noisy data give identical predictions and probabilities |
| test_sgd_partial_fit_after_fit_works | SGD partial_fit works after fit |
| test_sgd_partial_fit_as_first_call_with_classes | SGD partial_fit works as first call with classes=[0,1] |
| test_train_all_from_split_accepts_2014_2016 | train_all_from_split accepts years 2014-2016 |
| test_train_all_from_split_raises_on_year_outside_2014_2016 | Any test-year or out-of-range training year raises ValueError (parametrized) |
| test_train_all_from_split_accepts_subset_of_training_years | A subset of 2014-2016 is allowed (guard is <=) |
| test_train_model_unknown_name_raises | train_model with unknown name raises ValueError |
| test_one_class_y_train_raises | y_train with a single class raises ValueError (edge case; parametrized) |
| test_empty_training_set_raises | Empty training set raises ValueError (parametrized) |
| test_mismatched_x_and_y_lengths_raise | X and y of different lengths raise ValueError (parametrized) |
| test_train_all_from_split_mismatched_years_length_raises | years_train shorter than X/y raises ValueError |
| test_train_all_from_split_empty_training_set_raises | Empty split raises ValueError |
| test_real_data_logreg_and_sgd_train_on_training_years | Real data (skipped w/o input_data): logreg and sgd train on a 3000-row subsample of 2014-2016, predict 0/1; RF not trained |

## Failures and decisions (student)

One row per failing test. Decision is "Accepted" (the test is right; the builder fixes the code) or "Rejected" (the test is wrong; the tester fixes the test). Add the commit with the fix.

| Test | Cause | Decision | Fixed in commit |
| --- | --- | --- | --- |
| test_one_class_y_train_raises[random_forest] | A one-class y_train is accepted by RandomForest and gives a degenerate model without any error. The test is right. Same defect as review comment 1 (accepted). | Accepted | 01e5099 |
| test_train_all_from_split_mismatched_years_length_raises | years_train shorter than X and y passes the guard because only the metadata set is checked. The test is right. Same defect as review comment 1. | Accepted | 01e5099 |

## Runs (added by `python harness.py test N`; do not edit)

### Run 1: FAILED

- Time: 2026-11-03T03:47:28+02:00
- Commit: 06afce4
- Result: 2 failed, 42 passed, 1 warning in 8.25s
- Files: test_step4_models.py

```
... (10 earlier lines omitted)
tests/test_step4_models.py::test_build_model_random_state_is_42[logreg] PASSED [  6%]
tests/test_step4_models.py::test_build_model_random_state_is_42[random_forest] PASSED [  9%]
tests/test_step4_models.py::test_build_model_random_state_is_42[sgd] PASSED [ 11%]
tests/test_step4_models.py::test_logreg_is_balanced_and_has_larger_max_iter_than_default PASSED [ 13%]
tests/test_step4_models.py::test_random_forest_has_200_trees PASSED      [ 15%]
tests/test_step4_models.py::test_sgd_has_no_balanced_class_weight_and_log_loss PASSED [ 18%]
tests/test_step4_models.py::test_build_model_returns_new_unfitted_objects PASSED [ 20%]
tests/test_step4_models.py::test_build_model_unknown_name_raises_value_error[svm] PASSED [ 22%]
tests/test_step4_models.py::test_build_model_unknown_name_raises_value_error[] PASSED [ 25%]
tests/test_step4_models.py::test_build_model_unknown_name_raises_value_error[LogReg] PASSED [ 27%]
tests/test_step4_models.py::test_build_model_unknown_name_raises_value_error[xgboost] PASSED [ 29%]
tests/test_step4_models.py::test_each_model_fits_and_predicts_well_on_separable_data[logreg] PASSED [ 31%]
tests/test_step4_models.py::test_each_model_fits_and_predicts_well_on_separable_data[random_forest] PASSED [ 34%]
tests/test_step4_models.py::test_each_model_fits_and_predicts_well_on_separable_data[sgd] PASSED [ 36%]
tests/test_step4_models.py::test_predictions_use_only_labels_0_and_1[logreg] PASSED [ 38%]
tests/test_step4_models.py::test_predictions_use_only_labels_0_and_1[random_forest] PASSED [ 40%]
tests/test_step4_models.py::test_predictions_use_only_labels_0_and_1[sgd] PASSED [ 43%]
tests/test_step4_models.py::test_train_all_returns_all_named_models_fitted PASSED [ 45%]
tests/test_step4_models.py::test_same_random_state_gives_identical_results_twice[logreg] PASSED [ 47%]
tests/test_step4_models.py::test_same_random_state_gives_identical_results_twice[random_forest] PASSED [ 50%]
tests/test_step4_models.py::test_same_random_state_gives_identical_results_twice[sgd] PASSED [ 52%]
tests/test_step4_models.py::test_sgd_partial_fit_after_fit_works PASSED  [ 54%]
tests/test_step4_models.py::test_sgd_partial_fit_as_first_call_with_classes PASSED [ 56%]
tests/test_step4_models.py::test_train_all_from_split_accepts_2014_2016 PASSED [ 59%]
tests/test_step4_models.py::test_train_all_from_split_raises_on_year_outside_2014_2016[years0] PASSED [ 61%]
tests/test_step4_models.py::test_train_all_from_split_raises_on_year_outside_2014_2016[years1] PASSED [ 63%]
tests/test_step4_models.py::test_train_all_from_split_raises_on_year_outside_2014_2016[years2] PASSED [ 65%]
tests/test_step4_models.py::test_train_all_from_split_raises_on_year_outside_2014_2016[years3] PASSED [ 68%]
tests/test_step4_models.py::test_train_all_from_split_accepts_subset_of_training_years PASSED [ 70%]
tests/test_step4_models.py::test_train_model_unknown_name_raises PASSED  [ 72%]
tests/test_step4_models.py::test_one_class_y_train_raises[logreg] PASSED [ 75%]
tests/test_step4_models.py::test_one_class_y_train_raises[random_forest] FAILED [ 77%]
tests/test_step4_models.py::test_one_class_y_train_raises[sgd] PASSED    [ 79%]
tests/test_step4_models.py::test_empty_training_set_raises[logreg] PASSED [ 81%]
tests/test_step4_models.py::test_empty_training_set_raises[random_forest] PASSED [ 84%]
tests/test_step4_models.py::test_empty_training_set_raises[sgd] PASSED   [ 86%]
tests/test_step4_models.py::test_mismatched_x_and_y_lengths_raise[logreg] PASSED [ 88%]
tests/test_step4_models.py::test_mismatched_x_and_y_lengths_raise[random_forest] PASSED [ 90%]
tests/test_step4_models.py::test_mismatched_x_and_y_lengths_raise[sgd] PASSED [ 93%]
tests/test_step4_models.py::test_train_all_from_split_mismatched_years_length_raises FAILED [ 95%]
tests/test_step4_models.py::test_train_all_from_split_empty_training_set_raises PASSED [ 97%]
tests/test_step4_models.py::test_real_data_logreg_and_sgd_train_on_training_years PASSED [100%]

================================== FAILURES ===================================
________________ test_one_class_y_train_raises[random_forest] _________________

name = 'random_forest'

    @pytest.mark.parametrize("name", ["logreg", "random_forest", "sgd"])
    def test_one_class_y_train_raises(name):
        X, _ = make_data()
>       with pytest.raises(ValueError):
E       Failed: DID NOT RAISE ValueError

tests\test_step4_models.py:164: Failed
__________ test_train_all_from_split_mismatched_years_length_raises ___________

    def test_train_all_from_split_mismatched_years_length_raises():
        split = make_split(TRAIN_YEARS)
        split["years_train"] = split["years_train"][:-3]
>       with pytest.raises(ValueError):
E       Failed: DID NOT RAISE ValueError

tests\test_step4_models.py:184: Failed
============================== warnings summary ===============================
..\..\..\..\..\AppData\Roaming\Python\Python311\site-packages\dash\testing\plugin.py:92
  C:\Users\thema\AppData\Roaming\Python\Python311\site-packages\dash\testing\plugin.py:92: PytestRemovedIn10Warning: The hookimpl pytest_addhooks uses old-style configuration options (marks or attributes).
  Please use the pytest.hookimpl(tryfirst=True) decorator instead
   to configure the hooks.
   See https://docs.pytest.org/en/latest/deprecations.html#configuring-hook-specs-impls-using-markers
    @pytest.mark.tryfirst

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=================================== PASSES ====================================
=========================== short test summary info ===========================
PASSED tests/test_step4_models.py::test_model_names_has_logreg_random_forest_sgd
PASSED tests/test_step4_models.py::test_build_model_returns_expected_classes
PASSED tests/test_step4_models.py::test_build_model_random_state_is_42[logreg]
PASSED tests/test_step4_models.py::test_build_model_random_state_is_42[random_forest]
PASSED tests/test_step4_models.py::test_build_model_random_state_is_42[sgd]
PASSED tests/test_step4_models.py::test_logreg_is_balanced_and_has_larger_max_iter_than_default
PASSED tests/test_step4_models.py::test_random_forest_has_200_trees
PASSED tests/test_step4_models.py::test_sgd_has_no_balanced_class_weight_and_log_loss
PASSED tests/test_step4_models.py::test_build_model_returns_new_unfitted_objects
PASSED tests/test_step4_models.py::test_build_model_unknown_name_raises_value_error[svm]
PASSED tests/test_step4_models.py::test_build_model_unknown_name_raises_value_error[]
PASSED tests/test_step4_models.py::test_build_model_unknown_name_raises_value_error[LogReg]
PASSED tests/test_step4_models.py::test_build_model_unknown_name_raises_value_error[xgboost]
PASSED tests/test_step4_models.py::test_each_model_fits_and_predicts_well_on_separable_data[logreg]
PASSED tests/test_step4_models.py::test_each_model_fits_and_predicts_well_on_separable_data[random_forest]
PASSED tests/test_step4_models.py::test_each_model_fits_and_predicts_well_on_separable_data[sgd]
PASSED tests/test_step4_models.py::test_predictions_use_only_labels_0_and_1[logreg]
PASSED tests/test_step4_models.py::test_predictions_use_only_labels_0_and_1[random_forest]
PASSED tests/test_step4_models.py::test_predictions_use_only_labels_0_and_1[sgd]
PASSED tests/test_step4_models.py::test_train_all_returns_all_named_models_fitted
PASSED tests/test_step4_models.py::test_same_random_state_gives_identical_results_twice[logreg]
PASSED tests/test_step4_models.py::test_same_random_state_gives_identical_results_twice[random_forest]
PASSED tests/test_step4_models.py::test_same_random_state_gives_identical_results_twice[sgd]
PASSED tests/test_step4_models.py::test_sgd_partial_fit_after_fit_works
PASSED tests/test_step4_models.py::test_sgd_partial_fit_as_first_call_with_classes
PASSED tests/test_step4_models.py::test_train_all_from_split_accepts_2014_2016
PASSED tests/test_step4_models.py::test_train_all_from_split_raises_on_year_outside_2014_2016[years0]
PASSED tests/test_step4_models.py::test_train_all_from_split_raises_on_year_outside_2014_2016[years1]
PASSED tests/test_step4_models.py::test_train_all_from_split_raises_on_year_outside_2014_2016[years2]
PASSED tests/test_step4_models.py::test_train_all_from_split_raises_on_year_outside_2014_2016[years3]
PASSED tests/test_step4_models.py::test_train_all_from_split_accepts_subset_of_training_years
PASSED tests/test_step4_models.py::test_train_model_unknown_name_raises
PASSED tests/test_step4_models.py::test_one_class_y_train_raises[logreg]
PASSED tests/test_step4_models.py::test_one_class_y_train_raises[sgd]
PASSED tests/test_step4_models.py::test_empty_training_set_raises[logreg]
PASSED tests/test_step4_models.py::test_empty_training_set_raises[random_forest]
PASSED tests/test_step4_models.py::test_empty_training_set_raises[sgd]
PASSED tests/test_step4_models.py::test_mismatched_x_and_y_lengths_raise[logreg]
PASSED tests/test_step4_models.py::test_mismatched_x_and_y_lengths_raise[random_forest]
PASSED tests/test_step4_models.py::test_mismatched_x_and_y_lengths_raise[sgd]
PASSED tests/test_step4_models.py::test_train_all_from_split_empty_training_set_raises
PASSED tests/test_step4_models.py::test_real_data_logreg_and_sgd_train_on_training_years
FAILED tests/test_step4_models.py::test_one_class_y_train_raises[random_forest]
FAILED tests/test_step4_models.py::test_train_all_from_split_mismatched_years_length_raises
=================== 2 failed, 42 passed, 1 warning in 8.25s ===================
```

### Run 2: PASSED

- Time: 2026-11-03T04:01:35+02:00
- Commit: dbf9838
- Result: 44 passed, 1 warning in 6.95s
- Files: test_step4_models.py

```
============================= test session starts =============================
platform win32 -- Python 3.11.4, pytest-9.2.0, pluggy-1.7.0 -- C:\Program Files\Python311\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\thema\OneDrive\Desktop\Project2\project2-harness2\project2-harness2
configfile: pytest.ini
plugins: anyio-4.8.0, dash-2.18.1
collecting ... collected 44 items

tests/test_step4_models.py::test_model_names_has_logreg_random_forest_sgd PASSED [  2%]
tests/test_step4_models.py::test_build_model_returns_expected_classes PASSED [  4%]
tests/test_step4_models.py::test_build_model_random_state_is_42[logreg] PASSED [  6%]
tests/test_step4_models.py::test_build_model_random_state_is_42[random_forest] PASSED [  9%]
tests/test_step4_models.py::test_build_model_random_state_is_42[sgd] PASSED [ 11%]
tests/test_step4_models.py::test_logreg_is_balanced_and_has_larger_max_iter_than_default PASSED [ 13%]
tests/test_step4_models.py::test_random_forest_has_200_trees PASSED      [ 15%]
tests/test_step4_models.py::test_sgd_has_no_balanced_class_weight_and_log_loss PASSED [ 18%]
tests/test_step4_models.py::test_build_model_returns_new_unfitted_objects PASSED [ 20%]
tests/test_step4_models.py::test_build_model_unknown_name_raises_value_error[svm] PASSED [ 22%]
tests/test_step4_models.py::test_build_model_unknown_name_raises_value_error[] PASSED [ 25%]
tests/test_step4_models.py::test_build_model_unknown_name_raises_value_error[LogReg] PASSED [ 27%]
tests/test_step4_models.py::test_build_model_unknown_name_raises_value_error[xgboost] PASSED [ 29%]
tests/test_step4_models.py::test_each_model_fits_and_predicts_well_on_separable_data[logreg] PASSED [ 31%]
tests/test_step4_models.py::test_each_model_fits_and_predicts_well_on_separable_data[random_forest] PASSED [ 34%]
tests/test_step4_models.py::test_each_model_fits_and_predicts_well_on_separable_data[sgd] PASSED [ 36%]
tests/test_step4_models.py::test_predictions_use_only_labels_0_and_1[logreg] PASSED [ 38%]
tests/test_step4_models.py::test_predictions_use_only_labels_0_and_1[random_forest] PASSED [ 40%]
tests/test_step4_models.py::test_predictions_use_only_labels_0_and_1[sgd] PASSED [ 43%]
tests/test_step4_models.py::test_train_all_returns_all_named_models_fitted PASSED [ 45%]
tests/test_step4_models.py::test_same_random_state_gives_identical_results_twice[logreg] PASSED [ 47%]
tests/test_step4_models.py::test_same_random_state_gives_identical_results_twice[random_forest] PASSED [ 50%]
tests/test_step4_models.py::test_same_random_state_gives_identical_results_twice[sgd] PASSED [ 52%]
tests/test_step4_models.py::test_sgd_partial_fit_after_fit_works PASSED  [ 54%]
tests/test_step4_models.py::test_sgd_partial_fit_as_first_call_with_classes PASSED [ 56%]
tests/test_step4_models.py::test_train_all_from_split_accepts_2014_2016 PASSED [ 59%]
tests/test_step4_models.py::test_train_all_from_split_raises_on_year_outside_2014_2016[years0] PASSED [ 61%]
tests/test_step4_models.py::test_train_all_from_split_raises_on_year_outside_2014_2016[years1] PASSED [ 63%]
tests/test_step4_models.py::test_train_all_from_split_raises_on_year_outside_2014_2016[years2] PASSED [ 65%]
tests/test_step4_models.py::test_train_all_from_split_raises_on_year_outside_2014_2016[years3] PASSED [ 68%]
tests/test_step4_models.py::test_train_all_from_split_accepts_subset_of_training_years PASSED [ 70%]
tests/test_step4_models.py::test_train_model_unknown_name_raises PASSED  [ 72%]
tests/test_step4_models.py::test_one_class_y_train_raises[logreg] PASSED [ 75%]
tests/test_step4_models.py::test_one_class_y_train_raises[random_forest] PASSED [ 77%]
tests/test_step4_models.py::test_one_class_y_train_raises[sgd] PASSED    [ 79%]
tests/test_step4_models.py::test_empty_training_set_raises[logreg] PASSED [ 81%]
tests/test_step4_models.py::test_empty_training_set_raises[random_forest] PASSED [ 84%]
tests/test_step4_models.py::test_empty_training_set_raises[sgd] PASSED   [ 86%]
tests/test_step4_models.py::test_mismatched_x_and_y_lengths_raise[logreg] PASSED [ 88%]
tests/test_step4_models.py::test_mismatched_x_and_y_lengths_raise[random_forest] PASSED [ 90%]
tests/test_step4_models.py::test_mismatched_x_and_y_lengths_raise[sgd] PASSED [ 93%]
tests/test_step4_models.py::test_train_all_from_split_mismatched_years_length_raises PASSED [ 95%]
tests/test_step4_models.py::test_train_all_from_split_empty_training_set_raises PASSED [ 97%]
tests/test_step4_models.py::test_real_data_logreg_and_sgd_train_on_training_years PASSED [100%]

============================== warnings summary ===============================
..\..\..\..\..\AppData\Roaming\Python\Python311\site-packages\dash\testing\plugin.py:92
  C:\Users\thema\AppData\Roaming\Python\Python311\site-packages\dash\testing\plugin.py:92: PytestRemovedIn10Warning: The hookimpl pytest_addhooks uses old-style configuration options (marks or attributes).
  Please use the pytest.hookimpl(tryfirst=True) decorator instead
   to configure the hooks.
   See https://docs.pytest.org/en/latest/deprecations.html#configuring-hook-specs-impls-using-markers
    @pytest.mark.tryfirst

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=================================== PASSES ====================================
=========================== short test summary info ===========================
PASSED tests/test_step4_models.py::test_model_names_has_logreg_random_forest_sgd
PASSED tests/test_step4_models.py::test_build_model_returns_expected_classes
PASSED tests/test_step4_models.py::test_build_model_random_state_is_42[logreg]
PASSED tests/test_step4_models.py::test_build_model_random_state_is_42[random_forest]
PASSED tests/test_step4_models.py::test_build_model_random_state_is_42[sgd]
PASSED tests/test_step4_models.py::test_logreg_is_balanced_and_has_larger_max_iter_than_default
PASSED tests/test_step4_models.py::test_random_forest_has_200_trees
PASSED tests/test_step4_models.py::test_sgd_has_no_balanced_class_weight_and_log_loss
PASSED tests/test_step4_models.py::test_build_model_returns_new_unfitted_objects
PASSED tests/test_step4_models.py::test_build_model_unknown_name_raises_value_error[svm]
PASSED tests/test_step4_models.py::test_build_model_unknown_name_raises_value_error[]
PASSED tests/test_step4_models.py::test_build_model_unknown_name_raises_value_error[LogReg]
PASSED tests/test_step4_models.py::test_build_model_unknown_name_raises_value_error[xgboost]
PASSED tests/test_step4_models.py::test_each_model_fits_and_predicts_well_on_separable_data[logreg]
PASSED tests/test_step4_models.py::test_each_model_fits_and_predicts_well_on_separable_data[random_forest]
PASSED tests/test_step4_models.py::test_each_model_fits_and_predicts_well_on_separable_data[sgd]
PASSED tests/test_step4_models.py::test_predictions_use_only_labels_0_and_1[logreg]
PASSED tests/test_step4_models.py::test_predictions_use_only_labels_0_and_1[random_forest]
PASSED tests/test_step4_models.py::test_predictions_use_only_labels_0_and_1[sgd]
PASSED tests/test_step4_models.py::test_train_all_returns_all_named_models_fitted
PASSED tests/test_step4_models.py::test_same_random_state_gives_identical_results_twice[logreg]
PASSED tests/test_step4_models.py::test_same_random_state_gives_identical_results_twice[random_forest]
PASSED tests/test_step4_models.py::test_same_random_state_gives_identical_results_twice[sgd]
PASSED tests/test_step4_models.py::test_sgd_partial_fit_after_fit_works
PASSED tests/test_step4_models.py::test_sgd_partial_fit_as_first_call_with_classes
PASSED tests/test_step4_models.py::test_train_all_from_split_accepts_2014_2016
PASSED tests/test_step4_models.py::test_train_all_from_split_raises_on_year_outside_2014_2016[years0]
PASSED tests/test_step4_models.py::test_train_all_from_split_raises_on_year_outside_2014_2016[years1]
PASSED tests/test_step4_models.py::test_train_all_from_split_raises_on_year_outside_2014_2016[years2]
PASSED tests/test_step4_models.py::test_train_all_from_split_raises_on_year_outside_2014_2016[years3]
PASSED tests/test_step4_models.py::test_train_all_from_split_accepts_subset_of_training_years
PASSED tests/test_step4_models.py::test_train_model_unknown_name_raises
PASSED tests/test_step4_models.py::test_one_class_y_train_raises[logreg]
PASSED tests/test_step4_models.py::test_one_class_y_train_raises[random_forest]
PASSED tests/test_step4_models.py::test_one_class_y_train_raises[sgd]
PASSED tests/test_step4_models.py::test_empty_training_set_raises[logreg]
PASSED tests/test_step4_models.py::test_empty_training_set_raises[random_forest]
PASSED tests/test_step4_models.py::test_empty_training_set_raises[sgd]
PASSED tests/test_step4_models.py::test_mismatched_x_and_y_lengths_raise[logreg]
PASSED tests/test_step4_models.py::test_mismatched_x_and_y_lengths_raise[random_forest]
PASSED tests/test_step4_models.py::test_mismatched_x_and_y_lengths_raise[sgd]
PASSED tests/test_step4_models.py::test_train_all_from_split_mismatched_years_length_raises
PASSED tests/test_step4_models.py::test_train_all_from_split_empty_training_set_raises
PASSED tests/test_step4_models.py::test_real_data_logreg_and_sgd_train_on_training_years
======================== 44 passed, 1 warning in 6.95s ========================
```
