import sqlite3

DB_NAME = 'price_tracker.db'

def normalize_product_name(product):
    """Normalize product name for consistent storage and retrieval."""
    return product.strip()[:100] if product else "Unknown"

def create_db():
    """Create the database and table if they don't exist."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product TEXT NOT NULL,
                price REAL NOT NULL,
                date TEXT NOT NULL,
                UNIQUE(product, date)
            )
        ''')
        conn.commit()
        conn.close()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database error: {e}")

def insert_price(product, price, date):
    """Insert a new price record into the database."""
    try:
        product = normalize_product_name(product)
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO prices (product, price, date) VALUES (?, ?, ?)', 
                      (product, price, date))
        conn.commit()
        rows = cursor.rowcount
        conn.close()
        if rows == 0:
            print(f"Price for {product} on {date} already exists")
        else:
            print(f"Price inserted: {product} - ₹{price} on {date}")
        return rows > 0
    except Exception as e:
        print(f"Insert error: {e}")
        return False

def get_prices(product):
    """Retrieve all price records for a given product, ordered by date."""
    try:
        product = normalize_product_name(product)
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        # Use exact match first, then try LIKE for partial matches
        cursor.execute('SELECT date, price FROM prices WHERE product = ? ORDER BY date', (product,))
        rows = cursor.fetchall()
        
        # If no exact match, try partial match
        if not rows:
            cursor.execute('SELECT date, price FROM prices WHERE product LIKE ? ORDER BY date', 
                          (f'%{product}%',))
            rows = cursor.fetchall()
        
        conn.close()
        return rows
    except Exception as e:
        print(f"Fetch error: {e}")
        return []

def get_all_products():
    """Get list of all products in database."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT product FROM prices ORDER BY product')
        products = [row[0] for row in cursor.fetchall()]
        conn.close()
        return products
    except Exception as e:
        print(f"Error fetching products: {e}")
        return []

def get_latest_price(product):
    """Get the most recent price for a product."""
    try:
        product = normalize_product_name(product)
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT price FROM prices WHERE product = ? ORDER BY date DESC LIMIT 1', 
                      (product,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        print(f"Error getting latest price: {e}")
        return None
