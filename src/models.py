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

from src.config import CACHE_DIR, SEED, TRAIN_YEARS

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


def train_model(name: str, X_train: np.ndarray, y_train: np.ndarray) -> Any:
    """Build the named classifier and fit it on the training data."""
    model = build_model(name)
    model.fit(X_train, y_train)
    return model


def train_all(X_train: np.ndarray, y_train: np.ndarray) -> dict[str, Any]:
    """Train every classifier in MODEL_NAMES on the same training data."""
    return {name: train_model(name, X_train, y_train) for name in MODEL_NAMES}


def train_all_from_split(split: dict) -> dict[str, Any]:
    """Static Step 4 entry point: train all models on a Step 3 split; training years must be within TRAIN_YEARS."""
    years = set(np.unique(split["years_train"]).tolist())
    if not years <= set(TRAIN_YEARS):
        raise ValueError(f"training data contains years outside {TRAIN_YEARS}: {sorted(years - set(TRAIN_YEARS))}")
    return train_all(split["X_train"], split["y_train"])


def train_with_report(split: dict) -> tuple[dict[str, Any], pd.DataFrame]:
    """Train all models (with the same year guard) and return them plus a TRAINING-only sanity table.

    Columns: model, train_seconds, train_accuracy, convergence_warnings. The accuracy is measured on the
    training rows themselves; it is a sanity check, not an evaluation.
    """
    years = set(np.unique(split["years_train"]).tolist())
    if not years <= set(TRAIN_YEARS):
        raise ValueError(f"training data contains years outside {TRAIN_YEARS}")
    models: dict[str, Any] = {}
    rows = []
    for name in MODEL_NAMES:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")  # record, never hide, warnings
            start = time.perf_counter()
            model = train_model(name, split["X_train"], split["y_train"])
            seconds = time.perf_counter() - start
        n_conv = sum(issubclass(w.category, ConvergenceWarning) for w in caught)
        acc = float((model.predict(split["X_train"]) == split["y_train"]).mean())
        models[name] = model
        rows.append((name, round(seconds, 2), round(acc, 4), n_conv))
    return models, pd.DataFrame(rows, columns=["model", "train_seconds", "train_accuracy", "convergence_warnings"])


def save_models(models: dict[str, Any], model_dir=MODEL_DIR) -> None:
    """Save fitted models with joblib into a git-ignored folder."""
    model_dir.mkdir(parents=True, exist_ok=True)
    for name, model in models.items():
        joblib.dump(model, model_dir / f"{name}.joblib")
