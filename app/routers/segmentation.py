"""
Customer segmentation endpoint (Step 14).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schemas
from app.auth import get_current_user
from app.ml_utils import get_customer_segment
from db import models
from db.database import get_db

router = APIRouter(tags=["Customer Segmentation"])


@router.get("/customer-segment/{customer_id}", response_model=schemas.SegmentResponse)
def customer_segment(customer_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    customer = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    segment = get_customer_segment(customer)
    return schemas.SegmentResponse(customer_id=customer_id, segment=segment)
