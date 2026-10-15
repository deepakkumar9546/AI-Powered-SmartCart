"""
Exploratory data analysis over the cleaned SmartCart datasets. Prints answers to the
required business questions and saves charts under ml/artifacts/eda/.
"""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data", "cleaned")
EDA_DIR = os.path.join(BASE_DIR, "artifacts", "eda")
os.makedirs(EDA_DIR, exist_ok=True)


def main():
    customers = pd.read_csv(os.path.join(DATA_DIR, "customers.csv"))
    products = pd.read_csv(os.path.join(DATA_DIR, "products.csv"))
    orders = pd.read_csv(os.path.join(DATA_DIR, "orders.csv"), parse_dates=["order_date"])

    completed = orders[orders["order_status"] == "completed"].copy()
    completed["revenue"] = completed["price"] * completed["quantity"]
    merged = completed.merge(products[["product_id", "category", "product_name"]], on="product_id", how="left")

    print("=== Which product category has the highest sales? ===")
    category_sales = merged.groupby("category")["revenue"].sum().sort_values(ascending=False)
    print(category_sales, "\n")

    print("=== Which products generate the highest revenue? ===")
    product_revenue = merged.groupby("product_name")["revenue"].sum().sort_values(ascending=False).head(10)
    print(product_revenue, "\n")

    print("=== Which customers spend the most? ===")
    top_customers = customers.sort_values("total_spending", ascending=False)[["customer_id", "total_spending"]].head(10)
    print(top_customers, "\n")

    print("=== Average order value ===")
    avg_order_value = completed["revenue"].sum() / completed["order_id"].nunique()
    print(round(avg_order_value, 2), "\n")

    print("=== Most common payment method ===")
    print(orders["payment_method"].value_counts().idxmax(), "\n")

    print("=== City with highest number of customers ===")
    print(customers["city"].value_counts().idxmax(), "\n")

    print("=== Products with the highest ratings ===")
    print(products.sort_values("rating", ascending=False)[["product_name", "rating"]].head(10), "\n")

    print("=== Percentage of customers with repeat purchases ===")
    repeat_customers = customers[customers["total_purchases"] > 1].shape[0]
    pct_repeat = repeat_customers / customers.shape[0] * 100
    print(f"{pct_repeat:.1f}%\n")

    print("=== Monthly revenue ===")
    monthly_revenue = merged.set_index("order_date").resample("ME")["revenue"].sum()
    print(monthly_revenue, "\n")

    print("=== Products with low stock (<10) ===")
    low_stock = products[products["stock"] < 10][["product_name", "stock"]]
    print(low_stock, "\n")

    category_sales.plot(kind="bar", title="Revenue by Category", figsize=(8, 5))
    plt.tight_layout()
    plt.savefig(os.path.join(EDA_DIR, "revenue_by_category.png"))
    plt.close()

    monthly_revenue.plot(kind="line", marker="o", title="Monthly Revenue", figsize=(8, 5))
    plt.tight_layout()
    plt.savefig(os.path.join(EDA_DIR, "monthly_revenue.png"))
    plt.close()

    orders["payment_method"].value_counts().plot(kind="bar", title="Payment Method Usage", figsize=(8, 5))
    plt.tight_layout()
    plt.savefig(os.path.join(EDA_DIR, "payment_methods.png"))
    plt.close()

    customers["city"].value_counts().head(10).plot(kind="bar", title="Top 10 Cities by Customer Count", figsize=(8, 5))
    plt.tight_layout()
    plt.savefig(os.path.join(EDA_DIR, "top_cities.png"))
    plt.close()

    print(f"Saved EDA charts to {EDA_DIR}")


if __name__ == "__main__":
    main()
