# Step 3 Report: Preprocessing

Written by the builder agent. All numbers come from `python -m src.main --step 3` (code in `src/preprocess.py`, tables in `results/step3_*`).

## Scaling

Pipeline, in this order (class `Preprocessor`):

1. **`log1p`** (`apply_log1p`). Counts are heavy-tailed (max about 92,000), so one `StandardScaler` on raw counts would let a few huge values set the mean and std and squash everything else toward zero. `log1p` compresses the tail first and keeps zero at zero, so sparsity is preserved. It is stateless, so it cannot leak.
2. **Drop all-zero training columns**, then
3. **Minimum-support filter** (`nonzero_feature_mask`, `MIN_SUPPORT = 10`): keep columns that are non-zero in at least 10 training rows. This subsumes step 2 (all-zero columns have support 0). Purpose: a column with 1-9 non-zero training rows has a tiny training std, so an ordinary test value becomes a huge z-score.
4. **`StandardScaler`** fit on the kept columns of the 2014-2016 rows only.

Output is float32. The train matrix is 54,000 x 931 (201 MB), the test matrix 45,000 x 931 (168 MB). Test years are transformed with the same fitted mask and scaler (`Preprocessor.transform` never refits; it raises if called before `fit`).

Sanity check on the real data: the scaled training columns have mean about 0 (max absolute 1e-7) and std between 0.9999997 and 1.0000002; the test matrix has overall mean 0.087, i.e. it is not re-centred on itself, and contains no NaN or inf.

### Feature counts after each filter

| Stage | Features |
|---|---|
| Raw features | 1848 |
| After dropping all-zero training columns | 1093 |
| After min support >= 10 training rows (kept) | 931 |
| Dropped for low support (1-9 non-zero training rows) | 162 |
| Dropped columns that are non-zero somewhere in 2017-2021 | 212 |

The kept column names, in order, are in `results/step3_kept_features.csv` (`Preprocessor.kept_features_`). Train and test matrices have identical columns in identical order because both go through the same mask.

**Caveat (measured, not hidden).** The filter does not remove all extreme z-scores: the largest absolute test value is about 212, and 59,047 test cells (of about 41.9 million) exceed |z| = 20. Columns with just 10+ training non-zeros and a rare spike can still do this. This is real drift and is left as is; I did not clip, since nothing in the plan calls for it.

## Train/test split

`split_by_year` (calls `check_no_overlap` first). Training years 2014-2016, test years 2017-2021. Rows and class balance (`results/step3_split.csv`):

| Side | Year | Rows | Malware | Benign |
|---|---|---|---|---|
| train | 2014 | 18000 | 9000 | 9000 |
| train | 2015 | 18000 | 9000 | 9000 |
| train | 2016 | 18000 | 9000 | 9000 |
| test | 2017 | 18000 | 9000 | 9000 |
| test | 2018 | 18000 | 9000 | 9000 |
| test | 2019 | 3000 | 1500 | 1500 |
| test | 2020 | 3000 | 1500 | 1500 |
| test | 2021 | 3000 | 1500 | 1500 |

Totals: train 54,000 rows (50% malware); test 45,000 rows (50% malware). Duplicate rows were kept (see Step 1 report); 33% of 2017 test rows have a feature vector that also occurs in 2014-2016.

`make_tuning_split` gives the validation variant (train 2014-2015, validate 2016); it is not used yet.

## Leakage prevention

1. `check_no_overlap` raises `ValueError` if either year set is empty, if they intersect, or if any training year is not earlier than every test year (for example train 2014+2018 / test 2017 raises; checked). `split_by_year` and therefore `prepare_split` always call it.
2. The column mask, the scaler mean/std and later the models are fit on training rows only (`Preprocessor.fit` receives only the training matrix in `prepare_split`). Test rows only go through `transform`.
3. `log1p` is stateless.
4. The mask is computed from training support only, so a column that is non-zero only in test years is dropped, not used.
5. Tuning (`make_tuning_split`) uses 2014-2016 only; test years are never touched.

Not covered here: Step 2's `concept_drift_matrix` is exempt (diagnostic only, see PLAN.md section 0), and Step 7 refits the preprocessor per window.

## Limits

- I ran the pipeline on the real data but did not write tests (tester's job); the checks above were done in a one-off script.
- A column active only after 2016 is lost for the static model (212 such columns); Step 7 windows recover them by refitting.
