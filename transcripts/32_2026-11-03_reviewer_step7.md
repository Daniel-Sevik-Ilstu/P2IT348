# Transcript: reviewer, Step 7 (started 2026-11-03T06:22:57+02:00)

## User 2026-11-03T04:23:13.136Z

<pasted_content id="f91c">
You are the REVIEWER agent for Project 2 (Android malware classification under data drift).

You review work done by a separate builder agent. You have not seen the builder's conversation, and you must not look for it.

## Your task: review Step 7, Sustainable ML Approach

Read only: AGENTS.md, PLAN.md, and the code changes in .harness/diffs/step7_diff.patch (the diff from step7-start to the latest commit). You may open the changed files in src/ for context.

Do NOT open docs/, transcripts/, tests/, or other files in reviews/. They contain explanations that would bias your review.

Look in particular at:
- Is evaluation time-forward (train on years up to t, test on year t+1)?
- Is there a never-updated baseline model for comparison?
- Is the comparison fair (same test years, same metrics)?

Also look for bugs, anything that does not match ASSIGNMENT.md or PLAN.md, unclear code, and missing error handling.

## Output

1. Create reviews/step7_review.md by copying templates/review_report.md, and fill in the step number and title at the top.
2. Fill in the Comments table: one numbered row per issue, with severity (High, Medium, Low), location (file and line or function), the issue, and a suggested fix.
3. Leave the Decision log table empty. The student fills it in.
4. Do not edit any code or other files.
5. Commit only reviews/step7_review.md with a message starting with [reviewer], e.g., "[reviewer] Step 7 review".

Be specific and honest. Report only real problems; do not pad the list. If you are unsure, say so in the comment.

This session's transcript will be saved as transcripts/32_2026-11-03_reviewer_step7.md.
</pasted_content id="f91c">

<pasted_content id="f91c">
Lead engineer notes for this review:
- Read only the files the instructions above allow. Do not open docs/, tests/, transcripts/ or other review reports.
- Verified data facts: 2014-2018 files have 9,000 rows and 2019-2021 files have 1,500 (ASSIGNMENT.md's 1,500 is wrong for 2014-2018); 1,849 columns; the first column is apkname.
- Priorities: leakage between years (anything fit or chosen using test years: scaling, feature selection, tuning, column lists); the label mapping (benign = 0, malware = 1) and pos_label; wrong metric averaging; code that silently passes on bad input; anything that contradicts PLAN.md or AGENTS.md.
- For this step specifically, this is the most leakage-prone step, so check carefully: (1) for every test year t, no model, scaler, min-support mask or clip statistic is fit on year t or any later year; (2) the incremental strategy predicts year t BEFORE calling partial_fit on year t (test-then-train), and the scaler used for year t was not fit on year t; (3) the static baseline is never updated and is the same model as in Step 4; (4) all strategies are evaluated on the same test rows with the same metrics; (5) the sliding window really contains only the 3 years before t; (6) refitting preprocessing per window uses only that window's rows.
- Where code exists, you may check a claim with a quick read-only command (for example python -c ...). Say what you ran. Do not modify anything except the review report.
- Rate severity honestly. Mark style preferences as Low and say so. I will accept or reject each comment, so give a reason I can evaluate.
</pasted_content id="f91c">

## User 

<system-reminder>
Codebase and user instructions are shown below. Be sure to adhere to these instructions. IMPORTANT: These instructions OVERRIDE any default behavior and you MUST follow them exactly as written.

Contents of c:\Users\thema\OneDrive\Desktop\Project2\project2-harness2\project2-harness2\CLAUDE.md (project instructions, checked into the codebase):

@AGENTS.md

Contents of c:\Users\thema\OneDrive\Desktop\Project2\project2-harness2\project2-harness2\AGENTS.md (project instructions, checked into the codebase):

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
</system-reminder>

## User 

<system-reminder>
As you answer the user's questions, you can use the following context:
# userEmail
The user's email address is themalevolence.1@gmail.com. Use it only to identify the user, such as for authorship, attribution, or filtering their own work. Never send it to an unrelated service, such as in a request header, URL, or payload, unless the user explicitly asks.
# gitStatus
This is the git status at the start of the conversation. Note that this status is a snapshot in time, and will not update during the conversation.

Current branch: master

Main branch (you will usually use this for PRs): main

Git user: Daniel

Status:
(clean)

Recent commits:
276df23 [builder] step 7 transcript from builder
b53fe30 [builder] Step 7: results tables, figure and report (docs/step7_sustainable_approach.md)
d454776 [builder] Step 7: update PLAN.md for result file names, pooled table and helper functions
841c4c0 [builder] Step 7: wire run_step7 into main (--step 7 and full pipeline)
fd559ae [builder] Step 7: window strategies, incremental learning, summaries (src/sustainable.py)

Claude Code attached this context automatically; it isn't part of the user's message. It describes the user's own account and workspace, so they don't need it reported back.
</system-reminder>

## User 

<system-reminder>
Attribution for git commits and pull requests you create from here on (this replaces Claude Code's own earlier attribution guidance, such as a previous copy of this reminder; the user's own instructions about these lines, such as a CLAUDE.md or memory rule, take precedence over this reminder, but do not add attribution lines this reminder leaves out):
- End git commit messages with:
Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
- End pull request descriptions with:
🤖 Generated with [Claude Code](https://claude.com/claude-code)
</system-reminder>

## User 

<pasted_content id="f91c">
You are the REVIEWER agent for Project 2 (Android malware classification under data drift).

You review work done by a separate builder agent. You have not seen the builder's conversation, and you must not look for it.

## Your task: review Step 7, Sustainable ML Approach

Read only: AGENTS.md, PLAN.md, and the code changes in .harness/diffs/step7_diff.patch (the diff from step7-start to the latest commit). You may open the changed files in src/ for context.

Do NOT open docs/, transcripts/, tests/, or other files in reviews/. They contain explanations that would bias your review.

Look in particular at:
- Is evaluation time-forward (train on years up to t, test on year t+1)?
- Is there a never-updated baseline model for comparison?
- Is the comparison fair (same test years, same metrics)?

Also look for bugs, anything that does not match ASSIGNMENT.md or PLAN.md, unclear code, and missing error handling.

## Output

1. Create reviews/step7_review.md by copying templates/review_report.md, and fill in the step number and title at the top.
2. Fill in the Comments table: one numbered row per issue, with severity (High, Medium, Low), location (file and line or function), the issue, and a suggested fix.
3. Leave the Decision log table empty. The student fills it in.
4. Do not edit any code or other files.
5. Commit only reviews/step7_review.md with a message starting with [reviewer], e.g., "[reviewer] Step 7 review".

Be specific and honest. Report only real problems; do not pad the list. If you are unsure, say so in the comment.

This session's transcript will be saved as transcripts/32_2026-11-03_reviewer_step7.md.
</pasted_content id="f91c">

<pasted_content id="f91c">
Lead engineer notes for this review:
- Read only the files the instructions above allow. Do not open docs/, tests/, transcripts/ or other review reports.
- Verified data facts: 2014-2018 files have 9,000 rows and 2019-2021 files have 1,500 (ASSIGNMENT.md's 1,500 is wrong for 2014-2018); 1,849 columns; the first column is apkname.
- Priorities: leakage between years (anything fit or chosen using test years: scaling, feature selection, tuning, column lists); the label mapping (benign = 0, malware = 1) and pos_label; wrong metric averaging; code that silently passes on bad input; anything that contradicts PLAN.md or AGENTS.md.
- For this step specifically, this is the most leakage-prone step, so check carefully: (1) for every test year t, no model, scaler, min-support mask or clip statistic is fit on year t or any later year; (2) the incremental strategy predicts year t BEFORE calling partial_fit on year t (test-then-train), and the scaler used for year t was not fit on year t; (3) the static baseline is never updated and is the same model as in Step 4; (4) all strategies are evaluated on the same test rows with the same metrics; (5) the sliding window really contains only the 3 years before t; (6) refitting preprocessing per window uses only that window's rows.
- Where code exists, you may check a claim with a quick read-only command (for example python -c ...). Say what you ran. Do not modify anything except the review report.
- Rate severity honestly. Mark style preferences as Low and say so. I will accept or reject each comment, so give a reason I can evaluate.
</pasted_content id="f91c">

**Tool call: Read** 2026-11-03T04:23:32.098Z

```
{
 "file_path": "c:\\Users\\thema\\OneDrive\\Desktop\\Project2\\project2-harness2\\project2-harness2\\PLAN.md"
}
```

**Tool result** 2026-11-03T04:23:32.244Z

```
1	# PLAN.md: Project 2 plan (Steps 1-7)
2	
3	Author: builder agent. Status: initial version (Step 0), before review.
4	Data facts used here come from AGENTS.md. Nothing in this plan has been run yet; no result is claimed.
5	
6	## 0. Global decisions
7	
8	### Train/test split by year
9	
10	| Role | Years | Use |
11	|---|---|---|
12	| Train | 2014, 2015, 2016 | fit preprocessing and models |
13	| Tuning (only if needed) | train on 2014-2015, validate on 2016 | choose hyperparameters; then refit on 2014-2016 |
14	| Test | 2017, 2018, 2019, 2020, 2021 | evaluation only; every metric is reported pooled AND per year |
15	
16	### How leakage between years is prevented
17	
18	1. One function `check_no_overlap(train_years, test_years)` (in `src/preprocess.py`) raises `ValueError` if either set is empty, if the sets intersect, or if `max(train_years) >= min(test_years)` (training years must all precede test years). Every train/predict call in Steps 3-7 goes through it.
19	   - **Exemption (Step 2).** `concept_drift_matrix` in `src/drift.py` is diagnostic: it fits a scaler and a model on each single year (including 2017-2021) and predicts other years, so it does not obey the train-2014-2016 rule or `check_no_overlap`. Nothing it produces feeds Steps 3-7 (no features, hyperparameters or split choices). The leakage tests skip `drift.py`; they apply to Steps 3-7 only.
20	2. Every fitted object (zero-column mask, `StandardScaler`, classifiers) is fit on the training rows only. Test rows are only passed to `transform` / `predict`. `log1p` is stateless, so it cannot leak.
21	3. Tuning never touches 2017-2021.
22	4. Step 7: year t is predicted before it is used for training (see Step 7). Expanding/sliding windows refit preprocessing on the window only.
23	5. Cross-year duplicates: the 2014-2018 files have many duplicate rows and repeated apknames. Step 1 reports (a) exact duplicate feature rows within a year and (b) apknames or identical feature vectors shared between a training year and a test year. I keep all rows by default (AGENTS.md); no rows are removed from the main results. Step 1 reports, per test year, the count and share of test rows whose exact feature vector also occurs in the training years (2014-2016). Steps 5 and 6 add a sensitivity row (`subset = "no_train_duplicate"`) with metrics on only the test rows that have no exact duplicate in the training years, and state in the report how many test rows were excluded.
24	6. Step 2 (KS tests, accuracy matrix) is descriptive. Its output is never used to select features, hyperparameters or the split.
25	
26	### Conventions (from AGENTS.md)
27	random_state=42; features as float32/int32; pathlib paths relative to the repo root; docstrings and type hints on every function; one module per concern; cache in the git-ignored `cache/` folder (see `load_all` in Step 1 for the cache rules); small commits tagged `[builder]`.
28	
29	### Shared constants (`src/config.py`)
30	`ROOT`, `DATA_DIR`, `RESULTS_DIR`, `DOCS_DIR`
... [29421 more characters in the .jsonl file]
```

**Tool call: Read** 2026-11-03T04:23:32.498Z

```
{
 "file_path": "c:\\Users\\thema\\OneDrive\\Desktop\\Project2\\project2-harness2\\project2-harness2\\.harness\\diffs\\step7_diff.patch"
}
```

**Tool result** 2026-11-03T04:23:32.664Z

```
1	diff --git a/results/step4_training.csv b/results/step4_training.csv
2	index 1478b5b..7915b7d 100644
3	--- a/results/step4_training.csv
4	+++ b/results/step4_training.csv
5	@@ -1,4 +1,4 @@
6	 model,train_seconds,train_accuracy,convergence_warnings,warning_messages
7	-logreg,1.93,0.9897,0,
8	-random_forest,4.66,0.9969,0,
9	-sgd,3.69,0.9884,0,
10	+logreg,2.65,0.9897,0,
11	+random_forest,8.18,0.9969,0,
12	+sgd,5.02,0.9884,0,
13	diff --git a/results/step4_training.md b/results/step4_training.md
14	index 075457b..788fe10 100644
15	--- a/results/step4_training.md
16	+++ b/results/step4_training.md
17	@@ -1,5 +1,5 @@
18	 | model | train_seconds | train_accuracy | convergence_warnings | warning_messages |
19	 |---|---|---|---|---|
20	-| logreg | 1.9300 | 0.9897 | 0 |  |
21	-| random_forest | 4.6600 | 0.9969 | 0 |  |
22	-| sgd | 3.6900 | 0.9884 | 0 |  |
23	+| logreg | 2.6500 | 0.9897 | 0 |  |
24	+| random_forest | 8.1800 | 0.9969 | 0 |  |
25	+| sgd | 5.0200 | 0.9884 | 0 |  |
26	diff --git a/results/step7_cost.csv b/results/step7_cost.csv
27	new file mode 100644
28	index 0000000..59d24c1
29	--- /dev/null
30	+++ b/results/step7_cost.csv
31	@@ -0,0 +1,10 @@
32	+strategy,classifier,n_fits,total_seconds,mean_seconds_per_update,max_seconds,mean_train_rows
33	+static,logreg,1,2.65,2.65,2.65,54000.0
34	+expanding,logreg,5,54.3618,10.8724,14.1077,81000.0
35	+sliding,logreg,5,31.3158,6.2632,8.9642,45000.0
36	+static,sgd,1,5.02,5.02,5.02,54000.0
37	+expanding,sgd,5,61.5999,12.32,17.1582,81000.0
38	+sliding,sgd,5,40.2812,8.0562,9.6258,45000.0
39	+incremental,sgd,5,7.3575,1.4715,7.1278,19200.0
40	+static,random_forest,1,8.18,8.18,8.18,54000.0
41	+expanding,random_forest,5,100.5555,20.1111,26.4147,81000.0
42	diff --git a/results/step7_cost.md b/results/step7_cost.md
43	new file mode 100644
44	index 0000000..72cc7f4
45	--- /dev/null
46	+++ b/results/step7_cost.md
47	@@ -0,0 +1,11 @@
48	+| strategy | classifier | n_fits | total_seconds | mean_seconds_per_update | max_seconds | mean_train_rows |
49	+|---|---|---|---|---|---|---|
50	+| static | logreg | 1 | 2.6500 | 2.6500 | 2.6500 | 54000 |
51	+| expanding | logreg | 5 | 54.3618 | 10.8724 | 14.1077 | 81000 |
52	+| sliding | logreg | 5 | 31.3158 | 6.2632 | 8.9642 | 45000 |
53	+| static | sgd | 1 | 5.0200 | 5.0200 | 5.0200 | 54000 |
54	+| expanding | sgd | 5 | 61.5999 | 12.3200 | 17.1582 | 81000 |
55	+| sliding | sgd | 5 | 40.2812 | 8.0562 | 9.6258 | 45000 |
56	+| incremental | sgd | 5 | 7.3575 | 1.4715 | 7.1278 | 19200 |
57	+| static | random_forest | 1 | 8.1800 | 8.1800 | 8.1800 | 54000 |
58	+| expanding | random_forest | 5 | 100.5555 | 20.1111 | 26.4147 | 81000 |
59	diff --git a/results/step7_f1_by_year.png b/results/step7_f1_by_year.png
60	new file mode 100644
61	index 0000000..c570c1f
62	Binary files /dev/null and b/results/step7_f1_by_year.png differ
63	diff --git a/results/step7_pooled.csv b/results/step7_pooled.csv
64	new file mode 100644
65	index 0000000..c906f87
66	--- /dev/null
67	+++ b/results/step7_pooled.csv
... [39476 more characters in the .jsonl file]
```

**Tool call: Read** 2026-11-03T04:23:33.101Z

```
{
 "file_path": "c:\\Users\\thema\\OneDrive\\Desktop\\Project2\\project2-harness2\\project2-harness2\\templates\\review_report.md"
}
```

**Tool result** 2026-11-03T04:23:33.140Z

```
1	# Step N Review: Step title
2	
3	- Reviewer transcript: transcripts/NN_YYYY-MM-DD_reviewer_stepN.md
4	- What was reviewed: (Step 0: PLAN.md at commit abc1234; Steps 1-7: the diff from stepN-start to commit abc1234)
5	
6	## Comments (reviewer)
7	
8	One row per issue. Number the rows 1, 2, 3, ...
9	
10	| # | Severity | Location | Issue | Suggested fix |
11	| --- | --- | --- | --- | --- |
12	
13	## Decision log (student)
14	
15	One row per comment above, with the same number. Decision is Accepted or Rejected. For accepted comments, add the commit that fixed it.
16	
17	| # | Decision | Reason | Fixed in commit |
18	| --- | --- | --- | --- |
19	
```

**Tool call: Read** 

```
{
 "file_path": "c:\\Users\\thema\\OneDrive\\Desktop\\Project2\\project2-harness2\\project2-harness2\\PLAN.md"
}
```

**Tool call: Read** 

```
{
 "file_path": "c:\\Users\\thema\\OneDrive\\Desktop\\Project2\\project2-harness2\\project2-harness2\\.harness\\diffs\\step7_diff.patch"
}
```

**Tool call: Read** 

```
{
 "file_path": "c:\\Users\\thema\\OneDrive\\Desktop\\Project2\\project2-harness2\\project2-harness2\\templates\\review_report.md"
}
```

**Tool result** 

```
1	# PLAN.md: Project 2 plan (Steps 1-7)
2	
3	Author: builder agent. Status: initial version (Step 0), before review.
4	Data facts used here come from AGENTS.md. Nothing in this plan has been run yet; no result is claimed.
5	
6	## 0. Global decisions
7	
8	### Train/test split by year
9	
10	| Role | Years | Use |
11	|---|---|---|
12	| Train | 2014, 2015, 2016 | fit preprocessing and models |
13	| Tuning (only if needed) | train on 2014-2015, validate on 2016 | choose hyperparameters; then refit on 2014-2016 |
14	| Test | 2017, 2018, 2019, 2020, 2021 | evaluation only; every metric is reported pooled AND per year |
15	
16	### How leakage between years is prevented
17	
18	1. One function `check_no_overlap(train_years, test_years)` (in `src/preprocess.py`) raises `ValueError` if either set is empty, if the sets intersect, or if `max(train_years) >= min(test_years)` (training years must all precede test years). Every train/predict call in Steps 3-7 goes through it.
19	   - **Exemption (Step 2).** `concept_drift_matrix` in `src/drift.py` is diagnostic: it fits a scaler and a model on each single year (including 2017-2021) and predicts other years, so it does not obey the train-2014-2016 rule or `check_no_overlap`. Nothing it produces feeds Steps 3-7 (no features, hyperparameters or split choices). The leakage tests skip `drift.py`; they apply to Steps 3-7 only.
20	2. Every fitted object (zero-column mask, `StandardScaler`, classifiers) is fit on the training rows only. Test rows are only passed to `transform` / `predict`. `log1p` is stateless, so it cannot leak.
21	3. Tuning never touches 2017-2021.
22	4. Step 7: year t is predicted before it is used for training (see Step 7). Expanding/sliding windows refit preprocessing on the window only.
23	5. Cross-year duplicates: the 2014-2018 files have many duplicate rows and repeated apknames. Step 1 reports (a) exact duplicate feature rows within a year and (b) apknames or identical feature vectors shared between a training year and a test year. I keep all rows by default (AGENTS.md); no rows are removed from the main results. Step 1 reports, per test year, the count and share of test rows whose exact feature vector also occurs in the training years (2014-2016). Steps 5 and 6 add a sensitivity row (`subset = "no_train_duplicate"`) with metrics on only the test rows that have no exact duplicate in the training years, and state in the report how many test rows were excluded.
24	6. Step 2 (KS tests, accuracy matrix) is descriptive. Its output is never used to select features, hyperparameters or the split.
25	
26	### Conventions (from AGENTS.md)
27	random_state=42; features as float32/int32; pathlib paths relative to the repo root; docstrings and type hints on every function; one module per concern; cache in the git-ignored `cache/` folder (see `load_all` in Step 1 for the cache rules); small commits tagged `[builder]`.
28	
29	### Shared constants (`src/config.py`)
30	`ROOT`, `DATA_DIR`, `RESULTS_DIR`, `DOCS_DIR`
... [29421 more characters in the .jsonl file]
```

**Tool result** 

```
1	diff --git a/results/step4_training.csv b/results/step4_training.csv
2	index 1478b5b..7915b7d 100644
3	--- a/results/step4_training.csv
4	+++ b/results/step4_training.csv
5	@@ -1,4 +1,4 @@
6	 model,train_seconds,train_accuracy,convergence_warnings,warning_messages
7	-logreg,1.93,0.9897,0,
8	-random_forest,4.66,0.9969,0,
9	-sgd,3.69,0.9884,0,
10	+logreg,2.65,0.9897,0,
11	+random_forest,8.18,0.9969,0,
12	+sgd,5.02,0.9884,0,
13	diff --git a/results/step4_training.md b/results/step4_training.md
14	index 075457b..788fe10 100644
15	--- a/results/step4_training.md
16	+++ b/results/step4_training.md
17	@@ -1,5 +1,5 @@
18	 | model | train_seconds | train_accuracy | convergence_warnings | warning_messages |
19	 |---|---|---|---|---|
20	-| logreg | 1.9300 | 0.9897 | 0 |  |
21	-| random_forest | 4.6600 | 0.9969 | 0 |  |
22	-| sgd | 3.6900 | 0.9884 | 0 |  |
23	+| logreg | 2.6500 | 0.9897 | 0 |  |
24	+| random_forest | 8.1800 | 0.9969 | 0 |  |
25	+| sgd | 5.0200 | 0.9884 | 0 |  |
26	diff --git a/results/step7_cost.csv b/results/step7_cost.csv
27	new file mode 100644
28	index 0000000..59d24c1
29	--- /dev/null
30	+++ b/results/step7_cost.csv
31	@@ -0,0 +1,10 @@
32	+strategy,classifier,n_fits,total_seconds,mean_seconds_per_update,max_seconds,mean_train_rows
33	+static,logreg,1,2.65,2.65,2.65,54000.0
34	+expanding,logreg,5,54.3618,10.8724,14.1077,81000.0
35	+sliding,logreg,5,31.3158,6.2632,8.9642,45000.0
36	+static,sgd,1,5.02,5.02,5.02,54000.0
37	+expanding,sgd,5,61.5999,12.32,17.1582,81000.0
38	+sliding,sgd,5,40.2812,8.0562,9.6258,45000.0
39	+incremental,sgd,5,7.3575,1.4715,7.1278,19200.0
40	+static,random_forest,1,8.18,8.18,8.18,54000.0
41	+expanding,random_forest,5,100.5555,20.1111,26.4147,81000.0
42	diff --git a/results/step7_cost.md b/results/step7_cost.md
43	new file mode 100644
44	index 0000000..72cc7f4
45	--- /dev/null
46	+++ b/results/step7_cost.md
47	@@ -0,0 +1,11 @@
48	+| strategy | classifier | n_fits | total_seconds | mean_seconds_per_update | max_seconds | mean_train_rows |
49	+|---|---|---|---|---|---|---|
50	+| static | logreg | 1 | 2.6500 | 2.6500 | 2.6500 | 54000 |
51	+| expanding | logreg | 5 | 54.3618 | 10.8724 | 14.1077 | 81000 |
52	+| sliding | logreg | 5 | 31.3158 | 6.2632 | 8.9642 | 45000 |
53	+| static | sgd | 1 | 5.0200 | 5.0200 | 5.0200 | 54000 |
54	+| expanding | sgd | 5 | 61.5999 | 12.3200 | 17.1582 | 81000 |
55	+| sliding | sgd | 5 | 40.2812 | 8.0562 | 9.6258 | 45000 |
56	+| incremental | sgd | 5 | 7.3575 | 1.4715 | 7.1278 | 19200 |
57	+| static | random_forest | 1 | 8.1800 | 8.1800 | 8.1800 | 54000 |
58	+| expanding | random_forest | 5 | 100.5555 | 20.1111 | 26.4147 | 81000 |
59	diff --git a/results/step7_f1_by_year.png b/results/step7_f1_by_year.png
60	new file mode 100644
61	index 0000000..c570c1f
62	Binary files /dev/null and b/results/step7_f1_by_year.png differ
63	diff --git a/results/step7_pooled.csv b/results/step7_pooled.csv
64	new file mode 100644
65	index 0000000..c906f87
66	--- /dev/null
67	+++ b/results/step7_pooled.csv
... [39476 more characters in the .jsonl file]
```

**Tool result** 

```
1	# Step N Review: Step title
2	
3	- Reviewer transcript: transcripts/NN_YYYY-MM-DD_reviewer_stepN.md
4	- What was reviewed: (Step 0: PLAN.md at commit abc1234; Steps 1-7: the diff from stepN-start to commit abc1234)
5	
6	## Comments (reviewer)
7	
8	One row per issue. Number the rows 1, 2, 3, ...
9	
10	| # | Severity | Location | Issue | Suggested fix |
11	| --- | --- | --- | --- | --- |
12	
13	## Decision log (student)
14	
15	One row per comment above, with the same number. Decision is Accepted or Rejected. For accepted comments, add the commit that fixed it.
16	
17	| # | Decision | Reason | Fixed in commit |
18	| --- | --- | --- | --- |
19	
```

**Tool call: Read** 2026-11-03T04:23:35.182Z

```
{
 "file_path": "c:\\Users\\thema\\OneDrive\\Desktop\\Project2\\project2-harness2\\project2-harness2\\.harness\\diffs\\step7_diff.patch",
 "offset": 633,
 "limit": 240
}
```

**Tool result** 2026-11-03T04:23:35.230Z

```
633	+    return {"strategy": strategy, "classifier": classifier, "year": t, "n": len(y_true),
634	+            **compute_metrics(y_true, y_pred), **confusion_counts(y_true, y_pred),
635	+            "train_seconds": seconds, "train_rows": train_rows, "window": f"{min(years)}-{max(years)}",
636	+            "convergence_warnings": n_conv}
637	+
638	+
639	+def run_window_strategy(
640	+    df: pd.DataFrame, strategy: str, model_name: str = "logreg", arrays: YearArrays | None = None
641	+) -> pd.DataFrame:
642	+    """Static, expanding or sliding strategy: for each test year t, fit on its window only, predict t.
643	+
644	+    The static window is the same for every t, so it is fitted once (same result as refitting five times).
645	+    Returns one row per test year.
646	+    """
647	+    arrays = year_arrays(df) if arrays is None else arrays
648	+    features = feature_columns(df)
649	+    rows, fitted = [], {}
650	+    for t in TEST_YEARS:
651	+        years = window_years(strategy, t)  # raises if any year >= t
652	+        if strategy != "static" or years not in fitted:
653	+            fitted[years] = fit_on_years(arrays, features, years, t, model_name)
654	+        pre, model, seconds, n_rows, n_conv = fitted[years]
655	+        X_t, y_t = arrays[t]
656	+        pred = model.predict(pre.transform(X_t))  # year t is only transformed/predicted here
657	+        # Static cost is paid once (first test year); later rows record 0 retraining seconds.
658	+        paid = seconds if (strategy != "static" or t == TEST_YEARS[0]) else 0.0
659	+        rows.append(_result_row(strategy, model_name, t, y_t, pred, paid, n_rows, years, n_conv))
660	+    return pd.DataFrame(rows)
661	+
662	+
663	+def run_incremental(df: pd.DataFrame, model_name: str = "sgd", arrays: YearArrays | None = None) -> pd.DataFrame:
664	+    """Incremental test-then-train: fit on 2014-2016, then for each t predict t and only afterwards `partial_fit` on t.
665	+
666	+    The preprocessor (zero-column mask, scaler) is fitted on 2014-2016 and frozen, so year t never influences it.
667	+    train_seconds of a row is the cost of the update that produced the model used for that row's prediction
668	+    (2017: the initial fit; later years: the partial_fit on the previous year).
669	+    """
670	+    arrays = year_arrays(df) if arrays is None else arrays
671	+    features = feature_columns(df)
672	+    pre, model, seconds, n_rows, n_conv = fit_on_years(arrays, features, tuple(TRAIN_YEARS), TEST_YEARS[0], model_name)
673	+    seen = list(TRAIN_YEARS)
674	+    rows = []
675	+    for t in TEST_YEARS:
676	+        if max(seen) >= t:  # every year used so far must precede the year being predicted
677	+            raise AssertionError(f"incremental model has seen {seen}, which includes a year >= {t}")
678	+        X_t, y_t = arrays[t]
679	+        Z_t = pre.transform(X_t)  # frozen preprocessor: transform only
680	+        pred = model.predict(Z_t)  # 1) predict t ...
681	+        rows.append(_resu
... [10120 more characters in the .jsonl file]
```

**Tool call: Grep** 2026-11-03T04:23:36.073Z

```
{
 "pattern": "def (fit|transform|__init__|check_no_overlap|prepare_split)|clip|Z_CLIP|class Preprocessor",
 "path": "c:\\Users\\thema\\OneDrive\\Desktop\\Project2\\project2-harness2\\project2-harness2\\src\\preprocess.py",
 "output_mode": "content"
}
```

**Tool result** 2026-11-03T04:23:36.197Z

```
18:    Z_CLIP,
23:def check_no_overlap(train_years: Iterable[int], test_years: Iterable[int]) -> None:
68:class Preprocessor:
69:    """log1p -> minimum-support column filter -> StandardScaler -> fixed clip, all learned from training rows only.
74:    def __init__(self, min_support: int = MIN_SUPPORT) -> None:
85:    def fit(self, X_train_raw: np.ndarray, feature_names: list[str] | None = None) -> "Preprocessor":
98:    def transform(self, X_raw: np.ndarray, clip: bool = True) -> np.ndarray:
99:        """Apply the fitted log1p, mask and scaler (never refits), clip to +-Z_CLIP; returns float32.
101:        `clip=False` is only for reporting the size of the extreme values.
109:        # Fixed constant clip: the same for train and test, nothing learned from any data.
110:        return np.clip(Z, -Z_CLIP, Z_CLIP, out=Z) if clip else Z
112:    def fit_transform(self, X_train_raw: np.ndarray, feature_names: list[str] | None = None) -> np.ndarray:
129:def prepare_split(
140:    X_train, X_test = pre.transform(X_train_raw, clip=False), pre.transform(X_test_raw, clip=False)
141:    clip_stats = clip_report(X_train, X_test)  # measured before clipping
142:    clip_by_year = clip_by_year_report(X_train, a["years_train"], X_test, a["years_test"])  # also before clipping
143:    np.clip(X_train, -Z_CLIP, Z_CLIP, out=X_train)
144:    np.clip(X_test, -Z_CLIP, Z_CLIP, out=X_test)
145:    return {"X_train": X_train, "X_test": X_test, "preprocessor": pre, "clip_stats": clip_stats,
146:            "clip_by_year": clip_by_year, **a}
149:def clip_by_year_report(
152:    """Per year (train and test): share of UNCLIPPED scaled entries beyond +-Z_CLIP and mean absolute z-score."""
157:            rows.append((side, int(year), int(A.shape[0]), float((A > Z_CLIP).mean()), float(A.mean(dtype=np.float64))))
158:    return pd.DataFrame(rows, columns=["side", "year", "n", "clip_share", "mean_abs_z"])
161:def clip_report(X_train: np.ndarray, X_test: np.ndarray) -> pd.DataFrame:
162:    """Max abs z and number of entries beyond +-Z_CLIP for UNCLIPPED scaled matrices; also the values after clipping."""
166:        rows.append((side, float(A.max()), int((A > Z_CLIP).sum()), float(min(A.max(), Z_CLIP)), 0))
167:    return pd.DataFrame(rows, columns=["side", "max_abs_z_before", "n_clipped", "max_abs_z_after", "n_beyond_clip_after"])
```

**Tool call: Read** 

```
{
 "file_path": "c:\\Users\\thema\\OneDrive\\Desktop\\Project2\\project2-harness2\\project2-harness2\\.harness\\diffs\\step7_diff.patch",
 "offset": 633,
 "limit": 240
}
```

**Tool call: Grep** 

```
{
 "pattern": "def (fit|transform|__init__|check_no_overlap|prepare_split)|clip|Z_CLIP|class Preprocessor",
 "path": "c:\\Users\\thema\\OneDrive\\Desktop\\Project2\\project2-harness2\\project2-harness2\\src\\preprocess.py",
 "output_mode": "content"
}
```

**Tool result** 

```
633	+    return {"strategy": strategy, "classifier": classifier, "year": t, "n": len(y_true),
634	+            **compute_metrics(y_true, y_pred), **confusion_counts(y_true, y_pred),
635	+            "train_seconds": seconds, "train_rows": train_rows, "window": f"{min(years)}-{max(years)}",
636	+            "convergence_warnings": n_conv}
637	+
638	+
639	+def run_window_strategy(
640	+    df: pd.DataFrame, strategy: str, model_name: str = "logreg", arrays: YearArrays | None = None
641	+) -> pd.DataFrame:
642	+    """Static, expanding or sliding strategy: for each test year t, fit on its window only, predict t.
643	+
644	+    The static window is the same for every t, so it is fitted once (same result as refitting five times).
645	+    Returns one row per test year.
646	+    """
647	+    arrays = year_arrays(df) if arrays is None else arrays
648	+    features = feature_columns(df)
649	+    rows, fitted = [], {}
650	+    for t in TEST_YEARS:
651	+        years = window_years(strategy, t)  # raises if any year >= t
652	+        if strategy != "static" or years not in fitted:
653	+            fitted[years] = fit_on_years(arrays, features, years, t, model_name)
654	+        pre, model, seconds, n_rows, n_conv = fitted[years]
655	+        X_t, y_t = arrays[t]
656	+        pred = model.predict(pre.transform(X_t))  # year t is only transformed/predicted here
657	+        # Static cost is paid once (first test year); later rows record 0 retraining seconds.
658	+        paid = seconds if (strategy != "static" or t == TEST_YEARS[0]) else 0.0
659	+        rows.append(_result_row(strategy, model_name, t, y_t, pred, paid, n_rows, years, n_conv))
660	+    return pd.DataFrame(rows)
661	+
662	+
663	+def run_incremental(df: pd.DataFrame, model_name: str = "sgd", arrays: YearArrays | None = None) -> pd.DataFrame:
664	+    """Incremental test-then-train: fit on 2014-2016, then for each t predict t and only afterwards `partial_fit` on t.
665	+
666	+    The preprocessor (zero-column mask, scaler) is fitted on 2014-2016 and frozen, so year t never influences it.
667	+    train_seconds of a row is the cost of the update that produced the model used for that row's prediction
668	+    (2017: the initial fit; later years: the partial_fit on the previous year).
669	+    """
670	+    arrays = year_arrays(df) if arrays is None else arrays
671	+    features = feature_columns(df)
672	+    pre, model, seconds, n_rows, n_conv = fit_on_years(arrays, features, tuple(TRAIN_YEARS), TEST_YEARS[0], model_name)
673	+    seen = list(TRAIN_YEARS)
674	+    rows = []
675	+    for t in TEST_YEARS:
676	+        if max(seen) >= t:  # every year used so far must precede the year being predicted
677	+            raise AssertionError(f"incremental model has seen {seen}, which includes a year >= {t}")
678	+        X_t, y_t = arrays[t]
679	+        Z_t = pre.transform(X_t)  # frozen preprocessor: transform only
680	+        pred = model.predict(Z_t)  # 1) predict t ...
681	+        rows.append(_resu
... [10120 more characters in the .jsonl file]
```

**Tool result** 

```
18:    Z_CLIP,
23:def check_no_overlap(train_years: Iterable[int], test_years: Iterable[int]) -> None:
68:class Preprocessor:
69:    """log1p -> minimum-support column filter -> StandardScaler -> fixed clip, all learned from training rows only.
74:    def __init__(self, min_support: int = MIN_SUPPORT) -> None:
85:    def fit(self, X_train_raw: np.ndarray, feature_names: list[str] | None = None) -> "Preprocessor":
98:    def transform(self, X_raw: np.ndarray, clip: bool = True) -> np.ndarray:
99:        """Apply the fitted log1p, mask and scaler (never refits), clip to +-Z_CLIP; returns float32.
101:        `clip=False` is only for reporting the size of the extreme values.
109:        # Fixed constant clip: the same for train and test, nothing learned from any data.
110:        return np.clip(Z, -Z_CLIP, Z_CLIP, out=Z) if clip else Z
112:    def fit_transform(self, X_train_raw: np.ndarray, feature_names: list[str] | None = None) -> np.ndarray:
129:def prepare_split(
140:    X_train, X_test = pre.transform(X_train_raw, clip=False), pre.transform(X_test_raw, clip=False)
141:    clip_stats = clip_report(X_train, X_test)  # measured before clipping
142:    clip_by_year = clip_by_year_report(X_train, a["years_train"], X_test, a["years_test"])  # also before clipping
143:    np.clip(X_train, -Z_CLIP, Z_CLIP, out=X_train)
144:    np.clip(X_test, -Z_CLIP, Z_CLIP, out=X_test)
145:    return {"X_train": X_train, "X_test": X_test, "preprocessor": pre, "clip_stats": clip_stats,
146:            "clip_by_year": clip_by_year, **a}
149:def clip_by_year_report(
152:    """Per year (train and test): share of UNCLIPPED scaled entries beyond +-Z_CLIP and mean absolute z-score."""
157:            rows.append((side, int(year), int(A.shape[0]), float((A > Z_CLIP).mean()), float(A.mean(dtype=np.float64))))
158:    return pd.DataFrame(rows, columns=["side", "year", "n", "clip_share", "mean_abs_z"])
161:def clip_report(X_train: np.ndarray, X_test: np.ndarray) -> pd.DataFrame:
162:    """Max abs z and number of entries beyond +-Z_CLIP for UNCLIPPED scaled matrices; also the values after clipping."""
166:        rows.append((side, float(A.max()), int((A > Z_CLIP).sum()), float(min(A.max(), Z_CLIP)), 0))
167:    return pd.DataFrame(rows, columns=["side", "max_abs_z_before", "n_clipped", "max_abs_z_after", "n_beyond_clip_after"])
```

**Tool call: Read** 2026-11-03T04:24:00.427Z

```
{
 "file_path": "c:\\Users\\thema\\OneDrive\\Desktop\\Project2\\project2-harness2\\project2-harness2\\src\\preprocess.py",
 "offset": 20,
 "limit": 95
}
```

**Tool result** 2026-11-03T04:24:00.491Z

```
20	from src.data import feature_columns
21	
22	
23	def check_no_overlap(train_years: Iterable[int], test_years: Iterable[int]) -> None:
24	    """Raise ValueError unless train and test years are non-empty, disjoint, and every train year precedes every test year."""
25	    train, test = set(train_years), set(test_years)
26	    if not train or not test:
27	        raise ValueError("train_years and test_years must both be non-empty")
28	    if train & test:
29	        raise ValueError(f"train and test years overlap: {sorted(train & test)}")
30	    if max(train) >= min(test):
31	        raise ValueError(f"training years {sorted(train)} must all precede test years {sorted(test)}")
32	
33	
34	def split_by_year(
35	    df: pd.DataFrame,
36	    train_years: Iterable[int] = TRAIN_YEARS,
37	    test_years: Iterable[int] = TEST_YEARS,
38	) -> tuple[pd.DataFrame, pd.DataFrame]:
39	    """Return (train, test) frames selected by the `year` column, after checking the years cannot leak."""
40	    train_years, test_years = tuple(train_years), tuple(test_years)
41	    check_no_overlap(train_years, test_years)  # guard first: nothing is selected for a bad split
42	    train = df[df[YEAR_COL].isin(train_years)]
43	    test = df[df[YEAR_COL].isin(test_years)]
44	    # Every requested year must be present, otherwise the split is silently smaller than asked for.
45	    for name, part, years in (("train", train, train_years), ("test", test, test_years)):
46	        missing = sorted(set(years) - set(part[YEAR_COL].unique()))
47	        if missing:
48	            raise ValueError(f"requested {name} years missing from the data: {missing}")
49	    return train, test
50	
51	
52	def apply_log1p(X: np.ndarray) -> np.ndarray:
53	    """Return log(1 + X) as float32; raises ValueError on NaN/inf or negative input (counts must be finite and >= 0)."""
54	    if not np.isfinite(X).all():  # checked once here, so fit and transform each pay for it once per call
55	        raise ValueError("log1p input must be finite (no NaN or inf)")
56	    if X.size and X.min() < 0:
57	        raise ValueError("log1p input must be non-negative")
58	    return np.log1p(X, dtype=np.float32)
59	
60	
61	def nonzero_feature_mask(X_train: np.ndarray, min_support: int = MIN_SUPPORT) -> np.ndarray:
62	    """Boolean mask of columns with at least `min_support` non-zero values in the TRAINING rows."""
63	    if min_support < 1:
64	        raise ValueError(f"min_support must be >= 1, got {min_support}")
65	    return (X_train != 0).sum(axis=0) >= min_support
66	
67	
68	class Preprocessor:
69	    """log1p -> minimum-support column filter -> StandardScaler -> fixed clip, all learned from training rows only.
70	
71	    sklearn-like (fit/transform/fit_transform), not a BaseEstimator: no get_params, not usable in a Pipeline.
72	    """
73	
74	    def __init__(self, min_support: int = MIN_SUPPORT) -> None:
75	        """Store the support threshold; nothing is learned until `fit`."""
76	        if min_support < 1:
77	
... [2387 more characters in the .jsonl file]
```

**Tool call: Bash** 2026-11-03T04:24:35.667Z

```
{
 "command": "cd \"c:/Users/thema/OneDrive/Desktop/Project2/project2-harness2/project2-harness2\" && git rev-parse --short HEAD && git status --short | head"
}
```

**Tool result** 2026-11-03T04:24:37.856Z

```
276df23
```

**Tool call: Write** 2026-11-03T04:24:59.743Z

```
{
 "file_path": "C:\\Users\\thema\\OneDrive\\Desktop\\Project2\\project2-harness2\\project2-harness2\\reviews\\step7_review.md",
 "content": "# Step 7 Review: Sustainable ML Approach\n\n- Reviewer transcript: transcripts/32_2026-11-03_reviewer_step7.md\n- What was reviewed: the diff from step7-start to commit 276df23 (.harness/diffs/step7_diff.patch), with src/preprocess.py opened for context. I read AGENTS.md, PLAN.md and the diff only. I ran no commands that execute code, so every claim below comes from reading the code and the committed result tables.\n\n**Leakage checks (lead engineer's list). I found no defect in any of them.**\n1. For every test year t, the mask, scaler, clip statistics and model are fit on `window_years(strategy, t)` only. The clip is the constant `Z_CLIP`. `fit_on_years` calls `check_no_overlap(years, [t])`, which enforces `max(train) < min(test)`, and `Preprocessor.fit` sees only the stacked window rows.\n2. The incremental strategy predicts year t first (`model.predict(Z_t)`) and calls `partial_fit` afterwards. The scaler and mask are frozen on 2014-2016. The seen-years assertion runs before every prediction.\n3. The static baseline is never updated. `static_from_models` only calls `predict` on the Step 4 objects. `run_incremental` trains a fresh SGD, so the Step 4 SGD is not mutated.\n4. All strategies are scored on the same test years, with the same `compute_metrics` (malware is the positive class), and on the same row counts (n = 18,000 / 18,000 / 3,000 x 3). The 2017 rows of static, expanding and sliding are identical, as expected.\n5. The sliding window is `range(t-3, t)`. `step7_window_composition.csv` confirms that 2021 uses 2018-2020 only.\n6. Per-window preprocessing is refit on that window only.\n\nEvaluation is time-forward, there is a never-updated baseline, and the comparison is like-for-like within a classifier. The comments below are about robustness and how the results should be read.\n\n## Comments (reviewer)\n\n| # | Severity | Location | Issue | Suggested fix |\n| --- | --- | --- | --- | --- |\n| 1 | Medium | `src/sustainable.py` `static_from_models` / `run_all_strategies` | The \"static\" rows come from whatever `split` and `models` the caller passes. There is no check that they are the 2014-2016 fit, or that `split[\"X_test\"]` holds the same rows as `arrays[t]` used by the other strategies. The Step 4 guard `train_all_from_split` is skipped. Today the tables agree (static and expanding match exactly on 2017), but a stale or mismatched split would silently break the \"same test rows\" requirement. | In `static_from_models`, assert `set(split[\"years_train\"]) == set(TRAIN_YEARS)`. Also assert per year that `split[\"y_test\"][sel]` equals `arrays[t][1]`, or at least that the lengths match. |\n| 2 | Medium | Results interpretation (`step7_summary`, `step7_pooled`) | Every strategy collapses to near chance in 2019: accuracy 0.54-0.56, recall about 0.99, precision about 0.52. That means almost everythin
... [4996 more characters in the .jsonl file]
```

**Tool call: Bash** 2026-11-03T04:25:00.408Z

```
{
 "command": "cd \"C:/Users/thema/OneDrive/Desktop/Project2/project2-harness2/project2-harness2\" && git add reviews/step7_review.md && git commit -q -m \"[reviewer] Step 7 review\n\nCo-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>\" && git log --oneline -1"
}
```

**Tool result** 2026-11-03T04:25:01.318Z

```
File created successfully at: C:\Users\thema\OneDrive\Desktop\Project2\project2-harness2\project2-harness2\reviews\step7_review.md (file state is current in your context — no need to Read it back)
```

**Tool result** 2026-11-03T04:25:01.713Z

```
warning: in the working copy of 'reviews/step7_review.md', LF will be replaced by CRLF the next time Git touches it
e2613f6 [reviewer] Step 7 review
```

## Assistant 2026-11-03T04:25:15.906Z

I finished the Step 7 review and committed it as `e2613f6`. I didn't run any code; every finding comes from reading the diff and `src/preprocess.py`.

**Leakage checks:** I checked all six items on your list and found no leakage:
- Each year-t fit uses only that window's rows.
- The incremental strategy predicts year t before `partial_fit` on it, with a scaler frozen on 2014-2016.
- The static baseline is only used to predict and is never updated.
- All strategies use the same test years, row counts and metrics.
- The sliding window is exactly the 3 years before t.

**Comments (8):**
- **Medium:**
  1. The static rows trust whatever `split` and `models` the caller passes, with no check that they match the 2014-2016 fit or the same test rows.
  2. Every strategy collapses to near chance in 2019 (accuracy 0.54-0.56, recall about 0.99). The headline +0.10 F1 gain is really a 2020-21 effect. I can't tell from the diff whether the cause is real drift or a data difference between the 9,000-row and 1,500-row files.
  3. The differences between expanding, sliding and incremental are small, from one run with no uncertainty estimate. They are also confounded by window size and by the frozen preprocessing in the incremental strategy.
- **Low:**
  4. Training cost isn't comparable: static logreg shows 2.65 s against 4.87 s for expanding 2017, which is an identical fit.
  5. Missing static training seconds silently become a total of 0.0.
  6. Step 7 has no duplicate-rows sensitivity check, so 2018 gains may be partly inflated by cross-year duplicates.
  7. Thin handling of missing years, and memory use is high on a laptop.
  8. Redundant leakage guards in `fit_on_years` (style only).

I left the Decision log empty and edited nothing else. The commit message ends with the Sonnet 5.5 attribution line.
