import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "sample.db")

def seed():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.executescript(
        """
        CREATE TABLE customers(
            customer_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            signup_date TEXT NOT NULL,
            country TEXT NOT NULL
        );
        
        CREATE TABLE products(
            product_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL
        );

        CREATE TABLE orders(
        order_id INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        order_date TEXT NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
        );
        """
    )

    customers = [
        (1, "Ava Thompson", "ava@example.com", "2023-01-15", "USA"),
        (2, "Liam Chen", "liam@example.com", "2023-02-20", "Canada"),
        (3, "Sofia Rossi", "sofia@example.com", "2023-03-05", "Italy"),
        (4, "Noah Patel", "noah@example.com", "2023-04-12", "USA"),
        (5, "Emma Garcia", "emma@example.com", "2023-05-01", "Mexico"),
    ]

    cursor.executemany("INSERT INTO customers VALUES (?,?,?,?,?)", customers)

    products = [
        (1, "Wireless Mouse", "Electronics", 25.99),
        (2, "Standing Desk", "Furniture", 349.00),
        (3, "Coffee Grinder", "Kitchen", 59.50),
        (4, "Mechanical Keyboard", "Electronics", 89.99),
        (5, "Desk Lamp", "Furniture", 34.75),
    ]

    cursor.executemany("INSERT INTO products VALUES (?,?,?,?)", products)

    orders = [
        (1, 1, 1, 2, "2024-01-10"),
        (2, 1, 4, 1, "2024-01-15"),
        (3, 2, 2, 1, "2024-02-01"),
        (4, 3, 3, 3, "2024-02-10"),
        (5, 4, 5, 2, "2024-03-01"),
        (6, 5, 1, 1, "2024-03-05"),
        (7, 2, 4, 1, "2024-03-20"),
        (8, 1, 3, 1, "2024-04-01"),
    ]
    cursor.executemany("INSERT INTO orders VALUES (?,?,?,?,?)", orders)

    conn.commit()
    conn.close()
    print("Database seeded successfully.")


if __name__ == "__main__":
    seed()
