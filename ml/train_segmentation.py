"""
Segments customers into behavioral groups using K-Means clustering on purchasing
features, then maps clusters to business-friendly labels (Step 8).
"""

import os

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data", "cleaned")
ARTIFACTS_DIR = os.path.join(BASE_DIR, "artifacts")
EDA_DIR = os.path.join(ARTIFACTS_DIR, "eda")
os.makedirs(EDA_DIR, exist_ok=True)

FEATURE_COLUMNS = ["total_purchases", "total_spending", "average_order_value", "website_visits", "purchase_frequency"]
SEGMENT_LABELS = ["Premium Customer", "Regular Customer", "Occasional Customer", "At-Risk Customer"]


def load_customer_features():
    customers = pd.read_csv(os.path.join(DATA_DIR, "customers.csv"), parse_dates=["registration_date"])
    today = pd.Timestamp.utcnow().tz_localize(None)
    days_since_registration = (today - customers["registration_date"]).dt.days.clip(lower=1)
    customers["purchase_frequency"] = customers["total_purchases"] / days_since_registration
    return customers


def main():
    customers = load_customer_features()
    X = customers[FEATURE_COLUMNS]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Elbow method to justify the chosen number of clusters.
    inertias = []
    k_range = range(1, 11)
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(X_scaled)
        inertias.append(km.inertia_)

    plt.figure(figsize=(8, 5))
    plt.plot(list(k_range), inertias, marker="o")
    plt.xlabel("Number of clusters (k)")
    plt.ylabel("Inertia")
    plt.title("Elbow Method for Optimal k")
    plt.savefig(os.path.join(EDA_DIR, "elbow_method.png"))
    plt.close()

    n_clusters = 4
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_assignments = kmeans.fit_predict(X_scaled)
    score = silhouette_score(X_scaled, cluster_assignments)
    print(f"Silhouette score for k={n_clusters}: {score:.3f}")

    customers["cluster"] = cluster_assignments
    cluster_order = (
        customers.groupby("cluster")["total_spending"].mean().sort_values(ascending=False).index.tolist()
    )
    cluster_label_map = {int(cluster): SEGMENT_LABELS[rank] for rank, cluster in enumerate(cluster_order)}

    customers["segment"] = customers["cluster"].map(cluster_label_map)
    print("\nSegment profile (mean feature values):")
    print(customers.groupby("segment")[FEATURE_COLUMNS].mean())

    joblib.dump(
        {
            "kmeans": kmeans,
            "scaler": scaler,
            "feature_columns": FEATURE_COLUMNS,
            "cluster_label_map": cluster_label_map,
        },
        os.path.join(ARTIFACTS_DIR, "segmentation_model.pkl"),
    )
    print(f"\nSaved segmentation_model.pkl to {ARTIFACTS_DIR}")


if __name__ == "__main__":
    main()
