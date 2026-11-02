# Step 1 Test Log: Prepare the data

- Tester transcript: transcripts/06_2026-11-02_tester_step1.md
- Row counts: ASSIGNMENT.md says 1,500 rows per file; AGENTS.md says 9,000 (2014-2018) and 1,500 (2019-2021). Tests follow AGENTS.md (the verified facts). Synthetic tests use the real 1,849-column schema with a few rows, and do not assume a row count.

## Tests written (tester)

One row per test function.

| Test | What it checks (from the assignment or plan) |
| --- | --- |
| test_parse_filename_valid | Valid names return (year, label); malware=1, benign=0 |
| test_parse_filename_invalid_raises | Wrong year, bad class, extra suffix, missing _api, stray name, empty string raise ValueError |
| test_parse_filename_rejects_directory_path | Name with directories does not match the regex |
| test_load_file_drops_first_column | `apkname` is not present after loading |
| test_load_file_has_1848_features_plus_label_year | 1,848 feature columns in original order, plus label and year |
| test_load_file_label_and_year_from_filename | Labels contain only the one class matching the file name; year from file name |
| test_load_file_dtypes | Features int32, label int8, year int16 |
| test_load_file_does_not_assume_row_count | Any row count loads (no fixed 1,500 assumption) |
| test_load_file_wrong_column_count_raises | Too few columns raises ValueError |
| test_load_file_extra_column_raises | Too many columns raises ValueError |
| test_load_file_wrong_first_column_raises | First column must be `apkname` |
| test_load_file_bad_filename_raises | File with a non-matching name raises (year/class come only from file name) |
| test_load_file_negative_value_raises | Negative counts rejected |
| test_load_file_missing_value_raises | Missing values rejected (none allowed after loading) |
| test_load_file_no_missing_values_on_valid_input | No NaN in a loaded valid file |
| test_load_file_all_zero_feature_kept | Edge case: all-zero feature column is kept and loads |
| test_read_apknames_returns_ids_only | `read_apknames` returns only the id column |
| test_list_data_files_returns_16_sorted | 16 files, sorted |
| test_list_data_files_stray_csv_raises | Stray CSV (notes.csv) raises |
| test_list_data_files_missing_file_raises | Missing year/class file raises |
| test_list_data_files_empty_dir_raises | Empty folder raises |
| test_load_year_combines_both_classes | Year frame = malware + benign rows, both labels present, correct counts |
| test_validate_feature_order_mismatched_order_raises | Swapped column order raises |
| test_validate_feature_order_mismatched_names_raises | Different column name raises |
| test_validate_feature_order_ok | Identical features pass |
| test_combine_years_row_count_and_columns | Full 16-file synthetic folder; combining years 2014-2016: rows = sum of inputs; ignore_index; 1,850 columns; years in order |
| test_combine_years_labels_balanced_per_year | Full 16-file synthetic folder; combining 2014-2015: per-year/class counts preserved |
| test_combine_years_mismatched_features_raises | combine_years validates feature order |
| test_load_all_synthetic_end_to_end | load_all on 16 synthetic files: row total, all years, both labels, no apkname, no NaN |
| test_cache_key_changes_when_file_changes | cache_key is stable and changes with file size |
| test_cache_key_changes_with_mtime | cache_key changes with mtime |
| test_train_duplicate_mask_flags_test_row_equal_to_train_row | Test row equal to a 2014-2016 row is flagged; unique row is not |
| test_real_16_files_and_columns | Real data: 16 files, 1,849 raw columns, first column `apkname` (skipped without data) |
| test_real_year_sizes_labels_and_nan | Real data, years 2014 and 2019: 9,000 / 1,500 rows per file (AGENTS.md), single label per file matching name, 2x rows per year with equal class counts, no NaN, non-negative |

## Failures and decisions (student)

One row per failing test. Decision is "Accepted" (the test is right; the builder fixes the code) or "Rejected" (the test is wrong; the tester fixes the test). Add the commit with the fix.

| Test | Cause | Decision | Fixed in commit |
| --- | --- | --- | --- |
| test_combine_years_row_count_and_columns | Test builds a folder with only 2014 and 2015, but list_data_files requires all 16 files by design (PLAN.md Step 1). The test setup is wrong, not the code. | Rejected | b434e99 |
| test_combine_years_labels_balanced_per_year | Same cause: a two-year folder fails the 16-file check inside load_year. | Rejected | b434e99 |

## Runs (added by `python harness.py test N`; do not edit)

### Run 1: FAILED

- Time: 2026-11-02T09:22:44+02:00
- Commit: ab5e696
- Result: 2 failed, 42 passed, 2 warnings in 18.12s
- Files: test_step1_data.py

```
... (76 earlier lines omitted)
        """List the dataset CSVs, validating every name.
    
        macOS resource-fork files (name starting with "._") are skipped. Every other
        *.csv must parse, so a stray or misnamed CSV raises ValueError. Also raises
        unless there is exactly one malware and one benign file per year (16 files).
        """
        files = sorted(p for p in Path(data_dir).glob("*.csv") if not p.name.startswith("._"))
        seen: set[tuple[int, int]] = set()
        for path in files:
            key = parse_filename(path.name)  # raises on a stray file
            if key in seen:
                raise ValueError(f"Duplicate year/class file: {path.name}")
            seen.add(key)
        expected = {(y, lab) for y in ALL_YEARS for lab in (0, 1)}
        if seen != expected:
>           raise ValueError(f"Missing files (year, label): {sorted(expected - seen)}")
E           ValueError: Missing files (year, label): [(2017, 0), (2017, 1), (2018, 0), (2018, 1), (2019, 0), (2019, 1), (2020, 0), (2020, 1), (2021, 0), (2021, 1)]

src\data.py:62: ValueError
_________________ test_combine_years_labels_balanced_per_year _________________

tmp_path = WindowsPath('C:/Users/thema/AppData/Local/Temp/pytest-of-thema/pytest-0/test_combine_years_labels_bala0')

    def test_combine_years_labels_balanced_per_year(tmp_path):
        make_dir(tmp_path, years=(2014, 2015), n_rows=4)
>       out = data.combine_years({y: data.load_year(y, tmp_path) for y in (2014, 2015)})
                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\test_step1_data.py:252: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
tests\test_step1_data.py:252: in <dictcomp>
    out = data.combine_years({y: data.load_year(y, tmp_path) for y in (2014, 2015)})
                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^
src\data.py:120: in load_year
    parts = [load_file(p) for p in list_data_files(data_dir) if parse_filename(p.name)[0] == year]
                                   ^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

data_dir = WindowsPath('C:/Users/thema/AppData/Local/Temp/pytest-of-thema/pytest-0/test_combine_years_labels_bala0')

    def list_data_files(data_dir: Path = DATA_DIR) -> list[Path]:
        """List the dataset CSVs, validating every name.
    
        macOS resource-fork files (name starting with "._") are skipped. Every other
        *.csv must parse, so a stray or misnamed CSV raises ValueError. Also raises
        unless there is exactly one malware and one benign file per year (16 files).
        """
        files = sorted(p for p in Path(data_dir).glob("*.csv") if not p.name.startswith("._"))
        seen: set[tuple[int, int]] = set()
        for path in files:
            key = parse_filename(path.name)  # raises on a stray file
            if key in seen:
                raise ValueError(f"Duplicate year/class file: {path.name}")
            seen.add(key)
        expected = {(y, lab) for y in ALL_YEARS for lab in (0, 1)}
        if seen != expected:
>           raise ValueError(f"Missing files (year, label): {sorted(expected - seen)}")
E           ValueError: Missing files (year, label): [(2016, 0), (2016, 1), (2017, 0), (2017, 1), (2018, 0), (2018, 1), (2019, 0), (2019, 1), (2020, 0), (2020, 1), (2021, 0), (2021, 1)]

src\data.py:62: ValueError
============================== warnings summary ===============================
..\..\..\..\..\AppData\Roaming\Python\Python311\site-packages\dash\testing\plugin.py:92
  C:\Users\thema\AppData\Roaming\Python\Python311\site-packages\dash\testing\plugin.py:92: PytestRemovedIn10Warning: The hookimpl pytest_addhooks uses old-style configuration options (marks or attributes).
  Please use the pytest.hookimpl(tryfirst=True) decorator instead
   to configure the hooks.
   See https://docs.pytest.org/en/latest/deprecations.html#configuring-hook-specs-impls-using-markers
    @pytest.mark.tryfirst

tests/test_step1_data.py::test_load_file_missing_value_raises
  C:\Users\thema\AppData\Roaming\Python\Python311\site-packages\pandas\io\parsers\c_parser_wrapper.py:234: RuntimeWarning: invalid value encountered in cast
    chunks = self._reader.read_low_memory(nrows)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=================================== PASSES ====================================
=========================== short test summary info ===========================
PASSED tests/test_step1_data.py::test_parse_filename_valid[sampled_2014_malware_api.csv-expected0]
PASSED tests/test_step1_data.py::test_parse_filename_valid[sampled_2021_benign_api.csv-expected1]
PASSED tests/test_step1_data.py::test_parse_filename_valid[sampled_2017_malware_api.csv-expected2]
PASSED tests/test_step1_data.py::test_parse_filename_invalid_raises[sampled_2013_malware_api.csv]
PASSED tests/test_step1_data.py::test_parse_filename_invalid_raises[sampled_2022_benign_api.csv]
PASSED tests/test_step1_data.py::test_parse_filename_invalid_raises[sampled_2015_goodware_api.csv]
PASSED tests/test_step1_data.py::test_parse_filename_invalid_raises[sampled_2015_malware_api.csv.bak]
PASSED tests/test_step1_data.py::test_parse_filename_invalid_raises[sampled_2015_malware.csv]
PASSED tests/test_step1_data.py::test_parse_filename_invalid_raises[notes.csv]
PASSED tests/test_step1_data.py::test_parse_filename_invalid_raises[]
PASSED tests/test_step1_data.py::test_parse_filename_rejects_directory_path
PASSED tests/test_step1_data.py::test_load_file_drops_first_column
PASSED tests/test_step1_data.py::test_load_file_has_1848_features_plus_label_year
PASSED tests/test_step1_data.py::test_load_file_label_and_year_from_filename[sampled_2015_malware_api.csv-1-2015]
PASSED tests/test_step1_data.py::test_load_file_label_and_year_from_filename[sampled_2019_benign_api.csv-0-2019]
PASSED tests/test_step1_data.py::test_load_file_dtypes
PASSED tests/test_step1_data.py::test_load_file_does_not_assume_row_count
PASSED tests/test_step1_data.py::test_load_file_wrong_column_count_raises
PASSED tests/test_step1_data.py::test_load_file_extra_column_raises
PASSED tests/test_step1_data.py::test_load_file_wrong_first_column_raises
PASSED tests/test_step1_data.py::test_load_file_bad_filename_raises
PASSED tests/test_step1_data.py::test_load_file_negative_value_raises
PASSED tests/test_step1_data.py::test_load_file_missing_value_raises
PASSED tests/test_step1_data.py::test_load_file_no_missing_values_on_valid_input
PASSED tests/test_step1_data.py::test_load_file_all_zero_feature_kept
PASSED tests/test_step1_data.py::test_read_apknames_returns_ids_only
PASSED tests/test_step1_data.py::test_list_data_files_returns_16_sorted
PASSED tests/test_step1_data.py::test_list_data_files_stray_csv_raises
PASSED tests/test_step1_data.py::test_list_data_files_missing_file_raises
PASSED tests/test_step1_data.py::test_list_data_files_empty_dir_raises
PASSED tests/test_step1_data.py::test_load_year_combines_both_classes
PASSED tests/test_step1_data.py::test_validate_feature_order_mismatched_order_raises
PASSED tests/test_step1_data.py::test_validate_feature_order_mismatched_names_raises
PASSED tests/test_step1_data.py::test_validate_feature_order_ok
PASSED tests/test_step1_data.py::test_combine_years_mismatched_features_raises
PASSED tests/test_step1_data.py::test_load_all_synthetic_end_to_end
PASSED tests/test_step1_data.py::test_cache_key_changes_when_file_changes
PASSED tests/test_step1_data.py::test_cache_key_changes_with_mtime
PASSED tests/test_step1_data.py::test_train_duplicate_mask_flags_test_row_equal_to_train_row
PASSED tests/test_step1_data.py::test_real_16_files_and_columns
PASSED tests/test_step1_data.py::test_real_year_sizes_labels_and_nan[2014]
PASSED tests/test_step1_data.py::test_real_year_sizes_labels_and_nan[2019]
FAILED tests/test_step1_data.py::test_combine_years_row_count_and_columns - V...
FAILED tests/test_step1_data.py::test_combine_years_labels_balanced_per_year
================== 2 failed, 42 passed, 2 warnings in 18.12s ==================
```

### Run 2: PASSED

- Time: 2026-11-02T09:56:27+02:00
- Commit: 15a3857
- Result: 44 passed, 2 warnings in 5.27s
- Files: test_step1_data.py

```
============================= test session starts =============================
platform win32 -- Python 3.11.4, pytest-9.2.0, pluggy-1.7.0 -- C:\Program Files\Python311\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\thema\OneDrive\Desktop\Project2\project2-harness2\project2-harness2
configfile: pytest.ini
plugins: anyio-4.8.0, dash-2.18.1
collecting ... collected 44 items

tests/test_step1_data.py::test_parse_filename_valid[sampled_2014_malware_api.csv-expected0] PASSED [  2%]
tests/test_step1_data.py::test_parse_filename_valid[sampled_2021_benign_api.csv-expected1] PASSED [  4%]
tests/test_step1_data.py::test_parse_filename_valid[sampled_2017_malware_api.csv-expected2] PASSED [  6%]
tests/test_step1_data.py::test_parse_filename_invalid_raises[sampled_2013_malware_api.csv] PASSED [  9%]
tests/test_step1_data.py::test_parse_filename_invalid_raises[sampled_2022_benign_api.csv] PASSED [ 11%]
tests/test_step1_data.py::test_parse_filename_invalid_raises[sampled_2015_goodware_api.csv] PASSED [ 13%]
tests/test_step1_data.py::test_parse_filename_invalid_raises[sampled_2015_malware_api.csv.bak] PASSED [ 15%]
tests/test_step1_data.py::test_parse_filename_invalid_raises[sampled_2015_malware.csv] PASSED [ 18%]
tests/test_step1_data.py::test_parse_filename_invalid_raises[notes.csv] PASSED [ 20%]
tests/test_step1_data.py::test_parse_filename_invalid_raises[] PASSED    [ 22%]
tests/test_step1_data.py::test_parse_filename_rejects_directory_path PASSED [ 25%]
tests/test_step1_data.py::test_load_file_drops_first_column PASSED       [ 27%]
tests/test_step1_data.py::test_load_file_has_1848_features_plus_label_year PASSED [ 29%]
tests/test_step1_data.py::test_load_file_label_and_year_from_filename[sampled_2015_malware_api.csv-1-2015] PASSED [ 31%]
tests/test_step1_data.py::test_load_file_label_and_year_from_filename[sampled_2019_benign_api.csv-0-2019] PASSED [ 34%]
tests/test_step1_data.py::test_load_file_dtypes PASSED                   [ 36%]
tests/test_step1_data.py::test_load_file_does_not_assume_row_count PASSED [ 38%]
tests/test_step1_data.py::test_load_file_wrong_column_count_raises PASSED [ 40%]
tests/test_step1_data.py::test_load_file_extra_column_raises PASSED      [ 43%]
tests/test_step1_data.py::test_load_file_wrong_first_column_raises PASSED [ 45%]
tests/test_step1_data.py::test_load_file_bad_filename_raises PASSED      [ 47%]
tests/test_step1_data.py::test_load_file_negative_value_raises PASSED    [ 50%]
tests/test_step1_data.py::test_load_file_missing_value_raises PASSED     [ 52%]
tests/test_step1_data.py::test_load_file_no_missing_values_on_valid_input PASSED [ 54%]
tests/test_step1_data.py::test_load_file_all_zero_feature_kept PASSED    [ 56%]
tests/test_step1_data.py::test_read_apknames_returns_ids_only PASSED     [ 59%]
tests/test_step1_data.py::test_list_data_files_returns_16_sorted PASSED  [ 61%]
tests/test_step1_data.py::test_list_data_files_stray_csv_raises PASSED   [ 63%]
tests/test_step1_data.py::test_list_data_files_missing_file_raises PASSED [ 65%]
tests/test_step1_data.py::test_list_data_files_empty_dir_raises PASSED   [ 68%]
tests/test_step1_data.py::test_load_year_combines_both_classes PASSED    [ 70%]
tests/test_step1_data.py::test_validate_feature_order_mismatched_order_raises PASSED [ 72%]
tests/test_step1_data.py::test_validate_feature_order_mismatched_names_raises PASSED [ 75%]
tests/test_step1_data.py::test_validate_feature_order_ok PASSED          [ 77%]
tests/test_step1_data.py::test_combine_years_row_count_and_columns PASSED [ 79%]
tests/test_step1_data.py::test_combine_years_labels_balanced_per_year PASSED [ 81%]
tests/test_step1_data.py::test_combine_years_mismatched_features_raises PASSED [ 84%]
tests/test_step1_data.py::test_load_all_synthetic_end_to_end PASSED      [ 86%]
tests/test_step1_data.py::test_cache_key_changes_when_file_changes PASSED [ 88%]
tests/test_step1_data.py::test_cache_key_changes_with_mtime PASSED       [ 90%]
tests/test_step1_data.py::test_train_duplicate_mask_flags_test_row_equal_to_train_row PASSED [ 93%]
tests/test_step1_data.py::test_real_16_files_and_columns PASSED          [ 95%]
tests/test_step1_data.py::test_real_year_sizes_labels_and_nan[2014] PASSED [ 97%]
tests/test_step1_data.py::test_real_year_sizes_labels_and_nan[2019] PASSED [100%]

============================== warnings summary ===============================
..\..\..\..\..\AppData\Roaming\Python\Python311\site-packages\dash\testing\plugin.py:92
  C:\Users\thema\AppData\Roaming\Python\Python311\site-packages\dash\testing\plugin.py:92: PytestRemovedIn10Warning: The hookimpl pytest_addhooks uses old-style configuration options (marks or attributes).
  Please use the pytest.hookimpl(tryfirst=True) decorator instead
   to configure the hooks.
   See https://docs.pytest.org/en/latest/deprecations.html#configuring-hook-specs-impls-using-markers
    @pytest.mark.tryfirst

tests/test_step1_data.py::test_load_file_missing_value_raises
  C:\Users\thema\AppData\Roaming\Python\Python311\site-packages\pandas\io\parsers\c_parser_wrapper.py:234: RuntimeWarning: invalid value encountered in cast
    chunks = self._reader.read_low_memory(nrows)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=================================== PASSES ====================================
=========================== short test summary info ===========================
PASSED tests/test_step1_data.py::test_parse_filename_valid[sampled_2014_malware_api.csv-expected0]
PASSED tests/test_step1_data.py::test_parse_filename_valid[sampled_2021_benign_api.csv-expected1]
PASSED tests/test_step1_data.py::test_parse_filename_valid[sampled_2017_malware_api.csv-expected2]
PASSED tests/test_step1_data.py::test_parse_filename_invalid_raises[sampled_2013_malware_api.csv]
PASSED tests/test_step1_data.py::test_parse_filename_invalid_raises[sampled_2022_benign_api.csv]
PASSED tests/test_step1_data.py::test_parse_filename_invalid_raises[sampled_2015_goodware_api.csv]
PASSED tests/test_step1_data.py::test_parse_filename_invalid_raises[sampled_2015_malware_api.csv.bak]
PASSED tests/test_step1_data.py::test_parse_filename_invalid_raises[sampled_2015_malware.csv]
PASSED tests/test_step1_data.py::test_parse_filename_invalid_raises[notes.csv]
PASSED tests/test_step1_data.py::test_parse_filename_invalid_raises[]
PASSED tests/test_step1_data.py::test_parse_filename_rejects_directory_path
PASSED tests/test_step1_data.py::test_load_file_drops_first_column
PASSED tests/test_step1_data.py::test_load_file_has_1848_features_plus_label_year
PASSED tests/test_step1_data.py::test_load_file_label_and_year_from_filename[sampled_2015_malware_api.csv-1-2015]
PASSED tests/test_step1_data.py::test_load_file_label_and_year_from_filename[sampled_2019_benign_api.csv-0-2019]
PASSED tests/test_step1_data.py::test_load_file_dtypes
PASSED tests/test_step1_data.py::test_load_file_does_not_assume_row_count
PASSED tests/test_step1_data.py::test_load_file_wrong_column_count_raises
PASSED tests/test_step1_data.py::test_load_file_extra_column_raises
PASSED tests/test_step1_data.py::test_load_file_wrong_first_column_raises
PASSED tests/test_step1_data.py::test_load_file_bad_filename_raises
PASSED tests/test_step1_data.py::test_load_file_negative_value_raises
PASSED tests/test_step1_data.py::test_load_file_missing_value_raises
PASSED tests/test_step1_data.py::test_load_file_no_missing_values_on_valid_input
PASSED tests/test_step1_data.py::test_load_file_all_zero_feature_kept
PASSED tests/test_step1_data.py::test_read_apknames_returns_ids_only
PASSED tests/test_step1_data.py::test_list_data_files_returns_16_sorted
PASSED tests/test_step1_data.py::test_list_data_files_stray_csv_raises
PASSED tests/test_step1_data.py::test_list_data_files_missing_file_raises
PASSED tests/test_step1_data.py::test_list_data_files_empty_dir_raises
PASSED tests/test_step1_data.py::test_load_year_combines_both_classes
PASSED tests/test_step1_data.py::test_validate_feature_order_mismatched_order_raises
PASSED tests/test_step1_data.py::test_validate_feature_order_mismatched_names_raises
PASSED tests/test_step1_data.py::test_validate_feature_order_ok
PASSED tests/test_step1_data.py::test_combine_years_row_count_and_columns
PASSED tests/test_step1_data.py::test_combine_years_labels_balanced_per_year
PASSED tests/test_step1_data.py::test_combine_years_mismatched_features_raises
PASSED tests/test_step1_data.py::test_load_all_synthetic_end_to_end
PASSED tests/test_step1_data.py::test_cache_key_changes_when_file_changes
PASSED tests/test_step1_data.py::test_cache_key_changes_with_mtime
PASSED tests/test_step1_data.py::test_train_duplicate_mask_flags_test_row_equal_to_train_row
PASSED tests/test_step1_data.py::test_real_16_files_and_columns
PASSED tests/test_step1_data.py::test_real_year_sizes_labels_and_nan[2014]
PASSED tests/test_step1_data.py::test_real_year_sizes_labels_and_nan[2019]
======================= 44 passed, 2 warnings in 5.27s ========================
```

### Run 3: PASSED

- Time: 2026-11-02T10:00:57+02:00
- Commit: e43e263
- Result: 44 passed, 2 warnings in 5.21s
- Files: test_step1_data.py

```
============================= test session starts =============================
platform win32 -- Python 3.11.4, pytest-9.2.0, pluggy-1.7.0 -- C:\Program Files\Python311\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\thema\OneDrive\Desktop\Project2\project2-harness2\project2-harness2
configfile: pytest.ini
plugins: anyio-4.8.0, dash-2.18.1
collecting ... collected 44 items

tests/test_step1_data.py::test_parse_filename_valid[sampled_2014_malware_api.csv-expected0] PASSED [  2%]
tests/test_step1_data.py::test_parse_filename_valid[sampled_2021_benign_api.csv-expected1] PASSED [  4%]
tests/test_step1_data.py::test_parse_filename_valid[sampled_2017_malware_api.csv-expected2] PASSED [  6%]
tests/test_step1_data.py::test_parse_filename_invalid_raises[sampled_2013_malware_api.csv] PASSED [  9%]
tests/test_step1_data.py::test_parse_filename_invalid_raises[sampled_2022_benign_api.csv] PASSED [ 11%]
tests/test_step1_data.py::test_parse_filename_invalid_raises[sampled_2015_goodware_api.csv] PASSED [ 13%]
tests/test_step1_data.py::test_parse_filename_invalid_raises[sampled_2015_malware_api.csv.bak] PASSED [ 15%]
tests/test_step1_data.py::test_parse_filename_invalid_raises[sampled_2015_malware.csv] PASSED [ 18%]
tests/test_step1_data.py::test_parse_filename_invalid_raises[notes.csv] PASSED [ 20%]
tests/test_step1_data.py::test_parse_filename_invalid_raises[] PASSED    [ 22%]
tests/test_step1_data.py::test_parse_filename_rejects_directory_path PASSED [ 25%]
tests/test_step1_data.py::test_load_file_drops_first_column PASSED       [ 27%]
tests/test_step1_data.py::test_load_file_has_1848_features_plus_label_year PASSED [ 29%]
tests/test_step1_data.py::test_load_file_label_and_year_from_filename[sampled_2015_malware_api.csv-1-2015] PASSED [ 31%]
tests/test_step1_data.py::test_load_file_label_and_year_from_filename[sampled_2019_benign_api.csv-0-2019] PASSED [ 34%]
tests/test_step1_data.py::test_load_file_dtypes PASSED                   [ 36%]
tests/test_step1_data.py::test_load_file_does_not_assume_row_count PASSED [ 38%]
tests/test_step1_data.py::test_load_file_wrong_column_count_raises PASSED [ 40%]
tests/test_step1_data.py::test_load_file_extra_column_raises PASSED      [ 43%]
tests/test_step1_data.py::test_load_file_wrong_first_column_raises PASSED [ 45%]
tests/test_step1_data.py::test_load_file_bad_filename_raises PASSED      [ 47%]
tests/test_step1_data.py::test_load_file_negative_value_raises PASSED    [ 50%]
tests/test_step1_data.py::test_load_file_missing_value_raises PASSED     [ 52%]
tests/test_step1_data.py::test_load_file_no_missing_values_on_valid_input PASSED [ 54%]
tests/test_step1_data.py::test_load_file_all_zero_feature_kept PASSED    [ 56%]
tests/test_step1_data.py::test_read_apknames_returns_ids_only PASSED     [ 59%]
tests/test_step1_data.py::test_list_data_files_returns_16_sorted PASSED  [ 61%]
tests/test_step1_data.py::test_list_data_files_stray_csv_raises PASSED   [ 63%]
tests/test_step1_data.py::test_list_data_files_missing_file_raises PASSED [ 65%]
tests/test_step1_data.py::test_list_data_files_empty_dir_raises PASSED   [ 68%]
tests/test_step1_data.py::test_load_year_combines_both_classes PASSED    [ 70%]
tests/test_step1_data.py::test_validate_feature_order_mismatched_order_raises PASSED [ 72%]
tests/test_step1_data.py::test_validate_feature_order_mismatched_names_raises PASSED [ 75%]
tests/test_step1_data.py::test_validate_feature_order_ok PASSED          [ 77%]
tests/test_step1_data.py::test_combine_years_row_count_and_columns PASSED [ 79%]
tests/test_step1_data.py::test_combine_years_labels_balanced_per_year PASSED [ 81%]
tests/test_step1_data.py::test_combine_years_mismatched_features_raises PASSED [ 84%]
tests/test_step1_data.py::test_load_all_synthetic_end_to_end PASSED      [ 86%]
tests/test_step1_data.py::test_cache_key_changes_when_file_changes PASSED [ 88%]
tests/test_step1_data.py::test_cache_key_changes_with_mtime PASSED       [ 90%]
tests/test_step1_data.py::test_train_duplicate_mask_flags_test_row_equal_to_train_row PASSED [ 93%]
tests/test_step1_data.py::test_real_16_files_and_columns PASSED          [ 95%]
tests/test_step1_data.py::test_real_year_sizes_labels_and_nan[2014] PASSED [ 97%]
tests/test_step1_data.py::test_real_year_sizes_labels_and_nan[2019] PASSED [100%]

============================== warnings summary ===============================
..\..\..\..\..\AppData\Roaming\Python\Python311\site-packages\dash\testing\plugin.py:92
  C:\Users\thema\AppData\Roaming\Python\Python311\site-packages\dash\testing\plugin.py:92: PytestRemovedIn10Warning: The hookimpl pytest_addhooks uses old-style configuration options (marks or attributes).
  Please use the pytest.hookimpl(tryfirst=True) decorator instead
   to configure the hooks.
   See https://docs.pytest.org/en/latest/deprecations.html#configuring-hook-specs-impls-using-markers
    @pytest.mark.tryfirst

tests/test_step1_data.py::test_load_file_missing_value_raises
  C:\Users\thema\AppData\Roaming\Python\Python311\site-packages\pandas\io\parsers\c_parser_wrapper.py:234: RuntimeWarning: invalid value encountered in cast
    chunks = self._reader.read_low_memory(nrows)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=================================== PASSES ====================================
=========================== short test summary info ===========================
PASSED tests/test_step1_data.py::test_parse_filename_valid[sampled_2014_malware_api.csv-expected0]
PASSED tests/test_step1_data.py::test_parse_filename_valid[sampled_2021_benign_api.csv-expected1]
PASSED tests/test_step1_data.py::test_parse_filename_valid[sampled_2017_malware_api.csv-expected2]
PASSED tests/test_step1_data.py::test_parse_filename_invalid_raises[sampled_2013_malware_api.csv]
PASSED tests/test_step1_data.py::test_parse_filename_invalid_raises[sampled_2022_benign_api.csv]
PASSED tests/test_step1_data.py::test_parse_filename_invalid_raises[sampled_2015_goodware_api.csv]
PASSED tests/test_step1_data.py::test_parse_filename_invalid_raises[sampled_2015_malware_api.csv.bak]
PASSED tests/test_step1_data.py::test_parse_filename_invalid_raises[sampled_2015_malware.csv]
PASSED tests/test_step1_data.py::test_parse_filename_invalid_raises[notes.csv]
PASSED tests/test_step1_data.py::test_parse_filename_invalid_raises[]
PASSED tests/test_step1_data.py::test_parse_filename_rejects_directory_path
PASSED tests/test_step1_data.py::test_load_file_drops_first_column
PASSED tests/test_step1_data.py::test_load_file_has_1848_features_plus_label_year
PASSED tests/test_step1_data.py::test_load_file_label_and_year_from_filename[sampled_2015_malware_api.csv-1-2015]
PASSED tests/test_step1_data.py::test_load_file_label_and_year_from_filename[sampled_2019_benign_api.csv-0-2019]
PASSED tests/test_step1_data.py::test_load_file_dtypes
PASSED tests/test_step1_data.py::test_load_file_does_not_assume_row_count
PASSED tests/test_step1_data.py::test_load_file_wrong_column_count_raises
PASSED tests/test_step1_data.py::test_load_file_extra_column_raises
PASSED tests/test_step1_data.py::test_load_file_wrong_first_column_raises
PASSED tests/test_step1_data.py::test_load_file_bad_filename_raises
PASSED tests/test_step1_data.py::test_load_file_negative_value_raises
PASSED tests/test_step1_data.py::test_load_file_missing_value_raises
PASSED tests/test_step1_data.py::test_load_file_no_missing_values_on_valid_input
PASSED tests/test_step1_data.py::test_load_file_all_zero_feature_kept
PASSED tests/test_step1_data.py::test_read_apknames_returns_ids_only
PASSED tests/test_step1_data.py::test_list_data_files_returns_16_sorted
PASSED tests/test_step1_data.py::test_list_data_files_stray_csv_raises
PASSED tests/test_step1_data.py::test_list_data_files_missing_file_raises
PASSED tests/test_step1_data.py::test_list_data_files_empty_dir_raises
PASSED tests/test_step1_data.py::test_load_year_combines_both_classes
PASSED tests/test_step1_data.py::test_validate_feature_order_mismatched_order_raises
PASSED tests/test_step1_data.py::test_validate_feature_order_mismatched_names_raises
PASSED tests/test_step1_data.py::test_validate_feature_order_ok
PASSED tests/test_step1_data.py::test_combine_years_row_count_and_columns
PASSED tests/test_step1_data.py::test_combine_years_labels_balanced_per_year
PASSED tests/test_step1_data.py::test_combine_years_mismatched_features_raises
PASSED tests/test_step1_data.py::test_load_all_synthetic_end_to_end
PASSED tests/test_step1_data.py::test_cache_key_changes_when_file_changes
PASSED tests/test_step1_data.py::test_cache_key_changes_with_mtime
PASSED tests/test_step1_data.py::test_train_duplicate_mask_flags_test_row_equal_to_train_row
PASSED tests/test_step1_data.py::test_real_16_files_and_columns
PASSED tests/test_step1_data.py::test_real_year_sizes_labels_and_nan[2014]
PASSED tests/test_step1_data.py::test_real_year_sizes_labels_and_nan[2019]
======================= 44 passed, 2 warnings in 5.21s ========================
```
