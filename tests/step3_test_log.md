# Step 3 Test Log: Preprocess Data for Model Training

- Tester transcript: transcripts/15_2026-11-03_tester_step3.md

- Source followed for row counts: AGENTS.md (2014-2018 = 9,000 rows per file, 2019-2021 = 1,500), not ASSIGNMENT.md. Tests use small synthetic frames, so row counts only matter for the real-data test.
- Missing-year and NaN behaviour are not stated explicitly in PLAN.md; tests follow the AGENTS.md "fail loudly" rule.

## Tests written (tester)

One row per test function.

| Test | What it checks (from the assignment or plan) |
| --- | --- |
| test_train_and_test_share_no_years_in_prepare_split | Train and test outputs of prepare_split share no year |
| test_prepare_split_train_years_exactly_2014_2016_and_test_2017_2021 | Train years are exactly 2014-2016, test years 2017-2021 |
| test_every_test_year_is_later_than_every_training_year | Every test year is later than every training year |
| test_split_row_counts_and_alignment | Row counts of X, y, years line up on both sides |
| test_split_by_year_returns_disjoint_rows_of_requested_years | split_by_year returns disjoint rows of the requested years |
| test_check_no_overlap_accepts_valid_split | Valid 2014-2016 / 2017-2021 split does not raise |
| test_check_no_overlap_raises_on_bad_splits | Shared year, train after test, interleaved, empty train/test all raise ValueError (parametrized) |
| test_split_by_year_raises_on_overlap | split_by_year raises on overlapping years |
| test_split_by_year_missing_requested_year_fails_loudly | Requested test year absent from data raises ValueError (fail loudly) |
| test_prepare_split_missing_test_year_fails_loudly | prepare_split with a missing test year raises ValueError |
| test_tuning_split_uses_2014_2015_train_and_2016_validation_only | Tuning split trains on 2014-2015, validates on 2016 only |
| test_train_and_test_have_identical_column_count_and_order | Train and test have the same columns in the same (original) order |
| test_transform_gives_same_columns_for_train_and_test_values | transform gives the same column count for train and test rows |
| test_training_columns_have_mean_zero_and_std_one | Training columns have mean ~0 and std ~1 |
| test_test_data_is_transformed_not_refit | With a strongly shifted test set, test columns are not re-centred (scaler not refit) |
| test_fitted_statistics_equal_training_only_statistics | Scaler mean/scale equal log1p statistics of training rows on kept columns |
| test_changing_test_rows_does_not_change_fitted_scaler_or_mask | Changing test rows leaves scaler mean/scale and kept columns unchanged |
| test_transform_does_not_modify_fitted_scaler | transform leaves the fitted scaler unchanged |
| test_output_is_float32_and_finite | Outputs are float32 and finite |
| test_fit_transform_equals_fit_then_transform | fit_transform equals fit then transform |
| test_transform_before_fit_raises | transform before fit raises |
| test_apply_log1p_equals_numpy_log1p_and_float32 | apply_log1p equals np.log1p, float32 |
| test_apply_log1p_negative_input_raises | Negative input raises ValueError |
| test_log1p_compresses_heavy_tail | log1p compresses a count of 92,000 to below 12 |
| test_min_support_constant_is_10 | MIN_SUPPORT is 10 |
| test_mask_nine_nonzero_dropped_ten_kept | Column non-zero in 9 training rows dropped, 10 kept |
| test_mask_all_zero_column_dropped | All-zero column dropped |
| test_mask_custom_min_support | Custom min_support threshold respected |
| test_preprocessor_drops_zero_low_support_and_test_only_columns | All-zero, low-support (9 train rows) and test-only columns dropped; 10-row column kept |
| test_mask_ignores_test_rows | Test-year support cannot keep a column all-zero in training |
| test_dropped_column_cannot_produce_large_zscore_on_test | Test z-scores stay modest (no huge values from dropped near-constant columns) |
| test_constant_nonzero_column_does_not_create_nan_or_inf | Constant non-zero column yields no NaN/inf |
| test_nan_in_input_raises_or_yields_finite_output | NaN input raises ValueError or yields finite output (not silent NaN) |
| test_real_data_split_has_no_year_overlap_and_matching_columns | Real data: years, shared column count <= 1848, train mean ~0, float32 (skipped without input_data/) |

## Failures and decisions (student)

One row per failing test. Decision is "Accepted" (the test is right; the builder fixes the code) or "Rejected" (the test is wrong; the tester fixes the test). Add the commit with the fix.

| Test | Cause | Decision | Fixed in commit |
| test_split_by_year_missing_requested_year_fails_loudly | The code does not check that the requested years exist in the data, so a missing year gives no error. The test is right. Same defect as review comment 2 (accepted). | Accepted | |
| test_prepare_split_missing_test_year_fails_loudly | A missing test year (2019) silently gives a smaller split. The test is right. Same defect as review comment 2. | Accepted | |
| test_nan_in_input_raises_or_yields_finite_output | NaN passes through log1p and StandardScaler and appears in the model input. The test is right. Same defect as review comment 3 (accepted). | Accepted | |
| test_real_data_split_has_no_year_overlap_and_matching_columns | The real-data check asserts training column means are within 0.001 of 0, but the accepted clip to plus or minus 10 (review comment 1) moves rare columns by up to about 0.02. The code is correct and the test is out of date. | Rejected | |

## Runs (added by `python harness.py test N`; do not edit)

### Run 1: FAILED

- Time: 2026-11-03T01:55:08+02:00
- Commit: 0474b83
- Result: 3 failed, 35 passed, 1 warning in 7.84s
- Files: test_step3_preprocess.py

```
... (13 earlier lines omitted)
tests/test_step3_preprocess.py::test_check_no_overlap_accepts_valid_split PASSED [ 15%]
tests/test_step3_preprocess.py::test_check_no_overlap_raises_on_bad_splits[train0-test0] PASSED [ 18%]
tests/test_step3_preprocess.py::test_check_no_overlap_raises_on_bad_splits[train1-test1] PASSED [ 21%]
tests/test_step3_preprocess.py::test_check_no_overlap_raises_on_bad_splits[train2-test2] PASSED [ 23%]
tests/test_step3_preprocess.py::test_check_no_overlap_raises_on_bad_splits[train3-test3] PASSED [ 26%]
tests/test_step3_preprocess.py::test_check_no_overlap_raises_on_bad_splits[train4-test4] PASSED [ 28%]
tests/test_step3_preprocess.py::test_split_by_year_raises_on_overlap PASSED [ 31%]
tests/test_step3_preprocess.py::test_split_by_year_missing_requested_year_fails_loudly FAILED [ 34%]
tests/test_step3_preprocess.py::test_prepare_split_missing_test_year_fails_loudly FAILED [ 36%]
tests/test_step3_preprocess.py::test_tuning_split_uses_2014_2015_train_and_2016_validation_only PASSED [ 39%]
tests/test_step3_preprocess.py::test_train_and_test_have_identical_column_count_and_order PASSED [ 42%]
tests/test_step3_preprocess.py::test_transform_gives_same_columns_for_train_and_test_values PASSED [ 44%]
tests/test_step3_preprocess.py::test_training_columns_have_mean_zero_and_std_one PASSED [ 47%]
tests/test_step3_preprocess.py::test_test_data_is_transformed_not_refit PASSED [ 50%]
tests/test_step3_preprocess.py::test_fitted_statistics_equal_training_only_statistics PASSED [ 52%]
tests/test_step3_preprocess.py::test_changing_test_rows_does_not_change_fitted_scaler_or_mask PASSED [ 55%]
tests/test_step3_preprocess.py::test_transform_does_not_modify_fitted_scaler PASSED [ 57%]
tests/test_step3_preprocess.py::test_output_is_float32_and_finite PASSED [ 60%]
tests/test_step3_preprocess.py::test_fit_transform_equals_fit_then_transform PASSED [ 63%]
tests/test_step3_preprocess.py::test_transform_before_fit_raises PASSED  [ 65%]
tests/test_step3_preprocess.py::test_apply_log1p_equals_numpy_log1p_and_float32 PASSED [ 68%]
tests/test_step3_preprocess.py::test_apply_log1p_negative_input_raises PASSED [ 71%]
tests/test_step3_preprocess.py::test_log1p_compresses_heavy_tail PASSED  [ 73%]
tests/test_step3_preprocess.py::test_min_support_constant_is_10 PASSED   [ 76%]
tests/test_step3_preprocess.py::test_mask_nine_nonzero_dropped_ten_kept PASSED [ 78%]
tests/test_step3_preprocess.py::test_mask_all_zero_column_dropped PASSED [ 81%]
tests/test_step3_preprocess.py::test_mask_custom_min_support PASSED      [ 84%]
tests/test_step3_preprocess.py::test_preprocessor_drops_zero_low_support_and_test_only_columns PASSED [ 86%]
tests/test_step3_preprocess.py::test_mask_ignores_test_rows PASSED       [ 89%]
tests/test_step3_preprocess.py::test_dropped_column_cannot_produce_large_zscore_on_test PASSED [ 92%]
tests/test_step3_preprocess.py::test_constant_nonzero_column_does_not_create_nan_or_inf PASSED [ 94%]
tests/test_step3_preprocess.py::test_nan_in_input_raises_or_yields_finite_output FAILED [ 97%]
tests/test_step3_preprocess.py::test_real_data_split_has_no_year_overlap_and_matching_columns PASSED [100%]

================================== FAILURES ===================================
___________ test_split_by_year_missing_requested_year_fails_loudly ____________

    def test_split_by_year_missing_requested_year_fails_loudly():
>       with pytest.raises(ValueError):
E       Failed: DID NOT RAISE ValueError

tests\test_step3_preprocess.py:113: Failed
______________ test_prepare_split_missing_test_year_fails_loudly ______________

    def test_prepare_split_missing_test_year_fails_loudly():
        df = make_df()
        df = df[df["year"] != 2019]
>       with pytest.raises(ValueError):
E       Failed: DID NOT RAISE ValueError

tests\test_step3_preprocess.py:120: Failed
______________ test_nan_in_input_raises_or_yields_finite_output _______________

    def test_nan_in_input_raises_or_yields_finite_output():
        X = np.ones((30, 2), dtype=np.float32)
        X[:, 1] = np.arange(30)
        X[3, 1] = np.nan
        try:
            out = Preprocessor().fit_transform(X, ["c", "v"])
        except ValueError:
            return
>       assert np.isfinite(out).all(), "NaN silently propagated into the model input"
E       AssertionError: NaN silently propagated into the model input
E       assert np.False_
E        +  where np.False_ = <built-in method all of numpy.ndarray object at 0x000001A1CC1B0210>()
E        +    where <built-in method all of numpy.ndarray object at 0x000001A1CC1B0210> = array([[ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True, False],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True]]).all
E        +      where array([[ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True, False],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True],\n       [ True,  True]]) = <ufunc 'isfinite'>(array([[ 0.        , -3.0642078 ],\n       [ 0.        , -2.2235796 ],\n       [ 0.        , -1.7318436 ],\n       [ 0.        ,         nan],\n       [ 0.        , -1.1123295 ],\n       [ 0.        , -0.8912153 ],\n       [ 0.        , -0.7042661 ],\n       [ 0.        , -0.5423231 ],\n       [ 0.        , -0.39947933],\n       [ 0.        , -0.27170125],\n       [ 0.        , -0.15611188],\n       [ 0.        , -0.05058713],\n       [ 0.        ,  0.04648615],\n       [ 0.        ,  0.13636227],\n       [ 0.        ,  0.22003475],\n       [ 0.        ,  0.2983051 ],\n       [ 0.        ,  0.3718288 ],\n       [ 0.        ,  0.44114888],\n       [ 0.        ,  0.5067199 ],\n       [ 0.        ,  0.56892693],\n       [ 0.        ,  0.62809825],\n       [ 0.        ,  0.6845163 ],\n       [ 0.        ,  0.738426  ],\n       [ 0.        ,  0.7900411 ],\n       [ 0.        ,  0.8395488 ],\n       [ 0.        ,  0.88711435],\n       [ 0.        ,  0.9328849 ],\n       [ 0.        ,  0.97699046],\n       [ 0.        ,  1.0195479 ],\n       [ 0.        ,  1.060663  ]], dtype=float32))
E        +        where <ufunc 'isfinite'> = np.isfinite

tests\test_step3_preprocess.py:287: AssertionError
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
PASSED tests/test_step3_preprocess.py::test_train_and_test_share_no_years_in_prepare_split
PASSED tests/test_step3_preprocess.py::test_prepare_split_train_years_exactly_2014_2016_and_test_2017_2021
PASSED tests/test_step3_preprocess.py::test_every_test_year_is_later_than_every_training_year
PASSED tests/test_step3_preprocess.py::test_split_row_counts_and_alignment
PASSED tests/test_step3_preprocess.py::test_split_by_year_returns_disjoint_rows_of_requested_years
PASSED tests/test_step3_preprocess.py::test_check_no_overlap_accepts_valid_split
PASSED tests/test_step3_preprocess.py::test_check_no_overlap_raises_on_bad_splits[train0-test0]
PASSED tests/test_step3_preprocess.py::test_check_no_overlap_raises_on_bad_splits[train1-test1]
PASSED tests/test_step3_preprocess.py::test_check_no_overlap_raises_on_bad_splits[train2-test2]
PASSED tests/test_step3_preprocess.py::test_check_no_overlap_raises_on_bad_splits[train3-test3]
PASSED tests/test_step3_preprocess.py::test_check_no_overlap_raises_on_bad_splits[train4-test4]
PASSED tests/test_step3_preprocess.py::test_split_by_year_raises_on_overlap
PASSED tests/test_step3_preprocess.py::test_tuning_split_uses_2014_2015_train_and_2016_validation_only
PASSED tests/test_step3_preprocess.py::test_train_and_test_have_identical_column_count_and_order
PASSED tests/test_step3_preprocess.py::test_transform_gives_same_columns_for_train_and_test_values
PASSED tests/test_step3_preprocess.py::test_training_columns_have_mean_zero_and_std_one
PASSED tests/test_step3_preprocess.py::test_test_data_is_transformed_not_refit
PASSED tests/test_step3_preprocess.py::test_fitted_statistics_equal_training_only_statistics
PASSED tests/test_step3_preprocess.py::test_changing_test_rows_does_not_change_fitted_scaler_or_mask
PASSED tests/test_step3_preprocess.py::test_transform_does_not_modify_fitted_scaler
PASSED tests/test_step3_preprocess.py::test_output_is_float32_and_finite
PASSED tests/test_step3_preprocess.py::test_fit_transform_equals_fit_then_transform
PASSED tests/test_step3_preprocess.py::test_transform_before_fit_raises
PASSED tests/test_step3_preprocess.py::test_apply_log1p_equals_numpy_log1p_and_float32
PASSED tests/test_step3_preprocess.py::test_apply_log1p_negative_input_raises
PASSED tests/test_step3_preprocess.py::test_log1p_compresses_heavy_tail
PASSED tests/test_step3_preprocess.py::test_min_support_constant_is_10
PASSED tests/test_step3_preprocess.py::test_mask_nine_nonzero_dropped_ten_kept
PASSED tests/test_step3_preprocess.py::test_mask_all_zero_column_dropped
PASSED tests/test_step3_preprocess.py::test_mask_custom_min_support
PASSED tests/test_step3_preprocess.py::test_preprocessor_drops_zero_low_support_and_test_only_columns
PASSED tests/test_step3_preprocess.py::test_mask_ignores_test_rows
PASSED tests/test_step3_preprocess.py::test_dropped_column_cannot_produce_large_zscore_on_test
PASSED tests/test_step3_preprocess.py::test_constant_nonzero_column_does_not_create_nan_or_inf
PASSED tests/test_step3_preprocess.py::test_real_data_split_has_no_year_overlap_and_matching_columns
FAILED tests/test_step3_preprocess.py::test_split_by_year_missing_requested_year_fails_loudly
FAILED tests/test_step3_preprocess.py::test_prepare_split_missing_test_year_fails_loudly
FAILED tests/test_step3_preprocess.py::test_nan_in_input_raises_or_yields_finite_output
=================== 3 failed, 35 passed, 1 warning in 7.84s ===================
```

### Run 2: FAILED

- Time: 2026-11-03T02:19:36+02:00
- Commit: 9b7d8e3
- Result: 1 failed, 37 passed, 1 warning in 7.27s
- Files: test_step3_preprocess.py

```
============================= test session starts =============================
platform win32 -- Python 3.11.4, pytest-9.2.0, pluggy-1.7.0 -- C:\Program Files\Python311\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\thema\OneDrive\Desktop\Project2\project2-harness2\project2-harness2
configfile: pytest.ini
plugins: anyio-4.8.0, dash-2.18.1
collecting ... collected 38 items

tests/test_step3_preprocess.py::test_train_and_test_share_no_years_in_prepare_split PASSED [  2%]
tests/test_step3_preprocess.py::test_prepare_split_train_years_exactly_2014_2016_and_test_2017_2021 PASSED [  5%]
tests/test_step3_preprocess.py::test_every_test_year_is_later_than_every_training_year PASSED [  7%]
tests/test_step3_preprocess.py::test_split_row_counts_and_alignment PASSED [ 10%]
tests/test_step3_preprocess.py::test_split_by_year_returns_disjoint_rows_of_requested_years PASSED [ 13%]
tests/test_step3_preprocess.py::test_check_no_overlap_accepts_valid_split PASSED [ 15%]
tests/test_step3_preprocess.py::test_check_no_overlap_raises_on_bad_splits[train0-test0] PASSED [ 18%]
tests/test_step3_preprocess.py::test_check_no_overlap_raises_on_bad_splits[train1-test1] PASSED [ 21%]
tests/test_step3_preprocess.py::test_check_no_overlap_raises_on_bad_splits[train2-test2] PASSED [ 23%]
tests/test_step3_preprocess.py::test_check_no_overlap_raises_on_bad_splits[train3-test3] PASSED [ 26%]
tests/test_step3_preprocess.py::test_check_no_overlap_raises_on_bad_splits[train4-test4] PASSED [ 28%]
tests/test_step3_preprocess.py::test_split_by_year_raises_on_overlap PASSED [ 31%]
tests/test_step3_preprocess.py::test_split_by_year_missing_requested_year_fails_loudly PASSED [ 34%]
tests/test_step3_preprocess.py::test_prepare_split_missing_test_year_fails_loudly PASSED [ 36%]
tests/test_step3_preprocess.py::test_tuning_split_uses_2014_2015_train_and_2016_validation_only PASSED [ 39%]
tests/test_step3_preprocess.py::test_train_and_test_have_identical_column_count_and_order PASSED [ 42%]
tests/test_step3_preprocess.py::test_transform_gives_same_columns_for_train_and_test_values PASSED [ 44%]
tests/test_step3_preprocess.py::test_training_columns_have_mean_zero_and_std_one PASSED [ 47%]
tests/test_step3_preprocess.py::test_test_data_is_transformed_not_refit PASSED [ 50%]
tests/test_step3_preprocess.py::test_fitted_statistics_equal_training_only_statistics PASSED [ 52%]
tests/test_step3_preprocess.py::test_changing_test_rows_does_not_change_fitted_scaler_or_mask PASSED [ 55%]
tests/test_step3_preprocess.py::test_transform_does_not_modify_fitted_scaler PASSED [ 57%]
tests/test_step3_preprocess.py::test_output_is_float32_and_finite PASSED [ 60%]
tests/test_step3_preprocess.py::test_fit_transform_equals_fit_then_transform PASSED [ 63%]
tests/test_step3_preprocess.py::test_transform_before_fit_raises PASSED  [ 65%]
tests/test_step3_preprocess.py::test_apply_log1p_equals_numpy_log1p_and_float32 PASSED [ 68%]
tests/test_step3_preprocess.py::test_apply_log1p_negative_input_raises PASSED [ 71%]
tests/test_step3_preprocess.py::test_log1p_compresses_heavy_tail PASSED  [ 73%]
tests/test_step3_preprocess.py::test_min_support_constant_is_10 PASSED   [ 76%]
tests/test_step3_preprocess.py::test_mask_nine_nonzero_dropped_ten_kept PASSED [ 78%]
tests/test_step3_preprocess.py::test_mask_all_zero_column_dropped PASSED [ 81%]
tests/test_step3_preprocess.py::test_mask_custom_min_support PASSED      [ 84%]
tests/test_step3_preprocess.py::test_preprocessor_drops_zero_low_support_and_test_only_columns PASSED [ 86%]
tests/test_step3_preprocess.py::test_mask_ignores_test_rows PASSED       [ 89%]
tests/test_step3_preprocess.py::test_dropped_column_cannot_produce_large_zscore_on_test PASSED [ 92%]
tests/test_step3_preprocess.py::test_constant_nonzero_column_does_not_create_nan_or_inf PASSED [ 94%]
tests/test_step3_preprocess.py::test_nan_in_input_raises_or_yields_finite_output PASSED [ 97%]
tests/test_step3_preprocess.py::test_real_data_split_has_no_year_overlap_and_matching_columns FAILED [100%]

================================== FAILURES ===================================
________ test_real_data_split_has_no_year_overlap_and_matching_columns ________

real_data_dir = WindowsPath('C:/Users/thema/OneDrive/Desktop/Project2/project2-harness2/project2-harness2/input_data')

    def test_real_data_split_has_no_year_overlap_and_matching_columns(real_data_dir):
        from src.data import load_all
    
        df = load_all(real_data_dir)
        s = prepare_split(df)
        assert set(np.unique(s["years_train"])) == {2014, 2015, 2016}
        assert set(np.unique(s["years_test"])) == {2017, 2018, 2019, 2020, 2021}
        assert s["X_train"].shape[1] == s["X_test"].shape[1] <= 1848
>       assert np.allclose(s["X_train"].mean(axis=0), 0.0, atol=1e-3)
E       assert False
E        +  where False = <function allclose at 0x000001D6F94C4730>(array([-2.06834376e-02, -1.32279620e-02, -4.18178830e-03, -1.21354004e-02,\n       -2.34155660e-03, -1.86463390e-02,  1.24330874e-08, -1.05482875e-04,\n       -2.05243528e-02, -1.06583945e-02, -1.40452078e-02, -9.03772434e-06,\n       -2.33003702e-02, -7.99342990e-03, -6.33773394e-03,  2.26056134e-08,\n       -1.04636727e-02, -1.70820262e-02, -1.30608771e-02, -8.72341916e-03,\n       -7.50273792e-03, -8.69312696e-03, -2.42416840e-02, -2.11633756e-04,\n       -1.97867601e-04, -2.27484424e-02, -1.24881321e-04, -1.37146330e-03,\n       -2.27484424e-02, -2.27484424e-02, -2.27873345e-04, -1.51843615e-02,\n       -2.23833974e-02, -2.05753007e-04, -2.27484424e-02,  3.16478577e-08,\n       -4.97323498e-08, -1.80844903e-08, -2.78934836e-04, -3.88115208e-04,\n        1.35633682e-08, -6.63097890e-04, -7.23379614e-08, -2.03450519e-08,\n       -2.80209584e-04, -3.41448758e-04, -4.73886845e-04, -3.60575359e-04,\n       -7.89422484e-04, -3.47295136e-04, -1.46516319e-02, -9.04224517e-09,\n       -3.34753748e-03,  1.58239288e-08,  1.13028067e-08, -7.22372672e-03,\n       -7.97639973e-03, -1.77103002e-02, -1.45920850e-02, -1.17551675e-02,\n       -1.26832426e-02, -1.17551675e-02, -1.96442977e-02, -2.34168544e-02...\n       -4.67247143e-03, -1.22339930e-02, -1.94058544e-03, -8.58258281e-04,\n       -1.48031441e-03, -2.43557133e-02, -2.43557133e-02, -2.44042240e-02,\n       -2.27484517e-02, -2.82570163e-08, -2.68441669e-09, -2.32894326e-05,\n       -2.26835534e-02,  3.61689807e-08, -1.65502988e-02, -1.80225514e-04,\n       -1.73588502e-04, -3.73531628e-04, -1.92079897e-05,  2.71267364e-08,\n        3.99836786e-08, -5.29819077e-09, -7.91196442e-09, -7.91196442e-09,\n       -7.84731237e-05, -3.50386991e-08, -3.61689807e-08, -6.32957153e-08,\n       -1.27810729e-03, -2.11887304e-02, -2.26056134e-08,  5.65140335e-09,\n        4.74717865e-08,  4.29506670e-08, -2.07750034e-02,  2.00624815e-08,\n       -3.07029441e-05, -1.51766492e-02, -1.91332661e-02, -6.10351591e-08,\n       -4.76300283e-06, -4.13759582e-04, -1.90309174e-02, -2.36231796e-02,\n       -1.80844903e-08, -1.00030180e-03, -1.37749892e-02,  1.80844903e-08,\n       -1.79239418e-02, -1.87882241e-02, -1.27409759e-03, -2.17108112e-02,\n       -9.91889101e-05, -2.14084197e-04, -1.46432387e-04,  5.14277723e-08,\n        3.95598221e-09,  3.34139223e-08, -1.58239288e-08, -8.48128693e-05,\n       -1.63890697e-08, -4.90394887e-05, -9.96681501e-06], dtype=float32), 0.0, atol=0.001)
E        +    where <function allclose at 0x000001D6F94C4730> = np.allclose
E        +    and   array([-2.06834376e-02, -1.32279620e-02, -4.18178830e-03, -1.21354004e-02,\n       -2.34155660e-03, -1.86463390e-02,  1.24330874e-08, -1.05482875e-04,\n       -2.05243528e-02, -1.06583945e-02, -1.40452078e-02, -9.03772434e-06,\n       -2.33003702e-02, -7.99342990e-03, -6.33773394e-03,  2.26056134e-08,\n       -1.04636727e-02, -1.70820262e-02, -1.30608771e-02, -8.72341916e-03,\n       -7.50273792e-03, -8.69312696e-03, -2.42416840e-02, -2.11633756e-04,\n       -1.97867601e-04, -2.27484424e-02, -1.24881321e-04, -1.37146330e-03,\n       -2.27484424e-02, -2.27484424e-02, -2.27873345e-04, -1.51843615e-02,\n       -2.23833974e-02, -2.05753007e-04, -2.27484424e-02,  3.16478577e-08,\n       -4.97323498e-08, -1.80844903e-08, -2.78934836e-04, -3.88115208e-04,\n        1.35633682e-08, -6.63097890e-04, -7.23379614e-08, -2.03450519e-08,\n       -2.80209584e-04, -3.41448758e-04, -4.73886845e-04, -3.60575359e-04,\n       -7.89422484e-04, -3.47295136e-04, -1.46516319e-02, -9.04224517e-09,\n       -3.34753748e-03,  1.58239288e-08,  1.13028067e-08, -7.22372672e-03,\n       -7.97639973e-03, -1.77103002e-02, -1.45920850e-02, -1.17551675e-02,\n       -1.26832426e-02, -1.17551675e-02, -1.96442977e-02, -2.34168544e-02...\n       -4.67247143e-03, -1.22339930e-02, -1.94058544e-03, -8.58258281e-04,\n       -1.48031441e-03, -2.43557133e-02, -2.43557133e-02, -2.44042240e-02,\n       -2.27484517e-02, -2.82570163e-08, -2.68441669e-09, -2.32894326e-05,\n       -2.26835534e-02,  3.61689807e-08, -1.65502988e-02, -1.80225514e-04,\n       -1.73588502e-04, -3.73531628e-04, -1.92079897e-05,  2.71267364e-08,\n        3.99836786e-08, -5.29819077e-09, -7.91196442e-09, -7.91196442e-09,\n       -7.84731237e-05, -3.50386991e-08, -3.61689807e-08, -6.32957153e-08,\n       -1.27810729e-03, -2.11887304e-02, -2.26056134e-08,  5.65140335e-09,\n        4.74717865e-08,  4.29506670e-08, -2.07750034e-02,  2.00624815e-08,\n       -3.07029441e-05, -1.51766492e-02, -1.91332661e-02, -6.10351591e-08,\n       -4.76300283e-06, -4.13759582e-04, -1.90309174e-02, -2.36231796e-02,\n       -1.80844903e-08, -1.00030180e-03, -1.37749892e-02,  1.80844903e-08,\n       -1.79239418e-02, -1.87882241e-02, -1.27409759e-03, -2.17108112e-02,\n       -9.91889101e-05, -2.14084197e-04, -1.46432387e-04,  5.14277723e-08,\n        3.95598221e-09,  3.34139223e-08, -1.58239288e-08, -8.48128693e-05,\n       -1.63890697e-08, -4.90394887e-05, -9.96681501e-06], dtype=float32) = <built-in method mean of numpy.ndarray object at 0x000001D695B074B0>(axis=0)
E        +      where <built-in method mean of numpy.ndarray object at 0x000001D695B074B0> = array([[-0.02941274, -0.08674348, -0.1169538 , ..., -0.3178972 ,\n        -0.34987155, -0.1694566 ],\n       [-0.02941274, -0.08674348, -0.1169538 , ..., -0.3178972 ,\n        -0.34987155, -0.1694566 ],\n       [-0.02941274, -0.08674348, -0.1169538 , ..., -0.3178972 ,\n        -0.34987155, -0.1694566 ],\n       ...,\n       [-0.02941274, -0.08674348, -0.1169538 , ..., -0.3178972 ,\n        -0.34987155, -0.1694566 ],\n       [-0.02941274, -0.08674348, -0.1169538 , ..., -0.3178972 ,\n        -0.34987155, -0.1694566 ],\n       [-0.02941274, -0.08674348, -0.1169538 , ..., -0.3178972 ,\n        -0.34987155, -0.1694566 ]], dtype=float32).mean

tests\test_step3_preprocess.py:300: AssertionError
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
PASSED tests/test_step3_preprocess.py::test_train_and_test_share_no_years_in_prepare_split
PASSED tests/test_step3_preprocess.py::test_prepare_split_train_years_exactly_2014_2016_and_test_2017_2021
PASSED tests/test_step3_preprocess.py::test_every_test_year_is_later_than_every_training_year
PASSED tests/test_step3_preprocess.py::test_split_row_counts_and_alignment
PASSED tests/test_step3_preprocess.py::test_split_by_year_returns_disjoint_rows_of_requested_years
PASSED tests/test_step3_preprocess.py::test_check_no_overlap_accepts_valid_split
PASSED tests/test_step3_preprocess.py::test_check_no_overlap_raises_on_bad_splits[train0-test0]
PASSED tests/test_step3_preprocess.py::test_check_no_overlap_raises_on_bad_splits[train1-test1]
PASSED tests/test_step3_preprocess.py::test_check_no_overlap_raises_on_bad_splits[train2-test2]
PASSED tests/test_step3_preprocess.py::test_check_no_overlap_raises_on_bad_splits[train3-test3]
PASSED tests/test_step3_preprocess.py::test_check_no_overlap_raises_on_bad_splits[train4-test4]
PASSED tests/test_step3_preprocess.py::test_split_by_year_raises_on_overlap
PASSED tests/test_step3_preprocess.py::test_split_by_year_missing_requested_year_fails_loudly
PASSED tests/test_step3_preprocess.py::test_prepare_split_missing_test_year_fails_loudly
PASSED tests/test_step3_preprocess.py::test_tuning_split_uses_2014_2015_train_and_2016_validation_only
PASSED tests/test_step3_preprocess.py::test_train_and_test_have_identical_column_count_and_order
PASSED tests/test_step3_preprocess.py::test_transform_gives_same_columns_for_train_and_test_values
PASSED tests/test_step3_preprocess.py::test_training_columns_have_mean_zero_and_std_one
PASSED tests/test_step3_preprocess.py::test_test_data_is_transformed_not_refit
PASSED tests/test_step3_preprocess.py::test_fitted_statistics_equal_training_only_statistics
PASSED tests/test_step3_preprocess.py::test_changing_test_rows_does_not_change_fitted_scaler_or_mask
PASSED tests/test_step3_preprocess.py::test_transform_does_not_modify_fitted_scaler
PASSED tests/test_step3_preprocess.py::test_output_is_float32_and_finite
PASSED tests/test_step3_preprocess.py::test_fit_transform_equals_fit_then_transform
PASSED tests/test_step3_preprocess.py::test_transform_before_fit_raises
PASSED tests/test_step3_preprocess.py::test_apply_log1p_equals_numpy_log1p_and_float32
PASSED tests/test_step3_preprocess.py::test_apply_log1p_negative_input_raises
PASSED tests/test_step3_preprocess.py::test_log1p_compresses_heavy_tail
PASSED tests/test_step3_preprocess.py::test_min_support_constant_is_10
PASSED tests/test_step3_preprocess.py::test_mask_nine_nonzero_dropped_ten_kept
PASSED tests/test_step3_preprocess.py::test_mask_all_zero_column_dropped
PASSED tests/test_step3_preprocess.py::test_mask_custom_min_support
PASSED tests/test_step3_preprocess.py::test_preprocessor_drops_zero_low_support_and_test_only_columns
PASSED tests/test_step3_preprocess.py::test_mask_ignores_test_rows
PASSED tests/test_step3_preprocess.py::test_dropped_column_cannot_produce_large_zscore_on_test
PASSED tests/test_step3_preprocess.py::test_constant_nonzero_column_does_not_create_nan_or_inf
PASSED tests/test_step3_preprocess.py::test_nan_in_input_raises_or_yields_finite_output
FAILED tests/test_step3_preprocess.py::test_real_data_split_has_no_year_overlap_and_matching_columns
=================== 1 failed, 37 passed, 1 warning in 7.27s ===================
```
