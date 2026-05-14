import sqlite3

def create_db():
    conn = sqlite3.connect("price_data.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS prices(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product TEXT,
        price REAL,
        date TEXT
    )
    """)

    conn.commit()
    conn.close()


def insert_price(product, price, date):

    conn = sqlite3.connect("price_data.db")
    c = conn.cursor()

    c.execute("INSERT INTO prices(product,price,date) VALUES(?,?,?)",
              (product, price, date))

    conn.commit()
    conn.close()


def get_prices(product):

    conn = sqlite3.connect("price_data.db")
    c = conn.cursor()

    c.execute("SELECT date,price FROM prices WHERE product=?",
              (product,))

    rows = c.fetchall()

    conn.close()

    return rows

