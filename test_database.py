# test_database.py - DATABASE TESTING SCRIPT

import sqlite3
import os
import hashlib
from datetime import datetime

print("=" * 60)
print("🍹 JUGO SWAT - DATABASE CONNECTION TEST")
print("=" * 60)

# 1. Folder check
print("\n📁 Step 1: Checking database folder...")
if not os.path.exists('database'):
    os.makedirs('database')
    print("   ✅ Created 'database' folder")
else:
    print("   ✅ 'database' folder exists")

# 2. Database connection
print("\n🔌 Step 2: Connecting to database...")
try:
    conn = sqlite3.connect('database/jugo_swat.db')
    cursor = conn.cursor()
    print("   ✅ Connected to jugo_swat.db")
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit()

# 3. Create tables (same as database.py)
print("\n📊 Step 3: Creating tables...")

tables_sql = {
    'admin': '''
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            created_at TIMESTAMP
        )
    ''',
    'flavors': '''
        CREATE TABLE IF NOT EXISTS flavors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            sale_price REAL,
            cost_price REAL,
            stock INTEGER DEFAULT 0,
            created_at TIMESTAMP
        )
    ''',
    'customers': '''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            address TEXT,
            shop_name TEXT,
            credit_limit REAL DEFAULT 0,
            created_at TIMESTAMP
        )
    ''',
    'sales': '''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT UNIQUE,
            customer_id INTEGER,
            customer_name TEXT,
            total_amount REAL,
            discount REAL,
            grand_total REAL,
            payment_mode TEXT,
            is_credit INTEGER DEFAULT 0,
            created_at TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''',
    'sale_items': '''
        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER,
            flavor_id INTEGER,
            flavor_name TEXT,
            quantity INTEGER,
            price REAL,
            total REAL,
            FOREIGN KEY (sale_id) REFERENCES sales(id),
            FOREIGN KEY (flavor_id) REFERENCES flavors(id)
        )
    ''',
    'stock_movements': '''
        CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flavor_id INTEGER,
            type TEXT,
            quantity INTEGER,
            notes TEXT,
            created_at TIMESTAMP,
            FOREIGN KEY (flavor_id) REFERENCES flavors(id)
        )
    ''',
    'settings': '''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            business_name TEXT,
            address TEXT,
            phone TEXT,
            email TEXT,
            logo_path TEXT,
            invoice_prefix TEXT DEFAULT 'JUGO-',
            last_invoice_number INTEGER DEFAULT 0
        )
    '''
}

for table_name, sql in tables_sql.items():
    try:
        cursor.execute(sql)
        print(f"   ✅ Table '{table_name}' ready")
    except Exception as e:
        print(f"   ❌ Error in {table_name}: {e}")

conn.commit()

# 4. Insert Admin
print("\n👤 Step 4: Setting up admin user...")
cursor.execute("SELECT * FROM admin WHERE username='admin'")
if not cursor.fetchone():
    hashed = hashlib.sha256('admin123'.encode()).hexdigest()
    cursor.execute('''
        INSERT INTO admin (username, password, created_at)
        VALUES (?, ?, ?)
    ''', ('admin', hashed, datetime.now()))
    conn.commit()
    print("   ✅ Admin created: admin / admin123")
else:
    print("   ℹ️ Admin already exists")

# 5. Insert Settings
print("\n⚙️ Step 5: Setting up business info...")
cursor.execute("SELECT * FROM settings WHERE id=1")
if not cursor.fetchone():
    cursor.execute('''
        INSERT INTO settings (id, business_name, address, phone, invoice_prefix)
        VALUES (1, 'JUGO SWAT', 'Swat, Pakistan', '03XX-XXXXXXX', 'JUGO-')
    ''')
    conn.commit()
    print("   ✅ Business settings saved")
else:
    print("   ℹ️ Settings already exist")

# 6. Insert Sample Flavors
print("\n🍹 Step 6: Adding sample flavors...")
cursor.execute("SELECT COUNT(*) FROM flavors")
count = cursor.fetchone()[0]

if count == 0:
    flavors = [
        ('Mango', 'Tropical', 120, 80, 50),
        ('Orange', 'Citrus', 100, 70, 100),
        ('Apple', 'Classic', 110, 75, 75),
        ('Strawberry', 'Berry', 130, 90, 40),
        ('Peach', 'Seasonal', 140, 95, 30),
        ('Mix Fruit', 'Special', 150, 100, 60)
    ]
    
    for f in flavors:
        cursor.execute('''
            INSERT INTO flavors (name, category, sale_price, cost_price, stock, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (*f, datetime.now()))
    
    conn.commit()
    print(f"   ✅ Added {len(flavors)} flavors")
else:
    print(f"   ℹ️ {count} flavors already exist")

# 7. Verify Data
print("\n📋 Step 7: Verification...")
print("-" * 60)

# Check admin
cursor.execute("SELECT username, created_at FROM admin")
admin = cursor.fetchone()
print(f"Admin User: {admin[0]} | Created: {admin[1][:10]}")

# Check settings
cursor.execute("SELECT business_name, phone FROM settings WHERE id=1")
settings = cursor.fetchone()
print(f"Business: {settings[0]} | Phone: {settings[1]}")

# Check flavors
print("\n🧃 Available Flavors:")
print(f"{'ID':<5} {'Name':<15} {'Category':<12} {'Price':<10} {'Stock':<10}")
print("-" * 60)

cursor.execute("SELECT id, name, category, sale_price, stock FROM flavors")
for row in cursor.fetchall():
    print(f"{row[0]:<5} {row[1]:<15} {row[2]:<12} Rs.{row[3]:<9} {row[4]} BOX")

# 8. Test Login
print("\n🔐 Step 8: Testing login...")
test_pass = hashlib.sha256('admin123'.encode()).hexdigest()
cursor.execute("SELECT * FROM admin WHERE username='admin' AND password=?", (test_pass,))
if cursor.fetchone():
    print("   ✅ Login test PASSED")
else:
    print("   ❌ Login test FAILED")

conn.close()

print("\n" + "=" * 60)
print("✅ DATABASE READY! Ab 'python main.py' chalayein")
print("=" * 60)