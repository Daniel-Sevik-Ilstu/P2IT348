"""Step 5 tests: evaluation of classifiers on held-out test years (malware = positive class).

Source followed for row counts: AGENTS.md (2014-2018: 9,000 rows per file; 2019-2021: 1,500), not ASSIGNMENT.md.
Entry point tested is main.run_step5 (not run_evaluation).
"""
import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

from src import evaluate, main
from src.config import TEST_YEARS, TRAIN_YEARS
from src.evaluate import (
    assert_test_years_only,
    compute_metrics,
    evaluate_model,
    pooled_table,
    save_table,
)

# Hand-checked example: TP=3, FP=1, FN=2, TN=4 (10 rows).
Y_TRUE = np.array([1, 1, 1, 1, 1, 0, 0, 0, 0, 0])
Y_PRED = np.array([1, 1, 1, 0, 0, 1, 0, 0, 0, 0])
# accuracy = (3+4)/10 = 0.7; precision = 3/(3+1) = 0.75; recall = 3/(3+2) = 0.6
# f1 = 2*0.75*0.6/(0.75+0.6) = 0.9/1.35 = 2/3


class FixedModel:
    """Stub classifier returning preset predictions (or a constant) and recording the rows it was asked about."""

    def __init__(self, preds=None, const=None):
        self.preds, self.const, self.seen = preds, const, []

    def predict(self, X):
        self.seen.append(np.asarray(X).copy())
        if self.const is not None:
            return np.full(len(X), self.const)
        return np.asarray(self.preds)[: len(X)]


def test_metrics_hand_checked():
    m = compute_metrics(Y_TRUE, Y_PRED)
    assert m["accuracy"] == pytest.approx(0.7)
    assert m["precision"] == pytest.approx(0.75)
    assert m["recall"] == pytest.approx(0.6)
    assert m["f1"] == pytest.approx(2 / 3)


def test_metrics_match_sklearn():
    m = compute_metrics(Y_TRUE, Y_PRED)
    assert m["accuracy"] == pytest.approx(accuracy_score(Y_TRUE, Y_PRED))
    assert m["precision"] == pytest.approx(precision_score(Y_TRUE, Y_PRED, pos_label=1))
    assert m["recall"] == pytest.approx(recall_score(Y_TRUE, Y_PRED, pos_label=1))
    assert m["f1"] == pytest.approx(f1_score(Y_TRUE, Y_PRED, pos_label=1))


def test_metrics_have_expected_keys_and_range():
    m = compute_metrics(Y_TRUE, Y_PRED)
    assert set(m) >= {"accuracy", "precision", "recall", "f1"}
    assert all(0.0 <= v <= 1.0 for v in m.values())


def test_malware_is_positive_class():
    # Swapping labels must swap precision/recall roles: hand example with 1 as positive vs 0 as positive.
    m = compute_metrics(Y_TRUE, Y_PRED)
    swapped = compute_metrics(1 - Y_TRUE, 1 - Y_PRED)
    # With 0 as positive: TP=4, FP=2, FN=1 -> precision 4/6, recall 4/5
    assert swapped["precision"] == pytest.approx(4 / 6)
    assert swapped["recall"] == pytest.approx(4 / 5)
    assert m["precision"] != pytest.approx(swapped["precision"])
    assert m["recall"] != pytest.approx(swapped["recall"])


def test_confusion_counts_add_up():
    if not hasattr(evaluate, "confusion_counts"):
        pytest.skip("confusion_counts not part of the plan's API")
    c = evaluate.confusion_counts(Y_TRUE, Y_PRED)
    assert (c["tp"], c["fp"], c["fn"], c["tn"]) == (3, 1, 2, 4)
    assert sum(c.values()) == len(Y_TRUE)


def test_all_benign_predictions_do_not_crash():
    m = compute_metrics(Y_TRUE, np.zeros_like(Y_TRUE))
    assert m["recall"] == 0.0
    assert m["precision"] == 0.0  # zero_division=0
    assert m["f1"] == 0.0
    assert m["accuracy"] == pytest.approx(0.5)


def test_all_malware_predictions():
    m = compute_metrics(Y_TRUE, np.ones_like(Y_TRUE))
    assert m["recall"] == 1.0
    assert m["precision"] == pytest.approx(0.5)
    assert all(0.0 <= v <= 1.0 for v in m.values())


def test_no_positive_in_truth_and_prediction_no_crash():
    m = compute_metrics(np.zeros(5, dtype=int), np.zeros(5, dtype=int))
    assert m["accuracy"] == 1.0
    assert m["precision"] == 0.0 and m["recall"] == 0.0 and m["f1"] == 0.0


def test_unequal_lengths_raise():
    with pytest.raises(ValueError):
        compute_metrics(np.array([1, 0, 1]), np.array([1, 0]))


def test_empty_input_raises_or_is_rejected():
    with pytest.raises(Exception):
        compute_metrics(np.array([], dtype=int), np.array([], dtype=int))


def test_evaluate_model_uses_given_rows_and_predictions():
    X = np.arange(20, dtype=float).reshape(10, 2)
    model = FixedModel(preds=Y_PRED)
    m = evaluate_model(model, X, Y_TRUE)
    assert m["accuracy"] == pytest.approx(0.7)
    assert len(model.seen) == 1 and model.seen[0].shape == X.shape
    np.testing.assert_array_equal(model.seen[0], X)


def test_pooled_table_columns_and_n_test():
    X = np.zeros((10, 2))
    models = {"a": FixedModel(preds=Y_PRED), "b": FixedModel(const=0)}
    t = pooled_table(models, X, Y_TRUE)
    assert list(t.columns) == ["model", "accuracy", "precision", "recall", "f1", "n_test"]
    assert list(t["model"]) == ["a", "b"]
    assert (t["n_test"] == 10).all()
    row = t.set_index("model").loc["a"]
    assert row["f1"] == pytest.approx(2 / 3)
    metric_cols = ["accuracy", "precision", "recall", "f1"]
    assert ((t[metric_cols] >= 0) & (t[metric_cols] <= 1)).all().all()


def test_assert_test_years_only_accepts_test_years():
    assert_test_years_only(np.array(list(TEST_YEARS) * 2))


@pytest.mark.parametrize("bad_year", [2014, 2015, 2016])
def test_assert_test_years_only_rejects_training_years(bad_year):
    with pytest.raises(ValueError):
        assert_test_years_only(np.array([2017, 2018, bad_year]))


def test_assert_test_years_only_rejects_mixed_train_and_test():
    with pytest.raises(ValueError):
        assert_test_years_only(np.array(list(TRAIN_YEARS) + list(TEST_YEARS)))


def test_per_year_table_rows_and_counts():
    years = np.array([2017] * 4 + [2018] * 3 + [2019] * 3)
    y = np.array([1, 0, 1, 0, 1, 1, 0, 1, 0, 0])
    pred = np.array([1, 0, 0, 0, 1, 1, 1, 1, 0, 0])
    X = np.zeros((10, 2))
    models = {"a": FixedModel(preds=pred), "b": FixedModel(const=1)}
    t = evaluate.per_year_table(models, X, y, years)
    assert len(t) == 2 * 3  # one row per model per year
    assert set(t["year"]) == {2017, 2018, 2019}
    assert t.groupby("model")["n"].sum().eq(10).all()
    # weighted per-year accuracy equals pooled accuracy
    a = t[t["model"] == "a"]
    assert (a["accuracy"] * a["n"]).sum() / a["n"].sum() == pytest.approx(accuracy_score(y, pred))
    # hand check for 2017: y=[1,0,1,0], pred=[1,0,0,0] -> acc 0.75, precision 1, recall 0.5
    r = a[a["year"] == 2017].iloc[0]
    assert r["accuracy"] == pytest.approx(0.75)
    assert r["precision"] == pytest.approx(1.0)
    assert r["recall"] == pytest.approx(0.5)


def test_per_year_table_rejects_training_years():
    years = np.array([2016, 2017])
    with pytest.raises(ValueError):
        evaluate.per_year_table({"a": FixedModel(const=1)}, np.zeros((2, 2)), np.array([1, 0]), years)


def test_sensitivity_tables_exclude_flagged_rows():
    years = np.array([2017] * 4 + [2018] * 4)
    y = np.array([1, 0, 1, 0, 1, 0, 1, 0])
    X = np.arange(16, dtype=float).reshape(8, 2)
    dup = np.array([True, False, False, False, True, True, False, False])
    models = {"a": FixedModel(preds=y)}
    pooled, per_year = evaluate.sensitivity_tables(models, X, y, years, dup)
    assert (pooled["n_test"] == 5).all()
    assert (pooled["n_excluded"] == 3).all()
    assert (per_year["n"] + per_year["n_excluded"]).tolist() == [4, 4]
    assert per_year["n_excluded"].tolist() == [1, 2]
    # the model must only have been shown the kept rows
    np.testing.assert_array_equal(models["a"].seen[0], X[~dup])


def test_sensitivity_tables_wrong_mask_length_raises():
    with pytest.raises(ValueError):
        evaluate.sensitivity_tables(
            {"a": FixedModel(const=1)}, np.zeros((4, 2)), np.array([1, 0, 1, 0]),
            np.array([2017] * 4), np.array([True, False]),
        )


def test_save_table_writes_csv_and_md(tmp_path, monkeypatch):
    monkeypatch.setattr(evaluate, "RESULTS_DIR", tmp_path)
    df = pd.DataFrame({"model": ["a"], "accuracy": [0.123456], "n_test": [10]})
    save_table(df, "step5_demo")
    csv = tmp_path / "step5_demo.csv"
    assert csv.exists() and (tmp_path / "step5_demo.md").exists()
    back = pd.read_csv(csv)
    assert list(back.columns) == ["model", "accuracy", "n_test"]
    assert back["accuracy"].iloc[0] == pytest.approx(0.1235)  # 4-decimal rounding


def _synthetic_frame(rows_per_year: int = 150, n_features: int = 6) -> pd.DataFrame:
    """Separable synthetic data for 2014-2021 so every model learns something."""
    rng = np.random.default_rng(42)
    parts = []
    for year in range(2014, 2022):
        label = rng.integers(0, 2, rows_per_year)
        X = rng.poisson(1.0, (rows_per_year, n_features)) + label[:, None] * rng.poisson(3.0, (rows_per_year, n_features))
        d = pd.DataFrame(X.astype(np.int32), columns=[f"f{i}" for i in range(n_features)])
        d["label"] = label.astype(np.int8)
        d["year"] = np.int16(year)
        parts.append(d)
    return pd.concat(parts, ignore_index=True)


def test_run_step5_evaluates_only_test_years(tmp_path, monkeypatch):
    """The pooled n_test must equal the number of 2017-2021 rows, never include 2014-2016 rows."""
    monkeypatch.setattr(evaluate, "RESULTS_DIR", tmp_path)
    if hasattr(main, "RESULTS_DIR"):
        monkeypatch.setattr(main, "RESULTS_DIR", tmp_path)
    df = _synthetic_frame()
    n_test = int(df["year"].isin(TEST_YEARS).sum())
    n_all = len(df)
    out = main.run_step5(df=df)
    assert isinstance(out, dict) and out
    pooled = next(v for v in out.values() if isinstance(v, pd.DataFrame) and "n_test" in v.columns)
    assert (pooled["n_test"] == n_test).all()
    assert n_test < n_all
    assert len(pooled) == 3  # logreg, random_forest, sgd
    metric_cols = ["accuracy", "precision", "recall", "f1"]
    assert ((pooled[metric_cols] >= 0) & (pooled[metric_cols] <= 1)).all().all()


def test_run_step5_rejects_test_rows_mixed_with_training_years():
    """A split whose test part contains training-year rows must raise."""
    from src.preprocess import prepare_split

    df = _synthetic_frame()
    split = prepare_split(df, TRAIN_YEARS, TEST_YEARS)
    bad = dict(split)
    bad["years_test"] = np.concatenate([split["years_test"][:-1], [2015]])
    with pytest.raises(ValueError):
        main.run_step5(df=df, split=bad)


def test_real_data_loaded_test_year_passes_and_train_year_fails(real_data_dir):
    from src.data import load_year

    df19 = load_year(2019, real_data_dir)
    assert_test_years_only(df19["year"].to_numpy())
    df15_years = np.array([2015, 2019])
    with pytest.raises(ValueError):
        assert_test_years_only(df15_years)
    # AGENTS.md (not ASSIGNMENT.md) holds the verified row counts: 2019 has 1,500 per file
    assert len(df19) == 3000
