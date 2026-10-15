// ---- SmartCart frontend logic ----
const API_BASE = "";

function getToken() { return localStorage.getItem("sc_token"); }
function getRole() { return localStorage.getItem("sc_role"); }
function getCustomerId() { return localStorage.getItem("sc_customer_id"); }

function setSession(token, role, customerId) {
  localStorage.setItem("sc_token", token);
  localStorage.setItem("sc_role", role);
  if (customerId !== null && customerId !== undefined) {
    localStorage.setItem("sc_customer_id", customerId);
  } else {
    localStorage.removeItem("sc_customer_id");
  }
}

function clearSession() {
  localStorage.removeItem("sc_token");
  localStorage.removeItem("sc_role");
  localStorage.removeItem("sc_customer_id");
}

async function api(path, options = {}) {
  const headers = options.headers || {};
  headers["Content-Type"] = "application/json";
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(API_BASE + path, { ...options, headers });
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || `Request failed (${res.status})`);
  }
  return data;
}

// ---------- Auth ----------
async function login() {
  const email = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-password").value;
  const msg = document.getElementById("auth-message");
  msg.textContent = "";
  try {
    const data = await api("/login", { method: "POST", body: JSON.stringify({ email, password }) });
    setSession(data.access_token, data.role, data.customer_id);
    onLoggedIn();
  } catch (e) {
    msg.textContent = e.message;
  }
}

async function register() {
  const payload = {
    name: document.getElementById("reg-name").value.trim(),
    email: document.getElementById("reg-email").value.trim(),
    password: document.getElementById("reg-password").value,
    age: parseInt(document.getElementById("reg-age").value) || null,
    gender: document.getElementById("reg-gender").value,
    city: document.getElementById("reg-city").value.trim(),
    role: document.getElementById("reg-role").value,
  };
  const msg = document.getElementById("auth-message");
  msg.textContent = "";
  try {
    const data = await api("/register", { method: "POST", body: JSON.stringify(payload) });
    setSession(data.access_token, data.role, data.customer_id);
    onLoggedIn();
  } catch (e) {
    msg.textContent = e.message;
  }
}

function logout() {
  clearSession();
  document.getElementById("view-app").classList.add("d-none");
  document.getElementById("view-auth").classList.remove("d-none");
  renderNav();
}

function onLoggedIn() {
  document.getElementById("view-auth").classList.add("d-none");
  document.getElementById("view-app").classList.remove("d-none");
  renderNav();
  if (getRole() === "admin") {
    document.getElementById("admin-tab").classList.remove("d-none");
  }
  loadProducts();
}

function renderNav() {
  const nav = document.getElementById("nav-links");
  if (getToken()) {
    const role = getRole();
    const cid = getCustomerId();
    nav.innerHTML = `
      <span class="badge bg-secondary">Role: ${role}</span>
      ${cid ? `<span class="badge bg-info text-dark">Customer #${cid}</span>` : ""}
      <button class="btn btn-sm btn-outline-light" onclick="logout()">Logout</button>
    `;
  } else {
    nav.innerHTML = "";
  }
}

// ---------- Tab switching ----------
document.addEventListener("DOMContentLoaded", () => {
  renderNav();
  if (getToken()) onLoggedIn();

  document.querySelectorAll("#appTabs .nav-link").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#appTabs .nav-link").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const pane = btn.dataset.pane;
      document.querySelectorAll(".app-pane").forEach((p) => p.classList.add("d-none"));
      document.getElementById("pane-" + pane).classList.remove("d-none");
      if (pane === "cart") loadCart();
      if (pane === "orders") loadOrders();
      if (pane === "recommendations") loadRecommendations();
      if (pane === "dashboard") loadDashboard();
      if (pane === "admin") loadAdmin();
    });
  });
});

// ---------- Products ----------
async function loadProducts() {
  const search = document.getElementById("product-search").value;
  const category = document.getElementById("product-category").value;
  const params = new URLSearchParams();
  if (search) params.set("search", search);
  if (category) params.set("category", category);
  params.set("limit", "60");
  try {
    const products = await api("/products?" + params.toString());
    renderProducts(products);
    populateCategories(products);
  } catch (e) {
    alert(e.message);
  }
}

function populateCategories(products) {
  const select = document.getElementById("product-category");
  if (select.options.length > 1) return;
  const categories = [...new Set(products.map((p) => p.category))].sort();
  categories.forEach((c) => {
    const opt = document.createElement("option");
    opt.value = c;
    opt.textContent = c;
    select.appendChild(opt);
  });
}

function renderProducts(products) {
  const grid = document.getElementById("products-grid");
  grid.innerHTML = products
    .map(
      (p) => `
    <div class="col-md-4 col-lg-3">
      <div class="card product-card shadow-sm">
        <div class="card-body">
          <h6 class="card-title">${p.product_name}</h6>
          <p class="text-muted mb-1">${p.category}</p>
          <p class="mb-1">💲${p.price.toFixed(2)} &nbsp; ⭐${p.rating.toFixed(1)}</p>
          <p class="mb-1 small">Stock: ${p.stock} ${p.stock < 10 ? '<span class="badge bg-danger">Low</span>' : ""}</p>
          <p class="mb-2 small">Discount: ${p.discount}%</p>
          <div class="mt-auto d-flex flex-column gap-2">
            <div class="input-group input-group-sm">
              <input type="number" min="1" value="1" class="form-control" id="qty-${p.product_id}">
              <button class="btn btn-outline-primary" onclick="addToCart(${p.product_id})">Add to Cart</button>
            </div>
            <button class="btn btn-sm btn-outline-secondary" onclick="predictPurchase(${p.product_id})">Predict purchase</button>
            <div id="predict-${p.product_id}" class="small"></div>
          </div>
        </div>
      </div>
    </div>`
    )
    .join("");
}

async function addToCart(productId) {
  const qty = parseInt(document.getElementById("qty-" + productId).value) || 1;
  const customerId = getCustomerId();
  if (!customerId) { alert("Only customers can use the cart."); return; }
  try {
    await api("/cart", {
      method: "POST",
      body: JSON.stringify({ customer_id: parseInt(customerId), product_id: productId, quantity: qty }),
    });
    alert("Added to cart!");
  } catch (e) {
    alert(e.message);
  }
}

async function predictPurchase(productId) {
  const customerId = getCustomerId();
  if (!customerId) { alert("Only customers can get predictions."); return; }
  const el = document.getElementById("predict-" + productId);
  try {
    const data = await api("/predict-purchase", {
      method: "POST",
      body: JSON.stringify({ customer_id: parseInt(customerId), product_id: productId }),
    });
    el.innerHTML = `<span class="badge ${data.prediction === "Likely to Purchase" ? "bg-success" : "bg-secondary"}">
      ${data.prediction} (${(data.purchase_probability * 100).toFixed(1)}%)</span>`;
  } catch (e) {
    el.innerHTML = `<span class="text-danger">${e.message}</span>`;
  }
}

// ---------- Cart ----------
async function loadCart() {
  const customerId = getCustomerId();
  const container = document.getElementById("cart-table");
  if (!customerId) { container.innerHTML = "<p>Only customers have a cart.</p>"; return; }
  try {
    const items = await api(`/cart/${customerId}`);
    if (!items.length) { container.innerHTML = "<p>Your cart is empty.</p>"; return; }
    container.innerHTML = `
      <table class="table table-bordered">
        <thead><tr><th>Cart ID</th><th>Product ID</th><th>Quantity</th><th>Actions</th></tr></thead>
        <tbody>
          ${items.map((i) => `
            <tr>
              <td>${i.cart_id}</td>
              <td>${i.product_id}</td>
              <td>${i.quantity}</td>
              <td>
                <button class="btn btn-sm btn-success" onclick="checkoutItem(${i.cart_id}, ${i.product_id}, ${i.quantity})">Buy Now</button>
                <button class="btn btn-sm btn-danger" onclick="removeCartItem(${i.cart_id})">Remove</button>
              </td>
            </tr>`).join("")}
        </tbody>
      </table>`;
  } catch (e) {
    container.innerHTML = `<p class="text-danger">${e.message}</p>`;
  }
}

async function removeCartItem(cartId) {
  try {
    await api(`/cart/${cartId}`, { method: "DELETE" });
    loadCart();
  } catch (e) {
    alert(e.message);
  }
}

async function checkoutItem(cartId, productId, quantity) {
  const customerId = getCustomerId();
  const paymentMethod = prompt("Payment method (e.g. Credit Card, UPI, Wallet):", "Credit Card");
  if (!paymentMethod) return;
  try {
    await api("/orders", {
      method: "POST",
      body: JSON.stringify({
        customer_id: parseInt(customerId),
        product_id: productId,
        quantity: quantity,
        payment_method: paymentMethod,
      }),
    });
    alert("Order placed!");
    loadCart();
  } catch (e) {
    alert(e.message);
  }
}

// ---------- Orders ----------
async function loadOrders() {
  const customerId = getCustomerId();
  const container = document.getElementById("orders-table");
  if (!customerId) { container.innerHTML = "<p>Only customers have orders.</p>"; return; }
  try {
    const orders = await api(`/customers/${customerId}/orders`);
    if (!orders.length) { container.innerHTML = "<p>No orders yet.</p>"; return; }
    container.innerHTML = `
      <table class="table table-bordered">
        <thead><tr><th>Order ID</th><th>Date</th><th>Payment</th><th>Status</th><th>Total</th><th>Items</th></tr></thead>
        <tbody>
          ${orders.map((o) => `
            <tr>
              <td>${o.order_id}</td>
              <td>${new Date(o.order_date).toLocaleString()}</td>
              <td>${o.payment_method}</td>
              <td>${o.order_status}</td>
              <td>$${o.total_amount.toFixed(2)}</td>
              <td>${o.items.map((it) => `#${it.product_id} x${it.quantity}`).join(", ")}</td>
            </tr>`).join("")}
        </tbody>
      </table>`;
  } catch (e) {
    container.innerHTML = `<p class="text-danger">${e.message}</p>`;
  }
}

// ---------- Recommendations ----------
async function loadRecommendations() {
  const customerId = getCustomerId();
  const container = document.getElementById("recommendations-list");
  if (!customerId) { container.innerHTML = "<p>Only customers get recommendations.</p>"; return; }
  try {
    const data = await api(`/recommendations/${customerId}`);
    container.innerHTML = data.recommendations
      .map(
        (r) => `
      <div class="col-md-4 col-lg-3">
        <div class="card shadow-sm">
          <div class="card-body">
            <h6>${r.product_name}</h6>
            <span class="badge bg-primary score-badge">Score: ${(r.score * 100).toFixed(1)}%</span>
          </div>
        </div>
      </div>`
      )
      .join("");
  } catch (e) {
    container.innerHTML = `<p class="text-danger">${e.message}</p>`;
  }
}

// ---------- Dashboard ----------
async function loadDashboard() {
  const customerId = getCustomerId();
  const container = document.getElementById("dashboard-content");
  if (!customerId) { container.innerHTML = "<p>Only customers have a dashboard.</p>"; return; }
  try {
    const d = await api(`/customer-dashboard/${customerId}`);
    container.innerHTML = `
      <div class="row g-3">
        <div class="col-md-6">
          <div class="card">
            <div class="card-body">
              <h6>Profile</h6>
              <p>${d.customer.name} (#${d.customer.customer_id})<br/>
              ${d.customer.city}, Age ${d.customer.age}</p>
              <p>Total orders: ${d.total_orders}<br/>
              Total spending: $${d.total_spending.toFixed(2)}<br/>
              Avg order value: $${d.average_order_value.toFixed(2)}</p>
              <span class="badge bg-success">Segment: ${d.segment}</span>
            </div>
          </div>
        </div>
        <div class="col-md-6">
          <div class="card">
            <div class="card-body">
              <h6>Recommended Products</h6>
              <ul class="list-group list-group-flush">
                ${d.recommended_products.map((r) => `<li class="list-group-item">${r.product_name} — ${(r.score * 100).toFixed(1)}%</li>`).join("")}
              </ul>
            </div>
          </div>
        </div>
        <div class="col-12">
          <div class="card">
            <div class="card-body">
              <h6>Purchase Predictions</h6>
              <ul class="list-group list-group-flush">
                ${d.purchase_predictions.map((p) => `<li class="list-group-item">Product #${p.product_id}: ${p.prediction} (${(p.purchase_probability * 100).toFixed(1)}%)</li>`).join("")}
              </ul>
            </div>
          </div>
        </div>
      </div>`;
  } catch (e) {
    container.innerHTML = `<p class="text-danger">${e.message}</p>`;
  }
}

// ---------- Admin ----------
async function loadAdmin() {
  const container = document.getElementById("admin-content");
  if (getRole() !== "admin") { container.innerHTML = "<p>Admin access required.</p>"; return; }
  try {
    const [summary, topProducts, topCustomers, categorySales, lowStock] = await Promise.all([
      api("/admin/sales-summary"),
      api("/admin/top-products"),
      api("/admin/top-customers"),
      api("/admin/category-sales"),
      api("/admin/low-stock-products"),
    ]);
    container.innerHTML = `
      <div class="row g-3">
        <div class="col-md-4">
          <div class="card"><div class="card-body">
            <h6>Sales Summary</h6>
            <p>Total orders: ${summary.total_orders}<br/>
            Total revenue: $${summary.total_revenue}<br/>
            Avg order value: $${summary.average_order_value}</p>
          </div></div>
        </div>
        <div class="col-md-8">
          <div class="card"><div class="card-body">
            <h6>Top Products</h6>
            <table class="table table-sm"><thead><tr><th>Product</th><th>Revenue</th><th>Units</th></tr></thead>
            <tbody>${topProducts.map((p) => `<tr><td>${p.product_name}</td><td>$${p.revenue}</td><td>${p.units_sold}</td></tr>`).join("")}</tbody></table>
          </div></div>
        </div>
        <div class="col-md-6">
          <div class="card"><div class="card-body">
            <h6>Top Customers</h6>
            <table class="table table-sm"><thead><tr><th>Name</th><th>Spending</th><th>Purchases</th></tr></thead>
            <tbody>${topCustomers.map((c) => `<tr><td>${c.name}</td><td>$${c.total_spending}</td><td>${c.total_purchases}</td></tr>`).join("")}</tbody></table>
          </div></div>
        </div>
        <div class="col-md-6">
          <div class="card"><div class="card-body">
            <h6>Category Sales</h6>
            <table class="table table-sm"><thead><tr><th>Category</th><th>Revenue</th><th>Units</th></tr></thead>
            <tbody>${categorySales.map((c) => `<tr><td>${c.category}</td><td>$${c.revenue}</td><td>${c.units_sold}</td></tr>`).join("")}</tbody></table>
          </div></div>
        </div>
        <div class="col-12">
          <div class="card"><div class="card-body">
            <h6>Low Stock Products</h6>
            <table class="table table-sm"><thead><tr><th>Product</th><th>Category</th><th>Stock</th></tr></thead>
            <tbody>${lowStock.map((p) => `<tr><td>${p.product_name}</td><td>${p.category}</td><td>${p.stock}</td></tr>`).join("")}</tbody></table>
          </div></div>
        </div>
      </div>`;
  } catch (e) {
    container.innerHTML = `<p class="text-danger">${e.message}</p>`;
  }
}
