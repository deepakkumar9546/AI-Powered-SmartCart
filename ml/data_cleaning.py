"""
Cleans the raw SmartCart datasets: handles missing values, duplicates, incorrect
dtypes, invalid prices/ages, missing ratings, and invalid foreign-key references.
Writes cleaned CSVs to data/cleaned/.
"""

import os

import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(os.path.dirname(BASE_DIR), "data", "raw")
CLEANED_DIR = os.path.join(os.path.dirname(BASE_DIR), "data", "cleaned")
os.makedirs(CLEANED_DIR, exist_ok=True)


def clean_customers(df):
    print(f"[customers] missing values:\n{df.isnull().sum()}\n")
    before = len(df)
    df = df.drop_duplicates(subset=["customer_id"]).copy()
    print(f"[customers] removed {before - len(df)} duplicate rows")

    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    invalid_age_mask = (df["age"] < 0) | (df["age"] > 100) | df["age"].isna()
    median_age = df.loc[~invalid_age_mask, "age"].median()
    print(f"[customers] fixing {invalid_age_mask.sum()} invalid ages with median={median_age}")
    df.loc[invalid_age_mask, "age"] = median_age
    df["age"] = df["age"].astype(int)

    df["total_purchases"] = df["total_purchases"].fillna(0).astype(int)
    df["total_spending"] = df["total_spending"].fillna(0.0)
    df["average_order_value"] = df["average_order_value"].fillna(0.0)
    df["website_visits"] = df["website_visits"].fillna(0).astype(int)
    return df


def clean_products(df):
    print(f"[products] missing values:\n{df.isnull().sum()}\n")
    before = len(df)
    df = df.drop_duplicates(subset=["product_id"]).copy()
    print(f"[products] removed {before - len(df)} duplicate rows")

    df["price"] = df["price"].astype(str).str.replace("$", "", regex=False).str.strip()
    df["price"] = pd.to_numeric(df["price"], errors="coerce")

    invalid_price_mask = (df["price"] <= 0) | df["price"].isna()
    median_price_by_category = df.loc[~invalid_price_mask].groupby("category")["price"].median()
    print(f"[products] fixing {invalid_price_mask.sum()} invalid prices using category medians")
    for idx in df[invalid_price_mask].index:
        category = df.loc[idx, "category"]
        df.loc[idx, "price"] = median_price_by_category.get(category, df["price"].median())

    missing_rating_mask = df["rating"].isna()
    mean_rating_by_category = df.loc[~missing_rating_mask].groupby("category")["rating"].mean()
    print(f"[products] filling {missing_rating_mask.sum()} missing ratings using category means")
    for idx in df[missing_rating_mask].index:
        category = df.loc[idx, "category"]
        df.loc[idx, "rating"] = round(mean_rating_by_category.get(category, df["rating"].mean()), 1)

    df["stock"] = df["stock"].fillna(0).astype(int)
    df["discount"] = df["discount"].fillna(0.0)
    return df


def clean_orders(df, valid_customer_ids, valid_product_ids):
    print(f"[orders] missing values:\n{df.isnull().sum()}\n")
    before = len(df)
    df = df.drop_duplicates(subset=["order_id"]).copy()

    invalid_ref_mask = ~df["customer_id"].isin(valid_customer_ids) | ~df["product_id"].isin(valid_product_ids)
    print(f"[orders] dropping {invalid_ref_mask.sum()} rows with invalid customer/product references")
    df = df[~invalid_ref_mask]

    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(1).astype(int)
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df.dropna(subset=["price"])
    print(f"[orders] removed {before - len(df)} rows total after cleaning")
    return df


def clean_customer_activity(df, valid_customer_ids, valid_product_ids):
    print(f"[customer_activity] missing values:\n{df.isnull().sum()}\n")
    before = len(df)
    df = df.drop_duplicates(subset=["customer_id", "product_id"]).copy()

    invalid_ref_mask = ~df["customer_id"].isin(valid_customer_ids) | ~df["product_id"].isin(valid_product_ids)
    print(f"[customer_activity] dropping {invalid_ref_mask.sum()} rows with invalid references")
    df = df[~invalid_ref_mask]

    numeric_cols = [
        "product_views", "cart_additions", "wishlist_additions",
        "previous_purchases", "time_spent", "purchased",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["purchased"] = df["purchased"].astype(int)
    print(f"[customer_activity] removed {before - len(df)} rows total after cleaning")
    return df


def main():
    customers = clean_customers(pd.read_csv(os.path.join(RAW_DIR, "customers.csv")))
    products = clean_products(pd.read_csv(os.path.join(RAW_DIR, "products.csv")))

    valid_customer_ids = set(customers["customer_id"])
    valid_product_ids = set(products["product_id"])

    orders = clean_orders(pd.read_csv(os.path.join(RAW_DIR, "orders.csv")), valid_customer_ids, valid_product_ids)
    activity = clean_customer_activity(
        pd.read_csv(os.path.join(RAW_DIR, "customer_activity.csv")), valid_customer_ids, valid_product_ids
    )

    customers.to_csv(os.path.join(CLEANED_DIR, "customers.csv"), index=False)
    products.to_csv(os.path.join(CLEANED_DIR, "products.csv"), index=False)
    orders.to_csv(os.path.join(CLEANED_DIR, "orders.csv"), index=False)
    activity.to_csv(os.path.join(CLEANED_DIR, "customer_activity.csv"), index=False)

    print(f"\nCleaned datasets saved to {CLEANED_DIR}")
    print("\nBasic EDA (cleaned customers):")
    print(customers.describe())


if __name__ == "__main__":
    main()
