# Step 4 Report: Models

Written by the builder agent. All numbers come from `python -m src.main --step 4` (code in `src/models.py`, results in `results/step4_training.*`). Nothing here is evaluated on the test years; that is Step 5.

## Training data

The Step 3 output: 54,000 rows (2014, 2015, 2016 at 18,000 each, 9,000 malware and 9,000 goodware per year) by 931 features (float32, log1p, standardized, clipped at ±10). The classes are exactly balanced in the training years.

## Classifiers

| Classifier | Hyperparameters | random_state | Why chosen |
|---|---|---|---|
| `logreg`: LogisticRegression | `class_weight="balanced"`, `solver="lbfgs"`, `max_iter=1000`, `C=1.0` | 42 | Linear baseline; works well on standardized count features and is cheap to train. |
| `random_forest`: RandomForestClassifier | `n_estimators=200`, `n_jobs=-1`, other settings default (unbounded depth, `max_features="sqrt"`) | 42 | Non-linear ensemble that can capture interactions between API calls and thresholds on counts; insensitive to feature scale. |
| `sgd`: SGDClassifier | `loss="log_loss"`, `penalty="l2"`, `alpha=1e-4`, `max_iter=1000`, `tol=1e-3`, no class weight | 42 | Logistic model trained by stochastic gradient descent; the only one of the three with `partial_fit`, so it is the incremental model for Step 7. |

No hyperparameter tuning was run (the optional `tune_logreg` in PLAN.md was not implemented); every value is the default or the PLAN.md choice.

## Class balance

- Training years are balanced (50% malware per year), so class imbalance is not an issue in this step.
- `logreg` still uses `class_weight="balanced"`. With balanced data the weights are 1.0 for both classes, so this has no effect now; it only protects against imbalance in later use.
- `sgd` uses no class weight on purpose: scikit-learn raises `ValueError` for `class_weight="balanced"` in `partial_fit`. I confirmed that `build_model("sgd")` can be fit and then `partial_fit` without error.
- `random_forest` uses no class weight.

## Training times and training-set sanity check

Measured on this laptop. The accuracy is on the **training** rows, so it is only a sanity check that the models fit; it says nothing about performance on new years.

| Model | Training time (s) | Training accuracy (not evaluation) | ConvergenceWarnings |
|---|---|---|---|
| logreg | 1.87 | 0.9897 | 0 |
| random_forest | 4.71 | 0.9969 | 0 |
| sgd | 3.60 | 0.9884 | 0 |

Total training time is about 10 seconds, well inside the 15-minute budget. `max_iter=1000` was enough for lbfgs to converge, so no solver change was needed and no warnings had to be hidden; the training code records warnings (it does not suppress them), and the count is 0 for all three models.

The training accuracies are high and very similar, and the random forest is the highest because deep trees fit the training data closely. This is expected and is not evidence about the test years; many training rows are duplicates (see Step 1), which also makes training accuracy optimistic.

## Implementation notes

- Functions in `src/models.py`: `build_model(name)`, `train_model(name, X, y)`, `train_all(X, y)`, `train_all_from_split(split)`, `MODEL_NAMES`, plus `train_with_report(split)` (trains with the same year guard and returns the timing table) and `save_models`.
- `train_all_from_split` and `train_with_report` raise `ValueError` if `split["years_train"]` contains a year outside 2014-2016.
- Fitted models are saved to `cache/models/*.joblib` (`cache/` is git-ignored). I did not use them elsewhere in this step.
- Not done: hyperparameter tuning, and no evaluation on 2017-2021 (Steps 5-6).
