"""
Order placement + retrieval endpoints (Step 11). Placing an order updates product
stock, customer aggregate stats, and customer_activity so later ML predictions and
segmentation reflect the new behavior (Step 21 flow).
"""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app import schemas
from app.auth import get_current_user
from db import models
from db.database import get_db

router = APIRouter(tags=["Orders"])


@router.post("/orders", response_model=schemas.OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(payload: schemas.OrderCreate, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    customer = db.query(models.Customer).filter(models.Customer.customer_id == payload.customer_id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    product = db.query(models.Product).filter(models.Product.product_id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    if product.stock < payload.quantity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient stock")

    unit_price = round(product.price * (1 - (product.discount or 0) / 100), 2)
    total_amount = round(unit_price * payload.quantity, 2)

    last_id_row = db.query(models.Order.order_id).order_by(models.Order.order_id.desc()).first()
    next_order_id = (last_id_row[0] + 1) if last_id_row else 1

    order = models.Order(
        order_id=next_order_id,
        customer_id=payload.customer_id,
        order_date=datetime.utcnow(),
        payment_method=payload.payment_method,
        order_status="completed",
        total_amount=total_amount,
    )
    db.add(order)
    db.flush()

    db.add(
        models.OrderItem(
            order_id=order.order_id,
            product_id=payload.product_id,
            quantity=payload.quantity,
            price=unit_price,
        )
    )

    product.stock -= payload.quantity

    customer.total_purchases += 1
    customer.total_spending = round(customer.total_spending + total_amount, 2)
    customer.average_order_value = round(customer.total_spending / customer.total_purchases, 2)

    activity = (
        db.query(models.CustomerActivity)
        .filter(
            models.CustomerActivity.customer_id == payload.customer_id,
            models.CustomerActivity.product_id == payload.product_id,
        )
        .first()
    )
    if activity:
        activity.previous_purchases += 1
        activity.purchased = 1
    else:
        db.add(
            models.CustomerActivity(
                customer_id=payload.customer_id,
                product_id=payload.product_id,
                product_views=1,
                cart_additions=1,
                wishlist_additions=0,
                previous_purchases=1,
                time_spent=0,
                purchased=1,
            )
        )

    cart_item = (
        db.query(models.CartItem)
        .filter(
            models.CartItem.customer_id == payload.customer_id, models.CartItem.product_id == payload.product_id
        )
        .first()
    )
    if cart_item:
        db.delete(cart_item)

    db.commit()
    db.refresh(order)
    return order


@router.get("/orders", response_model=List[schemas.OrderOut])
def list_orders(skip: int = 0, limit: int = 50, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    return (
        db.query(models.Order)
        .options(joinedload(models.Order.items))
        .order_by(models.Order.order_id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/orders/{order_id}", response_model=schemas.OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    order = (
        db.query(models.Order)
        .options(joinedload(models.Order.items))
        .filter(models.Order.order_id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


@router.get("/customers/{customer_id}/orders", response_model=List[schemas.OrderOut])
def get_customer_orders(customer_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    customer = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return (
        db.query(models.Order)
        .options(joinedload(models.Order.items))
        .filter(models.Order.customer_id == customer_id)
        .order_by(models.Order.order_id.desc())
        .all()
    )
