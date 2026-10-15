"""
SmartCart FastAPI application entry point: wires up all routers, CORS, DB table
creation, and serves the frontend SPA as static files.
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import (
    admin,
    auth_router,
    cart,
    customers,
    dashboard,
    orders,
    predict,
    products,
    recommendations,
    segmentation,
)
from db.database import Base, engine

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app = FastAPI(
    title="SmartCart API",
    description="AI-powered E-Commerce platform with purchase prediction, "
    "customer segmentation, and product recommendations.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


app.include_router(auth_router.router)
app.include_router(customers.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(predict.router)
app.include_router(recommendations.router)
app.include_router(segmentation.router)
app.include_router(dashboard.router)
app.include_router(admin.router)


@app.get("/api/health", tags=["Health"])
def health_check():
    return {"status": "ok"}


if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
