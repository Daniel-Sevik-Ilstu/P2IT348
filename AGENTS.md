# AGENTS.md: Project 2 context for all agents

Every agent (builder, reviewer, tester) reads this file first.

## Project goal

Classify Android apps as malware or goodware from their API-call features, and find a sustainable approach that stays accurate as the data drifts over 8 years (2014-2021). The full assignment is in ASSIGNMENT.md.

## Dataset

- Location: input_data/ (not committed to git).
- 16 CSV files named sampled_<YEAR>_<CLASS>_api.csv, e.g. sampled_2017_malware_api.csv. YEAR is 2014-2021. CLASS is "malware" or "benign" (benign = goodware). One malware file and one benign file per year.
- Year and class come ONLY from the file name. Parse them with a regex; fail loudly on a name that does not match.
- Columns: every file has 1,849 columns. The first column is "apkname" (package name + hash, an identifier). It must be dropped; the other 1,848 columns are API-call features (column names are Dalvik method signatures). All files have the same columns in the same order.
- Rows: ASSIGNMENT.md says 1,500 rows per file, but the real files differ: 2014-2018 files have 9,000 rows each; 2019-2021 files have 1,500 rows each. Code must not assume a fixed row count; it must check 1,849 columns and report the actual row counts.
- Label: target column "label", 1 = malware, 0 = goodware (benign).
- Feature values: non-negative integer call counts, heavy-tailed (max around 92,000). No missing values. Roughly 850-1,125 columns are all-zero within any single file. The 2014-2018 files contain many duplicate rows and repeated apknames; keep them unless PLAN.md justifies otherwise, and report them.
- Memory: the combined data is about 100,000 x 1,848. Load features as int32 or float32, not int64.

## Folder layout

- src/: project code (builder only).
- tests/: pytest tests test_stepN_*.py and test logs stepN_test_log.md (tester only; the student adds failure decisions).
- docs/: one builder report per step.
- reviews/: one review report per step (reviewer writes comments; student writes the decision log).
- results/: CSV and Markdown result tables (and optional PNG figures) written by the code.
- transcripts/: saved agent sessions (saved by the harness; agents never edit these).
- PLAN.md: the plan for Steps 1-7. README.md, REPORT.md and REFLECTION.md: written by the student.

## Coding conventions

- Python 3, pandas, numpy, scikit-learn, scipy. matplotlib is allowed for figures (add it to requirements.txt). No other libraries without asking.
- One module per concern in src/ (e.g. data.py, drift.py, preprocess.py, models.py, evaluate.py, sustainable.py) plus src/main.py as the entry point.
- Every function has a docstring and type hints; comments explain each major step.
- random_state=42 everywhere randomness is used.
- Paths are built with pathlib relative to the repository root. No hard-coded absolute paths.
- Train/test split is by year: training years 2014-2016, test years 2017-2021, with metrics reported for each test year separately. Anything fit to data (scalers, feature selection, models) is fit on training years only. If anything is tuned, tune on a validation year inside the training years, never on test years.
- Malware (label 1) is the positive class for precision, recall, and F1.
- The full pipeline should run in under about 15 minutes on a laptop. Any cache goes in a git-ignored folder.
- Small commits: one task per commit, under about 300 added lines each.

## How to run

- Whole project: python -m src.main (writes results/ and prints a summary).
- One step: python -m src.main --step N
- Tests: python harness.py test N (one step) or python harness.py test all.

## Commit rules

Every commit message starts with a role tag: [builder], [reviewer], [tester], or [student]. A git hook rejects other messages. Make small commits, one per task. Never rewrite or squash history.
