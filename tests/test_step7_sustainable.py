"""Step 7 tests: sustainable approach (static, expanding window, sliding window, incremental).

Row counts follow AGENTS.md (2014-2018: 18,000 rows per year; 2019-2021: 3,000), not ASSIGNMENT.md; the synthetic
tests use small frames. Entry point tested: main.run_step7 (PLAN.md), plus sustainable.window_years,
run_window_strategy, run_incremental and run_all_strategies.

Leakage checks use a recording stub for the Preprocessor and the classifier. Every synthetic row carries a constant
"tag" feature (year - 2000) in column 0, so a stub that receives a raw matrix can tell which years it was fitted on.
"""
import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import accuracy_score, f1_score

from src import evaluate, main, models as models_mod, sustainable
from src.config import TEST_YEARS, TRAIN_YEARS
from src.preprocess import prepare_split
from src.sustainable import (
    compare_to_static, pooled_by_strategy, run_all_strategies, run_incremental, run_window_strategy,
    window_composition, window_years,
)

METRICS = ["accuracy", "precision", "recall", "f1"]
ALL_YEARS = tuple(range(2014, 2022))
EXPECTED_PLAN = {  # PLAN.md: RF only for (a) and (b); SGD also gets (d)
    "logreg": {"static", "expanding", "sliding"},
    "sgd": {"static", "expanding", "sliding", "incremental"},
    "random_forest": {"static", "expanding"},
}


# ---------------------------------------------------------------- synthetic data
def _drift_frame(rows: int = 300, years=ALL_YEARS, seed: int = 42, tag: bool = False) -> pd.DataFrame:
    """Balanced synthetic count data whose signal moves from f_old to f_new over the years (concept drift)."""
    rng = np.random.default_rng(seed)
    parts = []
    for year in years:
        i = year - 2014
        label = rng.integers(0, 2, rows)
        s_old, s_new = max(0.0, 4.0 - 0.6 * i), min(4.0, 0.6 * i)
        cols = {
            "f_old": rng.poisson(2 + label * s_old),
            "f_new": rng.poisson(2 + label * s_new),
            "n0": rng.poisson(2, rows),
            "n1": rng.poisson(2, rows),
        }
        d = pd.DataFrame(cols).astype(np.int32)
        if tag:
            d.insert(0, "tag", np.int32(year - 2000))
        d["label"] = label.astype(np.int8)
        d["year"] = np.int16(year)
        parts.append(d)
    return pd.concat(parts, ignore_index=True)


def _tag_years(X) -> frozenset:
    """Years present in a raw or transformed matrix built from a tagged frame (column 0 = year - 2000)."""
    return frozenset(int(v) + 2000 for v in np.unique(np.asarray(X)[:, 0]))


class Spy:
    """Shared event log for the recording stubs."""

    def __init__(self):
        self.events = []  # (kind, model_id, years)
        self.violations = []
        self.next_id = 0  # unique ids (id() can be reused once an object is garbage collected)

    def new_id(self) -> int:
        self.next_id += 1
        return self.next_id


@pytest.fixture
def spy(monkeypatch):
    """Replace Preprocessor and train_model in sustainable with recording stubs."""
    s = Spy()

    class StubPre:
        def fit(self, X, feature_names=None):
            s.events.append(("pre_fit", s.new_id(), _tag_years(X)))
            return self

        def transform(self, X, clip=True):
            return np.asarray(X, dtype=np.float32)

    class StubModel:
        def __init__(self):
            self.seen: set = set()
            self.uid = s.new_id()

        def fit(self, X, y):
            self.seen = set(_tag_years(X))
            s.events.append(("fit", self.uid, _tag_years(X)))
            return self

        def partial_fit(self, X, y, classes=None):
            self.seen |= set(_tag_years(X))
            s.events.append(("partial_fit", self.uid, _tag_years(X)))
            return self

        def predict(self, X):
            ys = _tag_years(X)
            if self.seen and max(self.seen) >= min(ys):
                s.violations.append((sorted(self.seen), sorted(ys)))
            s.events.append(("predict", self.uid, ys))
            return np.zeros(len(X), dtype=int)

    monkeypatch.setattr(sustainable, "Preprocessor", StubPre)
    monkeypatch.setattr(sustainable, "train_model", lambda name, X, y: StubModel().fit(X, y))
    return s


@pytest.fixture
def redirect_results(tmp_path, monkeypatch):
    """Send every results/ write to tmp_path."""
    for mod in (evaluate, main, sustainable):
        if hasattr(mod, "RESULTS_DIR"):
            monkeypatch.setattr(mod, "RESULTS_DIR", tmp_path)
    return tmp_path


@pytest.fixture(scope="module")
def drift_df() -> pd.DataFrame:
    return _drift_frame()


@pytest.fixture(scope="module")
def all_results(drift_df) -> pd.DataFrame:
    """Real preprocessing and models on the drift frame, all strategies, random forest included."""
    return run_all_strategies(drift_df, rf=True)


# ---------------------------------------------------------------- window_years
@pytest.mark.parametrize("t,expected", [
    (2017, (2014, 2015, 2016)), (2018, (2014, 2015, 2016, 2017)), (2021, (2014, 2015, 2016, 2017, 2018, 2019, 2020)),
])
def test_expanding_window_is_all_years_before_t(t, expected):
    assert tuple(window_years("expanding", t)) == expected


@pytest.mark.parametrize("t,expected", [
    (2017, (2014, 2015, 2016)), (2018, (2015, 2016, 2017)), (2019, (2016, 2017, 2018)),
    (2020, (2017, 2018, 2019)), (2021, (2018, 2019, 2020)),
])
def test_sliding_window_is_three_years_before_t(t, expected):
    assert tuple(window_years("sliding", t)) == expected


@pytest.mark.parametrize("t", TEST_YEARS)
def test_static_window_is_2014_2016_for_every_t(t):
    assert tuple(window_years("static", t)) == (2014, 2015, 2016)


@pytest.mark.parametrize("strategy", ["static", "expanding", "sliding"])
@pytest.mark.parametrize("t", TEST_YEARS)
def test_window_never_contains_year_t_or_later(strategy, t):
    assert max(window_years(strategy, t)) < t


@pytest.mark.parametrize("t", [2013, 2014, 2016, 2022])
def test_window_years_rejects_non_test_year(t):
    """An empty or leaking window (t before the first test year) must raise, not return something."""
    for strategy in ("static", "expanding", "sliding"):
        with pytest.raises(ValueError):
            window_years(strategy, t)


def test_window_years_rejects_unknown_strategy():
    with pytest.raises(ValueError):
        window_years("magic", 2018)


# ---------------------------------------------------------------- leakage: recording stubs
@pytest.mark.parametrize("strategy,expected", [
    ("static", [{2014, 2015, 2016}]),
    ("expanding", [{2014, 2015, 2016}, {2014, 2015, 2016, 2017}, set(range(2014, 2019)), set(range(2014, 2020)),
                   set(range(2014, 2021))]),
    ("sliding", [{2014, 2015, 2016}, {2015, 2016, 2017}, {2016, 2017, 2018}, {2017, 2018, 2019}, {2018, 2019, 2020}]),
])
def test_fit_years_are_exactly_the_planned_window(spy, strategy, expected):
    run_window_strategy(_drift_frame(rows=20, tag=True), strategy, "logreg")
    fits = [set(e[2]) for e in spy.events if e[0] == "fit"]
    if strategy == "static":  # PLAN: static window is the same for every t; refitting five times is also acceptable
        assert fits and all(f == expected[0] for f in fits)
    else:
        assert fits == expected


@pytest.mark.parametrize("strategy", ["static", "expanding", "sliding"])
def test_preprocessor_never_fit_on_year_t_or_later(spy, strategy):
    """The scaler/mask used for year t is fit on exactly the same years as the model, none >= t."""
    run_window_strategy(_drift_frame(rows=20, tag=True), strategy, "logreg")
    pre_fits = [set(e[2]) for e in spy.events if e[0] == "pre_fit"]
    model_fits = [set(e[2]) for e in spy.events if e[0] == "fit"]
    assert pre_fits == model_fits
    # each fit is followed by a predict on a single later year
    fit_predict = [(e[0], e[2]) for e in spy.events if e[0] in ("fit", "predict")]
    for (k1, y1), (k2, y2) in zip(fit_predict, fit_predict[1:]):
        if k1 == "fit" and k2 == "predict":
            assert max(y1) < min(y2)


@pytest.mark.parametrize("strategy", ["static", "expanding", "sliding"])
def test_window_strategy_predicts_each_test_year_once_on_that_year_only(spy, strategy):
    run_window_strategy(_drift_frame(rows=20, tag=True), strategy, "logreg")
    predicted = [set(e[2]) for e in spy.events if e[0] == "predict"]
    assert predicted == [{t} for t in TEST_YEARS]
    assert not spy.violations


def test_no_model_trained_on_year_at_or_after_year_it_predicts_any_strategy(spy):
    """All strategies and all classifiers together: every predict happens after training only on earlier years."""
    out = run_all_strategies(_drift_frame(rows=20, tag=True), rf=True)
    assert not spy.violations
    seen_by_model: dict = {}
    for kind, mid, years in spy.events:  # replay in call order
        if kind in ("fit", "partial_fit"):
            seen_by_model.setdefault(mid, set()).update(years)
        elif kind == "predict":
            assert max(seen_by_model[mid]) < min(years), f"model trained on {sorted(seen_by_model[mid])}, predicted {sorted(years)}"
    assert set(out["year"]) == set(TEST_YEARS)


def test_incremental_predicts_year_t_before_partial_fit_on_t(spy):
    run_incremental(_drift_frame(rows=20, tag=True), "sgd")
    model_events = [(k, set(y)) for k, _, y in spy.events if k in ("fit", "predict", "partial_fit")]
    expected = [("fit", {2014, 2015, 2016})]
    for t in TEST_YEARS:
        expected += [("predict", {t}), ("partial_fit", {t})]
    assert model_events == expected
    assert not spy.violations


def test_incremental_preprocessor_fit_once_on_training_years_only(spy):
    """Preprocessor is frozen after the initial fit (PLAN); year t never influences scaler or mask."""
    run_incremental(_drift_frame(rows=20, tag=True), "sgd")
    pre_fits = [set(e[2]) for e in spy.events if e[0] == "pre_fit"]
    assert pre_fits == [{2014, 2015, 2016}]


def test_incremental_uses_one_model_object_throughout(spy):
    run_incremental(_drift_frame(rows=20, tag=True), "sgd")
    ids = {mid for k, mid, _ in spy.events if k in ("fit", "predict", "partial_fit")}
    assert len(ids) == 1


# ---------------------------------------------------------------- leakage: labels of year t cannot affect predictions for t
def test_flipping_labels_of_year_t_does_not_change_predictions_up_to_t():
    """Real models: predictions for years <= 2019 do not depend on 2019 labels (no future label use).

    Counts of predicted malware (tp + fp) are compared; labels only enter the metrics, not the predictions.
    Static must be unaffected at every year; the updating strategies must change after 2019.
    """
    base = _drift_frame()
    flipped = base.copy()
    sel = flipped["year"] == 2019
    flipped.loc[sel, "label"] = 1 - flipped.loc[sel, "label"]
    a = run_all_strategies(base, rf=False)
    b = run_all_strategies(flipped, rf=False)
    for d in (a, b):
        d["pred_pos"] = d["tp"] + d["fp"]
    key = ["strategy", "classifier", "year"]
    m = a.merge(b, on=key, suffixes=("_a", "_b"))
    early = m[m["year"] <= 2019]
    assert (early["pred_pos_a"] == early["pred_pos_b"]).all(), early[early["pred_pos_a"] != early["pred_pos_b"]][key]
    static = m[m["strategy"] == "static"]
    assert (static["pred_pos_a"] == static["pred_pos_b"]).all()
    for strat in ("expanding", "sliding", "incremental"):
        late = m[(m["strategy"] == strat) & (m["year"] >= 2020)]
        assert (late["pred_pos_a"] != late["pred_pos_b"]).any(), f"{strat} ignored 2019 labels when predicting 2020/2021"


# ---------------------------------------------------------------- the updated model really uses newer data
def test_expanding_and_sliding_models_differ_per_year_static_does_not(monkeypatch):
    captured = []
    real = sustainable.train_model

    def capture(name, X, y):
        m = real(name, X, y)
        captured.append((m.coef_.copy(), len(y)))
        return m

    monkeypatch.setattr(sustainable, "train_model", capture)
    df = _drift_frame()
    for strategy in ("expanding", "sliding"):
        captured.clear()
        run_window_strategy(df, strategy, "logreg")
        assert len(captured) == 5
        coefs = [c for c, _ in captured]
        for earlier, later in zip(coefs, coefs[1:]):
            assert not np.allclose(earlier, later), f"{strategy} model did not change after new year was added"
    captured.clear()
    run_window_strategy(df, "expanding", "logreg")
    sizes = [n for _, n in captured]
    assert sizes == [300 * k for k in (3, 4, 5, 6, 7)]  # expanding window grows by one year of rows each time
    captured.clear()
    run_window_strategy(df, "sliding", "logreg")
    assert [n for _, n in captured] == [900] * 5  # sliding window stays at three years
    captured.clear()
    run_window_strategy(df, "static", "logreg")
    assert len({n for _, n in captured}) == 1 and len(captured) >= 1
    coefs = [c for c, _ in captured]
    assert all(np.allclose(coefs[0], c) for c in coefs)  # static model is identical for every test year


def test_incremental_calls_partial_fit_each_year_and_model_changes(monkeypatch):
    holder = {}
    real = sustainable.train_model

    def capture(name, X, y):
        m = real(name, X, y)
        holder["model"] = m
        holder["coef0"] = m.coef_.copy()
        holder["calls"] = []
        orig = m.partial_fit

        def counting(X_, y_, *a, **k):
            holder["calls"].append(len(y_))
            return orig(X_, y_, *a, **k)

        m.partial_fit = counting
        return m

    monkeypatch.setattr(sustainable, "train_model", capture)
    run_incremental(_drift_frame(), "sgd")
    assert holder["calls"] == [300] * len(TEST_YEARS)  # one partial_fit per test year, with that year's rows
    assert not np.allclose(holder["coef0"], holder["model"].coef_)


# ---------------------------------------------------------------- the static baseline is never updated
@pytest.fixture
def step7_run(redirect_results):
    """run_step7 with fitted Step 4 models passed in; coefficients snapshotted before the run."""
    df = _drift_frame()
    split = prepare_split(df, TRAIN_YEARS, TEST_YEARS)
    models = models_mod.train_all_from_split(split)
    before = {n: (m.coef_.copy(), m.intercept_.copy()) for n, m in models.items() if hasattr(m, "coef_")}
    out = main.run_step7(df=df, split=split, models=models)
    return df, split, models, before, out


def test_static_baseline_models_unchanged_after_step7(step7_run):
    _, _, models, before, _ = step7_run
    assert before.keys() == {"logreg", "sgd"}
    for name, (coef, intercept) in before.items():
        assert np.array_equal(models[name].coef_, coef), f"{name} coefficients changed during Step 7"
        assert np.array_equal(models[name].intercept_, intercept)


def test_static_rows_equal_step4_models_predictions(step7_run):
    _, split, models, _, out = step7_run
    t = out["strategies"]
    for name, model in models.items():
        pred = model.predict(split["X_test"])
        for year in TEST_YEARS:
            sel = split["years_test"] == year
            row = t[(t["strategy"] == "static") & (t["classifier"] == name) & (t["year"] == year)]
            assert len(row) == 1
            assert row["f1"].iloc[0] == pytest.approx(f1_score(split["y_test"][sel], pred[sel], pos_label=1, zero_division=0))
            assert row["accuracy"].iloc[0] == pytest.approx(accuracy_score(split["y_test"][sel], pred[sel]))


def test_static_baseline_stub_models_are_only_asked_to_predict(redirect_results):
    """Passed-in static models must never receive fit or partial_fit from Step 7."""
    df = _drift_frame()
    split = prepare_split(df, TRAIN_YEARS, TEST_YEARS)

    class Frozen:
        def predict(self, X):
            return (np.asarray(X)[:, 1] > 0).astype(int)

        def fit(self, *a, **k):
            raise AssertionError("static model was fit")

        def partial_fit(self, *a, **k):
            raise AssertionError("static model was partial_fit")

    stubs = {"logreg": Frozen(), "sgd": Frozen(), "random_forest": Frozen()}
    out = sustainable.run_all_strategies(df, split, stubs, rf=True)
    assert len(out[out["strategy"] == "static"]) == 15


def test_step7_writes_expected_files(step7_run, redirect_results):
    _, _, _, _, out = step7_run
    f = redirect_results / "step7_strategies.csv"
    assert f.exists()
    t = pd.read_csv(f)
    assert list(t.columns) == ["strategy", "classifier", "year", "n", "accuracy", "precision", "recall", "f1"]
    assert len(t) == len(out["strategies"])


# ---------------------------------------------------------------- result structure
def test_one_row_per_strategy_classifier_year(all_results):
    t = all_results
    assert not t.duplicated(["strategy", "classifier", "year"]).any()
    got = {c: set(g["strategy"]) for c, g in t.groupby("classifier")}
    assert got == EXPECTED_PLAN
    assert len(t) == sum(len(s) for s in EXPECTED_PLAN.values()) * len(TEST_YEARS)
    for (_, _), g in t.groupby(["strategy", "classifier"]):
        assert sorted(g["year"]) == list(TEST_YEARS)


def test_metric_values_between_0_and_1(all_results):
    vals = all_results[METRICS]
    assert not vals.isna().any().any()
    assert ((vals >= 0) & (vals <= 1)).all().all()


def test_all_strategies_scored_on_same_test_rows(all_results, drift_df):
    counts = drift_df.groupby("year").size()
    for year, g in all_results.groupby("year"):
        assert (g["n"] == counts[year]).all()
        # class composition identical too: positives = tp + fn is a property of the test rows only
        assert g[["tp", "fn"]].sum(axis=1).nunique() == 1


def test_no_training_year_reported_as_test_year(all_results):
    assert set(all_results["year"]) == set(TEST_YEARS)


def test_pooled_matches_sum_of_per_year_counts(all_results):
    pooled = pooled_by_strategy(all_results)
    assert len(pooled) == 9
    assert ((pooled[METRICS] >= 0) & (pooled[METRICS] <= 1)).all().all()
    row = pooled[(pooled["strategy"] == "static") & (pooled["classifier"] == "logreg")].iloc[0]
    g = all_results[(all_results["strategy"] == "static") & (all_results["classifier"] == "logreg")]
    assert row["n"] == g["n"].sum()
    assert row["accuracy"] == pytest.approx((g["tp"].sum() + g["tn"].sum()) / g["n"].sum())


def test_compare_to_static_is_a_difference_against_the_static_row(all_results):
    cmp_ = compare_to_static(all_results)
    assert "static" not in set(cmp_["strategy"])
    r = cmp_.iloc[0]
    st = all_results[(all_results["strategy"] == "static") & (all_results["classifier"] == r["classifier"])
                     & (all_results["year"] == r["year"])].iloc[0]
    assert r["f1_diff"] == pytest.approx(r["f1"] - st["f1"])


def test_2017_agrees_for_static_expanding_sliding(all_results):
    """PLAN: for t = 2017 all three windows are 2014-2016, so their predictions coincide."""
    for clf in ("logreg", "random_forest"):
        g = all_results[(all_results["classifier"] == clf) & (all_results["year"] == 2017)]
        g = g[g["strategy"].isin(["static", "expanding", "sliding"])]
        assert g["f1"].nunique() == 1 or np.allclose(g["f1"], g["f1"].iloc[0])


# ---------------------------------------------------------------- behaviour on drifting data (sanity, not a performance claim)
def test_retraining_does_not_do_worse_than_static_in_final_year(all_results):
    g = all_results[(all_results["year"] == 2021) & (all_results["classifier"] == "logreg")].set_index("strategy")
    assert g.loc["sliding", "f1"] >= g.loc["static", "f1"]
    assert g.loc["expanding", "f1"] >= g.loc["static", "f1"]
    sgd = all_results[(all_results["year"] == 2021) & (all_results["classifier"] == "sgd")].set_index("strategy")
    assert sgd.loc["incremental", "f1"] >= sgd.loc["static", "f1"] - 0.02


# ---------------------------------------------------------------- window composition
def test_window_composition_rows_match_windows(drift_df):
    wc = window_composition(drift_df)
    row = wc[(wc["strategy"] == "sliding") & (wc["test_year"] == 2019)].iloc[0]
    assert row["train_rows"] == 900 and row["n_2016"] == 300 and row["n_2019"] == 0 and row["n_2014"] == 0
    row = wc[(wc["strategy"] == "expanding") & (wc["test_year"] == 2021)].iloc[0]
    assert row["train_rows"] == 2100 and row["n_2020"] == 300 and row["n_2021"] == 0


# ---------------------------------------------------------------- edge cases
def test_single_class_test_years_do_not_crash():
    df = _drift_frame()
    df.loc[df["year"] == 2019, "label"] = 1
    df.loc[df["year"] == 2021, "label"] = 0
    out = run_all_strategies(df, rf=False)
    vals = out[METRICS]
    assert not vals.isna().any().any()
    assert ((vals >= 0) & (vals <= 1)).all().all()
    assert len(out) == 35  # logreg 3 + sgd 4 strategies, x 5 years
    benign_year = out[out["year"] == 2021]
    assert (benign_year["recall"] == 0).all() and (benign_year["f1"] == 0).all()


def test_missing_year_is_not_invented():
    """Data without 2019: raise loudly, or report only years that exist; never a fabricated 2019 row."""
    df = _drift_frame(years=[y for y in ALL_YEARS if y != 2019], rows=60)
    try:
        out = run_all_strategies(df, rf=False)
    except Exception:  # failing loudly is acceptable
        return
    assert 2019 not in set(out["year"])


def test_missing_training_years_raise():
    """No data before the test years -> empty windows must raise rather than silently train on nothing."""
    df = _drift_frame(years=range(2017, 2022), rows=60)
    with pytest.raises(Exception):
        run_all_strategies(df, rf=False)


# ---------------------------------------------------------------- real data (skipped when input_data/ is empty)
def test_real_data_every_window_year_has_files(real_data_dir):
    """Every year used by any window or test year exists in the dataset (16 files: 8 years x malware/benign)."""
    import re

    years = set()
    for p in real_data_dir.glob("*.csv"):
        m = re.match(r"^sampled_(\d{4})_(malware|benign)_api\.csv$", p.name)
        assert m, f"unexpected file {p.name}"
        years.add(int(m.group(1)))
    assert years == set(ALL_YEARS)
    for t in TEST_YEARS:
        for strategy in ("static", "expanding", "sliding"):
            assert set(window_years(strategy, t)) <= years


# ---------------------------------------------------------------- accepted review comments (builder fixes)
def test_static_from_models_rejects_wrong_training_years():
    """Review comment 1: the static split must be trained on exactly 2014-2016."""
    df = _drift_frame()
    split = prepare_split(df, TRAIN_YEARS, TEST_YEARS)
    bad = {**split, "years_train": np.where(split["years_train"] == 2016, 2017, split["years_train"])}
    with pytest.raises(ValueError):
        sustainable.static_from_models(bad, {})


def test_static_from_models_rejects_mismatched_test_labels():
    """Review comment 1: static test labels per year must equal the arrays the other strategies use."""
    df = _drift_frame()
    split = prepare_split(df, TRAIN_YEARS, TEST_YEARS)
    arrays = sustainable.year_arrays(df)
    sustainable.static_from_models(split, {}, arrays=arrays)  # consistent: no error
    flipped = {**split, "y_test": 1 - split["y_test"]}
    with pytest.raises(ValueError):
        sustainable.static_from_models(flipped, {}, arrays=arrays)


def test_missing_year_raises_clear_value_error():
    """Review comment 7: a missing training or test year raises ValueError naming the year, before any fit."""
    df = _drift_frame(years=[y for y in ALL_YEARS if y != 2019], rows=30)
    with pytest.raises(ValueError, match="2019"):
        run_all_strategies(df, rf=False)
    with pytest.raises(ValueError, match="2015"):
        window_composition(_drift_frame(years=[y for y in ALL_YEARS if y != 2015], rows=30))


def test_cost_table_reports_nan_not_zero_when_static_seconds_missing():
    """Review comment 5: unknown static seconds must stay NaN in cost_table, never a silent 0.0."""
    df = _drift_frame()
    split = prepare_split(df, TRAIN_YEARS, TEST_YEARS)
    models = models_mod.train_all_from_split(split)
    out = sustainable.static_from_models(split, models, train_seconds=None)
    cost = sustainable.cost_table(out)
    assert cost["total_seconds"].isna().all() and cost["mean_seconds_per_update"].isna().all()


def test_cost_table_incremental_update_rows_separate(all_results):
    """Review comment 4: incremental update sizes are in update_rows, not mixed into mean_train_rows."""
    cost = sustainable.cost_table(all_results).set_index(["strategy", "classifier"])
    inc = cost.loc[("incremental", "sgd")]
    assert inc["mean_train_rows"] == 900 and inc["update_rows"] == 300
    assert cost.drop(index=("incremental", "sgd"))["update_rows"].isna().all()


def test_pred_malware_rate_and_year_diagnostic(all_results, drift_df):
    """Review comment 2: predicted-malware rate equals (tp + fp) / n; the 2018-vs-2019 diagnostic has one row per year."""
    assert np.allclose(all_results["pred_malware_rate"], (all_results["tp"] + all_results["fp"]) / all_results["n"])
    diag = sustainable.year_diagnostic(drift_df)
    assert {2018, 2019} <= set(diag["year"])
    assert ((diag["mean_nonzero_rate"] >= 0) & (diag["clip_share"] >= 0) & (diag["clip_share"] <= 1)).all()
