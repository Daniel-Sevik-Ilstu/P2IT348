# Process Reflection (1-2 pages)

## 1. What did the reviewer or tester catch that the builder missed? (at least two cases)

**Abnormal class weights (reviewer, Step 0).** The builder's plan used `SGDClassifier(class_weight="balanced")` and then `partial_fit` for Step 7. The reviewer said this would crash (as per transcripts/02_2026-11-02_reviewer_step0.md comment 1). It also said it had not run it because sklearn was not installed, so I tested it myself. The plan was fixed in commit 879dfa9 which made SGD to have no class weight now.

**Extreme values (reviewer, Step 3).** The builder's preprocessing only dropped rare features but the reviewer showed test z-scores up to 212.7 (transcripts/14_2026-11-03_reviewer_step3.md in comment 1). The fix was a fixed clip at plus or minus 10 (PLAN.md in ff32966 - code in c78155f).

**Missing years and NaN issues (tester, Step 3).** The tester wrote tests showing that a missing test year silently gave a smaller split and that NaN went straight through log1p. Four tests failed there; I accepted three (and rejected one, see question 2) (tests/step3_test_log.md, transcripts/15_2026-11-03_tester_step3.md). The builder fixed them in 24ce4c5 and ea0a530.

**One-class training data (tester, Step 4).** A random forest trained on a single class gave no error, and the year check only looked at metadata. Two tests failed and the builder added a common guard in 01e5099 (tests/step4_test_log.md - transcripts/20_2026-11-03_tester_step4.md).

**Step 6 reviewer issue.** It noticed that the 2019 to 2021 results look like "predict malware for everything" and asked for confusion counts which showed recall of about 0.99 and precision of about 0.50 (e8322d1 ibn transcripts/28_2026-11-03_reviewer_step6.md). This became the main finding.

## 2. One review comment you rejected, and why

Step 1, comment 8 (reviews/step1_review.md, transcripts/05_2026-11-02_reviewer_step1.md). The reviewer was worried about the code skipping files that start with "._". I rejected it because skipping them was my own instruction to the builder: they are macOS junk files from the zip, and a real data file named ._something is not realistic. The builders code was left unchanged and the report mentions the rule. I also had to reject a tester failure where the test was wrong, not the code: the Step 3 real-data test expected column means within 0.001 of zero, which stopped being true once the clip was added (tests/step3_test_log.md, fixed in 354110d). In Step 7 I rejected comment 8 (a repeated guard kept on purpose).

## 3. A prompt that did not work, and how you rewrote it

I ran "python harness.py session reviewer 4" by mistake when I wanted the Step 5 reviewer so the reviewer prompt asked it to write reviews/step4_review.md, which already existed with my decision log. The agent did not overwrite it. It stopped and asked what to do, and it also pointed out that the diff mixed Step 4 and Step 5 and that joblib is missing from requirements.txt (transcripts/23_2026-11-03_reviewer_step4.md). I started the right session, transcripts/24_2026-11-03_reviewer_step5.md and from then on I checked the step number before running the command.

## 4. One other decision where you overrode an agent, and why

In Step 0 the reviewer gave two options for the rule "every fit uses training years only" versus the Step 2 accuracy matrix which trains on every year. I chose the exemption instead of restricting it, since Step 2 is only a diagnostic and nothing from it feeds Steps 3 to 7 (reviews/step0_plan_review.md comment 2, fixed in 84dffaf). In Step 7 the builder fixed comments 1, 2, 4, 5 and 7 but left comment 3 (do not rank strategies whose differences are too small, say there is no uncertainty estimate) undone and its conclusions still ranked them. I did not trust the "fixed" status, found it by searching the doc and rewrote two paragraphs myself (b4b40df).

## 5. How you verified the agents' results (at least two results)

1. Row counts. The assignment says 1500 rows per file, but Step 1 reported 9000 rows per file for 2014 to 2018 and 1,500 for 2019 to 2021. I recorded the real counts in AGENTS.md and checked that the 18000 and 3000 rows per year appear in the Step 3 split table.
2. Accuracy from the confusion matrix. For logistic regression in results/step5_confusion.md, (17,927 + 20,771) / 45,000 = 0.8600, which matches results/step5_metrics.md.

## 6. Parts you wrote or edited by hand

No code in src/ or tests/ was written by hand. By hand I wrote the decision logs, the test-failure decisions and the commit ids in them and the prompts. I also did the AGENTS, README, REPORT and this file by hand.
