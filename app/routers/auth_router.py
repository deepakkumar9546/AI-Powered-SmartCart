"""
Authentication endpoints: registration (customer or admin) and login, issuing JWT
access tokens (Step 17).
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schemas
from app.auth import create_access_token, hash_password, verify_password
from db import models
from db.database import get_db

router = APIRouter(tags=["Authentication"])


@router.post("/register", response_model=schemas.Token, status_code=status.HTTP_201_CREATED)
def register(payload: schemas.UserRegister, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    customer_id = None
    if payload.role == "customer":
        last_id_row = db.query(models.Customer.customer_id).order_by(models.Customer.customer_id.desc()).first()
        next_id = (last_id_row[0] + 1) if last_id_row else 1
        customer = models.Customer(
            customer_id=next_id,
            name=payload.name or payload.email.split("@")[0],
            email=payload.email,
            age=payload.age or 18,
            gender=payload.gender or "unspecified",
            city=payload.city or "unknown",
            registration_date=date.today(),
            total_purchases=0,
            total_spending=0.0,
            average_order_value=0.0,
            website_visits=0,
        )
        db.add(customer)
        db.flush()
        customer_id = customer.customer_id

    user = models.User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        customer_id=customer_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.email, "role": user.role, "customer_id": customer_id})
    return schemas.Token(access_token=token, role=user.role, customer_id=customer_id)


@router.post("/login", response_model=schemas.Token)
def login(payload: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token({"sub": user.email, "role": user.role, "customer_id": user.customer_id})
    return schemas.Token(access_token=token, role=user.role, customer_id=user.customer_id)
