# Report: A Sustainable Malware Detection System (one page)

## Problem

Malware detectors are trained on old apps but have to judge new ones and the new ones do not look at all like the old ones. In this dataset the difference in data between 2014 and 2021 is huge as a lot of the features that can be tested/are present differ significantly from 2014 (docs/step2_drift_analysis.md). A model trained only on 2014 apps will be good for 2014 but bad on 2021 data. When I train on 2014 to 2016 and test on later years accuracy should still be good in 2017 and 2018 but then falls to about 0.54 in 2019 (results/step6_by_year.md).

## What was tried

Calude used three scikit-learn classifiers (logistic regression, random forest, SGD with log loss) with the same preprocessing, all fit on the training years only. The "static" model is trained on 2014 to 2016 and never changes. For the sustainable approach I compared it with three ways of updating the model before each test year always using only earlier years: an expanding window (all earlier years), a moving window (the last three years), and incremental SGD (predict a year, then using partial fit on it).

## Results

Every updating strategy beats the static model for every classifier. For logistic regression, accuracy goes from 0.86 (static) to 0.92 (sliding window), and the other classifiers improve by a similar amount. All of that gain comes from 2020 and 2021, where the static model is at chance level and the updated models score about 0.9. In 2019 nothing helps: every strategy stays at 0.54 to 0.56, because the first year of a shift is invisible until it has been labelled. The differences between expanding, sliding and incremental updates are small and I only ran one seed, so I can't really rank them. They do differ in cost (results/step7_cost.md): for logistic regression, the expanding window took the longest to retrain, the sliding window about half as long, and incremental SGD only a few seconds in total, close to the static model.

## Recommendation

I would deploy a model that is retrained at least once a year on a recent window (a sliding window or incremental SGD, since they cost less and did as well as the expanding window here). Drift monitoring should not rely on the KS feature drift between consecutive years, which barely moved in 2018 to 2019. Better warning signs were the share of apps the model calls malware (it jumped to nearly everything in 2019 to 2021 on a test set that is half malware) and accuracy on a small labelled sample of each new year. When one of those triggers, label some new apps and retrain right away: the 2019 apps were only a small part of the 2020 training data and still fixed the model. Limits: only one abrupt shift, one seed, duplicate rows kept, and the assumption that labels arrive instantly, which is optimistic.
