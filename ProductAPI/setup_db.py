import sqlite3

connection = sqlite3.connect("products.db")

connection.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        price INTEGER NOT NULL
    )
""")

connection.execute(
    "INSERT OR IGNORE INTO products (id, name, price) VALUES (?, ?, ?)",
    (82, "Pen", 5),
)

connection.commit()

rows = connection.execute("SELECT id, name, price FROM products").fetchall()
print(rows)

connection.close()