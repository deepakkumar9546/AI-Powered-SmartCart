"""
Pydantic schemas (request/response models) for the SmartCart API, with validation
for age, price, quantity, email, and ID fields (Step 18).
"""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CustomerBase(BaseModel):
    age: int = Field(..., ge=0, le=120)
    gender: str
    city: str


class CustomerCreate(CustomerBase):
    name: str
    email: EmailStr


class CustomerUpdate(BaseModel):
    age: Optional[int] = Field(None, ge=0, le=120)
    gender: Optional[str] = None
    city: Optional[str] = None


class CustomerOut(CustomerBase):
    model_config = ConfigDict(from_attributes=True)

    customer_id: int
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    registration_date: date
    total_purchases: int
    total_spending: float
    average_order_value: float
    website_visits: int


class ProductBase(BaseModel):
    product_name: str
    category: str
    price: float = Field(..., gt=0)
    rating: float = Field(0, ge=0, le=5)
    stock: int = Field(..., ge=0)
    discount: float = Field(0, ge=0, le=100)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    product_name: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    rating: Optional[float] = Field(None, ge=0, le=5)
    stock: Optional[int] = Field(None, ge=0)
    discount: Optional[float] = Field(None, ge=0, le=100)


class ProductOut(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    product_id: int


class CartItemCreate(BaseModel):
    customer_id: int = Field(..., gt=0)
    product_id: int = Field(..., gt=0)
    quantity: int = Field(1, gt=0)


class CartItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cart_id: int
    customer_id: int
    product_id: int
    quantity: int


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    quantity: int
    price: float


class OrderCreate(BaseModel):
    customer_id: int = Field(..., gt=0)
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)
    payment_method: str


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    order_id: int
    customer_id: int
    order_date: datetime
    payment_method: str
    order_status: str
    total_amount: float
    items: List[OrderItemOut] = []


class PredictionRequest(BaseModel):
    customer_id: int = Field(..., gt=0)
    product_id: int = Field(..., gt=0)


class PredictionResponse(BaseModel):
    customer_id: int
    product_id: int
    purchase_probability: float
    prediction: str


class RecommendationItem(BaseModel):
    product_id: int
    product_name: str
    score: float


class RecommendationResponse(BaseModel):
    customer_id: int
    recommendations: List[RecommendationItem]


class SegmentResponse(BaseModel):
    customer_id: int
    segment: str


class DashboardResponse(BaseModel):
    customer: CustomerOut
    total_orders: int
    total_spending: float
    average_order_value: float
    previous_purchases: int
    segment: str
    recommended_products: List[RecommendationItem]
    purchase_predictions: List[PredictionResponse]


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: str = Field("customer", pattern="^(customer|admin)$")
    name: Optional[str] = None
    age: Optional[int] = Field(None, ge=0, le=120)
    gender: Optional[str] = None
    city: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    customer_id: Optional[int] = None
