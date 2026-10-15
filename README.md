# SmartCart — AI-Powered E-Commerce Platform

A full-stack demo application: FastAPI backend + ML (purchase prediction, customer
segmentation, recommendations) + SQLite database + a simple HTML/JS frontend. Runs
entirely on your local machine.

## Project structure

```
SmartCart/
  data/
    generate_data.py       # synthetic customers/products/orders/activity (+ bad data)
    raw/                   # generated raw CSVs (created at runtime)
    cleaned/                # cleaned CSVs (created at runtime)
  ml/
    data_cleaning.py       # missing values, duplicates, dtype/price/age/rating fixes
    eda.py                 # business questions + charts (ml/artifacts/eda/*.png)
    feature_engineering.py # builds the customer-product feature matrix
    train_purchase_model.py# trains & compares LogisticRegression/DecisionTree/RandomForest
    train_segmentation.py  # K-Means customer segmentation + elbow method
    recommend.py           # content-based recommendation scoring
    artifacts/              # purchase_model.pkl, preprocessing.pkl, segmentation_model.pkl
  db/
    database.py            # SQLAlchemy engine/session (SQLite: smartcart.db)
    models.py              # customers, products, orders, order_items, cart, wishlist,
                            # customer_activity, users
    seed_db.py              # loads cleaned CSVs into the database + demo logins
  app/
    main.py                 # FastAPI app, routers, static frontend mount
    auth.py                 # JWT + bcrypt password hashing
    schemas.py               # Pydantic request/response models with validation
    ml_utils.py              # loads trained models and runs inference
    routers/                 # customers, products, cart, orders, predict,
                              # recommendations, segmentation, dashboard, admin, auth
  frontend/
    index.html, app.js, style.css   # single-page app (Bootstrap + vanilla JS)
  bootstrap.py              # one-shot setup: generate -> clean -> EDA -> train -> seed
  requirements.txt
```

## Setup (Windows PowerShell)

```powershell
cd SmartCart
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

python bootstrap.py          # generates data, cleans it, trains models, seeds DB

uvicorn app.main:app --reload
```

Then open **http://127.0.0.1:8000** in your browser — the frontend is served
directly by the API (no separate server needed). Interactive API docs are at
**http://127.0.0.1:8000/docs**.

Re-running `bootstrap.py` is safe: it regenerates artifacts/CSVs, but `seed_db.py`
skips reseeding if the database already has data. Delete `smartcart.db` to reseed
from scratch.

## Demo logins

| Role     | Email                         | Password      |
|----------|-------------------------------|---------------|
| Admin    | admin@smartcart.com           | Admin@123     |
| Customer | customer1@smartcart.com ... customer120@smartcart.com | Password123! |

You can also register a new account from the frontend's **Register** tab.

## Answers to the written questions in the spec

**Step 1 — Libraries used and why**
- **FastAPI, uvicorn[standard]** — the web framework and ASGI server.
- **SQLAlchemy** — ORM / database connectivity (SQLite).
- **pydantic, email-validator, python-multipart** — request/response validation
  (including email format) and form parsing.
- **python-jose[cryptography], bcrypt** — JWT issuance/verification and secure
  password hashing.
- **pandas, numpy** — data generation, cleaning, and feature engineering.
- **scikit-learn** — Logistic Regression / Decision Tree / Random Forest
  classifiers and K-Means clustering.
- **joblib** — serializing trained models (`purchase_model.pkl`, `segmentation_model.pkl`).
- **matplotlib** — EDA charts.
- **faker** — realistic synthetic names/cities/dates.
- Swagger UI (built into FastAPI at `/docs`) is used for API testing; no extra
  package is required for that.

**Step 3 — Required preprocessing before training**
1. Check and fill/drop missing values (ratings, quantities).
2. Remove duplicate customer/product/order rows.
3. Fix incorrect dtypes (e.g. price stored as `"123.45 $"` strings).
4. Clip/replace invalid prices (≤ 0) using category medians.
5. Clip/replace invalid ages (< 0 or > 100) using the median age.
6. Fill missing ratings with the category average.
7. Drop rows referencing non-existent customer/product IDs (referential integrity).
8. Merge the cleaned tables into one customer-product feature matrix and scale
   numeric features (`StandardScaler`) before training.

**Step 6 — Which model performs best and why**
Run `python -m ml.train_purchase_model` (included in `bootstrap.py`) — it prints a
comparison table (accuracy, precision, recall, F1, ROC-AUC, confusion matrix) for
all three models and writes it to `ml/artifacts/model_comparison.txt`. The script
automatically selects the model with the **highest ROC-AUC**, since this is a mild
class-imbalance problem (most activity rows are *not* purchases) where ROC-AUC
better reflects ranking quality across thresholds than raw accuracy. In practice,
**Random Forest** usually wins because it captures non-linear interactions between
engagement signals (views/cart adds/time spent) that Logistic Regression cannot,
while generalizing better than a single Decision Tree.

**Step 8 — Choosing the number of clusters**
`ml/train_segmentation.py` computes K-Means inertia for k = 1…10 and saves the
elbow curve to `ml/artifacts/eda/elbow_method.png`. The "elbow" (point of
diminishing returns in inertia reduction) combined with the need for exactly four
business-meaningful tiers (Premium / Regular / Occasional / At-Risk) justifies
**k = 4**; the script also prints the silhouette score as a secondary quality check.

## Key API endpoints

Auth: `POST /register`, `POST /login`
Customers: `POST|GET /customers`, `GET|PUT|DELETE /customers/{id}`
Products: `POST|GET /products`, `GET|PUT|DELETE /products/{id}`
Cart: `POST /cart`, `GET /cart/{customer_id}`, `PUT|DELETE /cart/{cart_id}`
Orders: `POST|GET /orders`, `GET /orders/{id}`, `GET /customers/{id}/orders`
ML: `POST /predict-purchase`, `GET /recommendations/{customer_id}`,
`GET /customer-segment/{customer_id}`, `GET /customer-dashboard/{customer_id}`
Admin (JWT role=admin required): `GET /admin/sales-summary`, `/admin/top-products`,
`/admin/top-customers`, `/admin/category-sales`, `/admin/customer-segments`,
`/admin/low-stock-products`

## Error handling

The API returns proper HTTP status codes: `404` (customer/product/order not
found), `400` (insufficient stock, bad quantity), `401` (invalid login / missing
or expired token), `403` (non-admin calling an admin endpoint), `409` (duplicate
email on register), `503` (ML model not yet trained — run `bootstrap.py`).
