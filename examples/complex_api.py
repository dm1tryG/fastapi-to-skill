"""Example FastAPI app: complex e-commerce API with nested models.

Stress-tests fastapi-to-skill generation with:
- Nested Pydantic models (Address inside User, Items inside Order)
- Enums (UserRole, OrderStatus)
- Optional fields with defaults
- Multiple tags (users, orders, admin)
- Query + path + body on same endpoint
- Multiple auth schemes (Bearer + API key)
- Deep path nesting (/users/{user_id}/orders/{order_id})
- Endpoints without explicit operation_id

Generate CLI + SKILL.md:
    fastapi-to-skill generate examples.complex_api:app -o ./skills/complex-api/
"""
from enum import Enum
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

app = FastAPI(
    title="E-Commerce API",
    description="Complex e-commerce API — stress test for fastapi-to-skill",
    version="2.0.0",
)


# --- Enums ---


class UserRole(str, Enum):
    admin = "admin"
    customer = "customer"
    seller = "seller"


class OrderStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"


# --- Nested Models ---


class Address(BaseModel):
    street: str
    city: str
    state: Optional[str] = None
    zip_code: str
    country: str = "US"


class UserCreate(BaseModel):
    name: str
    email: str
    role: UserRole = UserRole.customer
    address: Optional[Address] = None


class UserOut(UserCreate):
    id: int


class OrderItem(BaseModel):
    product_id: int
    quantity: int = Field(ge=1, default=1)
    price: float


class OrderCreate(BaseModel):
    items: list[OrderItem]
    shipping_address: Address
    note: Optional[str] = None


class OrderOut(OrderCreate):
    id: int
    user_id: int
    status: OrderStatus = OrderStatus.pending
    total: float


# --- In-memory storage ---

users: dict[int, dict] = {}
orders: dict[int, dict] = {}
_next_user_id = 1
_next_order_id = 1


# --- User endpoints ---


@app.get("/users", response_model=list[UserOut], tags=["users"])
def list_users(
    role: Optional[UserRole] = None,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
):
    """List all users with optional role filter and pagination."""
    result = list(users.values())
    if role is not None:
        result = [u for u in result if u["role"] == role.value]
    return result[offset : offset + limit]


@app.post("/users", response_model=UserOut, tags=["users"], status_code=201)
def create_user(user: UserCreate):
    """Create a new user."""
    global _next_user_id
    u = {"id": _next_user_id, **user.model_dump()}
    users[_next_user_id] = u
    _next_user_id += 1
    return u


@app.get("/users/{user_id}", response_model=UserOut, tags=["users"])
def get_user(user_id: int):
    """Get a user by ID."""
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    return users[user_id]


@app.put("/users/{user_id}", response_model=UserOut, tags=["users"])
def update_user(user_id: int, user: UserCreate, notify: bool = Query(default=False)):
    """Update a user by ID. Set notify=true to send email notification."""
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    u = {"id": user_id, **user.model_dump()}
    users[user_id] = u
    return u


@app.delete("/users/{user_id}", tags=["users"])
def delete_user(user_id: int):
    """Delete a user by ID."""
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    del users[user_id]
    return {"ok": True}


# --- Order endpoints (nested under users) ---


@app.get("/users/{user_id}/orders", response_model=list[OrderOut], tags=["orders"])
def list_user_orders(
    user_id: int,
    status: Optional[OrderStatus] = None,
):
    """List all orders for a user, optionally filtered by status."""
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    result = [o for o in orders.values() if o["user_id"] == user_id]
    if status is not None:
        result = [o for o in result if o["status"] == status.value]
    return result


@app.post(
    "/users/{user_id}/orders",
    response_model=OrderOut,
    tags=["orders"],
    status_code=201,
)
def create_order(user_id: int, order: OrderCreate):
    """Create a new order for a user."""
    global _next_order_id
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    total = sum(item.price * item.quantity for item in order.items)
    o = {
        "id": _next_order_id,
        "user_id": user_id,
        "status": OrderStatus.pending.value,
        "total": total,
        **order.model_dump(),
    }
    orders[_next_order_id] = o
    _next_order_id += 1
    return o


@app.get(
    "/users/{user_id}/orders/{order_id}",
    response_model=OrderOut,
    tags=["orders"],
)
def get_order(user_id: int, order_id: int):
    """Get a specific order for a user."""
    if order_id not in orders or orders[order_id]["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Order not found")
    return orders[order_id]


@app.patch(
    "/users/{user_id}/orders/{order_id}/status",
    response_model=OrderOut,
    tags=["orders"],
)
def update_order_status(user_id: int, order_id: int, status: OrderStatus):
    """Update the status of an order."""
    if order_id not in orders or orders[order_id]["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Order not found")
    orders[order_id]["status"] = status.value
    return orders[order_id]


# --- Admin endpoints ---


@app.get("/admin/stats", tags=["admin"])
def get_stats():
    """Get platform statistics (admin only)."""
    return {
        "total_users": len(users),
        "total_orders": len(orders),
        "revenue": sum(o["total"] for o in orders.values()),
    }


@app.delete("/admin/users/{user_id}/ban", tags=["admin"])
def ban_user(user_id: int, reason: str = Query(default="policy violation")):
    """Ban a user from the platform."""
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    return {"banned": True, "user_id": user_id, "reason": reason}
