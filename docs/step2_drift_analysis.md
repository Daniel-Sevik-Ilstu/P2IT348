# Step 2 Report: Data Drift Analysis

Written by the builder agent. All numbers come from `python -m src.main --step 2` (about one minute); tables are in `results/step2_*.csv`.

## Method

**Data and sampling.** The full dataset has 99,000 rows (2014-2018: 18,000 per year; 2019-2021: 3,000 per year). To make KS p-values comparable across year pairs, every year is subsampled to the same size, **3,000 rows (the smallest year), with `random_state=42`, class-balanced (1,500 malware + 1,500 goodware)**. Malware and goodware are pooled within a year; balanced sampling removes any change in class mix as a source of drift. Features are the 1,848 API-call counts (raw counts, not log-transformed).

**Feature drift (KS).** For each of the 28 year pairs and each feature we ran `scipy.stats.ks_2samp` (default `method="auto"`: scipy tries the exact calculation and falls back to the asymptotic one when it is unsuccessful on heavily tied counts; the fallback is silenced in code because it is expected). A feature that is constant with the same value in both samples (in practice all-zero in both) is **skipped, not tested, and counted** (`n_skipped`); no tested feature produced NaN (checked in code). Per pair: `mean_ks` = mean KS statistic over one **fixed set of 1,138 features for every pair** (features that are non-constant in at least one of the eight year samples), with skipped features counted as KS = 0 (effect size; 0 = identical distributions, 1 = disjoint); `pct_significant` = percent of tested features with `p < 0.05 / m`, where `m` is the number of tested features in that pair (Bonferroni). `n_tested` still differs between pairs (787-923 features skipped), but that now affects only the significance share, not `mean_ks`, which uses the same features in every pair. The per-feature `mean_ks` in the top-20 table fills skipped years with 0 before averaging over the seven "vs 2014" comparisons.

**Caveats.** KS assumes continuous data; these are tied counts, which makes p-values conservative. Duplicate rows (many in 2014-2018, see Step 1) mean the samples are not independent, which inflates significance. So the KS statistic is the main signal and `pct_significant` is secondary.

**Concept drift.** Accuracy matrix: for each year i, `log1p` -> minimum-support filter (keep columns non-zero in at least `MIN_SUPPORT = 10` of year i's training rows, same rule as Step 3) -> `StandardScaler` (both fit on year i's training rows only) -> `LogisticRegression(max_iter=1000, random_state=42)` is trained on year i's 3,000-row sample, then scored on year j. The diagonal uses a stratified 70/30 split of year i (accuracy on the held-out 30%); off-diagonal cells use the whole year-j sample. Because train and test years differ in both feature distribution and labelling rule, the matrix measures **combined drift** (covariate shift plus concept drift), not concept drift alone. Convergence: no fit raised a `ConvergenceWarning` (`max_iter=1000` was enough for all eight models). This is a diagnostic: it trains on 2017-2021 too and is exempt from the train-2014-2016 rule (PLAN.md section 0). Nothing from it feeds Steps 3-7. It is one run on one sample per year, so small differences (a point or two) should not be over-read; the noise level was not measured.

## Results: mean KS per year pair

Each year vs 2014:

| year_a | year_b | n_tested | n_skipped | mean_ks | pct_significant |
|---|---|---|---|---|---|
| 2014 | 2015 | 925 | 923 | 0.0226 | 16.4 |
| 2014 | 2016 | 976 | 872 | 0.0363 | 21.8 |
| 2014 | 2017 | 959 | 889 | 0.0437 | 25.9 |
| 2014 | 2018 | 1034 | 814 | 0.0432 | 25.1 |
| 2014 | 2019 | 1045 | 803 | 0.0515 | 27.3 |
| 2014 | 2020 | 1006 | 842 | 0.0612 | 34.7 |
| 2014 | 2021 | 1061 | 787 | 0.0849 | 36.9 |

Each year vs the previous year:

| year_a | year_b | n_tested | n_skipped | mean_ks | pct_significant |
|---|---|---|---|---|---|
| 2014 | 2015 | 925 | 923 | 0.0226 | 16.4 |
| 2015 | 2016 | 952 | 896 | 0.0241 | 16.9 |
| 2016 | 2017 | 959 | 889 | 0.0276 | 21.8 |
| 2017 | 2018 | 1002 | 846 | 0.0241 | 15.4 |
| 2018 | 2019 | 1034 | 814 | 0.0277 | 16.1 |
| 2019 | 2020 | 1037 | 811 | 0.0231 | 17.1 |
| 2020 | 2021 | 1036 | 812 | 0.0487 | 26.5 |

Full year x year matrix of mean KS (`results/step2_ks_matrix.csv`, heatmap `results/step2_ks_matrix.png`):

| year | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 |
|---|---|---|---|---|---|---|---|---|
| 2014 | 0.0000 | 0.0226 | 0.0363 | 0.0437 | 0.0432 | 0.0515 | 0.0612 | 0.0849 |
| 2015 | 0.0226 | 0.0000 | 0.0241 | 0.0335 | 0.0315 | 0.0414 | 0.0527 | 0.0819 |
| 2016 | 0.0363 | 0.0241 | 0.0000 | 0.0276 | 0.0278 | 0.0421 | 0.0513 | 0.0717 |
| 2017 | 0.0437 | 0.0335 | 0.0276 | 0.0000 | 0.0241 | 0.0459 | 0.0533 | 0.0786 |
| 2018 | 0.0432 | 0.0315 | 0.0278 | 0.0241 | 0.0000 | 0.0277 | 0.0396 | 0.0725 |
| 2019 | 0.0515 | 0.0414 | 0.0421 | 0.0459 | 0.0277 | 0.0000 | 0.0231 | 0.0640 |
| 2020 | 0.0612 | 0.0527 | 0.0513 | 0.0533 | 0.0396 | 0.0231 | 0.0000 | 0.0487 |
| 2021 | 0.0849 | 0.0819 | 0.0717 | 0.0786 | 0.0725 | 0.0640 | 0.0487 | 0.0000 |

Pairs ranked by mean KS (top 5 of 28; all in `results/step2_ks_all_pairs.csv`):

| year_a | year_b | n_tested | n_skipped | mean_ks | pct_significant |
|---|---|---|---|---|---|
| 2014 | 2021 | 1061 | 787 | 0.0849 | 36.9 |
| 2015 | 2021 | 1043 | 805 | 0.0819 | 36.7 |
| 2017 | 2021 | 1034 | 814 | 0.0786 | 35.8 |
| 2018 | 2021 | 1047 | 801 | 0.0725 | 34.2 |
| 2016 | 2021 | 1056 | 792 | 0.0717 | 37.5 |

## Features that drift most

Top 20 features by mean KS over the seven "vs 2014" comparisons (`ks_YYYY` = KS statistic of that year against 2014, shown for 3 of the 7 years; full set in `results/step2_top20_features.csv`; `mean_YYYY` = the feature's mean call count in that year's sample):

| feature | mean_ks | ks_2015 | ks_2018 | ks_2021 | mean_2014 | mean_2015 | mean_2016 | mean_2017 | mean_2018 | mean_2019 | mean_2020 | mean_2021 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `Landroid/os/Process;.myPid:()I` | 0.4603 | 0.2000 | 0.5030 | 0.6483 | 1.0940 | 2.5167 | 5.8603 | 6.6807 | 11.4653 | 9.5953 | 7.2123 | 11.3260 |
| `Landroid/app/NotificationManager;.notify:(Ljava/lang/String;ILandroid/app/Notification;)V` | 0.4092 | 0.2623 | 0.3940 | 0.5940 | 0.1317 | 0.5623 | 1.0477 | 1.1193 | 0.9913 | 0.8553 | 0.9697 | 1.5280 |
| `Landroid/webkit/WebView;.evaluateJavascript:(Ljava/lang/String;Landroid/webkit/ValueCallback;)V` | 0.3903 | 0.2603 | 0.3990 | 0.5090 | 0.0393 | 0.6267 | 1.0933 | 1.2407 | 1.1853 | 1.3430 | 2.0657 | 3.0843 |
| `Landroid/os/Handler;.obtainMessage:(IIILjava/lang/Object;)Landroid/os/Message;` | 0.3891 | 0.1133 | 0.4220 | 0.6040 | 0.1710 | 0.6147 | 1.4957 | 1.6517 | 1.9340 | 2.5133 | 3.6627 | 6.1830 |
| `Landroid/os/Handler;.obtainMessage:(III)Landroid/os/Message;` | 0.3841 | 0.1280 | 0.4037 | 0.5870 | 0.2877 | 0.8810 | 2.1207 | 2.3100 | 2.0237 | 2.1160 | 2.9827 | 4.4690 |
| `Landroid/os/PowerManager$WakeLock;.acquire:(J)V` | 0.3760 | 0.1733 | 0.3333 | 0.6247 | 0.3930 | 0.7773 | 1.0967 | 1.0830 | 1.2033 | 1.6153 | 2.0510 | 2.9970 |
| `Landroid/webkit/WebView;.getTitle:()Ljava/lang/String;` | 0.3706 | 0.2280 | 0.3930 | 0.4787 | 0.1443 | 0.6467 | 1.0187 | 1.2327 | 0.9670 | 0.8770 | 1.1863 | 2.1153 |
| `Landroid/content/Context;.getApplicationInfo:()Landroid/content/pm/ApplicationInfo;` | 0.3676 | 0.2243 | 0.3363 | 0.6060 | 4.2203 | 6.7013 | 9.9817 | 8.7307 | 9.6817 | 10.9233 | 13.1700 | 21.3390 |
| `Ljava/lang/StringBuilder;.append:(Ljava/lang/CharSequence;)Ljava/lang/StringBuilder;` | 0.3450 | 0.2173 | 0.3143 | 0.5447 | 2.2670 | 3.8230 | 5.5100 | 4.6550 | 4.2940 | 3.9817 | 4.8050 | 7.7267 |
| `Ljava/lang/String;.getBytes:(Ljava/nio/charset/Charset;)[B` | 0.3312 | 0.1127 | 0.2973 | 0.6450 | 0.2530 | 0.8707 | 1.5807 | 1.2147 | 2.9073 | 6.1820 | 10.5963 | 16.1970 |
| `Ljava/net/HttpURLConnection;.addRequestProperty:(Ljava/lang/String;Ljava/lang/String;)V` | 0.3223 | 0.1427 | 0.3650 | 0.4650 | 1.3877 | 2.1397 | 4.2607 | 4.3897 | 3.8893 | 3.4273 | 4.6693 | 9.9543 |
| `Ldalvik/system/DexClassLoader;.loadClass:(Ljava/lang/String;)Ljava/lang/Class;` | 0.3056 | 0.2303 | 0.2093 | 0.4053 | 2.8343 | 4.1593 | 4.5950 | 4.8703 | 2.8817 | 1.4903 | 1.1247 | 0.8993 |
| `Landroid/webkit/WebView;.post:(Ljava/lang/Runnable;)Z` | 0.3053 | 0.1980 | 0.3347 | 0.3913 | 0.1687 | 0.3680 | 0.4593 | 0.8157 | 0.6807 | 0.4243 | 0.5627 | 1.0867 |
| `Ljava/io/FileOutputStream;.write:(I)V` | 0.3028 | 0.1113 | 0.3270 | 0.4467 | 0.0663 | 0.1773 | 0.3653 | 0.4220 | 0.4343 | 0.4617 | 0.5207 | 0.9990 |
| `Ljava/net/HttpURLConnection;.getHeaderFields:()Ljava/util/Map;` | 0.2976 | 0.1240 | 0.3410 | 0.4373 | 0.8850 | 1.5223 | 2.9410 | 3.0503 | 3.2933 | 3.5897 | 4.8083 | 8.5963 |
| `Ljava/lang/StringBuilder;.append:(Ljava/lang/Object;)Ljava/lang/StringBuilder;` | 0.2957 | 0.1430 | 0.2427 | 0.4390 | 219.1010 | 260.5583 | 344.8433 | 290.4267 | 294.5097 | 302.2830 | 366.9540 | 582.8527 |
| `Ljava/lang/StringBuilder;.append:(I)Ljava/lang/StringBuilder;` | 0.2906 | 0.1697 | 0.2203 | 0.3803 | 285.7640 | 377.2587 | 485.0413 | 459.8510 | 412.8673 | 389.4407 | 450.7463 | 673.0033 |
| `Ljava/net/HttpURLConnection;.setFixedLengthStreamingMode:(I)V` | 0.2881 | 0.1140 | 0.3103 | 0.4403 | 0.5270 | 0.9330 | 1.7680 | 2.0033 | 1.6837 | 1.5987 | 2.1600 | 3.6363 |
| `Ljava/lang/String;.valueOf:(Ljava/lang/Object;)Ljava/lang/String;` | 0.2795 | 0.0753 | 0.2713 | 0.5683 | 50.1507 | 56.0157 | 119.2497 | 191.5253 | 217.5900 | 250.7293 | 373.3980 | 578.9250 |
| `Ljava/lang/StringBuilder;.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;` | 0.2778 | 0.1307 | 0.2317 | 0.3867 | 2135.9553 | 2492.0787 | 3408.9897 | 2850.3007 | 2936.2940 | 3095.0543 | 3641.4847 | 5657.1597 |

## Years that differ most

- The pair that differs most is **2014 vs 2021** (mean KS 0.0849). 2021 is the most different year from every other year except 2020, whose largest distance is to 2014 (0.061, against 0.049 to 2021).
- Mean KS against 2014 rises with the gap: 2015: 0.023, 2016: 0.036, 2017: 0.044, 2018: 0.043, 2019: 0.052, 2020: 0.061, 2021: 0.085. The exception is 2018 (0.0432), marginally below 2017 (0.0437).
- Consecutive-year KS is small (0.023-0.028) until 2020 -> 2021, which jumps to 0.0487, the largest year-to-year step.
- Many top drifting features rise sharply in call counts after 2014; for example `Landroid/os/Process;.myPid:()I` goes from a mean of about 1 call in 2014 to about 11 in 2018 and 2021. Possible causes (larger apps, changing Android API use) were not tested.

## Concept drift: accuracy matrix (train year = row, test year = column)

| train \ test | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 |
|---|---|---|---|---|---|---|---|---|
| 2014 | 0.9744 | 0.9280 | 0.9130 | 0.8177 | 0.8873 | 0.6377 | 0.6303 | 0.5190 |
| 2015 | 0.9350 | 0.9678 | 0.9603 | 0.8757 | 0.9017 | 0.5783 | 0.5603 | 0.5737 |
| 2016 | 0.9193 | 0.9433 | 0.9767 | 0.9667 | 0.9353 | 0.5743 | 0.5410 | 0.3507 |
| 2017 | 0.8530 | 0.8127 | 0.9000 | 0.9744 | 0.9413 | 0.6513 | 0.6407 | 0.6700 |
| 2018 | 0.8510 | 0.8413 | 0.8777 | 0.9653 | 0.9656 | 0.6000 | 0.5793 | 0.6400 |
| 2019 | 0.5727 | 0.6220 | 0.7333 | 0.7687 | 0.8540 | 0.9611 | 0.9370 | 0.7280 |
| 2020 | 0.6340 | 0.6330 | 0.6807 | 0.7640 | 0.7800 | 0.8870 | 0.9522 | 0.9333 |
| 2021 | 0.6047 | 0.6297 | 0.6810 | 0.6467 | 0.7107 | 0.8233 | 0.8810 | 0.9589 |

(`results/step2_accuracy_matrix.csv`, heatmap `results/step2_accuracy_matrix.png`.)

Reading it:
- The diagonal (held-out same-year data) is 0.95-0.98 (optimistic, see "Duplicates and the diagonal" below).
- Models trained on 2014-2018 score 0.52-0.67 on 2019-2021, except the 2016 model on 2021, which scores 0.35. That is far below the 0.50 chance level for balanced data.
- Models trained on 2019-2021 score 0.57-0.77 on 2014-2017.
- The break between 2018 and 2019 is the sharpest: the 2018 model drops from 0.97 on 2018 to 0.60 on 2019.
- Models trained on one of the years 2019-2021 do better on the next year (0.94 for 2019 -> 2020, 0.93 for 2020 -> 2021).
- **The low cell survives the min-support filter.** Before the filter (first version of this report) the 2016 -> 2021 cell was 0.362 and the 2021 sample had max |z| = 214 under the 2016 scaler. After the filter (686 columns kept for 2016) it is 0.351, with max |z| = 41 and 50 columns above 20. So extrapolation from rare columns is not the main cause. In an ad hoc check (not in `src/`) the 2016 model labels 75% of the 2021 rows malware: it catches 60% of 2021 malware but only 10% of 2021 goodware are classified correctly. Counts of many API calls in 2021 apps are much larger than in 2016 (e.g. `StringBuilder.append(String)` mean 5,657 vs 3,409), so 2021 goodware looks like 2016 malware to a model that learned "heavy API use = malware". This is covariate shift plus a learned boundary that does not transfer; I did not test it further.

## Duplicates and the diagonal (review #3)

The diagonal of the accuracy matrix is a random stratified 70/30 split inside one year sample. The samples contain many exact duplicate rows (identical feature vectors), so a duplicate can land in both the training and held-out parts, and the **diagonal is optimistic** compared with the cross-year cells. Duplicates are kept (AGENTS.md); the split was not changed. Duplicate feature rows per 3,000-row sample (rows identical to an earlier row; counted with `DataFrame.duplicated` on the 1,848 features, in an ad hoc check, not in `src/`):

| year | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 |
|---|---|---|---|---|---|---|---|---|
| duplicate rows | 508 | 688 | 770 | 1,440 | 1,632 | 1,741 | 1,845 | 1,831 |
| share of sample | 17% | 23% | 26% | 48% | 54% | 58% | 62% | 61% |

Nearly all duplicates also share the label (e.g. 2021: 1,826 of 1,831 with label included). The gap between the diagonal and the off-diagonal cells is therefore partly inflated, most for 2017-2021.

## Reading `pct_significant` (review #6)

`pct_significant` is computed per year pair with a Bonferroni correction over that pair's tested features only. It is a descriptive share, not a family-wise test across the 28 pairs, and should not be read as a test result across pairs. With 3,000 rows per sample, ties and duplicates, almost any real shift is significant, so `mean_ks` is the main signal.

## What this means for the models

- A model trained on 2014-2016 faces test years that are increasingly far from it in feature space (mean KS against 2014 of 0.04 for 2017 up to 0.08 for 2021). Expect performance to decrease for later test years, with the largest losses on 2019-2021.
- The accuracy matrix suggests this is combined drift (feature shift plus a changed decision boundary; the matrix cannot separate the two): the 2014-2016 models reach 0.82-0.97 on 2017-2018 but only 0.35-0.64 on 2019-2021. The matrix is a prediction only; Step 6 tests it with the real pipeline (all of 2014-2016 pooled, all rows).
- The mean KS matrix changes smoothly while accuracy collapses at 2019, so a modest average feature shift can still move the decision boundary a lot. We did not separate genuine change in app behaviour from dataset effects (2019-2021 have 6x fewer rows per year than 2014-2018).
- For Step 7: retraining on recent years looks promising, since adjacent-year pairs from 2019 on score about 0.94 while old models score 0.35-0.67 on those years. This is a hint to be verified in Step 7, not a result.
- Limitations: one 3,000-row sample per year (seed 42), no repeats; duplicates remain in the samples; the set of skipped all-zero features differs per pair (affects `n_tested` and the significance share only).
