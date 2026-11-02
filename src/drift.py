"""Step 2: measure feature drift (KS tests) and concept drift (train-on-i / test-on-j accuracy).

Diagnostic only: nothing here feeds Steps 3-7, so it is exempt from the train-2014-2016 rule
(see PLAN.md section 0).
"""
from __future__ import annotations

from itertools import combinations

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

from src.config import ALL_YEARS, LABEL_COL, SEED, YEAR_COL


def subsample_years(df: pd.DataFrame, n: int | None = None, seed: int = SEED) -> dict[int, pd.DataFrame]:
    """Return an equal-size, class-balanced random sample of n rows per year (n=None: smallest year)."""
    years = sorted(df[YEAR_COL].unique())
    if n is None:
        n = int(min((df[YEAR_COL] == y).sum() for y in years))
    half = n // 2
    out: dict[int, pd.DataFrame] = {}
    for y in years:
        parts = []
        for label in (0, 1):
            rows = df[(df[YEAR_COL] == y) & (df[LABEL_COL] == label)]
            if len(rows) < half:
                raise ValueError(f"year {y} class {label} has {len(rows)} rows, need {half}")
            parts.append(rows.sample(n=half, random_state=seed))
        out[int(y)] = pd.concat(parts).reset_index(drop=True)
    return out


def ks_feature_table(a: pd.DataFrame, b: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    """Run ks_2samp on each feature; features constant with the same value in both samples are skipped."""
    xa = a[features].to_numpy()
    xb = b[features].to_numpy()
    stat = np.full(len(features), np.nan)
    pval = np.full(len(features), np.nan)
    skipped = np.zeros(len(features), dtype=bool)
    for k in range(len(features)):
        ca, cb = xa[:, k], xb[:, k]
        # Constant in both samples with the same value: nothing to compare.
        if ca.min() == ca.max() and cb.min() == cb.max() and ca[0] == cb[0]:
            skipped[k] = True
            continue
        res = ks_2samp(ca, cb)
        stat[k], pval[k] = res.statistic, res.pvalue
    tested = ~skipped
    if np.isnan(stat[tested]).any() or np.isnan(pval[tested]).any():
        raise ValueError("KS produced NaN for a tested feature")
    return pd.DataFrame({"feature": features, "ks_stat": stat, "p_value": pval, "skipped": skipped})


def bonferroni_significant(p_values: np.ndarray, alpha: float = 0.05) -> np.ndarray:
    """Boolean mask p < alpha / m, with m the number of tested (non-NaN) p-values; NaN is never significant."""
    p = np.asarray(p_values, dtype=float)
    m = int((~np.isnan(p)).sum())
    if m == 0:
        return np.zeros(p.shape, dtype=bool)
    with np.errstate(invalid="ignore"):
        return p < alpha / m


def ks_all_pairs(samples: dict[int, pd.DataFrame], features: list[str]) -> dict[tuple[int, int], pd.DataFrame]:
    """KS feature table for every year pair (a < b); the other tables are views on this dict."""
    return {(a, b): ks_feature_table(samples[a], samples[b], features) for a, b in combinations(sorted(samples), 2)}


def _pair_row(a: int, b: int, table: pd.DataFrame) -> dict:
    """Summary of one pair's feature table: tested/skipped counts, mean KS, % Bonferroni-significant."""
    tested = ~table["skipped"].to_numpy()
    sig = bonferroni_significant(table["p_value"].to_numpy())
    return {
        "year_a": a,
        "year_b": b,
        "n_tested": int(tested.sum()),
        "n_skipped": int((~tested).sum()),
        "mean_ks": float(table.loc[tested, "ks_stat"].mean()),
        "share_significant": float(sig.sum() / max(tested.sum(), 1)),
    }


def ks_year_pairs(pairs: dict[tuple[int, int], pd.DataFrame], mode: str) -> pd.DataFrame:
    """One summary row per pair: mode 'vs_2014', 'consecutive' or 'all' (every pair)."""
    if mode == "vs_2014":
        keys = [k for k in pairs if k[0] == min(ALL_YEARS)]
    elif mode == "consecutive":
        keys = [k for k in pairs if k[1] - k[0] == 1]
    elif mode == "all":
        keys = list(pairs)
    else:
        raise ValueError(f"unknown mode {mode!r}")
    return pd.DataFrame([_pair_row(a, b, pairs[(a, b)]) for a, b in sorted(keys)])


def ks_matrix(pair_table: pd.DataFrame, years: list[int], value: str = "mean_ks") -> pd.DataFrame:
    """Symmetric year x year matrix of a pair-table column (diagonal 0)."""
    m = pd.DataFrame(0.0, index=years, columns=years)
    for _, r in pair_table.iterrows():
        m.loc[int(r.year_a), int(r.year_b)] = m.loc[int(r.year_b), int(r.year_a)] = r[value]
    return m


def most_different_years(pair_table: pd.DataFrame) -> pd.DataFrame:
    """Pairs ranked by mean KS, largest first."""
    return pair_table.sort_values("mean_ks", ascending=False).reset_index(drop=True)


def top_drifting_features(
    pairs: dict[tuple[int, int], pd.DataFrame],
    samples: dict[int, pd.DataFrame],
    features: list[str],
    k: int = 20,
) -> pd.DataFrame:
    """Top-k features by mean KS over the 'vs 2014' comparisons, with per-year KS and per-year means."""
    base = min(samples)
    later = [y for y in sorted(samples) if y != base]
    out = pd.DataFrame({"feature": features})
    for y in later:
        out[f"ks_{y}"] = pairs[(base, y)]["ks_stat"].to_numpy()
    out["mean_ks"] = out[[f"ks_{y}" for y in later]].mean(axis=1)  # NaN rows (skipped everywhere) sort last
    for y in sorted(samples):
        out[f"mean_{y}"] = samples[y][features].to_numpy().mean(axis=0)
    return out.sort_values("mean_ks", ascending=False).head(k).reset_index(drop=True)
