# Step 2 Test Log: Handle Data Drift

- Tester transcript: transcripts/11_2026-11-03_tester_step2.md
- Source followed for row counts: AGENTS.md (2019/2021 = 3,000 rows per year, 1,500 per file), not ASSIGNMENT.md's 1,500 per file.
- Concept-drift matrix is exempt from the train-years-only rule (PLAN.md section 0), so no year-leakage test is applied to it. The diagonal hold-out test checks only that a year's own accuracy is not training accuracy.

## Tests written (tester)

One row per test function. All in tests/test_step2_drift.py.

| Test | What it checks (from the assignment or plan) |
| --- | --- |
| test_ks_statistic_and_pvalue_within_unit_interval | KS statistic and p-value are in [0, 1] |
| test_ks_identical_samples_give_zero_and_not_significant | Identical samples: KS 0, p 1, nothing significant |
| test_ks_same_distribution_different_draws_is_small_and_mostly_insignificant | Two draws from one distribution: small KS, no Bonferroni hits |
| test_ks_detects_clearly_shifted_feature | A shifted feature has high KS and is flagged; an unshifted one is not |
| test_ks_is_symmetric | KS(a, b) equals KS(b, a) |
| test_ks_all_zero_feature_is_skipped_with_nan | All-zero feature is marked skipped with NaN stat and p |
| test_ks_constant_in_both_with_same_nonzero_value_is_skipped | Constant, same value in both samples: skipped |
| test_ks_constant_at_different_values_is_tested_and_maximal | Constant at different values in the two samples: tested, KS = 1 |
| test_ks_constant_in_one_sample_only_is_tested | Constant in only one sample: tested, KS 0.5 in hand case |
| test_ks_table_has_required_columns_and_one_row_per_feature | Output columns feature, ks_stat, p_value, skipped; one row per feature in order |
| test_bonferroni_uses_alpha_over_number_of_tested_features | Threshold is alpha / m, m excludes NaN (skipped) features; hand-computed |
| test_bonferroni_custom_alpha_and_all_nan | Custom alpha works; all-NaN input gives no significant features |
| test_subsample_equal_sizes_balanced_and_smallest_year_default | n=None uses smallest year; equal size per year; equal malware and benign |
| test_subsample_explicit_n_and_year_label_consistency | Explicit n respected; rows keep their year |
| test_subsample_reproducible_with_seed_and_varies_across_seeds | Same seed (42) reproduces; another seed differs |
| test_subsample_rows_come_from_the_source_year | Sampled rows are real rows of that year (no mixing years) |
| test_subsample_raises_when_a_class_is_too_small | Too few rows in a class raises ValueError |
| test_year_pair_modes_have_expected_row_counts | vs_2014 = 7 rows, consecutive = 7, all = 28; required columns; values in [0, 1] |
| test_year_pairs_unknown_mode_raises | Unknown mode raises ValueError |
| test_year_pairs_no_drift_vs_shifted_year | Shifted year has larger mean KS and significant features; unshifted pair has none |
| test_skipped_features_counted_in_pair_summary | n_skipped and n_tested in pair summary count dead features |
| test_most_different_years_sorted_descending_and_finds_shifted_year | Ranking is descending; shifted year ranks first |
| test_top_drifting_features_returns_k_sorted_and_finds_shifted_feature | Top-k returns k rows sorted descending; shifted feature first |
| test_top_drifting_features_k_larger_than_features_returns_all | k larger than feature count returns all features |
| test_concept_drift_matrix_square_indexed_by_years_and_in_unit_interval | Matrix is 8x8, indexed by years, no NaN, values in [0, 1] |
| test_concept_drift_matrix_learns_signal_on_stable_data | Stable concept gives high accuracy everywhere |
| test_concept_drift_matrix_shows_concept_drift | Flipped label rule in 2021: train-2014 accuracy on 2021 is low |
| test_concept_drift_diagonal_is_held_out_not_training_accuracy | Diagonal is held-out accuracy (noise labels give about 0.5) |
| test_concept_drift_matrix_is_deterministic_and_does_not_mutate_input | Same seed gives the same matrix; input frames unchanged |
| test_run_drift_analysis_writes_expected_outputs | Result tables have 7 rows (KS) / 8x8 (accuracy); step2_*.csv written |
| test_real_data_ks_between_two_years | Real 2019 vs 2021 (skipped without input_data/): 3,000 rows each, 1,848 features, valid KS, dead columns skipped |

## Failures and decisions (student)

One row per failing test. Decision is "Accepted" (the test is right; the builder fixes the code) or "Rejected" (the test is wrong; the tester fixes the test). Add the commit with the fix.

| Test | Cause | Decision | Fixed in commit |
| --- | --- | --- | --- |

## Runs (added by `python harness.py test N`; do not edit)

### Run 1: PASSED

- Time: 2026-11-03T01:02:57+02:00
- Commit: 0257211
- Result: 31 passed, 1 warning in 10.66s
- Files: test_step2_drift.py

```
============================= test session starts =============================
platform win32 -- Python 3.11.4, pytest-9.2.0, pluggy-1.7.0 -- C:\Program Files\Python311\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\thema\OneDrive\Desktop\Project2\project2-harness2\project2-harness2
configfile: pytest.ini
plugins: anyio-4.8.0, dash-2.18.1
collecting ... collected 31 items

tests/test_step2_drift.py::test_ks_statistic_and_pvalue_within_unit_interval PASSED [  3%]
tests/test_step2_drift.py::test_ks_identical_samples_give_zero_and_not_significant PASSED [  6%]
tests/test_step2_drift.py::test_ks_same_distribution_different_draws_is_small_and_mostly_insignificant PASSED [  9%]
tests/test_step2_drift.py::test_ks_detects_clearly_shifted_feature PASSED [ 12%]
tests/test_step2_drift.py::test_ks_is_symmetric PASSED                   [ 16%]
tests/test_step2_drift.py::test_ks_all_zero_feature_is_skipped_with_nan PASSED [ 19%]
tests/test_step2_drift.py::test_ks_constant_in_both_with_same_nonzero_value_is_skipped PASSED [ 22%]
tests/test_step2_drift.py::test_ks_constant_at_different_values_is_tested_and_maximal PASSED [ 25%]
tests/test_step2_drift.py::test_ks_constant_in_one_sample_only_is_tested PASSED [ 29%]
tests/test_step2_drift.py::test_ks_table_has_required_columns_and_one_row_per_feature PASSED [ 32%]
tests/test_step2_drift.py::test_bonferroni_uses_alpha_over_number_of_tested_features PASSED [ 35%]
tests/test_step2_drift.py::test_bonferroni_custom_alpha_and_all_nan PASSED [ 38%]
tests/test_step2_drift.py::test_subsample_equal_sizes_balanced_and_smallest_year_default PASSED [ 41%]
tests/test_step2_drift.py::test_subsample_explicit_n_and_year_label_consistency PASSED [ 45%]
tests/test_step2_drift.py::test_subsample_reproducible_with_seed_and_varies_across_seeds PASSED [ 48%]
tests/test_step2_drift.py::test_subsample_rows_come_from_the_source_year PASSED [ 51%]
tests/test_step2_drift.py::test_subsample_raises_when_a_class_is_too_small PASSED [ 54%]
tests/test_step2_drift.py::test_year_pair_modes_have_expected_row_counts PASSED [ 58%]
tests/test_step2_drift.py::test_year_pairs_unknown_mode_raises PASSED    [ 61%]
tests/test_step2_drift.py::test_year_pairs_no_drift_vs_shifted_year PASSED [ 64%]
tests/test_step2_drift.py::test_skipped_features_counted_in_pair_summary PASSED [ 67%]
tests/test_step2_drift.py::test_most_different_years_sorted_descending_and_finds_shifted_year PASSED [ 70%]
tests/test_step2_drift.py::test_top_drifting_features_returns_k_sorted_and_finds_shifted_feature PASSED [ 74%]
tests/test_step2_drift.py::test_top_drifting_features_k_larger_than_features_returns_all PASSED [ 77%]
tests/test_step2_drift.py::test_concept_drift_matrix_square_indexed_by_years_and_in_unit_interval PASSED [ 80%]
tests/test_step2_drift.py::test_concept_drift_matrix_learns_signal_on_stable_data PASSED [ 83%]
tests/test_step2_drift.py::test_concept_drift_matrix_shows_concept_drift PASSED [ 87%]
tests/test_step2_drift.py::test_concept_drift_diagonal_is_held_out_not_training_accuracy PASSED [ 90%]
tests/test_step2_drift.py::test_concept_drift_matrix_is_deterministic_and_does_not_mutate_input PASSED [ 93%]
tests/test_step2_drift.py::test_run_drift_analysis_writes_expected_outputs PASSED [ 96%]
tests/test_step2_drift.py::test_real_data_ks_between_two_years PASSED    [100%]

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
PASSED tests/test_step2_drift.py::test_ks_statistic_and_pvalue_within_unit_interval
PASSED tests/test_step2_drift.py::test_ks_identical_samples_give_zero_and_not_significant
PASSED tests/test_step2_drift.py::test_ks_same_distribution_different_draws_is_small_and_mostly_insignificant
PASSED tests/test_step2_drift.py::test_ks_detects_clearly_shifted_feature
PASSED tests/test_step2_drift.py::test_ks_is_symmetric
PASSED tests/test_step2_drift.py::test_ks_all_zero_feature_is_skipped_with_nan
PASSED tests/test_step2_drift.py::test_ks_constant_in_both_with_same_nonzero_value_is_skipped
PASSED tests/test_step2_drift.py::test_ks_constant_at_different_values_is_tested_and_maximal
PASSED tests/test_step2_drift.py::test_ks_constant_in_one_sample_only_is_tested
PASSED tests/test_step2_drift.py::test_ks_table_has_required_columns_and_one_row_per_feature
PASSED tests/test_step2_drift.py::test_bonferroni_uses_alpha_over_number_of_tested_features
PASSED tests/test_step2_drift.py::test_bonferroni_custom_alpha_and_all_nan
PASSED tests/test_step2_drift.py::test_subsample_equal_sizes_balanced_and_smallest_year_default
PASSED tests/test_step2_drift.py::test_subsample_explicit_n_and_year_label_consistency
PASSED tests/test_step2_drift.py::test_subsample_reproducible_with_seed_and_varies_across_seeds
PASSED tests/test_step2_drift.py::test_subsample_rows_come_from_the_source_year
PASSED tests/test_step2_drift.py::test_subsample_raises_when_a_class_is_too_small
PASSED tests/test_step2_drift.py::test_year_pair_modes_have_expected_row_counts
PASSED tests/test_step2_drift.py::test_year_pairs_unknown_mode_raises
PASSED tests/test_step2_drift.py::test_year_pairs_no_drift_vs_shifted_year
PASSED tests/test_step2_drift.py::test_skipped_features_counted_in_pair_summary
PASSED tests/test_step2_drift.py::test_most_different_years_sorted_descending_and_finds_shifted_year
PASSED tests/test_step2_drift.py::test_top_drifting_features_returns_k_sorted_and_finds_shifted_feature
PASSED tests/test_step2_drift.py::test_top_drifting_features_k_larger_than_features_returns_all
PASSED tests/test_step2_drift.py::test_concept_drift_matrix_square_indexed_by_years_and_in_unit_interval
PASSED tests/test_step2_drift.py::test_concept_drift_matrix_learns_signal_on_stable_data
PASSED tests/test_step2_drift.py::test_concept_drift_matrix_shows_concept_drift
PASSED tests/test_step2_drift.py::test_concept_drift_diagonal_is_held_out_not_training_accuracy
PASSED tests/test_step2_drift.py::test_concept_drift_matrix_is_deterministic_and_does_not_mutate_input
PASSED tests/test_step2_drift.py::test_run_drift_analysis_writes_expected_outputs
PASSED tests/test_step2_drift.py::test_real_data_ks_between_two_years
======================= 31 passed, 1 warning in 10.66s ========================
```
