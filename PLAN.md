# PLAN.md: Project 2 plan (Steps 1-7)

Author: builder agent. Status: initial version (Step 0), before review.
Data facts used here come from AGENTS.md. Nothing in this plan has been run yet; no result is claimed.

## 0. Global decisions

### Train/test split by year

| Role | Years | Use |
|---|---|---|
| Train | 2014, 2015, 2016 | fit preprocessing and models |
| Tuning (only if needed) | train on 2014-2015, validate on 2016 | choose hyperparameters; then refit on 2014-2016 |
| Test | 2017, 2018, 2019, 2020, 2021 | evaluation only; every metric is reported pooled AND per year |

### How leakage between years is prevented

1. One function `check_no_overlap(train_years, test_years)` (in `src/preprocess.py`) raises `ValueError` if either set is empty, if the sets intersect, or if `max(train_years) >= min(test_years)` (training years must all precede test years). Every train/predict call in Steps 3-7 goes through it.
   - **Exemption (Step 2).** `concept_drift_matrix` in `src/drift.py` is diagnostic: it fits a scaler and a model on each single year (including 2017-2021) and predicts other years, so it does not obey the train-2014-2016 rule or `check_no_overlap`. Nothing it produces feeds Steps 3-7 (no features, hyperparameters or split choices). The leakage tests skip `drift.py`; they apply to Steps 3-7 only.
2. Every fitted object (zero-column mask, `StandardScaler`, classifiers) is fit on the training rows only. Test rows are only passed to `transform` / `predict`. `log1p` is stateless, so it cannot leak.
3. Tuning never touches 2017-2021.
4. Step 7: year t is predicted before it is used for training (see Step 7). Expanding/sliding windows refit preprocessing on the window only.
5. Cross-year duplicates: the 2014-2018 files have many duplicate rows and repeated apknames. Step 1 reports (a) exact duplicate feature rows within a year and (b) apknames or identical feature vectors shared between a training year and a test year. I keep all rows by default (AGENTS.md); no rows are removed from the main results. Step 1 reports, per test year, the count and share of test rows whose exact feature vector also occurs in the training years (2014-2016). Steps 5 and 6 add a sensitivity row (`subset = "no_train_duplicate"`) with metrics on only the test rows that have no exact duplicate in the training years, and state in the report how many test rows were excluded.
6. Step 2 (KS tests, accuracy matrix) is descriptive. Its output is never used to select features, hyperparameters or the split.

### Conventions (from AGENTS.md)
random_state=42; features as float32/int32; pathlib paths relative to the repo root; docstrings and type hints on every function; one module per concern; cache in the git-ignored `cache/` folder (see `load_all` in Step 1 for the cache rules); small commits tagged `[builder]`.

### Shared constants (`src/config.py`)
`ROOT`, `DATA_DIR`, `RESULTS_DIR`, `DOCS_DIR`, `SEED = 42`, `MIN_SUPPORT = 10`, `CACHE_DIR`, `CACHE_SCHEMA_VERSION`, `TRAIN_YEARS = (2014, 2015, 2016)`, `TEST_YEARS = (2017, ..., 2021)`, `TUNE_TRAIN_YEARS = (2014, 2015)`, `TUNE_VAL_YEAR = 2016`, `N_RAW_COLUMNS = 1849`, `LABEL_COL = "label"`, `YEAR_COL = "year"`.

### Entry point (`src/main.py`)
`main(argv: list[str] | None = None) -> int`. `python -m src.main` runs Steps 1-7 in order; `--step N` (1-7) runs one step (running it first runs any earlier step it needs, using the cache). Prints a short summary, writes `results/`. Target: under about 15 minutes in total (see runtime notes per step).

---

## Changes after review

Source: `reviews/step0_plan_review.md` (Decision log). Comment 10 was Rejected and is not applied.

| Comment | Change in PLAN.md |
|---|---|
| 1 | SGD no longer uses `class_weight` (rejected by `partial_fit`); test must call `partial_fit` on `build_model("sgd")`. |
| 2 | Section 0: explicit exemption; `concept_drift_matrix` fits on single years, leakage tests skip `drift.py`. |
| 3 | `MIN_SUPPORT = 10`: keep columns non-zero in at least 10 training rows; documented in step 3 report; near-constant column test. |
| 4 | Step 1 reports test rows duplicated in 2014-2016 (`train_duplicate_mask`); Steps 5 and 6 add a no-duplicate sensitivity row; main results keep all rows. |
| 5 | `check_no_overlap` also requires `max(train_years) < min(test_years)`; Step 2 matrix exempt. |
| 6 | Cache keyed on file names, sizes, mtimes and schema version; column names stored; schema checks rerun on load; stored in git-ignored `cache/`. |
| 7 | `train_all_from_split` moved into the Step 4 function list; Step 7 guard is `window_years` plus `check_no_overlap`. |
| 8 | Step 7 report notes the row-count imbalance and lists each window's year composition. No equal-rows variant. |
| 9 | Step 2 report caveat: duplicates and ties inflate KS p-values; effect size is the main signal. |
| 11 | `list_data_files` runs `parse_filename` on every CSV so stray files raise; stray-file test added. |

---

## Step 1: Prepare the data (`src/data.py`)

**Approach.** Read the 16 CSVs, take year and class only from the file name, drop `apkname`, add `label` (malware=1, benign=0) and `year`, validate the schema, and combine.

**Functions.**
- `parse_filename(name: str) -> tuple[int, int]`: regex `^sampled_(\d{4})_(malware|benign)_api\.csv$` on the base name; returns `(year, label)`. Raises `ValueError` on any other name, a year outside 2014-2021, or a bad class.
- `list_data_files(data_dir: Path = DATA_DIR) -> list[Path]`: lists every `*.csv` in `data_dir` and runs `parse_filename` on each, so a stray or misnamed CSV raises `ValueError` (not ignored). Returns the sorted list; also raises if there is not exactly one malware and one benign file for each of 2014-2021 (16 files).
- `load_file(path: Path) -> pd.DataFrame`: reads the CSV, checks the shape is `(n, 1849)` and the first column is `apkname`, drops it, casts the 1,848 features to int32, appends `label` (int8) and `year` (int16) from `parse_filename`. Raises `ValueError` if the column count is not 1,849 or any value is negative or missing. Does not assert a row count.
- `read_apknames(path: Path) -> pd.Series`: the `apkname` column only (for the duplicate/overlap audit; never used as a feature).
- `load_year(year: int, data_dir: Path = DATA_DIR) -> pd.DataFrame`: concatenates that year's malware and benign files.
- `validate_feature_order(frames: list[pd.DataFrame]) -> None`: raises if any frame's feature columns differ from the first one in names or order.
- `combine_years(frames: dict[int, pd.DataFrame]) -> pd.DataFrame`: concatenates years in order (calls `validate_feature_order`); `ignore_index=True`.
- `load_all(data_dir: Path = DATA_DIR, use_cache: bool = True) -> pd.DataFrame`: the whole dataset (~100,000 x 1,850 incl. label, year). Cache rules: stored in `cache/` (git-ignored; `CACHE_DIR` in `src/config.py`). The cache key is a hash of each CSV's file name, size and mtime plus `CACHE_SCHEMA_VERSION` (a constant bumped whenever `src/data.py` changes how data is built). The cache file holds the feature column names with the arrays; on every cache load the schema checks run again (1,848 feature columns in the stored order, `label`/`year` present, no negatives). A key mismatch or failed check rebuilds from the CSVs. If this proves complicated, the cache is dropped rather than weakened.
- `cache_key(data_dir: Path) -> str`: the hash described above (used by `load_all`).
- `feature_columns(df: pd.DataFrame) -> list[str]`: all columns except `label` and `year` (1,848 names).
- `summarize_data(df: pd.DataFrame, data_dir: Path = DATA_DIR) -> pd.DataFrame`: one row per year: files loaded, rows, feature columns, malware count, benign count, exact duplicate rows, all-zero feature columns, apknames repeated within the year, and the number of rows in the year whose feature vector also occurs in an earlier year, and (test years) the number and share of rows whose feature vector occurs in 2014-2016.
- `train_duplicate_mask(df: pd.DataFrame, train_years=TRAIN_YEARS) -> np.ndarray`: boolean mask over all rows of `df`, True where the row's exact feature vector also occurs in a training-year row (for training-year rows themselves it is not used). Used by Steps 1, 5 and 6.
- `write_data_summary(summary: pd.DataFrame, path: Path) -> None`: Markdown + CSV.

**Report.** `docs/step1_data_summary.md`: files per year, real row counts (not 1,500), 1,849 raw columns and 1,848 features after dropping `apkname`, malware/benign counts per year, duplicate/overlap audit, dtype and memory use. Table also saved to `results/step1_data_summary.csv`.

**Testing.** Synthetic CSVs in `tmp_path`: `parse_filename` accepts valid names and rejects bad ones (wrong year, wrong class, extra suffix, path with directories); `load_file` drops the first column, gives 1,848 features, correct label from name, wrong column count raises; mismatched feature order raises; `combine_years` row count equals the sum of inputs; label and year columns are right. `list_data_files` raises on a stray CSV (e.g. `notes.csv`) in the folder and on a missing or duplicated year/class file. Cache: `cache_key` changes when a file's size or mtime changes or the schema version changes; a second `load_all` returns an equal frame; touching a CSV forces a rebuild; a cache with altered column names or order is rejected. Integration test (skipped if `input_data/` is absent): 16 files, 1,849 raw columns each, 18,000 rows per year for 2014-2018 and 3,000 for 2019-2021, equal malware and benign counts, no NaN.

---

## Step 2: Handle data drift (`src/drift.py`)

**Approach.** Measure feature drift with the two-sample Kolmogorov-Smirnov test, and check concept drift with a train-on-year-i / test-on-year-j accuracy matrix.

**Sampling.** Every year is subsampled to the same size `n = min(rows per year)` (3,000 with the current data; computed, not hard-coded), using `random_state=42`, stratified so each sample has equal malware and benign counts. Both classes are pooled per year, so drift here includes any change in the malware/goodware mix inside a year; the balanced sampling removes that source.

**Functions.**
- `subsample_years(df, n: int | None = None, seed: int = SEED) -> dict[int, pd.DataFrame]`: equal-size, class-balanced sample per year; `n=None` uses the smallest year.
- `ks_feature_table(a: pd.DataFrame, b: pd.DataFrame, features: list[str]) -> pd.DataFrame`: runs `scipy.stats.ks_2samp` on each feature; returns columns `feature, ks_stat, p_value, skipped`. A feature constant in both samples (same single value) is marked `skipped` (NaN stat/p) and counted, not tested.
- `ks_all_pairs(samples, features)` runs KS once for all 28 year pairs; `ks_year_pairs(pairs, mode)` summarises them. `mode="all"` (every pair, shown as a year x year matrix), `mode="vs_2014"` (each year 2015-2021 vs 2014) or `mode="consecutive"` (year vs previous year). Returns one row per pair: `year_a, year_b, n_tested, n_skipped, mean_ks, share_significant`.
- `bonferroni_significant(p_values: np.ndarray, alpha: float = 0.05) -> np.ndarray`: boolean mask with `p < alpha / m`, `m` = number of tested (non-skipped) features.
- `top_drifting_features(samples, features, k: int = 20) -> pd.DataFrame`: top-k features by mean KS statistic across the "vs 2014" comparisons (also lists the per-year KS for each).
- `most_different_years(pair_table: pd.DataFrame) -> pd.DataFrame`: pairs ranked by mean KS.
- `concept_drift_matrix(samples: dict[int, pd.DataFrame], features, seed: int = SEED) -> pd.DataFrame`: for each year i, fit log1p + StandardScaler + `LogisticRegression(max_iter=1000, random_state=42)` on year i's sample only (scaler fit on that year only), compute accuracy on every year j's sample (i==j uses a held-out 30% split of that year, so the diagonal is not training accuracy). Returns an 8x8 accuracy DataFrame.
- `run_drift_analysis(df) -> dict[str, pd.DataFrame]`: runs the above and writes `results/step2_ks_vs_2014.csv`, `step2_ks_consecutive.csv`, `step2_top20_features.csv`, `step2_accuracy_matrix.csv` and optional PNG heatmaps.

**Runtime.** 7 + 7 year pairs x ~1,800 `ks_2samp` calls on 3,000 points is well under a minute.

**Caveat to state in the report.** With 3,000 samples per year the KS test is very sensitive, so most features may be "significant" after Bonferroni; the mean KS statistic (effect size) is the more useful number. Features all-zero in both samples are skipped and reported as a count. Duplicate rows (many in 2014-2018) and heavily tied count data mean the samples are not independent, so KS p-values and "share significant" are inflated; the KS statistic (effect size) is the main signal. The subsampling is unchanged.

**Report.** `docs/step2_drift_analysis.md`: method, sample size, skipped counts, table of mean KS and share significant per pair, top-20 drifting features (Dalvik signatures), which years differ most, the accuracy matrix and what it says about concept drift.

**Testing.** Synthetic: identical samples give KS 0 and none significant; a shifted feature gives a high KS and is flagged; constant-in-both features are skipped and counted; `bonferroni_significant` uses `alpha / m` with `m` excluding skipped features (hand-computed case); `subsample_years` gives equal sizes, is reproducible with seed 42 and is class balanced; matrix is square and indexed by years; top-k returns k rows sorted descending. Real data (skipped if absent): the result tables have 7 rows each.

---

## Step 3: Preprocess (`src/preprocess.py`)

**Approach.** `log1p` to tame the heavy tail (counts up to ~92,000), drop features that are non-zero in fewer than `MIN_SUPPORT = 10` training rows (this includes all-zero columns), then `StandardScaler` fit on training years only, then clip the scaled values to a fixed ±`Z_CLIP = 10` (a constant, identical for train and test, nothing learned from any data). Output float32. The minimum-support filter removes the worst near-constant columns, but it does not stop extreme z-scores on drifted test years (measured: max abs z 212.7 in 2018, 150.6 in training), so the clip is what bounds them. **Changed after review comment 1** (the filter alone does not meet its stated purpose).

**Functions.**
- `check_no_overlap(train_years: Iterable[int], test_years: Iterable[int]) -> None`: raises `ValueError` if they share a year, if either is empty, or if `max(train_years) >= min(test_years)`. Not called by Step 2's `concept_drift_matrix` (exempt, see section 0).
- `split_by_year(df, train_years, test_years) -> tuple[pd.DataFrame, pd.DataFrame]`: calls `check_no_overlap`, returns the train and test frames (rows selected by `year`).
- `apply_log1p(X: np.ndarray) -> np.ndarray`: `np.log1p` as float32; raises on negative input.
- `nonzero_feature_mask(X_train: np.ndarray, min_support: int = MIN_SUPPORT) -> np.ndarray`: boolean mask of columns with at least `min_support` (10) non-zero values in the training rows only. `MIN_SUPPORT = 10` is added to `src/config.py`.
- `class Preprocessor` (sklearn-like fit/transform, not a `BaseEstimator`): `fit(X_train_raw: np.ndarray) -> Preprocessor` (applies log1p, learns the mask, fits `StandardScaler`), `transform(X_raw: np.ndarray, clip: bool = True) -> np.ndarray` (log1p, mask, scale, clip to ±`Z_CLIP`; `clip=False` only for reporting), `fit_transform`, attribute `kept_features_` (names/indices). Raises if `transform` is called before `fit`.
- `prepare_split(df, train_years, test_years) -> dict`: returns `X_train, y_train, years_train, X_test, y_test, years_test, preprocessor`; the preprocessor is fit on the training rows only.
- `make_tuning_split(df) -> dict`: same, with train 2014-2015 and validate 2016.

**Decision flagged.** Dropping all-zero training columns is only a size reduction (such columns have zero variance and no information in training). Dropping columns with 1-9 non-zero training rows is a deliberate extra filter (support below 10), chosen because a tiny training std turns ordinary test values into z-scores in the hundreds. A column that is non-zero only in a later year is lost for the static model. That loss is real drift and is reported (count of columns active in test years but dropped). Step 7 refits the mask on each window, which recovers them.

**Report.** `docs/step3_preprocessing.md`: log1p and why, number of columns dropped (split into all-zero and low-support 1-9 rows), the minimum-support rule (`MIN_SUPPORT = 10`, training rows only) and why, scaler details, the split table above, and the five leakage rules.

**Testing.** Synthetic: scaler mean/std come from training rows only (train mean ~0, std ~1; test is not centred on its own mean); the mask comes from training only (a column non-zero only in a test row is dropped); near-constant column: a column non-zero in 9 training rows is dropped and one non-zero in 10 is kept, and a test value in a dropped column cannot produce a large z-score; `log1p` equals `np.log1p`, negative input raises; `check_no_overlap` raises on overlap and on train years after test years (e.g. train 2018-2020 / test 2014); `transform` before `fit` raises. Leakage test on the real or synthetic frame: no `year` appears in both the train and test outputs of `prepare_split`, and training years are exactly 2014-2016. Changing test rows must not change the fitted scaler (fit twice, compare `mean_`).

---

## Step 4: Classifiers (`src/models.py`)

**Approach.** Three scikit-learn models, all `random_state=42`, trained on the preprocessed 2014-2016 data.

**Functions.**
- `build_model(name: str) -> sklearn estimator`: `name` in `{"logreg", "random_forest", "sgd"}`; raises `ValueError` otherwise.
- `train_model(name: str, X_train: np.ndarray, y_train: np.ndarray) -> estimator`: builds and fits.
- `train_all(X_train, y_train) -> dict[str, estimator]`.
- `train_all_from_split(split: dict) -> dict[str, estimator]`: the static Step 4 entry point; wraps `train_all` and raises if `set(split["years_train"]) <= set(TRAIN_YEARS)` is false. This guard is for the static 2014-2016 model only; Step 7 windows (2017+) do not use it. Step 7 uses `window_years` plus `check_no_overlap` instead (see Step 7).
- `tune_logreg(tune_split: dict) -> dict`: only if time allows: small grid on `C` using train 2014-2015 / validate 2016, scoring F1 (malware); returns best params and the grid scores.
- `MODEL_NAMES: tuple[str, ...]`.

**Models and hyperparameter justification.**
- `LogisticRegression(class_weight="balanced", max_iter=1000, solver="lbfgs", C=1.0, random_state=42)`: linear baseline that works well on scaled sparse-ish counts; `balanced` protects against label imbalance if present (the data is balanced per year, but later use may not be); `max_iter=1000` so lbfgs converges on ~1,000 standardized features (a `ConvergenceWarning` is treated as a problem to report); `C=1.0` is the default, changed only if tuning on 2016 says so.
- `RandomForestClassifier(n_estimators=200, n_jobs=-1, random_state=42)`: non-linear model that is insensitive to feature scale; 200 trees is a point where accuracy usually plateaus while training stays within a minute or two on ~54,000 rows; other settings default (unbounded depth, `max_features="sqrt"`).
- `SGDClassifier(loss="log_loss", penalty="l2", alpha=1e-4, max_iter=1000, tol=1e-3, random_state=42)`: a logistic model trained by SGD, needed because Step 7 uses `partial_fit` (LogisticRegression and RandomForest have none). No `class_weight`: sklearn rejects `class_weight="balanced"` in `partial_fit`, and the data is balanced per year. `alpha=1e-4` is the sklearn default and a standard regularisation level for ~50k samples. For `partial_fit` the first call passes `classes=[0, 1]`.

**Report.** `docs/step4_models.md`: the three models, why each, the hyperparameter table and justification, training time per model, any convergence warnings, and tuning results if run.

**Testing.** Synthetic separable data: each model trains and predicts both classes with accuracy above chance (e.g. > 0.9); `build_model` returns the right class with `random_state == 42` (and `class_weight == "balanced"` for logreg only, `n_estimators == 200` where applicable); unknown name raises; the model returned by `build_model("sgd")` can be fit and then called with `partial_fit(X, y)` without error (not just "has the method"); same seed gives identical predictions twice; training with rows from a test year raises (guard checked via `years_train` argument in `train_all_from_split`, see below). A test that the training matrix has only years 2014-2016, and that `train_all_from_split` raises on a split containing a test year.

---

## Steps 5 and 6: Evaluation (`src/evaluate.py`)

**Approach.** Predict on held-out test years 2017-2021 only. Malware (1) is the positive class. Step 5 is the pooled table; Step 6 is the per-year breakdown.

**Functions.**
- `compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]`: `accuracy, precision, recall, f1`, using `pos_label=1`, `zero_division=0`.
- `evaluate_model(model, X_test, y_test) -> dict[str, float]`.
- `pooled_table(models: dict, X_test, y_test) -> pd.DataFrame`: one row per classifier, columns `model, accuracy, precision, recall, f1, n_test` (Step 5; pooled over 2017-2021).
- `per_year_table(models: dict, X_test, y_test, years_test) -> pd.DataFrame`: one row per (model, year), same metrics plus `year, n`; only years in `TEST_YEARS` (Step 6).
- `drift_summary(per_year: pd.DataFrame) -> pd.DataFrame`: per model: first-test-year F1, last-test-year F1, drop, and the F1 slope across years.
- `assert_test_years_only(years: np.ndarray) -> None`: raises if any year is outside `TEST_YEARS`.
- `sensitivity_tables(models: dict, X_test, y_test, years_test, dup_mask: np.ndarray) -> tuple[pd.DataFrame, pd.DataFrame]`: the same pooled and per-year tables restricted to test rows where `dup_mask` is False (no exact duplicate in 2014-2016), with a `n_excluded` column; `dup_mask` comes from `train_duplicate_mask` (Step 1). Saved as `results/step5_pooled_no_dup.*` and `results/step6_per_year_no_dup.*`.
- `save_table(df: pd.DataFrame, stem: str) -> None`: writes `results/<stem>.csv` and `results/<stem>.md` (Markdown table with fixed rounding to 4 decimals).
- Entry point for Steps 5 (and later 6): `main.run_step5(df=None, split=None, models=None) -> dict[str, pd.DataFrame]`, consistent with `run_step1` to `run_step4` (the earlier `run_evaluation(df)` was not built). It reuses the Step 4 models when given, otherwise trains them on 2014-2016; writes `results/step5_metrics.*` (with a `baseline_accuracy` column), `results/step5_confusion.*` and `results/step5_pooled_no_dup.*`. Step 6 is `main.run_step6(df=None, split=None, models=None)` (same pattern; reuses the Step 4 models, never refits on a test year). It writes `results/step6_by_year.*` (columns `classifier, year, n, accuracy, precision, recall, f1`; `by_year_export` renames `model` to `classifier`), `results/step6_baseline_by_year.*` (`year_baseline_table`: n, class counts, majority-class accuracy per year), `results/step6_drift_summary.*` (`drift_summary`), `results/step6_per_year_no_dup.*` and the figure `results/step6_by_year.png` (`plot_by_year`; F1 and accuracy by year; replaces the planned name `step6_f1_by_year.png` as the lead engineer asked).

**Notes.** Pooled metrics weight years by size (2017-2018 are 6x larger than 2019-2021), so the per-year table is the primary view; the report says so.

**Reports.** `docs/step5_evaluation.md` (pooled table, accuracy as the primary metric, plus precision/recall/F1 and a short comparison). `docs/step6_test_results.md` (per-year table for each classifier, how performance changes as data drifts, link to Step 2 findings).

**Testing.** Hand-computed confusion matrix (e.g. TP=3, FP=1, FN=2, TN=4) gives the exact accuracy, precision, recall and F1; metrics treat 1 as positive (swapping labels changes precision/recall); all-benign predictions give recall 0 and precision 0 without raising; `per_year_table` has one row per model per test year, the row counts `n` sum to the pooled `n_test`, and weighted per-year accuracy equals the pooled accuracy; `assert_test_years_only` raises on a training year; files are written with the expected columns. `train_duplicate_mask` flags a hand-built test row identical to a training row and not a unique one; `sensitivity_tables` excludes exactly the flagged rows and `n + n_excluded` equals the full test count.

---

## Step 7: Sustainable approach (`src/sustainable.py`)

**Approach.** Compare four strategies on the same test years (2017-2021), same metrics (accuracy, precision, recall, F1; malware positive), reported per year and pooled. Rule for all of them: year t is predicted before any of its rows is used for training or for fitting preprocessing.

| Strategy | Training data used to predict year t |
|---|---|
| (a) static | 2014-2016 only, never updated (this is the Step 4/6 model) |
| (b) expanding window | all years before t (2014..t-1); preprocessing and model refit from scratch for each t |
| (c) sliding window | the 3 years before t (t-3..t-1); preprocessing and model refit for each t |
| (d) incremental | SGD fit on 2014-2016, then for t = 2017..2021: predict t, then `partial_fit` on t (test-then-train) |

For t=2017 the windows in (b) and (c) are both 2014-2016, so (a)-(c) agree on 2017; they differ from 2018 on.

**Functions.**
- Step 7 guard: every Step 7 fit goes through `window_years` (which raises if any returned year is >= t) and then `check_no_overlap(window, [t])`. `train_all_from_split` is not used here.
- `window_years(strategy: str, t: int) -> tuple[int, ...]`: training years for strategy `"static"`, `"expanding"` or `"sliding"` at test year t (static: 2014-2016; expanding: 2014..t-1; sliding: t-3..t-1); raises if t is not in `TEST_YEARS` or if any returned year is >= t.
- `run_window_strategy(df, strategy: str, model_name: str = "logreg") -> pd.DataFrame`: for each t: `check_no_overlap(window, [t])`, fit a new `Preprocessor` and model on the window only, predict t, compute metrics; returns one row per test year.
- `run_incremental(df, model_name: str = "sgd") -> pd.DataFrame`: initial `fit` of `Preprocessor` and SGD on 2014-2016 (preprocessor frozen afterwards, so later years use the same mask and scaler: a limitation noted in the report); loop over t, record the prediction on t first, then `partial_fit` on year t with the true labels. Returns one row per test year.
- `run_all_strategies(df, split=None, models=None, step4_seconds=None, rf=True) -> pd.DataFrame`: concatenates (a)-(d) with `strategy` and `classifier` columns, one row per (strategy, classifier, test year); static rows come from the Step 4 models when given. **Changed in Step 7:** the pooled rows are not in this table (a `year` column stays numeric); `pooled_by_strategy` writes them separately.
- `compare_to_static(results: pd.DataFrame) -> pd.DataFrame`: per strategy and year, difference in F1 and accuracy against the static model.
- `run_sustainable(df, split=None, models=None, step4_seconds=None, rf=True) -> dict[str, pd.DataFrame]`: writes `results/step7_strategies.*` (columns `strategy, classifier, year, n, accuracy, precision, recall, f1`; replaces the planned name `step7_strategy_metrics`, as the lead engineer asked), `step7_strategies_detail.*` (adds confusion counts, training seconds, rows and window), `step7_pooled.*`, `step7_vs_static.*`, `step7_summary.*` (mean F1, worst year), `step7_cost.*`, `step7_window_composition.*` and `step7_f1_by_year.png` (F1 and accuracy by year, dashed always-malware F1 0.667 and chance accuracy 0.5).
- Helpers: `year_arrays`, `fit_on_years` (the single place every window fit goes through: `check_no_overlap` plus a `max(years) < t` assertion), `static_from_models`, `pooled_by_strategy`, `summary_table`, `cost_table`, `window_composition`, `plot_strategies`. `run_incremental` also asserts before every prediction that no year seen so far is >= t.

**Model choice and decision flagged.** Windows (b)-(c) and the static baseline use LogisticRegression so that all five refits finish in a few minutes; (d) uses SGD. A fair isolation of "incremental vs retrain" would also run SGD under (a)-(c); I will add SGD-static as an extra row (cheap) so the incremental gain is compared with the same model family. RandomForest is run for (a) and (b) only (not (c) or (d)); measured, it fit within the budget. Runtime estimate: ~54,000-90,000 rows x ~1,000 features per LR refit, 5 refits per strategy; to be measured, not assumed.

**Assumption to state.** Labels for year t become available only after year t ends (test-then-train); a real labeling delay would hurt (d), (b) and (c) in practice. The report states this. Not simulated here.

**Row-count imbalance (to state in the report).** Years 2014-2018 have 18,000 rows each and 2019-2021 have 3,000, so the expanding window is dominated by old data and the 3-year window for 2021 (2018-2020) is 18,000 of 24,000 rows from 2018. The report notes that "retraining helps or not" may partly reflect this row-count imbalance rather than recency alone, and lists each window's year composition (rows per year in the training window for every strategy and test year; also saved as `results/step7_window_composition.csv`). No equal-rows variant is run.

**Report.** `docs/step7_sustainable_approach.md`: the four strategies, the table of F1/accuracy per year, the window composition table and the imbalance note above, comparison with the static model, cost (training time per strategy), conclusions that feed the one-page report.

**Testing.** Synthetic multi-year frame with an injected drift (class boundary shifts each year): `window_years` returns exactly the specified years (including edge cases t=2017 and t=2021); for every strategy and every t, `max(window) < t` (the no-test-year-in-training check, run through a spy that records the years passed to `fit`); `run_incremental` records predictions on t before `partial_fit` on t (verified with a stub model that logs call order and, separately, by checking the year-t labels are not seen at prediction time); static results are identical to the Step 6 model's results; result tables have one row per test year per strategy and the expected columns; on the injected-drift data the retraining/incremental strategies do not do worse than the static one in the final year (sanity check, not a performance claim).

---

## Cross-cutting test plan (tester)
- `tests/test_stepN_*.py` per step with synthetic data in `tmp_path`; real-data tests marked and skipped when `input_data/` is absent.
- A project-wide leakage test: every call that fits anything records the years it saw (via a spy/wrapper); none of 2017-2021 may appear before its own prediction. Applies to Steps 3-7; `drift.py` (Step 2) is exempt.
- `python harness.py test N` for one step and `python harness.py test all` for all.

## Implementation order and commits
One commit per task (about 300 added lines max): config + data, then drift, then preprocess, then models, then evaluate, then sustainable, then main and docs. Each step is followed by a review and test cycle outside this plan.

## Points where I disagree or want a decision
1. The accuracy matrix in Step 2 trains on later years and predicts earlier ones; this is a diagnostic only, not used for any design choice, and is exempt from the leakage rules (section 0).
2. Step 7 (d) freezes the scaler and zero-column mask from 2014-2016; an alternative (updating the scaler with `partial_fit`) is possible but not planned.
3. Cross-year duplicates (item 5 above) stay in the main results; the sensitivity row reports the effect.
