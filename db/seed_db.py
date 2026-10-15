"""
Loads the cleaned CSV datasets into the SQLite database and bootstraps demo login
credentials for every seeded customer plus a default admin account.
"""

import os

import pandas as pd

from app.auth import hash_password
from db import models
from db.database import Base, SessionLocal, engine

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEANED_DIR = os.path.join(BASE_DIR, "data", "cleaned")

DEFAULT_PASSWORD = "Password123!"
ADMIN_EMAIL = "admin@smartcart.com"
ADMIN_PASSWORD = "Admin@123"


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(models.Customer).count() > 0:
            print("Database already seeded. Skipping.")
            return

        customers_df = pd.read_csv(os.path.join(CLEANED_DIR, "customers.csv"), parse_dates=["registration_date"])
        products_df = pd.read_csv(os.path.join(CLEANED_DIR, "products.csv"))
        orders_df = pd.read_csv(os.path.join(CLEANED_DIR, "orders.csv"), parse_dates=["order_date"])
        activity_df = pd.read_csv(os.path.join(CLEANED_DIR, "customer_activity.csv"))

        for _, row in customers_df.iterrows():
            customer_id = int(row["customer_id"])
            db.add(
                models.Customer(
                    customer_id=customer_id,
                    name=f"Customer {customer_id}",
                    email=f"customer{customer_id}@smartcart.com",
                    age=int(row["age"]),
                    gender=row["gender"],
                    city=row["city"],
                    registration_date=row["registration_date"].date(),
                    total_purchases=int(row["total_purchases"]),
                    total_spending=float(row["total_spending"]),
                    average_order_value=float(row["average_order_value"]),
                    website_visits=int(row["website_visits"]),
                )
            )
        db.flush()

        for _, row in products_df.iterrows():
            db.add(
                models.Product(
                    product_id=int(row["product_id"]),
                    product_name=row["product_name"],
                    category=row["category"],
                    price=float(row["price"]),
                    rating=float(row["rating"]),
                    stock=int(row["stock"]),
                    discount=float(row["discount"]),
                )
            )
        db.flush()

        valid_customer_ids = set(customers_df["customer_id"])
        valid_product_ids = set(products_df["product_id"])

        for _, row in orders_df.iterrows():
            if row["customer_id"] not in valid_customer_ids or row["product_id"] not in valid_product_ids:
                continue
            total_amount = round(float(row["price"]) * int(row["quantity"]), 2)
            order = models.Order(
                order_id=int(row["order_id"]),
                customer_id=int(row["customer_id"]),
                order_date=row["order_date"].to_pydatetime(),
                payment_method=row["payment_method"],
                order_status=row["order_status"],
                total_amount=total_amount,
            )
            db.add(order)
            db.flush()
            db.add(
                models.OrderItem(
                    order_id=order.order_id,
                    product_id=int(row["product_id"]),
                    quantity=int(row["quantity"]),
                    price=float(row["price"]),
                )
            )
        db.flush()

        for _, row in activity_df.iterrows():
            db.add(
                models.CustomerActivity(
                    customer_id=int(row["customer_id"]),
                    product_id=int(row["product_id"]),
                    product_views=int(row["product_views"]),
                    cart_additions=int(row["cart_additions"]),
                    wishlist_additions=int(row["wishlist_additions"]),
                    previous_purchases=int(row["previous_purchases"]),
                    time_spent=float(row["time_spent"]),
                    purchased=int(row["purchased"]),
                )
            )
        db.flush()

        db.add(
            models.User(
                email=ADMIN_EMAIL,
                hashed_password=hash_password(ADMIN_PASSWORD),
                role="admin",
                customer_id=None,
            )
        )

        for customer_id in customers_df["customer_id"]:
            db.add(
                models.User(
                    email=f"customer{int(customer_id)}@smartcart.com",
                    hashed_password=hash_password(DEFAULT_PASSWORD),
                    role="customer",
                    customer_id=int(customer_id),
                )
            )

        db.commit()
        print(
            f"Seeded {len(customers_df)} customers, {len(products_df)} products, "
            f"{orders_df['order_id'].nunique()} orders, {len(activity_df)} activity rows"
        )
        print(f"Admin login -> email: {ADMIN_EMAIL}, password: {ADMIN_PASSWORD}")
        print(f"Any customer login -> email: customer<id>@smartcart.com, password: {DEFAULT_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
