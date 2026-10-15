"""
Aggregated customer dashboard endpoint (Step 15): profile, orders, segment,
recommendations, and purchase predictions in a single response.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schemas
from app.auth import get_current_user
from app.ml_utils import get_customer_segment, predict_purchase_probability
from db import models
from db.database import get_db
from ml.recommend import recommend_products

router = APIRouter(tags=["Customer Dashboard"])


@router.get("/customer-dashboard/{customer_id}", response_model=schemas.DashboardResponse)
def customer_dashboard(customer_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    customer = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    recommendations = recommend_products(db, customer_id, top_n=5)

    predictions = []
    for rec in recommendations:
        product = db.query(models.Product).filter(models.Product.product_id == rec["product_id"]).first()
        activity = (
            db.query(models.CustomerActivity)
            .filter(
                models.CustomerActivity.customer_id == customer_id,
                models.CustomerActivity.product_id == rec["product_id"],
            )
            .first()
        )
        try:
            probability = predict_purchase_probability(customer, product, activity)
        except HTTPException:
            probability = None
        if probability is not None:
            predictions.append(
                schemas.PredictionResponse(
                    customer_id=customer_id,
                    product_id=product.product_id,
                    purchase_probability=round(probability, 4),
                    prediction="Likely to Purchase" if probability >= 0.5 else "Unlikely to Purchase",
                )
            )

    try:
        segment = get_customer_segment(customer)
    except HTTPException:
        segment = "Unavailable"

    previous_purchases = (
        db.query(models.CustomerActivity)
        .filter(
            models.CustomerActivity.customer_id == customer_id, models.CustomerActivity.previous_purchases > 0
        )
        .count()
    )

    return schemas.DashboardResponse(
        customer=customer,
        total_orders=customer.total_purchases,
        total_spending=customer.total_spending,
        average_order_value=customer.average_order_value,
        previous_purchases=previous_purchases,
        segment=segment,
        recommended_products=[schemas.RecommendationItem(**r) for r in recommendations],
        purchase_predictions=predictions,
    )
