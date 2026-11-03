"""Step 4 tests: classifiers in src/models.py (based on PLAN.md Step 4 and AGENTS.md)."""
import numpy as np
import pytest
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression, SGDClassifier

from models import (
    MODEL_NAMES,
    build_model,
    train_all,
    train_all_from_split,
    train_model,
)

TRAIN_YEARS = (2014, 2015, 2016)


def make_data(n: int = 300, d: int = 6, seed: int = 0):
    """Small separable two-class dataset (class 1 shifted by +3 on every feature)."""
    rng = np.random.default_rng(seed)
    y = np.array([0, 1] * (n // 2))
    X = rng.normal(size=(n, d)).astype(np.float32) + 3.0 * y[:, None]
    return X, y


def make_split(years):
    """Dict shaped like the Step 3 split (only the training keys are needed)."""
    X, y = make_data(len(years) * 2 if len(years) > 100 else 300)
    yrs = np.resize(np.array(years), len(y))
    return {"X_train": X, "y_train": y, "years_train": yrs}


# ---------- build_model ----------

def test_model_names_has_logreg_random_forest_sgd():
    assert set(MODEL_NAMES) == {"logreg", "random_forest", "sgd"}


def test_build_model_returns_expected_classes():
    assert isinstance(build_model("logreg"), LogisticRegression)
    assert isinstance(build_model("random_forest"), RandomForestClassifier)
    assert isinstance(build_model("sgd"), SGDClassifier)


@pytest.mark.parametrize("name", ["logreg", "random_forest", "sgd"])
def test_build_model_random_state_is_42(name):
    assert build_model(name).random_state == 42


def test_logreg_is_balanced_and_has_larger_max_iter_than_default():
    m = build_model("logreg")
    assert m.class_weight == "balanced"
    assert m.max_iter > 100  # sklearn default is 100


def test_random_forest_has_200_trees():
    assert build_model("random_forest").n_estimators == 200


def test_sgd_has_no_balanced_class_weight_and_log_loss():
    m = build_model("sgd")
    assert m.class_weight != "balanced"
    assert m.loss == "log_loss"


def test_build_model_returns_new_unfitted_objects():
    a, b = build_model("logreg"), build_model("logreg")
    assert a is not b
    assert not hasattr(a, "coef_")


@pytest.mark.parametrize("bad", ["svm", "", "LogReg", "xgboost"])
def test_build_model_unknown_name_raises_value_error(bad):
    with pytest.raises(ValueError):
        build_model(bad)


# ---------- fit / predict ----------

@pytest.mark.parametrize("name", ["logreg", "random_forest", "sgd"])
def test_each_model_fits_and_predicts_well_on_separable_data(name):
    X, y = make_data()
    model = train_model(name, X, y)
    pred = model.predict(X)
    assert pred.shape == y.shape
    assert (pred == y).mean() > 0.9


@pytest.mark.parametrize("name", ["logreg", "random_forest", "sgd"])
def test_predictions_use_only_labels_0_and_1(name):
    X, y = make_data()
    model = train_model(name, X, y)
    rng = np.random.default_rng(1)
    X_new = rng.normal(size=(100, X.shape[1])).astype(np.float32) * 5
    assert set(np.unique(model.predict(X_new))) <= {0, 1}


def test_train_all_returns_all_named_models_fitted():
    X, y = make_data()
    models = train_all(X, y)
    assert set(models) == set(MODEL_NAMES)
    for m in models.values():
        assert m.predict(X).shape == y.shape


@pytest.mark.parametrize("name", ["logreg", "random_forest", "sgd"])
def test_same_random_state_gives_identical_results_twice(name):
    X, y = make_data()
    # Noisy overlapping data so equality is not trivial.
    rng = np.random.default_rng(5)
    X = X + rng.normal(scale=3.0, size=X.shape).astype(np.float32)
    m1, m2 = train_model(name, X, y), train_model(name, X, y)
    assert np.array_equal(m1.predict(X), m2.predict(X))
    assert np.allclose(m1.predict_proba(X), m2.predict_proba(X))


# ---------- SGD partial_fit ----------

def test_sgd_partial_fit_after_fit_works():
    X, y = make_data()
    model = build_model("sgd")
    model.fit(X, y)
    X2, y2 = make_data(seed=9)
    model.partial_fit(X2, y2)
    assert set(np.unique(model.predict(X2))) <= {0, 1}


def test_sgd_partial_fit_as_first_call_with_classes():
    X, y = make_data()
    model = build_model("sgd")
    model.partial_fit(X, y, classes=np.array([0, 1]))
    assert (model.predict(X) == y).mean() > 0.9


# ---------- year guard ----------

def test_train_all_from_split_accepts_2014_2016():
    models = train_all_from_split(make_split(TRAIN_YEARS))
    assert set(models) == set(MODEL_NAMES)


@pytest.mark.parametrize("years", [(2014, 2015, 2017), (2017,), (2013, 2014), (2014, 2021)])
def test_train_all_from_split_raises_on_year_outside_2014_2016(years):
    with pytest.raises(ValueError):
        train_all_from_split(make_split(years))


def test_train_all_from_split_accepts_subset_of_training_years():
    models = train_all_from_split(make_split((2014, 2015)))
    assert set(models) == set(MODEL_NAMES)


# ---------- edge cases ----------

def test_train_model_unknown_name_raises():
    X, y = make_data()
    with pytest.raises(ValueError):
        train_model("nope", X, y)


@pytest.mark.parametrize("name", ["logreg", "random_forest", "sgd"])
def test_one_class_y_train_raises(name):
    X, _ = make_data()
    with pytest.raises(ValueError):
        train_model(name, X, np.zeros(len(X), dtype=int))


@pytest.mark.parametrize("name", ["logreg", "random_forest", "sgd"])
def test_empty_training_set_raises(name):
    with pytest.raises(ValueError):
        train_model(name, np.empty((0, 6), dtype=np.float32), np.empty((0,), dtype=int))


@pytest.mark.parametrize("name", ["logreg", "random_forest", "sgd"])
def test_mismatched_x_and_y_lengths_raise(name):
    X, y = make_data()
    with pytest.raises(ValueError):
        train_model(name, X, y[:-5])


def test_train_all_from_split_mismatched_years_length_raises():
    split = make_split(TRAIN_YEARS)
    split["years_train"] = split["years_train"][:-3]
    with pytest.raises(ValueError):
        train_all_from_split(split)


def test_train_all_from_split_empty_training_set_raises():
    split = {
        "X_train": np.empty((0, 6), dtype=np.float32),
        "y_train": np.empty((0,), dtype=int),
        "years_train": np.empty((0,), dtype=int),
    }
    with pytest.raises(ValueError):
        train_all_from_split(split)


# ---------- real data (skipped when input_data/ is empty) ----------

def test_real_data_logreg_and_sgd_train_on_training_years(real_data_dir):
    from data import load_all
    from preprocess import prepare_split

    df = load_all(real_data_dir)
    split = prepare_split(df, TRAIN_YEARS, (2017, 2018, 2019, 2020, 2021))
    assert set(np.unique(split["years_train"])) <= set(TRAIN_YEARS)
    # Subsample so the test stays fast; the random forest is not trained on real data.
    idx = np.random.default_rng(42).choice(len(split["y_train"]), 3000, replace=False)
    for name in ("logreg", "sgd"):
        model = train_model(name, split["X_train"][idx], split["y_train"][idx])
        assert set(np.unique(model.predict(split["X_test"][:500]))) <= {0, 1}
