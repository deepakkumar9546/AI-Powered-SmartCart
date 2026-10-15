"""
Builds the customer-product feature matrix used to train and serve the purchase
prediction model (Step 5 / Step 6 of the SmartCart specification).
"""

import os

import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLEANED_DIR = os.path.join(os.path.dirname(BASE_DIR), "data", "cleaned")

FEATURE_COLUMNS = [
    "customer_age",
    "total_purchases",
    "total_spending",
    "average_order_value",
    "website_visits",
    "product_price",
    "product_rating",
    "product_views",
    "cart_additions",
    "wishlist_additions",
    "previous_purchases",
    "time_spent",
]
TARGET_COLUMN = "purchased"


def build_feature_dataset(cleaned_dir: str = CLEANED_DIR):
    customers = pd.read_csv(os.path.join(cleaned_dir, "customers.csv"))
    products = pd.read_csv(os.path.join(cleaned_dir, "products.csv"))
    activity = pd.read_csv(os.path.join(cleaned_dir, "customer_activity.csv"))

    df = activity.merge(
        customers[
            ["customer_id", "age", "total_purchases", "total_spending", "average_order_value", "website_visits"]
        ],
        on="customer_id",
        how="inner",
    )
    df = df.merge(products[["product_id", "price", "rating"]], on="product_id", how="inner")
    df = df.rename(columns={"age": "customer_age", "price": "product_price", "rating": "product_rating"})

    X = df[FEATURE_COLUMNS].copy()
    y = df[TARGET_COLUMN].copy()
    return X, y


if __name__ == "__main__":
    X, y = build_feature_dataset()
    print(f"Feature matrix shape: {X.shape}")
    print(f"Target distribution:\n{y.value_counts()}")
