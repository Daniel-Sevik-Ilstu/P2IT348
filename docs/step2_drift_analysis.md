# Step 2 Report: Data Drift Analysis

Written by the builder agent. All numbers come from `python -m src.main --step 2` (about one minute); tables are in `results/step2_*.csv`.

## Method

**Data and sampling.** The full dataset has 99,000 rows (2014-2018: 18,000 per year; 2019-2021: 3,000 per year). To make KS p-values comparable across year pairs, every year is subsampled to the same size, **3,000 rows (the smallest year), with `random_state=42`, class-balanced (1,500 malware + 1,500 goodware)**. Malware and goodware are pooled within a year; balanced sampling removes any change in class mix as a source of drift. Features are the 1,848 API-call counts (raw counts, not log-transformed).

**Feature drift (KS).** For each of the 28 year pairs and each feature we ran `scipy.stats.ks_2samp` (`method="asymp"`, because the exact method fails to converge on heavily tied count data). A feature that is constant with the same value in both samples (in practice all-zero in both) is **skipped, not tested, and counted** (`n_skipped`); no tested feature produced NaN (checked in code). Per pair: `mean_ks` = mean KS statistic over tested features (effect size; 0 = identical distributions, 1 = disjoint); `pct_significant` = percent of tested features with `p < 0.05 / m`, where `m` is the number of tested features in that pair (Bonferroni). `n_tested` differs between pairs (787-923 features skipped), so the feature set behind `mean_ks` differs slightly from pair to pair.

**Caveats.** KS assumes continuous data; these are tied counts, which makes p-values conservative. Duplicate rows (many in 2014-2018, see Step 1) mean the samples are not independent, which inflates significance. So the KS statistic is the main signal and `pct_significant` is secondary.

**Concept drift.** Accuracy matrix: for each year i, `log1p` -> `StandardScaler` (fit on year i's training rows only) -> `LogisticRegression(max_iter=1000, random_state=42)` is trained on year i's 3,000-row sample, then scored on year j. The diagonal uses a stratified 70/30 split of year i (accuracy on the held-out 30%); off-diagonal cells use the whole year-j sample. This is a diagnostic: it trains on 2017-2021 too and is exempt from the train-2014-2016 rule (PLAN.md section 0). Nothing from it feeds Steps 3-7. It is one run on one sample per year, so small differences (a point or two) should not be over-read; the noise level was not measured.

## Results: mean KS per year pair

Each year vs 2014:

| year_a | year_b | n_tested | n_skipped | mean_ks | pct_significant |
|---|---|---|---|---|---|
| 2014.0000 | 2015.0000 | 925.0000 | 923.0000 | 0.0278 | 16.4000 |
| 2014.0000 | 2016.0000 | 976.0000 | 872.0000 | 0.0423 | 21.8000 |
| 2014.0000 | 2017.0000 | 959.0000 | 889.0000 | 0.0518 | 25.9000 |
| 2014.0000 | 2018.0000 | 1034.0000 | 814.0000 | 0.0475 | 25.1000 |
| 2014.0000 | 2019.0000 | 1045.0000 | 803.0000 | 0.0561 | 27.3000 |
| 2014.0000 | 2020.0000 | 1006.0000 | 842.0000 | 0.0692 | 34.7000 |
| 2014.0000 | 2021.0000 | 1061.0000 | 787.0000 | 0.0910 | 36.9000 |

Each year vs the previous year:

| year_a | year_b | n_tested | n_skipped | mean_ks | pct_significant |
|---|---|---|---|---|---|
| 2014.0000 | 2015.0000 | 925.0000 | 923.0000 | 0.0278 | 16.4000 |
| 2015.0000 | 2016.0000 | 952.0000 | 896.0000 | 0.0288 | 16.9000 |
| 2016.0000 | 2017.0000 | 959.0000 | 889.0000 | 0.0327 | 21.8000 |
| 2017.0000 | 2018.0000 | 1002.0000 | 846.0000 | 0.0274 | 15.6000 |
| 2018.0000 | 2019.0000 | 1034.0000 | 814.0000 | 0.0304 | 16.1000 |
| 2019.0000 | 2020.0000 | 1037.0000 | 811.0000 | 0.0253 | 17.1000 |
| 2020.0000 | 2021.0000 | 1036.0000 | 812.0000 | 0.0535 | 26.5000 |

Full year x year matrix of mean KS (`results/step2_ks_matrix.csv`, heatmap `results/step2_ks_matrix.png`):

| year | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 |
|---|---|---|---|---|---|---|---|---|
| 2014.0000 | 0.0000 | 0.0278 | 0.0423 | 0.0518 | 0.0475 | 0.0561 | 0.0692 | 0.0910 |
| 2015.0000 | 0.0278 | 0.0000 | 0.0288 | 0.0408 | 0.0355 | 0.0459 | 0.0609 | 0.0894 |
| 2016.0000 | 0.0423 | 0.0288 | 0.0000 | 0.0327 | 0.0309 | 0.0461 | 0.0584 | 0.0773 |
| 2017.0000 | 0.0518 | 0.0408 | 0.0327 | 0.0000 | 0.0274 | 0.0508 | 0.0620 | 0.0865 |
| 2018.0000 | 0.0475 | 0.0355 | 0.0309 | 0.0274 | 0.0000 | 0.0304 | 0.0438 | 0.0788 |
| 2019.0000 | 0.0561 | 0.0459 | 0.0461 | 0.0508 | 0.0304 | 0.0000 | 0.0253 | 0.0688 |
| 2020.0000 | 0.0692 | 0.0609 | 0.0584 | 0.0620 | 0.0438 | 0.0253 | 0.0000 | 0.0535 |
| 2021.0000 | 0.0910 | 0.0894 | 0.0773 | 0.0865 | 0.0788 | 0.0688 | 0.0535 | 0.0000 |

Pairs ranked by mean KS (top 5 of 28; all in `results/step2_ks_all_pairs.csv`):

| year_a | year_b | n_tested | n_skipped | mean_ks | pct_significant |
|---|---|---|---|---|---|
| 2014.0000 | 2021.0000 | 1061.0000 | 787.0000 | 0.0910 | 36.9000 |
| 2015.0000 | 2021.0000 | 1043.0000 | 805.0000 | 0.0894 | 36.7000 |
| 2017.0000 | 2021.0000 | 1034.0000 | 814.0000 | 0.0865 | 35.8000 |
| 2018.0000 | 2021.0000 | 1047.0000 | 801.0000 | 0.0788 | 34.2000 |
| 2016.0000 | 2021.0000 | 1056.0000 | 792.0000 | 0.0773 | 37.5000 |

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

- The pair that differs most is **2014 vs 2021** (mean KS 0.0910). 2021 is the most different year from every other year except 2020, whose largest distance is to 2014 (0.069, against 0.053 to 2021).
- Mean KS against 2014 rises with the gap: 2015: 0.028, 2016: 0.042, 2017: 0.052, 2018: 0.048, 2019: 0.056, 2020: 0.069, 2021: 0.091. The exception is 2018 (0.048), slightly below 2017 (0.052).
- Consecutive-year KS is small (0.025-0.033) until 2020 -> 2021, which jumps to 0.0535, the largest year-to-year step.
- Many top drifting features rise sharply in call counts after 2014; for example `Landroid/os/Process;.myPid:()I` goes from a mean of about 1 call in 2014 to about 11 in 2018 and 2021. Possible causes (larger apps, changing Android API use) were not tested.

## Concept drift: accuracy matrix (train year = row, test year = column)

| train \ test | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 |
|---|---|---|---|---|---|---|---|---|
| 2014.0000 | 0.9633 | 0.9230 | 0.9167 | 0.8347 | 0.8947 | 0.5717 | 0.5623 | 0.6153 |
| 2015.0000 | 0.9310 | 0.9656 | 0.9517 | 0.8653 | 0.8957 | 0.6587 | 0.6413 | 0.6570 |
| 2016.0000 | 0.9153 | 0.9423 | 0.9756 | 0.9660 | 0.9350 | 0.5787 | 0.5473 | 0.3623 |
| 2017.0000 | 0.8577 | 0.8157 | 0.8990 | 0.9778 | 0.9403 | 0.6723 | 0.6740 | 0.6930 |
| 2018.0000 | 0.8347 | 0.8450 | 0.8730 | 0.9633 | 0.9622 | 0.6110 | 0.5920 | 0.6227 |
| 2019.0000 | 0.5673 | 0.6307 | 0.7343 | 0.7570 | 0.8393 | 0.9589 | 0.9387 | 0.7343 |
| 2020.0000 | 0.5883 | 0.6257 | 0.6787 | 0.7643 | 0.7703 | 0.8823 | 0.9511 | 0.9357 |
| 2021.0000 | 0.6103 | 0.6293 | 0.6747 | 0.6397 | 0.7140 | 0.8270 | 0.8877 | 0.9556 |

(`results/step2_accuracy_matrix.csv`, heatmap `results/step2_accuracy_matrix.png`.)

Reading it:
- The diagonal (held-out same-year data) is 0.95-0.98.
- Models trained on 2014-2018 score 0.55-0.69 on 2019-2021, except the 2016 model on 2021, which scores 0.36. That is below the 0.50 chance level for balanced data, so its decision boundary is systematically wrong on 2021.
- Models trained on 2019-2021 score 0.57-0.76 on 2014-2017.
- The break between 2018 and 2019 is the sharpest: the 2018 model drops from 0.96 on 2018 to 0.61 on 2019.
- Models trained on one of the years 2019-2021 do better on the next year (0.94 for 2019 -> 2020, 0.94 for 2020 -> 2021).

## What this means for the models

- A model trained on 2014-2016 faces test years that are increasingly far from it in feature space (mean KS against 2014 of 0.05 for 2017 up to 0.09 for 2021). Expect performance to decrease for later test years, with the largest losses on 2019-2021.
- The accuracy matrix suggests this is not only feature drift but also concept drift: the 2014-2016 models reach 0.83-0.97 on 2017-2018 but only 0.36-0.66 on 2019-2021. The matrix is a prediction only; Step 6 tests it with the real pipeline (all of 2014-2016 pooled, all rows).
- The mean KS matrix changes smoothly while accuracy collapses at 2019, so a modest average feature shift can still move the decision boundary a lot. We did not separate genuine change in app behaviour from dataset effects (2019-2021 have 6x fewer rows per year than 2014-2018).
- For Step 7: retraining on recent years looks promising, since adjacent-year pairs from 2019 on score about 0.94 while old models score 0.36-0.66 on those years. This is a hint to be verified in Step 7, not a result.
- Limitations: one 3,000-row sample per year (seed 42), no repeats; duplicates remain in the samples; the set of skipped all-zero features differs per pair.
