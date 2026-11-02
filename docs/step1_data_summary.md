# Step 1 Report: Prepare the Data

Written by the builder agent. All numbers below come from running `python -m src.main --step 1` on the real files in `input_data/` (tables also in `results/step1_data_summary.csv` and `results/step1_file_table.csv`). Code: `src/data.py`, `src/config.py`, `src/main.py`.

## What was done

1. `list_data_files` lists every `*.csv` in `input_data/` (names starting with `._` are skipped as macOS resource-fork files from the zip, not data; this is a deliberate rule), runs `parse_filename` on each, and raises if any other CSV does not match `sampled_<YEAR>_<malware|benign>_api.csv`, or if the 16 year/class files are not all present exactly once.
2. `load_file` reads the header, checks the raw header (read with the `csv` module, so duplicated names are caught) has 1,849 unique columns and that column 0 is `apkname`, then drops column 0 by position (`usecols`) and reads the 1,848 features as `int32`. Missing, non-integer or negative values raise, and so does a file with no data rows. No row count is assumed.
3. `label` (int8; malware = 1, benign = 0) and `year` (int16) come only from the file name.
4. `load_year` and `combine_years` concatenate the files, after checking every file has the same feature columns in the same order.
5. `load_all` caches the combined frame in the git-ignored `cache/` folder, keyed on file names, sizes, mtimes and `CACHE_SCHEMA_VERSION`. The feature column names are stored in the cache, and the schema check is rerun against the CSV header on every cache load (also: `label` in {0,1}, `year` in 2014-2021, no NaN, equal lengths). A corrupt or truncated cache file is ignored and rebuilt from the CSVs.

## Files loaded

16 files: one malware and one benign file for each year 2014-2021 (2 files per year). No stray files were found. Every file has 1,849 columns in the CSV, i.e. 1,848 after dropping `apkname`, and the feature names and order are identical in all 16 files.

| file | year | class | rows | columns after drop |
|---|---|---|---|---|
| sampled_2014_benign_api.csv | 2014 | benign | 9000 | 1848 |
| sampled_2014_malware_api.csv | 2014 | malware | 9000 | 1848 |
| sampled_2015_benign_api.csv | 2015 | benign | 9000 | 1848 |
| sampled_2015_malware_api.csv | 2015 | malware | 9000 | 1848 |
| sampled_2016_benign_api.csv | 2016 | benign | 9000 | 1848 |
| sampled_2016_malware_api.csv | 2016 | malware | 9000 | 1848 |
| sampled_2017_benign_api.csv | 2017 | benign | 9000 | 1848 |
| sampled_2017_malware_api.csv | 2017 | malware | 9000 | 1848 |
| sampled_2018_benign_api.csv | 2018 | benign | 9000 | 1848 |
| sampled_2018_malware_api.csv | 2018 | malware | 9000 | 1848 |
| sampled_2019_benign_api.csv | 2019 | benign | 1500 | 1848 |
| sampled_2019_malware_api.csv | 2019 | malware | 1500 | 1848 |
| sampled_2020_benign_api.csv | 2020 | benign | 1500 | 1848 |
| sampled_2020_malware_api.csv | 2020 | malware | 1500 | 1848 |
| sampled_2021_benign_api.csv | 2021 | benign | 1500 | 1848 |
| sampled_2021_malware_api.csv | 2021 | malware | 1500 | 1848 |

## Shape after dropping the first column

The lead engineer's expectation is confirmed: 9,000 rows per file for 2014-2018 and 1,500 rows per file for 2019-2021. The combined frame is **99,000 rows x 1,850 columns** (1,848 features + `label` + `year`), 732 MB in memory (features `int32`). Loading from the CSVs took about 8 s; loading from the cache about 1 s.

## Class counts per year

| year | malware | goodware | total |
|---|---|---|---|
| 2014 | 9000 | 9000 | 18000 |
| 2015 | 9000 | 9000 | 18000 |
| 2016 | 9000 | 9000 | 18000 |
| 2017 | 9000 | 9000 | 18000 |
| 2018 | 9000 | 9000 | 18000 |
| 2019 | 1500 | 1500 | 3000 |
| 2020 | 1500 | 1500 | 3000 |
| 2021 | 1500 | 1500 | 3000 |
| **all** | **49500** | **49500** | **99000** |

Every year is exactly balanced between malware and goodware.

## Issues found

**1. Row counts differ from ASSIGNMENT.md.** ASSIGNMENT.md says each file has 1,500 rows. Only the 2019-2021 files do; the 2014-2018 files have 9,000 rows each. So the total is 99,000 rows, not 16 x 1,500 = 24,000 (and not exactly the "about 100,000" in AGENTS.md). Years 2014-2018 are 6x larger than 2019-2021, so any pooled metric over 2017-2021 is dominated by 2017 and 2018.

**2. Duplicate rows, repeated apknames and all-zero columns per year.** Duplicates and repeated apknames are kept (no rows removed). "Duplicate rows" counts rows whose 1,848-value feature vector already appeared earlier in the same year (both classes pooled); "repeated apknames" counts rows whose apkname already appeared earlier in the same year; "all-zero columns" counts features that are 0 in every row of the year.

| year | rows | duplicate rows | % duplicate | repeated apknames | all-zero columns |
|---|---|---|---|---|---|
| 2014 | 18000 | 7291 | 40.5% | 4012 | 868 |
| 2015 | 18000 | 7846 | 43.6% | 3975 | 838 |
| 2016 | 18000 | 8496 | 47.2% | 4689 | 814 |
| 2017 | 18000 | 11970 | 66.5% | 5080 | 859 |
| 2018 | 18000 | 13138 | 73.0% | 6212 | 810 |
| 2019 | 3000 | 1741 | 58.0% | 232 | 850 |
| 2020 | 3000 | 1845 | 61.5% | 126 | 916 |
| 2021 | 3000 | 1831 | 61.0% | 382 | 858 |

Duplicate feature vectors are common in every year (40-73% of rows), not only in 2014-2018 as AGENTS.md suggested; the 2019-2021 files have many duplicate vectors but few repeated apknames. Two checks I ran independently with plain pandas (`DataFrame.duplicated`, `Series.duplicated`, column sums) on 2014 and 2019 gave the same numbers as the table (7,291 / 4,012 / 868 and 1,741 / 232 / 850). The row hash used for the cross-year counts is a 64-bit pandas hash, so a collision is possible in principle but unlikely at this size; the within-year counts above were confirmed with exact comparison for 2014 and 2019 only.

**3. Overlap with the training years (feeds the Step 5/6 sensitivity row).** Number of rows in each test year whose exact feature vector also occurs in a 2014-2016 row (`train_duplicate_mask`), and, for all years, rows whose vector occurs in any earlier year:

| year | rows | rows with a duplicate in 2014-2016 | share | rows with a duplicate in any earlier year |
|---|---|---|---|---|
| 2014 | 18000 | n/a (training) | n/a | 0 |
| 2015 | 18000 | n/a (training) | n/a | 622 |
| 2016 | 18000 | n/a (training) | n/a | 1827 |
| 2017 | 18000 | 5972 | 33.2% | 5972 |
| 2018 | 18000 | 1645 | 9.1% | 3866 |
| 2019 | 3000 | 57 | 1.9% | 391 |
| 2020 | 3000 | 67 | 2.2% | 1246 |
| 2021 | 3000 | 2 | 0.1% | 1461 |

A third of the 2017 test rows are exact copies of a training row, which makes 2017 look easier than it is. The overlap falls with distance from the training years. 
**3b. Label conflicts (review comment 1).** Some feature vectors occur with both labels. Per year (within the year), distinct conflicting vectors and the rows that carry them:

| year | rows | conflicting vectors | rows in conflict | % of rows |
|---|---|---|---|---|
| 2014 | 18000 | 8 | 282 | 1.6% |
| 2015 | 18000 | 11 | 431 | 2.4% |
| 2016 | 18000 | 9 | 666 | 3.7% |
| 2017 | 18000 | 12 | 1814 | 10.1% |
| 2018 | 18000 | 48 | 6577 | 36.5% |
| 2019 | 3000 | 3 | 79 | 2.6% |
| 2020 | 3000 | 8 | 116 | 3.9% |
| 2021 | 3000 | 5 | 517 | 17.2% |

With all years pooled, 107 distinct vectors occur with both labels, covering 13,719 of the 99,000 rows (13.9%). Those rows cannot all be classified correctly by any model that uses these features, and a test row equal to a training row can carry the opposite label. No rows were dropped. (The per-year figures are within-year; the pooled figure also counts conflicts across years. The pooled count matches the reviewer's independent check.)

**4. All-zero columns.** Between 810 and 916 of the 1,848 features are all-zero within a single year (about 44-50%), consistent with the 850-1,125 per file in AGENTS.md. These are per-year counts; I did not count columns that are all-zero across all 99,000 rows.

## Not done / limits

- I wrote no tests (the tester agent owns `tests/`). After the review fixes, `python harness.py test all` gives 42 passed, 2 failed; the 2 failures (`test_combine_years_row_count_and_columns`, `test_combine_years_labels_balanced_per_year`) build a two-year folder, which `list_data_files` rejects by design. The student rejected them as test errors, so `src/` was not changed for them.
- `src/main.py` only implements Step 1 so far; `--step 2..7` prints "not implemented yet" to stderr and exits with code 1.
- Cache: I observed the plain build (about 8-9 s), the cache hit (about 1 s, frame equal to the fresh build), and rejection of a cache whose feature names were altered (swapped two names in a copy; `load_all` rebuilt from the CSVs and the next call hit the new cache). Rebuild after touching a CSV (changed mtime) was not exercised on the real files.
