"""
Product recommendation endpoint (Step 13).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schemas
from app.auth import get_current_user
from db import models
from db.database import get_db
from ml.recommend import recommend_products

router = APIRouter(tags=["Recommendations"])


@router.get("/recommendations/{customer_id}", response_model=schemas.RecommendationResponse)
def get_recommendations(customer_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    customer = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    items = recommend_products(db, customer_id, top_n=5)
    return schemas.RecommendationResponse(customer_id=customer_id, recommendations=items)
