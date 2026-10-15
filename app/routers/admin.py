"""
Admin-only analytics endpoints (Step 16).
"""

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.ml_utils import get_customer_segment
from db import models
from db.database import get_db

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/sales-summary")
def sales_summary(db: Session = Depends(get_db), _admin=Depends(require_admin)):
    total_orders = db.query(func.count(models.Order.order_id)).scalar() or 0
    total_revenue = db.query(func.sum(models.Order.total_amount)).scalar() or 0.0
    avg_order_value = (total_revenue / total_orders) if total_orders else 0.0
    return {
        "total_orders": total_orders,
        "total_revenue": round(total_revenue, 2),
        "average_order_value": round(avg_order_value, 2),
    }


@router.get("/top-products")
def top_products(limit: int = 10, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    rows = (
        db.query(
            models.OrderItem.product_id,
            models.Product.product_name,
            func.sum(models.OrderItem.quantity * models.OrderItem.price).label("revenue"),
            func.sum(models.OrderItem.quantity).label("units_sold"),
        )
        .join(models.Product, models.Product.product_id == models.OrderItem.product_id)
        .group_by(models.OrderItem.product_id, models.Product.product_name)
        .order_by(func.sum(models.OrderItem.quantity * models.OrderItem.price).desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "product_id": r.product_id,
            "product_name": r.product_name,
            "revenue": round(r.revenue, 2),
            "units_sold": r.units_sold,
        }
        for r in rows
    ]


@router.get("/top-customers")
def top_customers(limit: int = 10, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    customers = db.query(models.Customer).order_by(models.Customer.total_spending.desc()).limit(limit).all()
    return [
        {
            "customer_id": c.customer_id,
            "name": c.name,
            "total_spending": c.total_spending,
            "total_purchases": c.total_purchases,
        }
        for c in customers
    ]


@router.get("/category-sales")
def category_sales(db: Session = Depends(get_db), _admin=Depends(require_admin)):
    rows = (
        db.query(
            models.Product.category,
            func.sum(models.OrderItem.quantity * models.OrderItem.price).label("revenue"),
            func.sum(models.OrderItem.quantity).label("units_sold"),
        )
        .join(models.OrderItem, models.OrderItem.product_id == models.Product.product_id)
        .group_by(models.Product.category)
        .order_by(func.sum(models.OrderItem.quantity * models.OrderItem.price).desc())
        .all()
    )
    return [{"category": r.category, "revenue": round(r.revenue, 2), "units_sold": r.units_sold} for r in rows]


@router.get("/customer-segments")
def customer_segments(limit: int = 200, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    customers = db.query(models.Customer).limit(limit).all()
    results = []
    for c in customers:
        try:
            segment = get_customer_segment(c)
        except Exception:
            segment = "Unavailable"
        results.append({"customer_id": c.customer_id, "name": c.name, "segment": segment})
    return results


@router.get("/low-stock-products")
def low_stock_products(threshold: int = 10, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    products = (
        db.query(models.Product)
        .filter(models.Product.stock <= threshold)
        .order_by(models.Product.stock.asc())
        .all()
    )
    return [
        {"product_id": p.product_id, "product_name": p.product_name, "stock": p.stock, "category": p.category}
        for p in products
    ]
