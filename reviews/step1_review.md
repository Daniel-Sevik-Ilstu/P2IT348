# Step 1 Review: Prepare the Data

- Reviewer transcript: transcripts/05_2026-11-02_reviewer_step1.md
- What was reviewed: the diff from step1-start to the latest commit (.harness/diffs/step1_diff.patch), with PLAN.md and AGENTS.md for context

## Comments (reviewer)

One row per issue. Number the rows 1, 2, 3, ...

| # | Severity | Location | Issue | Suggested fix |
| --- | --- | --- | --- | --- |
| 1 | Medium | src/data.py `summarize_data`, `train_duplicate_mask`, `_row_hashes` | Duplicates are found by feature vector only, ignoring the label. I ran a read-only check on the real data: 107 feature vectors occur with both label 0 and label 1, covering 13,719 of 99,000 rows. The audit (and the PLAN sensitivity mask) never mentions these. They cap achievable accuracy and make a test row "duplicated in training" with the opposite label. | Add a count of label-conflicting vectors (rows and vectors) per year to the summary, and mention it in the Step 1 report. No need to drop rows (PLAN keeps all). |
| 2 | Medium | src/data.py `_check_header` / `read_header` | The duplicate-column-name check is dead code. `pd.read_csv(nrows=0).columns` already renames duplicates (I ran it on a temp file: header `apkname,f,f,g` returned `['apkname','f','f.1','g']`), so `len(set(header)) != len(header)` can never be true. A real duplicated API name would pass silently as a different feature. | Read the header with the `csv` module (`next(csv.reader(f))`) so raw names are checked, or compare against the expected names from the first file. Add a test with a duplicated header. |
| 3 | Medium | src/data.py `load_file` | A CSV with a valid header but zero rows loads without error (I checked: shape `(0, 1850)`). Also nothing checks that a file has any rows, so a truncated file would be accepted. AGENTS.md says not to assume a row count, but an empty or very short file should still fail loudly. | Raise `ValueError` if `len(df) == 0`. Optionally warn when the two files of a year differ in row count (all 8 years are equal today). |
| 4 | Medium | src/data.py `_read_cache` | A corrupt or truncated cache file crashes instead of rebuilding. I wrote a bad `.npz` and `_read_cache` raised `zipfile.BadZipFile`, which is not caught (only `OSError, ValueError, KeyError`; `EOFError` is also possible). This contradicts the docstring/PLAN ("failed check rebuilds from the CSVs"). | Also catch `zipfile.BadZipFile` and `EOFError` (or `Exception` with a logged message) and return None. |
| 5 | Low | src/data.py `check_schema` (cache path) | On a cache hit the checks do not confirm that `label` is in {0,1}, `year` is in 2014-2021, or that X, label and year have the same length (a mismatch gives NaN rows via `pd.concat(axis=1)`). The PLAN says the schema checks rerun on load; these are the parts that matter for labels and year grouping. | In `check_schema` add: `df[LABEL_COL].isin([0,1]).all()`, `df[YEAR_COL].isin(ALL_YEARS).all()`, and no NaN. Check lengths in `_read_cache`. |
| 6 | Low | src/main.py `main` | `--step N` for N=2..7 prints "not implemented yet" and returns exit code 0, so a caller or the harness cannot tell nothing ran. This is a silent pass on a request that was not carried out. | Return a non-zero code (or raise `NotImplementedError`) until the step exists. |
| 7 | Low | src/main.py `run_step1` | `n_features = df.shape[1] - 2` hard-codes the label+year count instead of using `feature_columns(df)`. Works now but breaks if another metadata column is added. Style-level. | Use `len(feature_columns(df))`. |
| 8 | Low | src/data.py `list_data_files` | Files starting with `._` are silently skipped. PLAN.md says every stray CSV raises. The exception is reasonable (macOS archive junk) but is not in PLAN.md, and it also hides a misnamed file that begins with `._`. | Keep it, but document it in PLAN/the Step 1 report, or raise a warning listing the skipped files. |
| 9 | Low | src/data.py `_to_markdown` | The nested conditional expression for cell formatting is hard to read. Also `f"{v:.4f}"` prints a very small non-zero share as `0.0000`, and a float that happens to be whole prints as an int. Style preference plus a minor precision loss; the CSV is unaffected. | Replace with a small helper `_fmt(v)`; use `.4g` or more digits for shares. |
| 10 | Low | src/data.py `load_year`, `cache_key`, `load_all` | `list_data_files` (a directory scan plus 16 filename parses) is called once per year in `load_year` and again in `cache_key` and `load_all`, and `summarize_data` re-reads the first column of every file. Not a bug and cheap at 16 files; efficiency/style only. | Optionally pass the already-listed files into `load_year` and `cache_key`. |

Checks against the specific questions asked (no issue found):
- First column: `load_file` checks the header has 1,849 columns with `apkname` first, then reads with `usecols=range(1, 1849)`, so `apkname` is never loaded into a feature frame. `read_apknames` reads it separately for the audit only.
- Labels: `parse_filename` maps malware to 1 and benign to 0 via an anchored regex; year and class come only from the file name; bad names, paths and years outside 2014-2021 raise.
- Coverage: `list_data_files` requires exactly one malware and one benign file for each of 2014-2021 (16 files); `load_all` loads each year by parsing the year from the name. Result tables show 2 files per year.
- Counts: 1,849 columns before the drop and 1,848 after are enforced. Row counts are not asserted (as AGENTS.md says); the results show 9,000 rows per file for 2014-2018 and 1,500 for 2019-2021, not 1,500 everywhere as ASSIGNMENT.md says (known; the summary reports the real counts).
- Leakage: nothing in Step 1 is fit on data. `train_duplicate_mask` and the earlier-year audit are descriptive only.
- What I ran (read-only, temp files only): a small script that called `read_header` on a duplicate-header CSV, `_read_cache` on a corrupt file, `load_file` on a header-only CSV, and `load_all()` followed by a hash-based label-conflict count. I did not run the tests (not allowed to open tests/).

## Decision log (student)

One row per comment above, with the same number. Decision is Accepted or Rejected. For accepted comments, add the commit that fixed it.

| # | Decision | Reason | Fixed in commit |
| --- | --- | --- | --- |
| 1 | Accepted | Feature vectors that appear with both labels cap achievable accuracy and make a duplicated test row carry the opposite label. Add a per-year count of label-conflicting vectors and rows to the summary and the Step 1 report. Do not drop any rows. | |
| 2 | Accepted | The duplicate-column-name check can never fire because pandas renames duplicates. Read the raw header with the csv module so a real duplicate is caught, and add a duplicated-header test. | |
| 3 | Accepted | A header-only or truncated file must fail loudly. Raise ValueError when a file has zero rows. Skip the optional warning about differing row counts. | |
| 4 | Accepted | The docstring and PLAN say a failed cache check rebuilds from the CSVs. Catch zipfile.BadZipFile and EOFError in _read_cache so a corrupt cache rebuilds instead of crashing. | |
| 5 | Accepted | Labels and year grouping depend on these. On cache load check label is in 0 and 1, year is in 2014 to 2021, there are no NaN values, and X, label and year have equal length. | |
| 6 | Accepted | Exiting with code 0 for steps that are not built hides that nothing ran. Return a non-zero exit code for steps not yet implemented. | |
| 7 | Accepted | Trivial and safe: use len(feature_columns(df)) instead of the hard-coded minus 2. | |
| 8 | Rejected | Skipping files that start with ._ was my explicit instruction to the builder: they are macOS archive junk from the zip, not data. A real misnamed data file starting with ._ is not plausible. Keeping the code unchanged, one sentence in the report is enough. | — |
| 9 | Rejected | Only the Markdown display is affected, and the CSV holds the full-precision values and is the source of truth. This is a style preference and would cause churn in a working function. | — |
| 10 | Rejected | Efficiency only, with no bug. 16 filename parses are negligible, and changing function signatures now risks breaking the tester's tests for no benefit. | — |
