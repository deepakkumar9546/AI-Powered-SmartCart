"""
Generates synthetic SmartCart datasets (customers, products, orders, customer_activity)
with intentional data-quality issues (duplicates, invalid ages/prices, missing ratings,
bad foreign-key references) so that the cleaning step (ml/data_cleaning.py) has real
problems to fix.
"""

import os
import random
from datetime import datetime

import numpy as np
import pandas as pd
from faker import Faker

fake = Faker()
random.seed(42)
np.random.seed(42)
Faker.seed(42)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "raw")
os.makedirs(RAW_DIR, exist_ok=True)

NUM_CUSTOMERS = 120
NUM_PRODUCTS = 60
NUM_ORDERS = 550

CATEGORIES = [
    "Electronics", "Fashion", "Home & Kitchen", "Books", "Beauty",
    "Sports", "Toys", "Grocery", "Automotive", "Furniture",
]
ADJECTIVES = ["Premium", "Classic", "Deluxe", "Pro", "Essential", "Smart", "Eco", "Ultra", "Compact", "Portable"]
PAYMENT_METHODS = ["Credit Card", "Debit Card", "UPI", "Net Banking", "Cash on Delivery", "Wallet"]
ORDER_STATUSES = ["completed"] * 6 + ["cancelled", "returned", "pending"]
GENDERS = ["Male", "Female", "Other"]

PRICE_RANGES = {
    "Electronics": (50, 1500), "Fashion": (10, 200), "Home & Kitchen": (15, 400),
    "Books": (5, 60), "Beauty": (5, 150), "Sports": (10, 500),
    "Toys": (5, 150), "Grocery": (2, 50), "Automotive": (20, 800), "Furniture": (50, 2000),
}


def generate_customers():
    rows = []
    for customer_id in range(1, NUM_CUSTOMERS + 1):
        registration_date = fake.date_between(start_date="-3y", end_date="-1m")
        rows.append(
            {
                "customer_id": customer_id,
                "age": random.randint(18, 70),
                "gender": random.choice(GENDERS),
                "city": fake.city(),
                "registration_date": registration_date,
                "website_visits": random.randint(1, 100),
            }
        )
    return pd.DataFrame(rows)


def generate_products():
    rows = []
    for product_id in range(1, NUM_PRODUCTS + 1):
        category = random.choice(CATEGORIES)
        low, high = PRICE_RANGES.get(category, (10, 200))
        price = round(random.uniform(low, high), 2)
        rating = round(float(np.clip(np.random.normal(4.0, 0.7), 1, 5)), 1)
        rows.append(
            {
                "product_id": product_id,
                "product_name": f"{random.choice(ADJECTIVES)} {category.split(' & ')[0]} {fake.word().title()}",
                "category": category,
                "price": price,
                "rating": rating,
                "stock": random.choice([0, 2, 5, 8] + list(range(10, 200))),
                "discount": random.choice([0, 5, 10, 15, 20, 25, 30]),
            }
        )
    return pd.DataFrame(rows)


def generate_orders(customers_df, products_df):
    customer_ids = customers_df["customer_id"].tolist()
    customer_weights = np.random.dirichlet(np.ones(len(customer_ids)) * 0.5)
    product_ids = products_df["product_id"].tolist()
    product_price_map = products_df.set_index("product_id")["price"].to_dict()
    product_discount_map = products_df.set_index("product_id")["discount"].to_dict()

    rows = []
    for order_id in range(1, NUM_ORDERS + 1):
        customer_id = int(np.random.choice(customer_ids, p=customer_weights))
        product_id = random.choice(product_ids)
        quantity = random.randint(1, 5)
        base_price = product_price_map[product_id]
        discount = product_discount_map[product_id]
        unit_price = round(base_price * (1 - discount / 100), 2)
        order_date = fake.date_time_between(start_date="-2y", end_date="now")
        rows.append(
            {
                "order_id": order_id,
                "customer_id": customer_id,
                "product_id": product_id,
                "quantity": quantity,
                "order_date": order_date,
                "price": unit_price,
                "payment_method": random.choice(PAYMENT_METHODS),
                "order_status": random.choice(ORDER_STATUSES),
            }
        )
    return pd.DataFrame(rows)


def compute_customer_aggregates(customers_df, orders_df):
    completed = orders_df[orders_df["order_status"] == "completed"].copy()
    completed["revenue"] = completed["price"] * completed["quantity"]

    agg = completed.groupby("customer_id").agg(
        total_purchases=("order_id", "count"),
        total_spending=("revenue", "sum"),
    ).reset_index()
    agg["average_order_value"] = (agg["total_spending"] / agg["total_purchases"]).round(2)
    agg["total_spending"] = agg["total_spending"].round(2)

    customers_df = customers_df.merge(agg, on="customer_id", how="left")
    customers_df["total_purchases"] = customers_df["total_purchases"].fillna(0).astype(int)
    customers_df["total_spending"] = customers_df["total_spending"].fillna(0.0)
    customers_df["average_order_value"] = customers_df["average_order_value"].fillna(0.0)

    column_order = [
        "customer_id", "age", "gender", "city", "registration_date",
        "total_purchases", "total_spending", "average_order_value", "website_visits",
    ]
    return customers_df[column_order]


def generate_customer_activity(customers_df, products_df, orders_df):
    purchase_counts = (
        orders_df[orders_df["order_status"] == "completed"]
        .groupby(["customer_id", "product_id"])
        .size()
        .to_dict()
    )

    product_ids = products_df["product_id"].tolist()
    rows = []
    for customer_id in customers_df["customer_id"]:
        num_products_seen = random.randint(10, 25)
        seen_products = random.sample(product_ids, min(num_products_seen, len(product_ids)))
        for product_id in seen_products:
            previous_purchases = purchase_counts.get((customer_id, product_id), 0)
            product_views = random.randint(1, 50)
            cart_additions = random.randint(0, min(10, product_views))
            wishlist_additions = random.randint(0, 5)
            time_spent = round(product_views * random.uniform(5, 20), 1)

            signal = (
                0.03 * product_views
                + 0.25 * cart_additions
                + 0.15 * wishlist_additions
                + 1.5 * previous_purchases
                + 0.01 * time_spent
                + np.random.normal(0, 0.5)
            )
            purchase_probability = 1 / (1 + np.exp(-(signal - 2)))
            purchased = 1 if (previous_purchases > 0 or random.random() < purchase_probability) else 0

            rows.append(
                {
                    "customer_id": customer_id,
                    "product_id": product_id,
                    "product_views": product_views,
                    "cart_additions": cart_additions,
                    "wishlist_additions": wishlist_additions,
                    "previous_purchases": previous_purchases,
                    "time_spent": time_spent,
                    "purchased": purchased,
                }
            )
    return pd.DataFrame(rows)


def inject_data_quality_issues(customers_df, products_df, orders_df, activity_df):
    # Duplicate customer rows
    customers_df = pd.concat([customers_df, customers_df.sample(3, random_state=1)], ignore_index=True)
    # Invalid ages (negative / unrealistically high)
    bad_age_idx = customers_df.sample(4, random_state=2).index
    customers_df.loc[bad_age_idx[:2], "age"] = -5
    customers_df.loc[bad_age_idx[2:], "age"] = 150

    # Duplicate product rows
    products_df = pd.concat([products_df, products_df.sample(2, random_state=3)], ignore_index=True)
    # Invalid prices (negative, and a stray "$" causing wrong dtype)
    bad_price_idx = products_df.sample(4, random_state=4).index
    products_df.loc[bad_price_idx[:2], "price"] = -10
    products_df.loc[bad_price_idx[2:], "price"] = (
        products_df.loc[bad_price_idx[2:], "price"].astype(str) + " $"
    )
    # Missing ratings
    missing_rating_idx = products_df.sample(5, random_state=5).index
    products_df.loc[missing_rating_idx, "rating"] = np.nan

    # Orders with invalid customer/product references
    bad_ref_orders = pd.DataFrame(
        [
            {
                "order_id": 10001, "customer_id": 99999, "product_id": 1, "quantity": 1,
                "order_date": datetime.now(), "price": 10.0, "payment_method": "UPI", "order_status": "completed",
            },
            {
                "order_id": 10002, "customer_id": 1, "product_id": 99999, "quantity": 1,
                "order_date": datetime.now(), "price": 10.0, "payment_method": "UPI", "order_status": "completed",
            },
        ]
    )
    orders_df = pd.concat([orders_df, bad_ref_orders], ignore_index=True)

    return customers_df, products_df, orders_df, activity_df


def main():
    customers_df = generate_customers()
    products_df = generate_products()
    orders_df = generate_orders(customers_df, products_df)
    customers_df = compute_customer_aggregates(customers_df, orders_df)
    activity_df = generate_customer_activity(customers_df, products_df, orders_df)

    customers_df, products_df, orders_df, activity_df = inject_data_quality_issues(
        customers_df, products_df, orders_df, activity_df
    )

    customers_df.to_csv(os.path.join(RAW_DIR, "customers.csv"), index=False)
    products_df.to_csv(os.path.join(RAW_DIR, "products.csv"), index=False)
    orders_df.to_csv(os.path.join(RAW_DIR, "orders.csv"), index=False)
    activity_df.to_csv(os.path.join(RAW_DIR, "customer_activity.csv"), index=False)

    print(
        f"Generated {len(customers_df)} customers, {len(products_df)} products, "
        f"{len(orders_df)} orders, {len(activity_df)} activity records"
    )
    print(f"Raw data saved to {RAW_DIR}")


if __name__ == "__main__":
    main()
