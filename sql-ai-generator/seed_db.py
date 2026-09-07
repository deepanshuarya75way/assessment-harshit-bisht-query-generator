"""
Creates sample.db with a small e-commerce schema and some seed data.
Run once: python seed_db.py
Swap this out for your real database once you're ready -- the rest of the
app only needs a valid DATABASE_PATH pointing at a SQLite file with the
same shape (tables/columns), or a different connection layer entirely.
"""
import sqlite3
import os

DB_PATH = os.environ.get("DATABASE_PATH", "./sample.db")

SCHEMA = """
CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    signup_date TEXT NOT NULL,
    country TEXT NOT NULL
);

CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    order_date TEXT NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE order_items (
    id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);
"""

CUSTOMERS = [
    (1, "Amara Singh", "amara@example.com", "2024-01-15", "India"),
    (2, "Liam Chen", "liam@example.com", "2024-02-03", "USA"),
    (3, "Sofia Rossi", "sofia@example.com", "2024-02-20", "Italy"),
    (4, "Noah Kim", "noah@example.com", "2024-03-11", "South Korea"),
    (5, "Emma Dubois", "emma@example.com", "2024-04-02", "France"),
]

PRODUCTS = [
    (1, "Wireless Mouse", "Electronics", 19.99),
    (2, "Mechanical Keyboard", "Electronics", 89.99),
    (3, "Standing Desk", "Furniture", 349.00),
    (4, "Desk Lamp", "Furniture", 24.50),
    (5, "Noise Cancelling Headphones", "Electronics", 199.99),
]

ORDERS = [
    (1, 1, "2024-05-01", "completed"),
    (2, 2, "2024-05-03", "completed"),
    (3, 1, "2024-05-10", "completed"),
    (4, 3, "2024-05-15", "cancelled"),
    (5, 4, "2024-06-01", "completed"),
    (6, 5, "2024-06-05", "pending"),
]

ORDER_ITEMS = [
    (1, 1, 1, 2),
    (2, 1, 2, 1),
    (3, 2, 5, 1),
    (4, 3, 3, 1),
    (5, 4, 4, 2),
    (6, 5, 2, 1),
    (7, 5, 1, 1),
    (8, 6, 5, 1),
]

def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript(SCHEMA)
    cur.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?)", CUSTOMERS)
    cur.executemany("INSERT INTO products VALUES (?, ?, ?, ?)", PRODUCTS)
    cur.executemany("INSERT INTO orders VALUES (?, ?, ?, ?)", ORDERS)
    cur.executemany("INSERT INTO order_items VALUES (?, ?, ?, ?)", ORDER_ITEMS)
    conn.commit()
    conn.close()
    print(f"Created and seeded {DB_PATH}")

if __name__ == "__main__":
    main()
