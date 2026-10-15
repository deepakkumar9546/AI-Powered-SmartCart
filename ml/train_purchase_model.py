"""
Trains and compares three classification models (Logistic Regression, Decision Tree,
Random Forest) to predict whether a customer will purchase a given product, then
saves the best-performing model + preprocessing objects for serving (Step 6 / 7).
"""

import os

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

from ml.feature_engineering import FEATURE_COLUMNS, build_feature_dataset

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARTIFACTS_DIR = os.path.join(BASE_DIR, "artifacts")
os.makedirs(ARTIFACTS_DIR, exist_ok=True)


def evaluate_model(name, model, X_test, y_test):
    preds = model.predict(X_test)
    proba = model.predict_proba(X_test)[:, 1]
    metrics = {
        "model": name,
        "accuracy": accuracy_score(y_test, preds),
        "precision": precision_score(y_test, preds, zero_division=0),
        "recall": recall_score(y_test, preds, zero_division=0),
        "f1_score": f1_score(y_test, preds, zero_division=0),
        "roc_auc": roc_auc_score(y_test, proba),
    }
    cm = confusion_matrix(y_test, preds)
    return metrics, cm


def main():
    X, y = build_feature_dataset()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    candidates = {
        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
        "Decision Tree": DecisionTreeClassifier(max_depth=6, random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42),
    }

    results = []
    confusion_matrices = {}
    trained_models = {}
    for name, model in candidates.items():
        model.fit(X_train_scaled, y_train)
        metrics, cm = evaluate_model(name, model, X_test_scaled, y_test)
        results.append(metrics)
        confusion_matrices[name] = cm
        trained_models[name] = model

    results_df = pd.DataFrame(results).sort_values("roc_auc", ascending=False)
    print("Model comparison:\n", results_df.to_string(index=False))

    best_name = results_df.iloc[0]["model"]
    best_model = trained_models[best_name]
    print(f"\nBest model: {best_name} (highest ROC-AUC)")
    print(f"Confusion matrix:\n{confusion_matrices[best_name]}")

    joblib.dump(best_model, os.path.join(ARTIFACTS_DIR, "purchase_model.pkl"))
    joblib.dump(
        {"scaler": scaler, "feature_columns": FEATURE_COLUMNS},
        os.path.join(ARTIFACTS_DIR, "preprocessing.pkl"),
    )

    with open(os.path.join(ARTIFACTS_DIR, "model_comparison.txt"), "w") as f:
        f.write(results_df.to_string(index=False))
        f.write(f"\n\nBest model selected: {best_name} (highest ROC-AUC)\n")
        f.write(f"Confusion matrix ({best_name}):\n{confusion_matrices[best_name]}\n")

    print(f"\nSaved purchase_model.pkl and preprocessing.pkl to {ARTIFACTS_DIR}")


if __name__ == "__main__":
    main()
