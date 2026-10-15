"""
Loads trained ML artifacts (purchase prediction model + segmentation model) and
exposes simple inference helpers for the FastAPI routers. Raises 503 if a model has
not been trained yet.
"""

import os

import joblib
import pandas as pd
from fastapi import HTTPException, status

ARTIFACTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ml", "artifacts")

_purchase_model = None
_preprocessing = None
_segmentation = None


def _load_purchase_artifacts():
    global _purchase_model, _preprocessing
    if _purchase_model is None or _preprocessing is None:
        model_path = os.path.join(ARTIFACTS_DIR, "purchase_model.pkl")
        prep_path = os.path.join(ARTIFACTS_DIR, "preprocessing.pkl")
        if not os.path.exists(model_path) or not os.path.exists(prep_path):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Purchase prediction model is unavailable. Run the training pipeline first.",
            )
        _purchase_model = joblib.load(model_path)
        _preprocessing = joblib.load(prep_path)
    return _purchase_model, _preprocessing


def _load_segmentation_artifacts():
    global _segmentation
    if _segmentation is None:
        seg_path = os.path.join(ARTIFACTS_DIR, "segmentation_model.pkl")
        if not os.path.exists(seg_path):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Customer segmentation model is unavailable. Run the training pipeline first.",
            )
        _segmentation = joblib.load(seg_path)
    return _segmentation


def predict_purchase_probability(customer, product, activity) -> float:
    model, prep = _load_purchase_artifacts()
    scaler = prep["scaler"]
    feature_columns = prep["feature_columns"]

    row = {
        "customer_age": customer.age,
        "total_purchases": customer.total_purchases,
        "total_spending": customer.total_spending,
        "average_order_value": customer.average_order_value,
        "website_visits": customer.website_visits,
        "product_price": product.price,
        "product_rating": product.rating or 0,
        "product_views": activity.product_views if activity else 0,
        "cart_additions": activity.cart_additions if activity else 0,
        "wishlist_additions": activity.wishlist_additions if activity else 0,
        "previous_purchases": activity.previous_purchases if activity else 0,
        "time_spent": activity.time_spent if activity else 0,
    }
    X = pd.DataFrame([row])[feature_columns]
    X_scaled = scaler.transform(X)
    proba = model.predict_proba(X_scaled)[0][1]
    return float(proba)


def get_customer_segment(customer) -> str:
    artifacts = _load_segmentation_artifacts()
    kmeans = artifacts["kmeans"]
    scaler = artifacts["scaler"]
    label_map = artifacts["cluster_label_map"]
    feature_columns = artifacts["feature_columns"]

    today = pd.Timestamp.utcnow().tz_localize(None)
    days_since_registration = max((today - pd.Timestamp(customer.registration_date)).days, 1)
    purchase_frequency = customer.total_purchases / days_since_registration

    row = {
        "total_purchases": customer.total_purchases,
        "total_spending": customer.total_spending,
        "average_order_value": customer.average_order_value,
        "website_visits": customer.website_visits,
        "purchase_frequency": purchase_frequency,
    }
    X = pd.DataFrame([row])[feature_columns]
    X_scaled = scaler.transform(X)
    cluster = int(kmeans.predict(X_scaled)[0])
    return label_map[cluster]
