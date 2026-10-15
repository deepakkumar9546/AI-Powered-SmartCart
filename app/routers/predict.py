"""
Purchase prediction endpoint (Step 12).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schemas
from app.auth import get_current_user
from app.ml_utils import predict_purchase_probability
from db import models
from db.database import get_db

router = APIRouter(tags=["Purchase Prediction"])


@router.post("/predict-purchase", response_model=schemas.PredictionResponse)
def predict_purchase(
    payload: schemas.PredictionRequest, db: Session = Depends(get_db), _user=Depends(get_current_user)
):
    customer = db.query(models.Customer).filter(models.Customer.customer_id == payload.customer_id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    product = db.query(models.Product).filter(models.Product.product_id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    activity = (
        db.query(models.CustomerActivity)
        .filter(
            models.CustomerActivity.customer_id == payload.customer_id,
            models.CustomerActivity.product_id == payload.product_id,
        )
        .first()
    )

    probability = predict_purchase_probability(customer, product, activity)
    prediction = "Likely to Purchase" if probability >= 0.5 else "Unlikely to Purchase"

    return schemas.PredictionResponse(
        customer_id=payload.customer_id,
        product_id=payload.product_id,
        purchase_probability=round(probability, 4),
        prediction=prediction,
    )
