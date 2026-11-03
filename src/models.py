"""Step 4: build and train the three classifiers (LogisticRegression, RandomForest, SGD)."""
from __future__ import annotations

import time
import warnings
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression, SGDClassifier

from src.config import CACHE_DIR, SEED, TEST_YEARS, TRAIN_YEARS
from src.preprocess import check_no_overlap

MODEL_NAMES: tuple[str, ...] = ("logreg", "random_forest", "sgd")
MODEL_DIR = CACHE_DIR / "models"  # git-ignored (cache/ is in .gitignore)


def build_model(name: str) -> Any:
    """Return an unfitted classifier for `name` in MODEL_NAMES; raise ValueError otherwise."""
    if name == "logreg":
        # Linear baseline; "balanced" weights guard against imbalance in later use.
        return LogisticRegression(
            class_weight="balanced", max_iter=1000, solver="lbfgs", C=1.0, random_state=SEED
        )
    if name == "random_forest":
        # Non-linear ensemble, insensitive to feature scale.
        return RandomForestClassifier(n_estimators=200, n_jobs=-1, random_state=SEED)
    if name == "sgd":
        # Incremental logistic model for Step 7. No class_weight: "balanced" is rejected by partial_fit.
        return SGDClassifier(
            loss="log_loss", penalty="l2", alpha=1e-4, max_iter=1000, tol=1e-3, random_state=SEED
        )
    raise ValueError(f"unknown model name {name!r}; expected one of {MODEL_NAMES}")


def _check_training_arrays(X_train: np.ndarray, y_train: np.ndarray) -> None:
    """Raise ValueError unless X_train and y_train are non-empty, equal length, and y_train is exactly {0, 1}."""
    if len(X_train) == 0:
        raise ValueError("training set is empty")
    if len(X_train) != len(y_train):
        raise ValueError(f"X_train has {len(X_train)} rows but y_train has {len(y_train)}")
    classes = set(np.unique(y_train).tolist())
    if classes != {0, 1}:
        raise ValueError(f"y_train must contain exactly the classes 0 and 1, found {sorted(classes)}")


def _check_training_split(split: dict) -> None:
    """Shared Step 4 guard: years non-empty, aligned with X/y, within TRAIN_YEARS, disjoint from TEST_YEARS."""
    years_train = np.asarray(split["years_train"])
    if years_train.size == 0:
        raise ValueError("years_train is empty")
    if not (len(years_train) == len(split["X_train"]) == len(split["y_train"])):
        raise ValueError(
            f"length mismatch: years_train={len(years_train)}, X_train={len(split['X_train'])}, "
            f"y_train={len(split['y_train'])}"
        )
    years = set(np.unique(years_train).tolist())
    if not years <= set(TRAIN_YEARS):
        raise ValueError(f"training data contains years outside {TRAIN_YEARS}: {sorted(years - set(TRAIN_YEARS))}")
    check_no_overlap(years, TEST_YEARS)  # PLAN.md section 0: every train call goes through this check
    _check_training_arrays(split["X_train"], split["y_train"])


def train_model(name: str, X_train: np.ndarray, y_train: np.ndarray) -> Any:
    """Build the named classifier and fit it on the training data (after checking the arrays)."""
    _check_training_arrays(X_train, y_train)
    model = build_model(name)
    model.fit(X_train, y_train)
    return model


def train_all(X_train: np.ndarray, y_train: np.ndarray) -> dict[str, Any]:
    """Train every classifier in MODEL_NAMES on the same training data."""
    return {name: train_model(name, X_train, y_train) for name in MODEL_NAMES}


def train_all_from_split(split: dict) -> dict[str, Any]:
    """Static Step 4 entry point: train all models on a Step 3 split; training years must be within TRAIN_YEARS."""
    _check_training_split(split)
    return train_all(split["X_train"], split["y_train"])


def train_with_report(split: dict) -> tuple[dict[str, Any], pd.DataFrame]:
    """Train all models (with the shared guard) and return them plus a TRAINING-only sanity table.

    Columns: model, train_seconds, train_accuracy, convergence_warnings, warning_messages (all recorded warnings). The accuracy is measured on the
    training rows themselves; it is a sanity check, not an evaluation.
    """
    _check_training_split(split)  # same guard as train_all_from_split
    models: dict[str, Any] = {}
    rows = []
    for name in MODEL_NAMES:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")  # record, never hide, warnings
            start = time.perf_counter()
            model = train_model(name, split["X_train"], split["y_train"])
            seconds = time.perf_counter() - start
        n_conv = sum(issubclass(w.category, ConvergenceWarning) for w in caught)
        messages = []
        for w in caught:
            text = f"{w.category.__name__}: {w.message}"
            if issubclass(w.category, ConvergenceWarning):
                # Trace the hit: which model, how many iterations it used.
                text = f"{name} (n_iter_={getattr(model, 'n_iter_', 'n/a')}) {text}"
            messages.append(text)
            # Re-emit so no recorded warning is lost; the pipeline is not stopped.
            warnings.warn(text, w.category, stacklevel=2)
        acc = float((model.predict(split["X_train"]) == split["y_train"]).mean())
        models[name] = model
        rows.append((name, round(seconds, 2), round(acc, 4), n_conv, " | ".join(messages)))
    columns = ["model", "train_seconds", "train_accuracy", "convergence_warnings", "warning_messages"]
    return models, pd.DataFrame(rows, columns=columns)


def save_models(models: dict[str, Any], model_dir=MODEL_DIR) -> None:
    """Save fitted models with joblib into a git-ignored folder."""
    model_dir.mkdir(parents=True, exist_ok=True)
    for name, model in models.items():
        joblib.dump(model, model_dir / f"{name}.joblib")
