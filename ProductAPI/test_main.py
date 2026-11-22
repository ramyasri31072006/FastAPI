import sqlite3

from fastapi.testclient import TestClient

import maind

client = TestClient(maind.app)


def test_delete_without_token_returns_401():
    response = client.delete("/products/82")
    assert response.status_code == 401


def test_customer_cannot_delete_product():
    login = client.post(
        "/login",
        json={"username": "customer", "password": "customer-demo"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    response = client.delete(
        "/products/82",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_admin_can_delete_product(tmp_path, monkeypatch):
    test_db = tmp_path / "products.db"
    monkeypatch.setattr(maind, "DB_PATH", test_db)

    db = sqlite3.connect(test_db)
    try:
        db.execute(
            "CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, price INTEGER)"
        )
        db.execute(
            "INSERT INTO products (id, name, price) VALUES (?, ?, ?)",
            (82, "Pen", 5),
        )
        db.commit()
    finally:
        db.close()

    login = client.post(
        "/login",
        json={"username": "admin", "password": "admin-demo"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    response = client.delete(
        "/products/82",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204
    assert client.get("/products/82").status_code == 404