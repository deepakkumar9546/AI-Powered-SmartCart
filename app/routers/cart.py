"""
Shopping cart endpoints (Step 11).
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schemas
from app.auth import get_current_user
from db import models
from db.database import get_db

router = APIRouter(prefix="/cart", tags=["Cart"])


def _get_customer_or_404(db: Session, customer_id: int) -> models.Customer:
    customer = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return customer


def _get_product_or_404(db: Session, product_id: int) -> models.Product:
    product = db.query(models.Product).filter(models.Product.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


@router.post("", response_model=schemas.CartItemOut, status_code=status.HTTP_201_CREATED)
def add_to_cart(payload: schemas.CartItemCreate, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    _get_customer_or_404(db, payload.customer_id)
    product = _get_product_or_404(db, payload.product_id)
    if product.stock < payload.quantity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient stock")

    item = (
        db.query(models.CartItem)
        .filter(models.CartItem.customer_id == payload.customer_id, models.CartItem.product_id == payload.product_id)
        .first()
    )
    if item:
        item.quantity += payload.quantity
    else:
        item = models.CartItem(
            customer_id=payload.customer_id, product_id=payload.product_id, quantity=payload.quantity
        )
        db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{customer_id}", response_model=List[schemas.CartItemOut])
def get_cart(customer_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    _get_customer_or_404(db, customer_id)
    return db.query(models.CartItem).filter(models.CartItem.customer_id == customer_id).all()


@router.put("/{cart_id}", response_model=schemas.CartItemOut)
def update_cart_item(cart_id: int, quantity: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    if quantity <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity must be greater than 0")
    item = db.query(models.CartItem).filter(models.CartItem.cart_id == cart_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")
    item.quantity = quantity
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{cart_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cart_item(cart_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    item = db.query(models.CartItem).filter(models.CartItem.cart_id == cart_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")
    db.delete(item)
    db.commit()
    return None
