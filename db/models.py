from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .database import Base


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=False)
    city = Column(String, nullable=False)
    registration_date = Column(Date, nullable=False)
    total_purchases = Column(Integer, default=0)
    total_spending = Column(Float, default=0.0)
    average_order_value = Column(Float, default=0.0)
    website_visits = Column(Integer, default=0)

    __table_args__ = (CheckConstraint("age >= 0 AND age <= 120", name="ck_customer_age"),)

    orders = relationship("Order", back_populates="customer", cascade="all, delete-orphan")
    cart_items = relationship("CartItem", back_populates="customer", cascade="all, delete-orphan")
    wishlist_items = relationship("WishlistItem", back_populates="customer", cascade="all, delete-orphan")
    activities = relationship("CustomerActivity", back_populates="customer", cascade="all, delete-orphan")
    user = relationship("User", back_populates="customer", uselist=False)


class Product(Base):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String, nullable=False)
    category = Column(String, nullable=False, index=True)
    price = Column(Float, nullable=False)
    rating = Column(Float, default=0.0)
    stock = Column(Integer, default=0)
    discount = Column(Float, default=0.0)

    __table_args__ = (CheckConstraint("price >= 0", name="ck_product_price"),)

    order_items = relationship("OrderItem", back_populates="product")
    cart_items = relationship("CartItem", back_populates="product")
    wishlist_items = relationship("WishlistItem", back_populates="product")
    activities = relationship("CustomerActivity", back_populates="product")


class Order(Base):
    __tablename__ = "orders"

    order_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False)
    order_date = Column(DateTime, default=datetime.utcnow)
    payment_method = Column(String, nullable=False)
    order_status = Column(String, default="completed")
    total_amount = Column(Float, default=0.0)

    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    order_item_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)

    __table_args__ = (CheckConstraint("quantity > 0", name="ck_orderitem_qty"),)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


class CartItem(Base):
    __tablename__ = "cart"

    cart_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    quantity = Column(Integer, default=1)
    added_on = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("customer_id", "product_id", name="uq_cart_customer_product"),)

    customer = relationship("Customer", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")


class WishlistItem(Base):
    __tablename__ = "wishlist"

    wishlist_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    added_on = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("customer_id", "product_id", name="uq_wishlist_customer_product"),)

    customer = relationship("Customer", back_populates="wishlist_items")
    product = relationship("Product", back_populates="wishlist_items")


class CustomerActivity(Base):
    __tablename__ = "customer_activity"

    activity_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    product_views = Column(Integer, default=0)
    cart_additions = Column(Integer, default=0)
    wishlist_additions = Column(Integer, default=0)
    previous_purchases = Column(Integer, default=0)
    time_spent = Column(Float, default=0.0)
    purchased = Column(Integer, default=0)

    __table_args__ = (UniqueConstraint("customer_id", "product_id", name="uq_activity_customer_product"),)

    customer = relationship("Customer", back_populates="activities")
    product = relationship("Product", back_populates="activities")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="customer")  # "customer" or "admin"
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=True, unique=True)

    customer = relationship("Customer", back_populates="user")
