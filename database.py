import sqlite3
import os
import hashlib
from datetime import datetime


class Database:
    def __init__(self):
        if not os.path.exists('database'):
            os.makedirs('database')
        
        self.db_path = 'database/jugo_swat.db'
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.setup_admin()
    
    def create_tables(self):
        # Admin table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                password TEXT,
                created_at TIMESTAMP
            )
        ''')
        
        # Flavors table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS flavors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT,
                sale_price REAL,
                cost_price REAL,
                stock INTEGER DEFAULT 0,
                created_at TIMESTAMP
            )
        ''')
        
        # Customers table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                address TEXT,
                shop_name TEXT,
                credit_limit REAL DEFAULT 0,
                created_at TIMESTAMP
            )
        ''')

        # Suppliers table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                company_name TEXT,
                address TEXT,
                payable_balance REAL DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP
            )
        ''')
        
        # Sales table
        self.cursor.execute('''
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
        ''')
        
        # Sale Items table
        self.cursor.execute('''
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
        ''')
        
        # Stock Movements table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                flavor_id INTEGER,
                type TEXT,
                quantity INTEGER,
                notes TEXT,
                created_at TIMESTAMP,
                FOREIGN KEY (flavor_id) REFERENCES flavors(id)
            )
        ''')

        # Expenses table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                category TEXT,
                amount REAL,
                payment_mode TEXT,
                notes TEXT,
                created_at TIMESTAMP
            )
        ''')
        
        # Settings table
        self.cursor.execute('''
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
        ''')
        
        self.conn.commit()
    
    def setup_admin(self):
        self.cursor.execute("SELECT * FROM admin WHERE username='admin'")
        if not self.cursor.fetchone():
            hashed = hashlib.sha256('admin123'.encode()).hexdigest()
            self.cursor.execute('''
                INSERT INTO admin (username, password, created_at)
                VALUES (?, ?, ?)
            ''', ('admin', hashed, datetime.now()))
            self.conn.commit()
            
            self.cursor.execute("SELECT * FROM settings WHERE id=1")
            if not self.cursor.fetchone():
                self.cursor.execute('''
                    INSERT INTO settings (id, business_name, address, phone, invoice_prefix)
                    VALUES (1, 'JUGO SWAT', 'Swat, Pakistan', '03XX-XXXXXXX', 'JUGO-')
                ''')
                self.conn.commit()
    
    def verify_login(self, username, password):
        hashed = hashlib.sha256(password.encode()).hexdigest()
        self.cursor.execute(
            "SELECT * FROM admin WHERE username=? AND password=?", 
            (username, hashed)
        )
        return self.cursor.fetchone() is not None
    
    def change_password(self, username, new_password):
        hashed = hashlib.sha256(new_password.encode()).hexdigest()
        self.cursor.execute(
            "UPDATE admin SET password=? WHERE username=?",
            (hashed, username)
        )
        self.conn.commit()

    def reset_business_data(self):
        """Clear business data while preserving admin and settings."""
        tables_to_clear = [
            "supplier_transactions",
            "expenses",
            "stock_movements",
            "sale_items",
            "sales",
            "suppliers",
            "customers",
            "flavors",
        ]

        try:
            self.cursor.execute("PRAGMA foreign_keys = OFF")
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = {row[0] for row in self.cursor.fetchall()}

            for table_name in tables_to_clear:
                if table_name in existing_tables:
                    self.cursor.execute(f"DELETE FROM {table_name}")

            if "sqlite_sequence" in existing_tables:
                for table_name in tables_to_clear:
                    self.cursor.execute(
                        "DELETE FROM sqlite_sequence WHERE name = ?",
                        (table_name,)
                    )

            if "settings" in existing_tables:
                self.cursor.execute(
                    "UPDATE settings SET last_invoice_number = 0 WHERE id = 1"
                )

            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise
        finally:
            self.cursor.execute("PRAGMA foreign_keys = ON")

    # ============== FINANCIAL FUNCTIONS ==============
    
    def get_today_profit(self):
        """Aaj ka profit/loss calculate karein"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')

            # Aaj ki sales lo (only positive sales)
            self.cursor.execute("""
                SELECT COALESCE(SUM(grand_total), 0)
                FROM sales
                WHERE DATE(created_at) = ? AND grand_total > 0
            """, (today,))
            revenue = self.cursor.fetchone()[0] or 0

            # Cost for today's positive sales
            self.cursor.execute("""
                SELECT COALESCE(SUM(si.quantity * f.cost_price), 0)
                FROM sale_items si
                JOIN sales s ON s.id = si.sale_id
                JOIN flavors f ON si.flavor_id = f.id
                WHERE DATE(s.created_at) = ? AND s.grand_total > 0
            """, (today,))
            cost = self.cursor.fetchone()[0] or 0

            profit = revenue - cost
            
            return {
                'revenue': revenue,
                'cost': cost,
                'profit': profit,
                'margin': (profit / revenue * 100) if revenue > 0 else 0
            }
        except:
            return {'revenue': 0, 'cost': 0, 'profit': 0, 'margin': 0}
    
    def get_total_investment(self):
        """Total investment based on current stock boxes and cost price."""
        try:
            self.cursor.execute("""
                SELECT
                    COALESCE(SUM(COALESCE(stock, 0) * COALESCE(cost_price, 0)), 0) AS investment,
                    COALESCE(SUM(stock), 0) AS total_box
                FROM flavors
            """)
            result = self.cursor.fetchone()
            investment = result[0] or 0
            total_box = result[1] or 0

            return {
                'investment': investment,
                'BOX': total_box,
                'total_purchases': 0,
                'total_payments': 0
            }
        except:
            return {'investment': 0, 'BOX': 0, 'total_purchases': 0, 'total_payments': 0}
    
    def get_monthly_summary(self):
        """Is mahine ka summary"""
        try:
            current_month = datetime.now().strftime('%Y-%m')

            self.cursor.execute("""
                SELECT 
                    COALESCE(SUM(grand_total), 0) as revenue,
                    COUNT(*) as total_sales
                FROM sales
                WHERE strftime('%Y-%m', created_at) = ? AND grand_total > 0
            """, (current_month,))
            result = self.cursor.fetchone()
            revenue = result[0] or 0
            total_sales = result[1] or 0

            self.cursor.execute("""
                SELECT COALESCE(SUM(si.quantity * f.cost_price), 0)
                FROM sale_items si
                JOIN sales s ON s.id = si.sale_id
                JOIN flavors f ON si.flavor_id = f.id
                WHERE strftime('%Y-%m', s.created_at) = ? AND s.grand_total > 0
            """, (current_month,))
            cost = self.cursor.fetchone()[0] or 0

            profit = revenue - cost

            return {
                'revenue': revenue,
                'cost': cost,
                'profit': profit,
                'sales_count': total_sales,
                'margin': (profit / revenue * 100) if revenue > 0 else 0
            }
        except:
            return {'revenue': 0, 'cost': 0, 'profit': 0, 'sales_count': 0, 'margin': 0}
    
    def get_outstanding_credit(self):
        """Total outstanding credit (Credit Sales - Payments Received)"""
        try:
            self.cursor.execute("""
                SELECT 
                    COALESCE(SUM(CASE WHEN is_credit = 1 AND grand_total > 0 THEN grand_total ELSE 0 END), 0) -
                    COALESCE(SUM(CASE WHEN grand_total < 0 THEN ABS(grand_total) ELSE 0 END), 0) as outstanding
                FROM sales
            """)
            result = self.cursor.fetchone()
            return result[0] if result and result[0] else 0
        except:
            return 0

    def get_credit_payment_labels(self):
        """Map payment transactions to Credit Payment or Credit Settlement."""
        try:
            self.cursor.execute("""
                SELECT id, customer_id, grand_total, is_credit, created_at
                FROM sales
                WHERE grand_total != 0
                ORDER BY created_at ASC, id ASC
            """)
            rows = self.cursor.fetchall()

            balances = {}
            labels = {}

            epsilon = 0.01
            for sale_id, customer_id, grand_total, is_credit, _created_at in rows:
                if customer_id is None:
                    if grand_total < 0:
                        labels[sale_id] = "Credit Payment"
                    continue

                balance = balances.get(customer_id, 0)

                if grand_total > 0:
                    if is_credit:
                        balance += grand_total
                elif grand_total < 0:
                    payment_amount = abs(grand_total)
                    if balance > 0 and payment_amount >= (balance - epsilon):
                        labels[sale_id] = "Credit Settlement"
                    else:
                        labels[sale_id] = "Credit Payment"
                    balance -= payment_amount

                balances[customer_id] = balance

            return labels
        except Exception:
            return {}
    
    def close(self):
        self.conn.close()


# Global database instance
db = Database()
