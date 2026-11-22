import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query, Response
from pydantic import BaseModel
from secrets import token_urlsafe

app = FastAPI()

DB_PATH = Path(__file__).with_name("products.db")


class Product(BaseModel):
    name: str
    price: int


class PriceUpdate(BaseModel):
    price: int


class LoginRequest(BaseModel):
    username: str
    password: str


# Local practice accounts
demo_users = {
    "admin": {"password": "admin-demo", "role": "admin"},
    "customer": {"password": "customer-demo", "role": "customer"},
}

active_tokens: dict[str, str] = {}


@app.post("/login")
def login(credentials: LoginRequest):
    user = demo_users.get(credentials.username)

    if user is None or user["password"] != credentials.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = token_urlsafe(32)
    active_tokens[token] = credentials.username

    return {"access_token": token, "token_type": "bearer"}

@app.get("/products/{product_id}")
def get_product(product_id: int):
    with closing(sqlite3.connect(DB_PATH)) as connection:
        connection.row_factory = sqlite3.Row
        product = connection.execute(
            "SELECT id, name, price FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    return dict(product)


@app.post("/products", status_code=201)
def add_product(product: Product):
    with closing(sqlite3.connect(DB_PATH)) as connection:
        with connection:
            cursor = connection.execute(
                "INSERT INTO products (name, price) VALUES (?, ?)",
                (product.name, product.price),
            )
            product_id = cursor.lastrowid

    return {
        "id": product_id,
        "name": product.name,
        "price": product.price,
    }


@app.patch("/products/{product_id}")
def update_price(product_id: int, update: PriceUpdate):
    with closing(sqlite3.connect(DB_PATH)) as connection:
        connection.row_factory = sqlite3.Row
        with connection:
            cursor = connection.execute(
                "UPDATE products SET price = ? WHERE id = ?",
                (update.price, product_id),
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Product not found")

            product = connection.execute(
                "SELECT id, name, price FROM products WHERE id = ?",
                (product_id,),
            ).fetchone()

    return dict(product)


from fastapi import Header


@app.delete("/products/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    authorization: str = Header(default=""),
):
    scheme, _, token = authorization.partition(" ")
    username = active_tokens.get(token)

    if scheme.lower() != "bearer" or username is None:
        raise HTTPException(
            status_code=401,
            detail="Valid login token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if demo_users[username]["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin permission required")

    with closing(sqlite3.connect(DB_PATH)) as connection:
        with connection:
            cursor = connection.execute(
                "DELETE FROM products WHERE id = ?",
                (product_id,),
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Product not found")

    return Response(status_code=204)


@app.get("/products")
def list_products(
    max_price: int,
    order: Literal["asc", "desc"] = "asc",
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
):
    offset = (page - 1) * limit
    direction = "DESC" if order == "desc" else "ASC"

    with closing(sqlite3.connect(DB_PATH)) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            f"""
            SELECT id, name, price
            FROM products
            WHERE price <= ?
            ORDER BY price {direction}, id ASC
            LIMIT ? OFFSET ?
            """,
            (max_price, limit, offset),
        ).fetchall()

    return [dict(row) for row in rows]