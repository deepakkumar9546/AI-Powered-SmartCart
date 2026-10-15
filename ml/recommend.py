"""
Content-based product recommendation engine (Step 9). Scores candidate products for
a customer using category affinity (from past orders), product rating, and overall
popularity, then returns the top-N recommendations.
"""

from sqlalchemy import func
from sqlalchemy.orm import Session

from db import models


def _popularity_scores(db: Session):
    rows = (
        db.query(models.OrderItem.product_id, func.sum(models.OrderItem.quantity).label("units"))
        .group_by(models.OrderItem.product_id)
        .all()
    )
    if not rows:
        return {}
    max_units = max(r.units for r in rows) or 1
    return {r.product_id: r.units / max_units for r in rows}


def recommend_products(db: Session, customer_id: int, top_n: int = 5):
    purchased_product_ids = {
        row.product_id
        for row in (
            db.query(models.OrderItem.product_id)
            .join(models.Order, models.Order.order_id == models.OrderItem.order_id)
            .filter(models.Order.customer_id == customer_id)
            .all()
        )
    }

    purchased_categories = set()
    if purchased_product_ids:
        purchased_categories = {
            p.category
            for p in db.query(models.Product).filter(models.Product.product_id.in_(purchased_product_ids)).all()
        }

    popularity = _popularity_scores(db)

    query = db.query(models.Product)
    if purchased_product_ids:
        query = query.filter(~models.Product.product_id.in_(purchased_product_ids))
    candidates = query.all()

    scored = []
    for product in candidates:
        rating_score = (product.rating or 0) / 5
        category_match = 1.0 if product.category in purchased_categories else 0.0
        popularity_score = popularity.get(product.product_id, 0.0)

        if purchased_categories:
            score = 0.5 * category_match + 0.3 * rating_score + 0.2 * popularity_score
        else:
            score = 0.6 * rating_score + 0.4 * popularity_score

        scored.append(
            {
                "product_id": product.product_id,
                "product_name": product.product_name,
                "score": round(float(score), 4),
            }
        )

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_n]
