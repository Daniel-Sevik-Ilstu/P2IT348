"""Step 2 tests: data drift (KS feature drift, concept-drift accuracy matrix).

Written from ASSIGNMENT.md, AGENTS.md and PLAN.md (Step 2), not from the code's behaviour.
Concept-drift matrix is exempt from the train-years-only rule (PLAN.md section 0), so it is
not tested for year leakage; it is only tested for within-year hold-out on the diagonal.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.drift import (
    bonferroni_significant,
    concept_drift_matrix,
    ks_all_pairs,
    ks_feature_table,
    ks_year_pairs,
    most_different_years,
    run_drift_analysis,
    subsample_years,
    top_drifting_features,
)

YEARS = list(range(2014, 2022))


def make_df(years=YEARS, per_class=60, n_feat=6, seed=0, shift=None) -> pd.DataFrame:
    """Synthetic multi-year frame. `shift` = {year: amount} added to feature f0 of that year."""
    rng = np.random.default_rng(seed)
    parts = []
    for y in years:
        for label in (0, 1):
            x = rng.poisson(3, size=(per_class, n_feat)).astype(np.int32)
            x[:, 1] += 4 * label  # f1 carries the label so a classifier can learn something
            if shift and y in shift:
                x[:, 0] += shift[y]
            d = pd.DataFrame(x, columns=[f"f{i}" for i in range(n_feat)])
            d["label"] = label
            d["year"] = y
            parts.append(d)
    return pd.concat(parts, ignore_index=True)


def feats(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c not in ("label", "year")]


# ---------------------------------------------------------------- KS statistic

def test_ks_statistic_and_pvalue_within_unit_interval():
    rng = np.random.default_rng(1)
    a = pd.DataFrame(rng.poisson(3, (200, 5)), columns=list("abcde"))
    b = pd.DataFrame(rng.poisson(6, (200, 5)), columns=list("abcde"))
    t = ks_feature_table(a, b, list("abcde"))
    assert ((t.ks_stat >= 0) & (t.ks_stat <= 1)).all()
    assert ((t.p_value >= 0) & (t.p_value <= 1)).all()


def test_ks_identical_samples_give_zero_and_not_significant():
    df = make_df(years=[2014], per_class=100)
    f = feats(df)
    t = ks_feature_table(df, df.copy(), f)
    tested = t[~t.skipped]
    assert np.allclose(tested.ks_stat, 0.0)
    assert np.allclose(tested.p_value, 1.0)
    assert not bonferroni_significant(tested.p_value.to_numpy()).any()


def test_ks_same_distribution_different_draws_is_small_and_mostly_insignificant():
    rng = np.random.default_rng(3)
    a = pd.DataFrame(rng.normal(size=(2000, 20)), columns=[f"f{i}" for i in range(20)])
    b = pd.DataFrame(rng.normal(size=(2000, 20)), columns=a.columns)
    t = ks_feature_table(a, b, list(a.columns))
    assert t.ks_stat.max() < 0.1
    assert not bonferroni_significant(t.p_value.to_numpy()).any()


def test_ks_detects_clearly_shifted_feature():
    rng = np.random.default_rng(4)
    a = pd.DataFrame({"same": rng.normal(size=1000), "moved": rng.normal(size=1000)})
    b = pd.DataFrame({"same": rng.normal(size=1000), "moved": rng.normal(loc=3, size=1000)})
    t = ks_feature_table(a, b, ["same", "moved"]).set_index("feature")
    assert t.loc["moved", "ks_stat"] > 0.7
    assert t.loc["same", "ks_stat"] < 0.15
    sig = bonferroni_significant(t.p_value.to_numpy())
    assert sig.tolist() == [False, True]  # order: same, moved


def test_ks_is_symmetric():
    rng = np.random.default_rng(5)
    a = pd.DataFrame({"x": rng.poisson(2, 300)})
    b = pd.DataFrame({"x": rng.poisson(4, 300)})
    ab = ks_feature_table(a, b, ["x"]).ks_stat[0]
    ba = ks_feature_table(b, a, ["x"]).ks_stat[0]
    assert ab == pytest.approx(ba)


def test_ks_all_zero_feature_is_skipped_with_nan():
    a = pd.DataFrame({"z": np.zeros(50, dtype=int), "v": np.arange(50)})
    b = pd.DataFrame({"z": np.zeros(50, dtype=int), "v": np.arange(50) + 10})
    t = ks_feature_table(a, b, ["z", "v"]).set_index("feature")
    assert t.loc["z", "skipped"]
    assert np.isnan(t.loc["z", "ks_stat"]) and np.isnan(t.loc["z", "p_value"])
    assert not t.loc["v", "skipped"]


def test_ks_constant_in_both_with_same_nonzero_value_is_skipped():
    a = pd.DataFrame({"c": np.full(40, 7)})
    b = pd.DataFrame({"c": np.full(40, 7)})
    assert ks_feature_table(a, b, ["c"]).skipped.all()


def test_ks_constant_at_different_values_is_tested_and_maximal():
    """Constant in each sample but at different values is real drift: not skipped, KS = 1."""
    a = pd.DataFrame({"c": np.full(40, 1)})
    b = pd.DataFrame({"c": np.full(40, 5)})
    t = ks_feature_table(a, b, ["c"])
    assert not t.skipped[0]
    assert t.ks_stat[0] == pytest.approx(1.0)
    assert t.p_value[0] < 0.001


def test_ks_constant_in_one_sample_only_is_tested():
    a = pd.DataFrame({"c": np.zeros(60, dtype=int)})
    b = pd.DataFrame({"c": np.r_[np.zeros(30, dtype=int), np.ones(30, dtype=int)]})
    t = ks_feature_table(a, b, ["c"])
    assert not t.skipped[0]
    assert t.ks_stat[0] == pytest.approx(0.5)


def test_ks_table_has_required_columns_and_one_row_per_feature():
    df = make_df(years=[2014, 2015])
    f = feats(df)
    t = ks_feature_table(df[df.year == 2014], df[df.year == 2015], f)
    assert {"feature", "ks_stat", "p_value", "skipped"} <= set(t.columns)
    assert t.feature.tolist() == f


# ---------------------------------------------------------------- Bonferroni

def test_bonferroni_uses_alpha_over_number_of_tested_features():
    # m = 3 tested (NaN excluded) -> threshold 0.05/3 = 0.016667.
    # 0.014 passes with m=3 but would fail with m=4 (0.0125): this pins m excludes skipped.
    p = np.array([0.014, 0.02, 0.0, np.nan])
    assert bonferroni_significant(p).tolist() == [True, False, True, False]


def test_bonferroni_custom_alpha_and_all_nan():
    assert bonferroni_significant(np.array([0.004, 0.006]), alpha=0.01).tolist() == [True, False]
    out = bonferroni_significant(np.array([np.nan, np.nan]))
    assert out.shape == (2,) and not out.any()


# ---------------------------------------------------------------- subsampling

def test_subsample_equal_sizes_balanced_and_smallest_year_default():
    df = make_df(per_class=50)
    # make 2016 smaller: keep only 20 per class
    keep = ~((df.year == 2016) & (df.groupby(["year", "label"]).cumcount() >= 20))
    df = df[keep].reset_index(drop=True)
    s = subsample_years(df)
    assert sorted(s) == YEARS
    assert {len(v) for v in s.values()} == {40}
    for v in s.values():
        assert (v.label == 1).sum() == (v.label == 0).sum() == 20
        assert v.year.nunique() == 1


def test_subsample_explicit_n_and_year_label_consistency():
    df = make_df(per_class=50)
    s = subsample_years(df, n=30)
    for y, v in s.items():
        assert len(v) == 30 and (v.year == y).all()


def test_subsample_reproducible_with_seed_and_varies_across_seeds():
    df = make_df(per_class=80)
    a = subsample_years(df, n=40, seed=42)
    b = subsample_years(df, n=40, seed=42)
    c = subsample_years(df, n=40, seed=7)
    for y in a:
        pd.testing.assert_frame_equal(a[y], b[y])
    assert any(not a[y].equals(c[y]) for y in a)


def test_subsample_rows_come_from_the_source_year():
    df = make_df(per_class=50)
    s = subsample_years(df, n=20)
    f = feats(df)
    for y, v in s.items():
        src = {tuple(r) for r in df.loc[df.year == y, f + ["label"]].to_numpy()}
        assert all(tuple(r) in src for r in v[f + ["label"]].to_numpy())


def test_subsample_raises_when_a_class_is_too_small():
    df = make_df(per_class=10)
    with pytest.raises(ValueError):
        subsample_years(df, n=100)


# ---------------------------------------------------------------- year pairs

def test_year_pair_modes_have_expected_row_counts():
    df = make_df(per_class=40)
    s = subsample_years(df)
    pairs = ks_all_pairs(s, feats(df))
    assert len(pairs) == 28
    vs = ks_year_pairs(pairs, "vs_2014")
    cons = ks_year_pairs(pairs, "consecutive")
    allp = ks_year_pairs(pairs, "all")
    assert len(vs) == 7 and (vs.year_a == 2014).all()
    assert sorted(vs.year_b) == YEARS[1:]
    assert len(cons) == 7 and ((cons.year_b - cons.year_a) == 1).all()
    assert len(allp) == 28
    for t in (vs, cons, allp):
        assert {"year_a", "year_b", "n_tested", "n_skipped", "mean_ks", "share_significant"} <= set(t.columns)
        assert t.mean_ks.between(0, 1).all()
        assert t.share_significant.between(0, 1).all()


def test_year_pairs_unknown_mode_raises():
    df = make_df(per_class=20)
    pairs = ks_all_pairs(subsample_years(df), feats(df))
    with pytest.raises(ValueError):
        ks_year_pairs(pairs, "nonsense")


def test_year_pairs_no_drift_vs_shifted_year():
    """A year with a shifted feature has a larger mean KS and flagged features than an unshifted pair."""
    df = make_df(per_class=300, shift={2018: 6})
    s = subsample_years(df)
    pairs = ks_all_pairs(s, feats(df))
    allp = ks_year_pairs(pairs, "all").set_index(["year_a", "year_b"])
    assert allp.loc[(2014, 2018), "mean_ks"] > allp.loc[(2014, 2015), "mean_ks"]
    assert allp.loc[(2014, 2018), "share_significant"] > 0
    assert allp.loc[(2014, 2015), "share_significant"] == 0


def test_skipped_features_counted_in_pair_summary():
    df = make_df(per_class=40)
    df["dead"] = 0  # all-zero in every year
    s = subsample_years(df)
    f = feats(df)
    pairs = ks_all_pairs(s, f)
    row = ks_year_pairs(pairs, "vs_2014").iloc[0]
    assert row.n_skipped == 1
    assert row.n_tested == len(f) - 1


def test_most_different_years_sorted_descending_and_finds_shifted_year():
    df = make_df(per_class=300, shift={2020: 8})
    s = subsample_years(df)
    pairs = ks_all_pairs(s, feats(df))
    ranked = most_different_years(ks_year_pairs(pairs, "all"))
    assert ranked.mean_ks.is_monotonic_decreasing
    assert 2020 in (ranked.iloc[0].year_a, ranked.iloc[0].year_b)


# ---------------------------------------------------------------- top features

def test_top_drifting_features_returns_k_sorted_and_finds_shifted_feature():
    df = make_df(per_class=300, shift={y: 5 for y in range(2016, 2022)})
    s = subsample_years(df)
    f = feats(df)
    pairs = ks_all_pairs(s, f)
    top = top_drifting_features(pairs, s, f, k=3)
    assert len(top) == 3
    assert top.mean_ks.is_monotonic_decreasing
    assert top.feature.iloc[0] == "f0"
    assert top.mean_ks.between(0, 1).all()


def test_top_drifting_features_k_larger_than_features_returns_all():
    df = make_df(per_class=40)
    s = subsample_years(df)
    f = feats(df)
    top = top_drifting_features(ks_all_pairs(s, f), s, f, k=50)
    assert len(top) == len(f)


# ---------------------------------------------------------------- concept drift

def test_concept_drift_matrix_square_indexed_by_years_and_in_unit_interval():
    df = make_df(per_class=60)
    s = subsample_years(df)
    m = concept_drift_matrix(s, feats(df))
    assert m.shape == (8, 8)
    assert list(m.index) == YEARS and list(m.columns) == YEARS
    assert not m.isna().any().any()
    assert ((m >= 0) & (m <= 1)).all().all()


def test_concept_drift_matrix_learns_signal_on_stable_data():
    df = make_df(per_class=150)  # f1 separates classes in every year
    s = subsample_years(df)
    m = concept_drift_matrix(s, feats(df))
    assert np.diag(m.to_numpy()).mean() > 0.85
    assert m.to_numpy().mean() > 0.85


def test_concept_drift_matrix_shows_concept_drift():
    """Flip the label rule in 2021: a model trained on 2014 must do badly on 2021."""
    df = make_df(per_class=200)
    flip = df.year == 2021
    df.loc[flip, "label"] = 1 - df.loc[flip, "label"]
    m = concept_drift_matrix(subsample_years(df), feats(df))
    assert m.loc[2014, 2014] > 0.85
    assert m.loc[2014, 2021] < 0.3


def test_concept_drift_diagonal_is_held_out_not_training_accuracy():
    """Labels are pure noise: training accuracy would be high with many features, held-out ~0.5."""
    rng = np.random.default_rng(0)
    n_feat = 150
    parts = []
    for y in (2014, 2015):
        x = rng.poisson(3, size=(200, n_feat))
        d = pd.DataFrame(x, columns=[f"f{i}" for i in range(n_feat)])
        d["label"] = np.r_[np.zeros(100, int), np.ones(100, int)]  # independent of x
        d["year"] = y
        parts.append(d)
    df = pd.concat(parts, ignore_index=True)
    f = feats(df)
    m = concept_drift_matrix(subsample_years(df), f)
    assert m.loc[2014, 2014] < 0.7
    assert m.loc[2015, 2015] < 0.7


def test_concept_drift_matrix_is_deterministic_and_does_not_mutate_input():
    df = make_df(per_class=50)
    s = subsample_years(df)
    before = {y: v.copy() for y, v in s.items()}
    m1 = concept_drift_matrix(s, feats(df))
    m2 = concept_drift_matrix(s, feats(df))
    pd.testing.assert_frame_equal(m1, m2)
    for y in s:
        pd.testing.assert_frame_equal(s[y], before[y])


# ---------------------------------------------------------------- end to end

def test_run_drift_analysis_writes_expected_outputs(tmp_path):
    df = make_df(per_class=60)
    out = run_drift_analysis(df, results_dir=tmp_path)
    assert len(out["ks_vs_2014"]) == 7
    assert len(out["ks_consecutive"]) == 7
    assert out["accuracy_matrix"].shape == (8, 8)
    for name in ("ks_vs_2014", "ks_consecutive", "top20_features", "accuracy_matrix"):
        assert (tmp_path / f"step2_{name}.csv").is_file()
    got = pd.read_csv(tmp_path / "step2_ks_vs_2014.csv")
    assert len(got) == 7


# ---------------------------------------------------------------- real data

def test_real_data_ks_between_two_years(real_data_dir):
    """Real 2019 vs 2021 (3,000 rows each, per AGENTS.md): statistics valid, dead columns skipped."""
    from src.data import feature_columns, load_year

    a = load_year(2019, real_data_dir)
    b = load_year(2021, real_data_dir)
    f = feature_columns(a)
    assert len(f) == 1848
    assert len(a) == 3000 and len(b) == 3000  # AGENTS.md (not ASSIGNMENT.md's 1,500/file)
    t = ks_feature_table(a, b, f)
    tested = t[~t.skipped]
    assert 0 < len(tested) < 1848  # some columns are all-zero in both years
    assert tested.ks_stat.between(0, 1).all()
    assert tested.p_value.between(0, 1).all()
    both_zero = ((a[f] == 0).all() & (b[f] == 0).all()).to_numpy()
    assert t.skipped.sum() >= both_zero.sum()
    assert tested.ks_stat.mean() > 0  # 2019 vs 2021 are not identical
