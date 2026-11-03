"""Step 6 tests: per-year test data prediction (2017-2021, three classifiers).

Row counts follow AGENTS.md (2014-2018: 9,000 per file; 2019-2021: 1,500), not ASSIGNMENT.md.
Entry point tested: main.run_step6 (PLAN.md); helper: evaluate.per_year_table.
"""
import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

from src import evaluate, main
from src.config import TEST_YEARS, TRAIN_YEARS
from src.evaluate import assert_test_years_only, per_year_table

MODEL_NAMES = {"logreg", "random_forest", "sgd"}
METRICS = ["accuracy", "precision", "recall", "f1"]


# ---------------------------------------------------------------- helpers
class FixedModel:
    """Stub classifier: predict returns a preset array; any fitting raises (Step 6 must only predict)."""

    def __init__(self, pred: np.ndarray):
        self.pred = None if pred is None else np.asarray(pred)
        self.predict_calls = 0

    def predict(self, X):
        self.predict_calls += 1
        if self.pred is None:  # row-wise rule, valid for any subset of rows (e.g. the no-duplicate table)
            return (np.asarray(X)[:, 0] > 0).astype(int)
        assert len(X) == len(self.pred)
        return self.pred

    def fit(self, *a, **k):
        raise AssertionError("fit called in Step 6")

    def partial_fit(self, *a, **k):
        raise AssertionError("partial_fit called in Step 6")


def _frame(rows_per_year: int = 120, n_features: int = 6, years=range(2014, 2022)) -> pd.DataFrame:
    """Separable synthetic data, one block per year."""
    rng = np.random.default_rng(42)
    parts = []
    for year in years:
        label = rng.integers(0, 2, rows_per_year)
        X = rng.poisson(1.0, (rows_per_year, n_features)) + label[:, None] * rng.poisson(3.0, (rows_per_year, n_features))
        d = pd.DataFrame(X.astype(np.int32), columns=[f"f{i}" for i in range(n_features)])
        d["label"] = label.astype(np.int8)
        d["year"] = np.int16(year)
        parts.append(d)
    return pd.concat(parts, ignore_index=True)


@pytest.fixture
def redirect_results(tmp_path, monkeypatch):
    """Send every results/ write to tmp_path."""
    monkeypatch.setattr(evaluate, "RESULTS_DIR", tmp_path)
    if hasattr(main, "RESULTS_DIR"):
        monkeypatch.setattr(main, "RESULTS_DIR", tmp_path)
    return tmp_path


def _by_year(out: dict) -> pd.DataFrame:
    """The per-year table from run_step6 output (the frame with year, n and a model/classifier column)."""
    for v in out.values():
        if isinstance(v, pd.DataFrame) and {"year", "n", "f1"} <= set(v.columns) and "n_excluded" not in v.columns \
                and "n_malware" not in v.columns and "f1_drop" not in v.columns:
            return v
    raise AssertionError("no per-year table in run_step6 output")


def _name_col(t: pd.DataFrame) -> str:
    return "classifier" if "classifier" in t.columns else "model"


@pytest.fixture
def step6_out(redirect_results):
    df = _frame()
    return df, main.run_step6(df=df)


# ---------------------------------------------------------------- core checks
def test_one_row_per_test_year_per_classifier(step6_out):
    _, out = step6_out
    t = _by_year(out)
    col = _name_col(t)
    assert set(t[col]) == MODEL_NAMES
    assert len(t) == 15  # 3 classifiers x 5 test years
    pairs = list(zip(t[col], t["year"]))
    assert len(set(pairs)) == 15  # no duplicates
    for m in MODEL_NAMES:
        assert sorted(t.loc[t[col] == m, "year"]) == list(TEST_YEARS)


def test_all_metric_values_between_0_and_1(step6_out):
    _, out = step6_out
    t = _by_year(out)
    assert not t[METRICS].isna().any().any()
    assert ((t[METRICS] >= 0) & (t[METRICS] <= 1)).all().all()


def test_per_year_n_sums_to_total_test_rows(step6_out):
    df, out = step6_out
    t = _by_year(out)
    col = _name_col(t)
    total = int(df["year"].isin(TEST_YEARS).sum())
    for m in MODEL_NAMES:
        assert t.loc[t[col] == m, "n"].sum() == total
    # each year's n equals the number of rows in that year
    for y in TEST_YEARS:
        assert (t.loc[t["year"] == y, "n"] == int((df["year"] == y).sum())).all()


def test_no_training_year_in_per_year_table(step6_out):
    _, out = step6_out
    for v in out.values():
        if isinstance(v, pd.DataFrame) and "year" in v.columns:
            assert not set(v["year"]) & set(TRAIN_YEARS)
            assert set(v["year"]) <= set(TEST_YEARS)


def test_step6_writes_expected_files(redirect_results):
    main.run_step6(df=_frame())
    f = redirect_results / "step6_by_year.csv"
    assert f.exists()
    back = pd.read_csv(f)
    assert {"classifier", "year", "n", "accuracy", "precision", "recall", "f1"} <= set(back.columns)
    assert len(back) == 15
    assert ((back[METRICS] >= 0) & (back[METRICS] <= 1)).all().all()


# ---------------------------------------------------------------- no fitting in Step 6
def test_step6_only_predicts_with_given_models(redirect_results, monkeypatch):
    """Given fitted models, run_step6 must not fit models or the preprocessor again."""
    from src.preprocess import Preprocessor, prepare_split

    df = _frame()
    split = prepare_split(df, TRAIN_YEARS, TEST_YEARS)  # fitting happens here, before the spy
    models = {name: FixedModel(None) for name in sorted(MODEL_NAMES)}

    def boom(*a, **k):
        raise AssertionError("Preprocessor fitted in Step 6")

    monkeypatch.setattr(Preprocessor, "fit", boom)
    monkeypatch.setattr(Preprocessor, "fit_transform", boom)
    out = main.run_step6(df=df, split=split, models=models)
    assert len(_by_year(out)) == 15
    assert all(m.predict_calls >= 1 for m in models.values())


def test_step6_does_not_refit_passed_models(redirect_results):
    from sklearn.linear_model import LogisticRegression
    from src.preprocess import prepare_split

    df = _frame()
    split = prepare_split(df, TRAIN_YEARS, TEST_YEARS)
    lr = LogisticRegression(max_iter=1000, random_state=42).fit(split["X_train"], split["y_train"])
    before = (lr.coef_.copy(), lr.intercept_.copy())
    main.run_step6(df=df, split=split, models={"logreg": lr})
    assert np.array_equal(lr.coef_, before[0]) and np.array_equal(lr.intercept_, before[1])


# ---------------------------------------------------------------- hand-checked / sklearn agreement
def test_per_year_metrics_hand_checked_two_years():
    # 2017: y = [1,1,1,0,0], pred = [1,1,0,1,0] -> TP=2 FP=1 FN=1 TN=1
    #   acc 3/5, prec 2/3, rec 2/3, f1 2/3
    # 2018: y = [1,0,0,0], pred = [0,0,0,0] -> TP=0 FP=0 FN=1 TN=3
    #   acc 3/4, prec 0 (zero_division), rec 0, f1 0
    y = np.array([1, 1, 1, 0, 0, 1, 0, 0, 0])
    years = np.array([2017] * 5 + [2018] * 4)
    pred = np.array([1, 1, 0, 1, 0, 0, 0, 0, 0])
    t = per_year_table({"m": FixedModel(pred)}, np.zeros((9, 1)), y, years)
    r17 = t[t["year"] == 2017].iloc[0]
    r18 = t[t["year"] == 2018].iloc[0]
    assert (r17["n"], r18["n"]) == (5, 4)
    assert r17["accuracy"] == pytest.approx(0.6)
    assert r17["precision"] == pytest.approx(2 / 3)
    assert r17["recall"] == pytest.approx(2 / 3)
    assert r17["f1"] == pytest.approx(2 / 3)
    assert r18["accuracy"] == pytest.approx(0.75)
    assert r18["precision"] == 0 and r18["recall"] == 0 and r18["f1"] == 0


def test_per_year_metrics_match_sklearn():
    rng = np.random.default_rng(1)
    years = rng.choice(list(TEST_YEARS), 400)
    y = rng.integers(0, 2, 400)
    pred = np.where(rng.random(400) < 0.8, y, 1 - y)
    t = per_year_table({"m": FixedModel(pred)}, np.zeros((400, 1)), y, years)
    assert len(t) == len(set(years.tolist()))
    for _, r in t.iterrows():
        s = years == r["year"]
        assert r["n"] == s.sum()
        assert r["accuracy"] == pytest.approx(accuracy_score(y[s], pred[s]))
        assert r["precision"] == pytest.approx(precision_score(y[s], pred[s], pos_label=1, zero_division=0))
        assert r["recall"] == pytest.approx(recall_score(y[s], pred[s], pos_label=1, zero_division=0))
        assert r["f1"] == pytest.approx(f1_score(y[s], pred[s], pos_label=1, zero_division=0))


def test_run_step6_matches_sklearn_on_same_rows(redirect_results):
    """End to end: per-year numbers from run_step6 equal sklearn applied to the same models' predictions."""
    from src.models import train_all_from_split
    from src.preprocess import prepare_split

    df = _frame()
    split = prepare_split(df, TRAIN_YEARS, TEST_YEARS)
    models = train_all_from_split(split)
    t = _by_year(main.run_step6(df=df, split=split, models=models))
    col = _name_col(t)
    yt, yrs = split["y_test"], split["years_test"]
    for _, r in t.iterrows():
        pred = models[r[col]].predict(split["X_test"])
        s = yrs == r["year"]
        assert r["f1"] == pytest.approx(f1_score(yt[s], pred[s], pos_label=1, zero_division=0))
        assert r["accuracy"] == pytest.approx(accuracy_score(yt[s], pred[s]))


# ---------------------------------------------------------------- edge cases
def test_year_outside_test_range_is_rejected():
    y = np.array([0, 1, 0, 1])
    for bad in (2013, 2016, 2022):
        years = np.array([2017, 2017, bad, bad])
        with pytest.raises(ValueError):
            per_year_table({"m": FixedModel(y)}, np.zeros((4, 1)), y, years)
    with pytest.raises(ValueError):
        assert_test_years_only(np.array([2022]))


def test_single_class_test_year_does_not_crash(redirect_results):
    """A test year with only malware (or only goodware) still yields a row with metrics in [0, 1]."""
    df = _frame()
    df.loc[df["year"] == 2019, "label"] = 1
    df.loc[df["year"] == 2021, "label"] = 0
    t = _by_year(main.run_step6(df=df))
    assert len(t) == 15
    assert not t[METRICS].isna().any().any()
    assert ((t[METRICS] >= 0) & (t[METRICS] <= 1)).all().all()
    col = _name_col(t)
    # all-benign year: no positives, so precision/recall/f1 cannot be above 0 for a correct-or-not model
    assert (t.loc[t["year"] == 2021, ["precision", "recall", "f1"]] == 0).all().all()


def test_missing_test_year_is_not_invented(redirect_results):
    """If 2019 is absent from the data, either the step refuses, or the table has no 2019 row; no fake row."""
    df = _frame(years=[y for y in range(2014, 2022) if y != 2019])
    try:
        out = main.run_step6(df=df)
    except (ValueError, KeyError):
        return  # failing loudly is acceptable
    t = _by_year(out)
    assert 2019 not in set(t["year"])
    assert set(t["year"]) == {2017, 2018, 2020, 2021}
    assert (t["n"] > 0).all()


# ---------------------------------------------------------------- real data
def test_real_data_each_test_year_has_expected_rows(real_data_dir):
    """AGENTS.md (not ASSIGNMENT.md): 2017-2018 have 18,000 rows per year, 2019-2021 have 3,000.

    Does not retrain any model: uses a stub that predicts all-malware on the real rows.
    """
    from src.data import load_year

    expected = {2017: 18000, 2018: 18000, 2019: 3000, 2020: 3000, 2021: 3000}
    ys, labels = [], []
    for y, n in expected.items():
        d = load_year(y, real_data_dir)
        assert len(d) == n
        ys.append(d["year"].to_numpy())
        labels.append(d["label"].to_numpy())
    years, y = np.concatenate(ys), np.concatenate(labels)
    t = per_year_table({"m": FixedModel(np.ones(len(y), dtype=int))}, np.zeros((len(y), 1)), y, years)
    assert sorted(t["year"]) == list(TEST_YEARS)
    assert dict(zip(t["year"], t["n"])) == expected
    assert ((t[METRICS] >= 0) & (t[METRICS] <= 1)).all().all()
