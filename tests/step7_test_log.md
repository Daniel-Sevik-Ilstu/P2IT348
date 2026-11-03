# Step 7 Test Log: Sustainable ML Approach

- Tester transcript: transcripts/33_2026-11-03_tester_step7.md

## Tests written (tester)

One row per test function (parametrized tests count once). Row counts follow AGENTS.md (2014-2018: 18,000 rows per year; 2019-2021: 3,000 per year), not ASSIGNMENT.md; the synthetic tests use small frames, so this only matters for the real-data test. Entry point tested: main.run_step7 (PLAN.md), plus sustainable.window_years, run_window_strategy, run_incremental, run_all_strategies. Strategy plan followed from PLAN.md: logreg gets static/expanding/sliding, sgd also gets incremental, random_forest gets static/expanding only.

| Test | What it checks (from the assignment or plan) |
| --- | --- |
| test_expanding_window_is_all_years_before_t | expanding window for t is exactly 2014..t-1 (2017, 2018, 2021) |
| test_sliding_window_is_three_years_before_t | sliding window is exactly t-3..t-1 for 2017-2021 |
| test_static_window_is_2014_2016_for_every_t | static window is 2014-2016 for every test year |
| test_window_never_contains_year_t_or_later | max(window) < t for every strategy and test year |
| test_window_years_rejects_non_test_year | t = 2013, 2014, 2016, 2022 (empty or leaking window) raises ValueError |
| test_window_years_rejects_unknown_strategy | unknown strategy name raises ValueError |
| test_fit_years_are_exactly_the_planned_window | recording stub: years each fit sees equal the planned window (static / expanding / sliding), in order |
| test_preprocessor_never_fit_on_year_t_or_later | the scaler/mask fit uses the same years as the model and every fit precedes a predict on a later year |
| test_window_strategy_predicts_each_test_year_once_on_that_year_only | one predict per test year, on that year's rows only, no model trained on year >= t |
| test_no_model_trained_on_year_at_or_after_year_it_predicts_any_strategy | all strategies and classifiers (incl. RF): replay of all fit/partial_fit/predict calls never shows training year >= predicted year |
| test_incremental_predicts_year_t_before_partial_fit_on_t | call order is fit(2014-16), then predict(t), partial_fit(t) for t = 2017..2021 |
| test_incremental_preprocessor_fit_once_on_training_years_only | incremental preprocessor fitted once, on 2014-2016 only (frozen) |
| test_incremental_uses_one_model_object_throughout | incremental updates one model object (partial_fit), not new models |
| test_flipping_labels_of_year_t_does_not_change_predictions_up_to_t | real models: flipping 2019 labels leaves predictions for years <= 2019 unchanged for every strategy, static unchanged always, expanding/sliding/incremental change in 2020/2021 |
| test_expanding_and_sliding_models_differ_per_year_static_does_not | real logreg: expanding/sliding coefficients change each year, expanding rows grow by one year, sliding stays 3 years, static model identical every year |
| test_incremental_calls_partial_fit_each_year_and_model_changes | real SGD: partial_fit called once per test year with that year's rows; coefficients change |
| test_static_baseline_models_unchanged_after_step7 | Step 4 logreg and sgd coef_/intercept_ identical before and after run_step7 |
| test_static_rows_equal_step4_models_predictions | static rows equal sklearn metrics of the passed Step 4 models on the same rows |
| test_static_baseline_stub_models_are_only_asked_to_predict | passed static models raise on fit/partial_fit; Step 7 still produces 15 static rows |
| test_step7_writes_expected_files | results/step7_strategies.csv has columns strategy, classifier, year, n, accuracy, precision, recall, f1 |
| test_one_row_per_strategy_classifier_year | no duplicate (strategy, classifier, year); strategy set per classifier follows PLAN; 45 rows |
| test_metric_values_between_0_and_1 | accuracy, precision, recall, f1 in [0,1], no NaN |
| test_all_strategies_scored_on_same_test_rows | every strategy/classifier has the same n and the same positives per year |
| test_no_training_year_reported_as_test_year | only 2017-2021 appear in the year column |
| test_pooled_matches_sum_of_per_year_counts | pooled table from summed confusion counts, n and accuracy consistent, 9 rows |
| test_compare_to_static_is_a_difference_against_the_static_row | f1_diff = strategy F1 minus static F1 of the same classifier and year; no static rows |
| test_2017_agrees_for_static_expanding_sliding | for t = 2017 all three windows are 2014-2016, so F1 agrees (PLAN) |
| test_retraining_does_not_do_worse_than_static_in_final_year | sanity on injected drift: sliding/expanding F1 >= static in 2021; incremental within 0.02 of static SGD |
| test_window_composition_rows_match_windows | window composition rows per year match the sliding 2019 and expanding 2021 windows |
| test_single_class_test_years_do_not_crash | all-malware 2019 and all-benign 2021: 35 rows, no NaN, metrics in [0,1], 2021 recall and F1 = 0 |
| test_missing_year_is_not_invented | data without 2019: raises or has no 2019 row |
| test_missing_training_years_raise | data with no 2014-2016: empty windows raise |
| test_real_data_every_window_year_has_files | real data (skipped if absent): files cover exactly 2014-2021, all window years exist |

## Failures and decisions (student)

One row per failing test. Decision is "Accepted" (the test is right; the builder fixes the code) or "Rejected" (the test is wrong; the tester fixes the test). Add the commit with the fix.

| Test | Cause | Decision | Fixed in commit |
| --- | --- | --- | --- |

## Runs (added by `python harness.py test N`; do not edit)

### Run 1: PASSED

- Time: 2026-11-03T06:31:45+02:00
- Commit: 868ab62
- Result: 66 passed, 1 warning in 27.28s
- Files: test_step7_sustainable.py

```
... (279 earlier lines omitted)
    sliding           sgd  2018 300    0.7533     0.7714  0.7200 0.7448
    sliding           sgd  2019 300    0.7300     0.7292  0.7143 0.7216
    sliding           sgd  2020 300    0.7800     0.7356  0.8649 0.7950
    sliding           sgd  2021 300    0.8100     0.7527  0.9272 0.8309
incremental           sgd  2017 300    0.6967     0.6940  0.6503 0.6715
incremental           sgd  2018 300    0.7767     0.7578  0.8133 0.7846
incremental           sgd  2019 300    0.7467     0.7710  0.6871 0.7266
incremental           sgd  2020 300    0.7300     0.7343  0.7095 0.7216
incremental           sgd  2021 300    0.8300     0.8289  0.8344 0.8317
     static random_forest  2017 300    0.6833     0.6846  0.6224 0.6520
     static random_forest  2018 300    0.7433     0.7967  0.6533 0.7179
     static random_forest  2019 300    0.6300     0.6765  0.4694 0.5542
     static random_forest  2020 300    0.6733     0.7119  0.5676 0.6316
     static random_forest  2021 300    0.6233     0.6827  0.4702 0.5569
  expanding random_forest  2017 300    0.6833     0.6846  0.6224 0.6520
  expanding random_forest  2018 300    0.7433     0.7874  0.6667 0.7220
  expanding random_forest  2019 300    0.6900     0.7177  0.6054 0.6568
  expanding random_forest  2020 300    0.7067     0.6852  0.7500 0.7161
  expanding random_forest  2021 300    0.7233     0.7329  0.7086 0.7205
Step 7 summary:
   strategy    classifier  mean_f1  worst_f1  worst_year  mean_f1_2019_21  mean_accuracy_2019_21  mean_accuracy  mean_f1_gain_vs_static  mean_acc_2019_21_gain_vs_static
     static        logreg   0.5946    0.4500        2021           0.5097                 0.5900         0.6493                  0.0000                           0.0000
  expanding        logreg   0.7013    0.6595        2019           0.6788                 0.6933         0.7147                  0.1067                           0.1033
    sliding        logreg   0.7524    0.7092        2019           0.7613                 0.7567         0.7533                  0.1578                           0.1667
     static           sgd   0.5182    0.3091        2021           0.4287                 0.5578         0.6100                  0.0000                           0.0000
  expanding           sgd   0.6535    0.6043        2019           0.6333                 0.6700         0.6867                  0.1353                           0.1122
    sliding           sgd   0.7528    0.6715        2017           0.7825                 0.7733         0.7540                  0.2345                           0.2156
incremental           sgd   0.7472    0.6715        2017           0.7600                 0.7689         0.7560                  0.2290                           0.2111
     static random_forest   0.6225    0.5542        2019           0.5809                 0.6422         0.6707                  0.0000                           0.0000
  expanding random_forest   0.6935    0.6520        2017           0.6978                 0.7067         0.7093                  0.0710                           0.0644
Step 7 pooled:
   strategy    classifier    n  accuracy  precision  recall     f1
     static        logreg 1500    0.6493     0.6833  0.5372 0.6015
  expanding        logreg 1500    0.7147     0.7237  0.6806 0.7015
    sliding        logreg 1500    0.7533     0.7412  0.7673 0.7540
     static           sgd 1500    0.6100     0.6534  0.4438 0.5286
  expanding           sgd 1500    0.6867     0.7180  0.5995 0.6534
    sliding           sgd 1500    0.7540     0.7378  0.7767 0.7568
incremental           sgd 1500    0.7560     0.7587  0.7402 0.7493
     static random_forest 1500    0.6707     0.7123  0.5562 0.6246
  expanding random_forest 1500    0.7093     0.7199  0.6712 0.6947
Step 7 cost:
   strategy    classifier  n_fits  total_seconds  mean_seconds_per_update  max_seconds  mean_train_rows
     static        logreg       1         0.0000                      NaN          NaN            900.0
  expanding        logreg       5         0.0330                   0.0066       0.0073           1500.0
    sliding        logreg       5         0.0269                   0.0054       0.0056            900.0
     static           sgd       1         0.0000                      NaN          NaN            900.0
  expanding           sgd       5         0.0659                   0.0132       0.0199           1500.0
    sliding           sgd       5         0.0399                   0.0080       0.0091            900.0
incremental           sgd       5         0.0149                   0.0030       0.0105            420.0
     static random_forest       1         0.0000                      NaN          NaN            900.0
  expanding random_forest       5         2.1404                   0.4281       0.4470           1500.0
=========================== short test summary info ===========================
PASSED tests/test_step7_sustainable.py::test_expanding_window_is_all_years_before_t[2017-expected0]
PASSED tests/test_step7_sustainable.py::test_expanding_window_is_all_years_before_t[2018-expected1]
PASSED tests/test_step7_sustainable.py::test_expanding_window_is_all_years_before_t[2021-expected2]
PASSED tests/test_step7_sustainable.py::test_sliding_window_is_three_years_before_t[2017-expected0]
PASSED tests/test_step7_sustainable.py::test_sliding_window_is_three_years_before_t[2018-expected1]
PASSED tests/test_step7_sustainable.py::test_sliding_window_is_three_years_before_t[2019-expected2]
PASSED tests/test_step7_sustainable.py::test_sliding_window_is_three_years_before_t[2020-expected3]
PASSED tests/test_step7_sustainable.py::test_sliding_window_is_three_years_before_t[2021-expected4]
PASSED tests/test_step7_sustainable.py::test_static_window_is_2014_2016_for_every_t[2017]
PASSED tests/test_step7_sustainable.py::test_static_window_is_2014_2016_for_every_t[2018]
PASSED tests/test_step7_sustainable.py::test_static_window_is_2014_2016_for_every_t[2019]
PASSED tests/test_step7_sustainable.py::test_static_window_is_2014_2016_for_every_t[2020]
PASSED tests/test_step7_sustainable.py::test_static_window_is_2014_2016_for_every_t[2021]
PASSED tests/test_step7_sustainable.py::test_window_never_contains_year_t_or_later[2017-static]
PASSED tests/test_step7_sustainable.py::test_window_never_contains_year_t_or_later[2017-expanding]
PASSED tests/test_step7_sustainable.py::test_window_never_contains_year_t_or_later[2017-sliding]
PASSED tests/test_step7_sustainable.py::test_window_never_contains_year_t_or_later[2018-static]
PASSED tests/test_step7_sustainable.py::test_window_never_contains_year_t_or_later[2018-expanding]
PASSED tests/test_step7_sustainable.py::test_window_never_contains_year_t_or_later[2018-sliding]
PASSED tests/test_step7_sustainable.py::test_window_never_contains_year_t_or_later[2019-static]
PASSED tests/test_step7_sustainable.py::test_window_never_contains_year_t_or_later[2019-expanding]
PASSED tests/test_step7_sustainable.py::test_window_never_contains_year_t_or_later[2019-sliding]
PASSED tests/test_step7_sustainable.py::test_window_never_contains_year_t_or_later[2020-static]
PASSED tests/test_step7_sustainable.py::test_window_never_contains_year_t_or_later[2020-expanding]
PASSED tests/test_step7_sustainable.py::test_window_never_contains_year_t_or_later[2020-sliding]
PASSED tests/test_step7_sustainable.py::test_window_never_contains_year_t_or_later[2021-static]
PASSED tests/test_step7_sustainable.py::test_window_never_contains_year_t_or_later[2021-expanding]
PASSED tests/test_step7_sustainable.py::test_window_never_contains_year_t_or_later[2021-sliding]
PASSED tests/test_step7_sustainable.py::test_window_years_rejects_non_test_year[2013]
PASSED tests/test_step7_sustainable.py::test_window_years_rejects_non_test_year[2014]
PASSED tests/test_step7_sustainable.py::test_window_years_rejects_non_test_year[2016]
PASSED tests/test_step7_sustainable.py::test_window_years_rejects_non_test_year[2022]
PASSED tests/test_step7_sustainable.py::test_window_years_rejects_unknown_strategy
PASSED tests/test_step7_sustainable.py::test_fit_years_are_exactly_the_planned_window[static-expected0]
PASSED tests/test_step7_sustainable.py::test_fit_years_are_exactly_the_planned_window[expanding-expected1]
PASSED tests/test_step7_sustainable.py::test_fit_years_are_exactly_the_planned_window[sliding-expected2]
PASSED tests/test_step7_sustainable.py::test_preprocessor_never_fit_on_year_t_or_later[static]
PASSED tests/test_step7_sustainable.py::test_preprocessor_never_fit_on_year_t_or_later[expanding]
PASSED tests/test_step7_sustainable.py::test_preprocessor_never_fit_on_year_t_or_later[sliding]
PASSED tests/test_step7_sustainable.py::test_window_strategy_predicts_each_test_year_once_on_that_year_only[static]
PASSED tests/test_step7_sustainable.py::test_window_strategy_predicts_each_test_year_once_on_that_year_only[expanding]
PASSED tests/test_step7_sustainable.py::test_window_strategy_predicts_each_test_year_once_on_that_year_only[sliding]
PASSED tests/test_step7_sustainable.py::test_no_model_trained_on_year_at_or_after_year_it_predicts_any_strategy
PASSED tests/test_step7_sustainable.py::test_incremental_predicts_year_t_before_partial_fit_on_t
PASSED tests/test_step7_sustainable.py::test_incremental_preprocessor_fit_once_on_training_years_only
PASSED tests/test_step7_sustainable.py::test_incremental_uses_one_model_object_throughout
PASSED tests/test_step7_sustainable.py::test_flipping_labels_of_year_t_does_not_change_predictions_up_to_t
PASSED tests/test_step7_sustainable.py::test_expanding_and_sliding_models_differ_per_year_static_does_not
PASSED tests/test_step7_sustainable.py::test_incremental_calls_partial_fit_each_year_and_model_changes
PASSED tests/test_step7_sustainable.py::test_static_baseline_models_unchanged_after_step7
PASSED tests/test_step7_sustainable.py::test_static_rows_equal_step4_models_predictions
PASSED tests/test_step7_sustainable.py::test_static_baseline_stub_models_are_only_asked_to_predict
PASSED tests/test_step7_sustainable.py::test_step7_writes_expected_files
PASSED tests/test_step7_sustainable.py::test_one_row_per_strategy_classifier_year
PASSED tests/test_step7_sustainable.py::test_metric_values_between_0_and_1
PASSED tests/test_step7_sustainable.py::test_all_strategies_scored_on_same_test_rows
PASSED tests/test_step7_sustainable.py::test_no_training_year_reported_as_test_year
PASSED tests/test_step7_sustainable.py::test_pooled_matches_sum_of_per_year_counts
PASSED tests/test_step7_sustainable.py::test_compare_to_static_is_a_difference_against_the_static_row
PASSED tests/test_step7_sustainable.py::test_2017_agrees_for_static_expanding_sliding
PASSED tests/test_step7_sustainable.py::test_retraining_does_not_do_worse_than_static_in_final_year
PASSED tests/test_step7_sustainable.py::test_window_composition_rows_match_windows
PASSED tests/test_step7_sustainable.py::test_single_class_test_years_do_not_crash
PASSED tests/test_step7_sustainable.py::test_missing_year_is_not_invented
PASSED tests/test_step7_sustainable.py::test_missing_training_years_raise
PASSED tests/test_step7_sustainable.py::test_real_data_every_window_year_has_files
======================= 66 passed, 1 warning in 27.28s ========================
```

### Run 2: PASSED

- Time: 2026-11-03T06:41:16+02:00
- Commit: 6debdaf
- Result: 72 passed, 1 warning in 44.17s
- Files: test_step7_sustainable.py

```
... (291 earlier lines omitted)
incremental           sgd  2019 300    0.7467     0.7710  0.6871 0.7266
incremental           sgd  2020 300    0.7300     0.7343  0.7095 0.7216
incremental           sgd  2021 300    0.8300     0.8289  0.8344 0.8317
     static random_forest  2017 300    0.6833     0.6846  0.6224 0.6520
     static random_forest  2018 300    0.7433     0.7967  0.6533 0.7179
     static random_forest  2019 300    0.6300     0.6765  0.4694 0.5542
     static random_forest  2020 300    0.6733     0.7119  0.5676 0.6316
     static random_forest  2021 300    0.6233     0.6827  0.4702 0.5569
  expanding random_forest  2017 300    0.6833     0.6846  0.6224 0.6520
  expanding random_forest  2018 300    0.7433     0.7874  0.6667 0.7220
  expanding random_forest  2019 300    0.6900     0.7177  0.6054 0.6568
  expanding random_forest  2020 300    0.7067     0.6852  0.7500 0.7161
  expanding random_forest  2021 300    0.7233     0.7329  0.7086 0.7205
Step 7 summary:
   strategy    classifier  mean_f1  worst_f1  worst_year  mean_f1_2019_21  mean_accuracy_2019_21  mean_accuracy  pred_malware_rate_2019  mean_f1_gain_vs_static  mean_acc_2019_21_gain_vs_static
     static        logreg   0.5946    0.4500        2021           0.5097                 0.5900         0.6493                  0.3733                  0.0000                           0.0000
  expanding        logreg   0.7013    0.6595        2019           0.6788                 0.6933         0.7147                  0.4400                  0.1067                           0.1033
    sliding        logreg   0.7524    0.7092        2019           0.7613                 0.7567         0.7533                  0.4500                  0.1578                           0.1667
     static           sgd   0.5182    0.3091        2021           0.4287                 0.5578         0.6100                  0.3333                  0.0000                           0.0000
  expanding           sgd   0.6535    0.6043        2019           0.6333                 0.6700         0.6867                  0.4367                  0.1353                           0.1122
    sliding           sgd   0.7528    0.6715        2017           0.7825                 0.7733         0.7540                  0.4800                  0.2345                           0.2156
incremental           sgd   0.7472    0.6715        2017           0.7600                 0.7689         0.7560                  0.4367                  0.2290                           0.2111
     static random_forest   0.6225    0.5542        2019           0.5809                 0.6422         0.6707                  0.3400                  0.0000                           0.0000
  expanding random_forest   0.6935    0.6520        2017           0.6978                 0.7067         0.7093                  0.4133                  0.0710                           0.0644
Step 7 pooled:
   strategy    classifier    n  accuracy  precision  recall     f1  pred_malware_rate
     static        logreg 1500    0.6493     0.6833  0.5372 0.6015             0.3873
  expanding        logreg 1500    0.7147     0.7237  0.6806 0.7015             0.4633
    sliding        logreg 1500    0.7533     0.7412  0.7673 0.7540             0.5100
     static           sgd 1500    0.6100     0.6534  0.4438 0.5286             0.3347
  expanding           sgd 1500    0.6867     0.7180  0.5995 0.6534             0.4113
    sliding           sgd 1500    0.7540     0.7378  0.7767 0.7568             0.5187
incremental           sgd 1500    0.7560     0.7587  0.7402 0.7493             0.4807
     static random_forest 1500    0.6707     0.7123  0.5562 0.6246             0.3847
  expanding random_forest 1500    0.7093     0.7199  0.6712 0.6947             0.4593
Step 7 cost:
   strategy    classifier  n_fits  total_seconds  mean_seconds_per_update  max_seconds  mean_train_rows  update_rows
     static        logreg       1            NaN                      NaN          NaN            900.0          NaN
  expanding        logreg       5         0.0632                   0.0126       0.0164           1500.0          NaN
    sliding        logreg       5         0.0511                   0.0102       0.0147            900.0          NaN
     static           sgd       1            NaN                      NaN          NaN            900.0          NaN
  expanding           sgd       5         0.0975                   0.0195       0.0320           1500.0          NaN
    sliding           sgd       5         0.0756                   0.0151       0.0181            900.0          NaN
incremental           sgd       5         0.0258                   0.0052       0.0203            900.0        300.0
     static random_forest       1            NaN                      NaN          NaN            900.0          NaN
  expanding random_forest       5         2.5054                   0.5011       0.8602           1500.0          NaN
=========================== short test summary info ===========================
PASSED tests/test_step7_sustainable.py::test_expanding_window_is_all_years_before_t[2017-expected0]
PASSED tests/test_step7_sustainable.py::test_expanding_window_is_all_years_before_t[2018-expected1]
PASSED tests/test_step7_sustainable.py::test_expanding_window_is_all_years_before_t[2021-expected2]
PASSED tests/test_step7_sustainable.py::test_sliding_window_is_three_years_before_t[2017-expected0]
PASSED tests/test_step7_sustainable.py::test_sliding_window_is_three_years_before_t[2018-expected1]
PASSED tests/test_step7_sustainable.py::test_sliding_window_is_three_years_before_t[2019-expected2]
PASSED tests/test_step7_sustainable.py::test_sliding_window_is_three_years_before_t[2020-expected3]
PASSED tests/test_step7_sustainable.py::test_sliding_window_is_three_years_before_t[2021-expected4]
PASSED tests/test_step7_sustainable.py::test_static_window_is_2014_2016_for_every_t[2017]
PASSED tests/test_step7_sustainable.py::test_static_window_is_2014_2016_for_every_t[2018]
PASSED tests/test_step7_sustainable.py::test_static_window_is_2014_2016_for_every_t[2019]
PASSED tests/test_step7_sustainable.py::test_static_window_is_2014_2016_for_every_t[2020]
PASSED tests/test_step7_sustainable.py::test_static_window_is_2014_2016_for_every_t[2021]
PASSED tests/test_step7_sustainable.py::test_window_never_contains_year_t_or_later[2017-static]
PASSED tests/test_step7_sustainable.py::test_window_never_contains_year_t_or_later[2017-expanding]
PASSED tests/test_step7_sustainable.py::test_window_never_contains_year_t_or_later[2017-sliding]
PASSED tests/test_step7_sustainable.py::test_window_never_contains_year_t_or_later[2018-static]
PASSED tests/test_step7_sustainable.py::test_window_never_contains_year_t_or_later[2018-expanding]
PASSED tests/test_step7_sustainable.py::test_window_never_contains_year_t_or_later[2018-sliding]
PASSED tests/test_step7_sustainable.py::test_window_never_contains_year_t_or_later[2019-static]
PASSED tests/test_step7_sustainable.py::test_window_never_contains_year_t_or_later[2019-expanding]
PASSED tests/test_step7_sustainable.py::test_window_never_contains_year_t_or_later[2019-sliding]
PASSED tests/test_step7_sustainable.py::test_window_never_contains_year_t_or_later[2020-static]
PASSED tests/test_step7_sustainable.py::test_window_never_contains_year_t_or_later[2020-expanding]
PASSED tests/test_step7_sustainable.py::test_window_never_contains_year_t_or_later[2020-sliding]
PASSED tests/test_step7_sustainable.py::test_window_never_contains_year_t_or_later[2021-static]
PASSED tests/test_step7_sustainable.py::test_window_never_contains_year_t_or_later[2021-expanding]
PASSED tests/test_step7_sustainable.py::test_window_never_contains_year_t_or_later[2021-sliding]
PASSED tests/test_step7_sustainable.py::test_window_years_rejects_non_test_year[2013]
PASSED tests/test_step7_sustainable.py::test_window_years_rejects_non_test_year[2014]
PASSED tests/test_step7_sustainable.py::test_window_years_rejects_non_test_year[2016]
PASSED tests/test_step7_sustainable.py::test_window_years_rejects_non_test_year[2022]
PASSED tests/test_step7_sustainable.py::test_window_years_rejects_unknown_strategy
PASSED tests/test_step7_sustainable.py::test_fit_years_are_exactly_the_planned_window[static-expected0]
PASSED tests/test_step7_sustainable.py::test_fit_years_are_exactly_the_planned_window[expanding-expected1]
PASSED tests/test_step7_sustainable.py::test_fit_years_are_exactly_the_planned_window[sliding-expected2]
PASSED tests/test_step7_sustainable.py::test_preprocessor_never_fit_on_year_t_or_later[static]
PASSED tests/test_step7_sustainable.py::test_preprocessor_never_fit_on_year_t_or_later[expanding]
PASSED tests/test_step7_sustainable.py::test_preprocessor_never_fit_on_year_t_or_later[sliding]
PASSED tests/test_step7_sustainable.py::test_window_strategy_predicts_each_test_year_once_on_that_year_only[static]
PASSED tests/test_step7_sustainable.py::test_window_strategy_predicts_each_test_year_once_on_that_year_only[expanding]
PASSED tests/test_step7_sustainable.py::test_window_strategy_predicts_each_test_year_once_on_that_year_only[sliding]
PASSED tests/test_step7_sustainable.py::test_no_model_trained_on_year_at_or_after_year_it_predicts_any_strategy
PASSED tests/test_step7_sustainable.py::test_incremental_predicts_year_t_before_partial_fit_on_t
PASSED tests/test_step7_sustainable.py::test_incremental_preprocessor_fit_once_on_training_years_only
PASSED tests/test_step7_sustainable.py::test_incremental_uses_one_model_object_throughout
PASSED tests/test_step7_sustainable.py::test_flipping_labels_of_year_t_does_not_change_predictions_up_to_t
PASSED tests/test_step7_sustainable.py::test_expanding_and_sliding_models_differ_per_year_static_does_not
PASSED tests/test_step7_sustainable.py::test_incremental_calls_partial_fit_each_year_and_model_changes
PASSED tests/test_step7_sustainable.py::test_static_baseline_models_unchanged_after_step7
PASSED tests/test_step7_sustainable.py::test_static_rows_equal_step4_models_predictions
PASSED tests/test_step7_sustainable.py::test_static_baseline_stub_models_are_only_asked_to_predict
PASSED tests/test_step7_sustainable.py::test_step7_writes_expected_files
PASSED tests/test_step7_sustainable.py::test_one_row_per_strategy_classifier_year
PASSED tests/test_step7_sustainable.py::test_metric_values_between_0_and_1
PASSED tests/test_step7_sustainable.py::test_all_strategies_scored_on_same_test_rows
PASSED tests/test_step7_sustainable.py::test_no_training_year_reported_as_test_year
PASSED tests/test_step7_sustainable.py::test_pooled_matches_sum_of_per_year_counts
PASSED tests/test_step7_sustainable.py::test_compare_to_static_is_a_difference_against_the_static_row
PASSED tests/test_step7_sustainable.py::test_2017_agrees_for_static_expanding_sliding
PASSED tests/test_step7_sustainable.py::test_retraining_does_not_do_worse_than_static_in_final_year
PASSED tests/test_step7_sustainable.py::test_window_composition_rows_match_windows
PASSED tests/test_step7_sustainable.py::test_single_class_test_years_do_not_crash
PASSED tests/test_step7_sustainable.py::test_missing_year_is_not_invented
PASSED tests/test_step7_sustainable.py::test_missing_training_years_raise
PASSED tests/test_step7_sustainable.py::test_real_data_every_window_year_has_files
PASSED tests/test_step7_sustainable.py::test_static_from_models_rejects_wrong_training_years
PASSED tests/test_step7_sustainable.py::test_static_from_models_rejects_mismatched_test_labels
PASSED tests/test_step7_sustainable.py::test_missing_year_raises_clear_value_error
PASSED tests/test_step7_sustainable.py::test_cost_table_reports_nan_not_zero_when_static_seconds_missing
PASSED tests/test_step7_sustainable.py::test_cost_table_incremental_update_rows_separate
PASSED tests/test_step7_sustainable.py::test_pred_malware_rate_and_year_diagnostic
======================= 72 passed, 1 warning in 44.17s ========================
```
