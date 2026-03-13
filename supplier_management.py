import customtkinter as ctk
from tkinter import messagebox, filedialog
from database import db
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from functools import partial
from ui_utils import center_window


class SupplierManager:
    def __init__(self, parent_frame):
        self.parent = parent_frame
        self.ensure_tables_exist()
        self.setup_ui()
    
    def ensure_tables_exist(self):
        """Ensure supplier tables exist in database"""
        try:
            # Suppliers table
            db.cursor.execute("""
                CREATE TABLE IF NOT EXISTS suppliers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT,
                    company_name TEXT,
                    address TEXT,
                    payable_balance REAL DEFAULT 0,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            db.cursor.execute("PRAGMA table_info(suppliers)")
            existing_columns = {column[1] for column in db.cursor.fetchall()}

            if "company_name" not in existing_columns:
                db.cursor.execute("ALTER TABLE suppliers ADD COLUMN company_name TEXT")
            if "address" not in existing_columns:
                db.cursor.execute("ALTER TABLE suppliers ADD COLUMN address TEXT")
            if "payable_balance" not in existing_columns:
                db.cursor.execute("ALTER TABLE suppliers ADD COLUMN payable_balance REAL DEFAULT 0")
            if "notes" not in existing_columns:
                db.cursor.execute("ALTER TABLE suppliers ADD COLUMN notes TEXT")
            
            # Supplier transactions table
            db.cursor.execute("""
                CREATE TABLE IF NOT EXISTS supplier_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    supplier_id INTEGER,
                    date TEXT NOT NULL,
                    invoice_no TEXT UNIQUE,
                    type TEXT CHECK(type IN ('purchase', 'payment')),
                    amount REAL DEFAULT 0,
                    payment_type TEXT DEFAULT 'credit',
                    details TEXT,
                    flavor_id INTEGER,
                    quantity INTEGER DEFAULT 0,
                    purchase_price REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
                    FOREIGN KEY (flavor_id) REFERENCES flavors(id)
                )
            """)
            
            db.conn.commit()
        except Exception as e:
            print(f"Table creation error: {e}")
    
    def setup_ui(self):
        # Clear parent
        for widget in self.parent.winfo_children():
            widget.destroy()
        
        # Create scrollable frame
        self.scroll_frame = ctk.CTkScrollableFrame(self.parent)
        self.scroll_frame.pack(fill="both", expand=True)
        
        # Title
        ctk.CTkLabel(
            self.scroll_frame,
            text="🏭 Supplier Management",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(pady=(20, 10))

        self.create_supplier_profile()

        # ===== DASHBOARD CARDS =====
        self.create_dashboard()
        
        # ===== ACTION BUTTONS =====
        self.create_action_buttons()
        
        # ===== RECENT TRANSACTIONS =====
        self.create_recent_transactions()

    def get_current_supplier(self):
        """Return the supplier currently used by this module"""
        try:
            db.cursor.execute("""
                SELECT id, name, phone, company_name, address, payable_balance, notes
                FROM suppliers
                ORDER BY id ASC
                LIMIT 1
            """)
            return db.cursor.fetchone()
        except Exception as e:
            print(f"Supplier load error: {e}")
            return None

    def create_supplier_profile(self):
        """Show supplier profile summary with edit button"""
        supplier = self.get_current_supplier()

        frame = ctk.CTkFrame(self.scroll_frame)
        frame.pack(fill="x", padx=20, pady=10)

        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 10))

        ctk.CTkLabel(
            header,
            text="Supplier Profile",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="Edit Supplier" if supplier else "Add Supplier",
            width=120,
            height=32,
            fg_color="#3498DB",
            hover_color="#2980B9",
            command=lambda: self.show_supplier_profile_dialog(supplier)
        ).pack(side="right")

        body = ctk.CTkFrame(frame, fg_color="transparent")
        body.pack(fill="x", padx=20, pady=(0, 15))

        if not supplier:
            ctk.CTkLabel(
                body,
                text="No supplier profile found. Add your supplier details first.",
                font=ctk.CTkFont(size=13),
                text_color="gray"
            ).pack(anchor="w")
            return

        supplier_id, name, phone, company_name, address, payable_balance, notes = supplier

        details = [
            f"Name: {name or '-'}",
            f"Phone: {phone or '-'}",
            f"Company: {company_name or '-'}",
            f"Address: {address or '-'}",
            f"Opening Balance: Rs. {(payable_balance or 0):,.0f}",
        ]

        for detail in details:
            ctk.CTkLabel(
                body,
                text=detail,
                font=ctk.CTkFont(size=13)
            ).pack(anchor="w", pady=2)

        ctk.CTkLabel(
            body,
            text=f"Notes: {notes or '-'}",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(anchor="w", pady=(6, 0))

    def show_supplier_profile_dialog(self, supplier=None):
        """Open add/edit dialog for supplier profile"""
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Edit Supplier" if supplier else "Add Supplier")
        dialog.transient(self.parent)
        dialog.grab_set()
        center_window(dialog, 520, 760)

        ctk.CTkLabel(
            dialog,
            text="Edit Supplier Profile" if supplier else "Add Supplier Profile",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=20)

        form = ctk.CTkFrame(dialog, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=30, pady=10)

        ctk.CTkLabel(form, text="Supplier Name *", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(8, 5))
        name_entry = ctk.CTkEntry(form, height=35)
        name_entry.pack(fill="x")

        ctk.CTkLabel(form, text="Phone", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 5))
        phone_entry = ctk.CTkEntry(form, height=35)
        phone_entry.pack(fill="x")

        ctk.CTkLabel(form, text="Company Name", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 5))
        company_entry = ctk.CTkEntry(form, height=35)
        company_entry.pack(fill="x")

        ctk.CTkLabel(form, text="Address", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 5))
        address_entry = ctk.CTkEntry(form, height=35)
        address_entry.pack(fill="x")

        ctk.CTkLabel(form, text="Opening Balance", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 5))
        balance_entry = ctk.CTkEntry(form, height=35, placeholder_text="0")
        balance_entry.pack(fill="x")

        ctk.CTkLabel(form, text="Notes", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 5))
        notes_box = ctk.CTkTextbox(form, height=120)
        notes_box.pack(fill="both", expand=True)

        supplier_id = None
        if supplier:
            supplier_id, name, phone, company_name, address, payable_balance, notes = supplier
            name_entry.insert(0, name or "")
            phone_entry.insert(0, phone or "")
            company_entry.insert(0, company_name or "")
            address_entry.insert(0, address or "")
            balance_entry.insert(0, str(payable_balance or 0))
            notes_box.insert("1.0", notes or "")

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=20)

        ctk.CTkButton(
            btn_frame,
            text="Save",
            fg_color="#2ECC71",
            hover_color="#27AE60",
            height=38,
            command=lambda: self.save_supplier_profile(
                dialog,
                supplier_id,
                name_entry.get().strip(),
                phone_entry.get().strip(),
                company_entry.get().strip(),
                address_entry.get().strip(),
                balance_entry.get().strip(),
                notes_box.get("1.0", "end").strip()
            )
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            fg_color="#95A5A6",
            hover_color="#7F8C8D",
            height=38,
            command=dialog.destroy
        ).pack(side="left", padx=5)

    def save_supplier_profile(self, dialog, supplier_id, name, phone, company_name, address, balance_text, notes):
        """Save supplier profile changes"""
        if not name:
            messagebox.showwarning("Validation", "Supplier name is required.")
            return

        try:
            opening_balance = float(balance_text) if balance_text else 0
        except ValueError:
            messagebox.showwarning("Validation", "Opening balance must be a valid number.")
            return

        try:
            if supplier_id:
                db.cursor.execute("""
                    UPDATE suppliers
                    SET name = ?, phone = ?, company_name = ?, address = ?,
                        payable_balance = ?, notes = ?
                    WHERE id = ?
                """, (name, phone, company_name, address, opening_balance, notes, supplier_id))
            else:
                db.cursor.execute("""
                    INSERT INTO suppliers (name, phone, company_name, address, payable_balance, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (name, phone, company_name, address, opening_balance, notes))

            db.conn.commit()
            dialog.destroy()
            self.setup_ui()
            messagebox.showinfo("Success", "Supplier profile saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save supplier profile: {str(e)}")
    
    def create_dashboard(self):
        """Create dashboard with summary cards"""
        dashboard_frame = ctk.CTkFrame(self.scroll_frame)
        dashboard_frame.pack(fill="x", padx=20, pady=10)
        
        # Get supplier stats
        stats = self.get_supplier_stats()
        
        # Cards data
        cards = [
            ("📦 Total Purchases", f"Rs. {stats['total_purchases']:,.0f}", "#3498DB"),
            ("💰 Total Payments", f"Rs. {stats['total_payments']:,.0f}", "#2ECC71"),
            ("💳 Remaining Balance", f"Rs. {stats['balance']:,.0f}", "#E74C3C" if stats['balance'] > 0 else "#27AE60"),
            ("📅 Last Purchase", stats['last_purchase'] or "No purchases", "#9B59B6"),
        ]
        
        for i, (title, value, color) in enumerate(cards):
            card = ctk.CTkFrame(dashboard_frame, corner_radius=10)
            card.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")
            dashboard_frame.grid_columnconfigure(i, weight=1)
            
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=12), text_color="gray").pack(pady=(15, 5))
            ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=20, weight="bold"), text_color=color).pack(pady=(5, 15))
    
    def get_supplier_stats(self):
        """Calculate supplier statistics"""
        try:
            # Total purchases (credit only)
            db.cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) 
                FROM supplier_transactions 
                WHERE type = 'purchase' AND payment_type = 'credit'
            """)
            total_purchases = db.cursor.fetchone()[0] or 0
            
            # Total payments
            db.cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) 
                FROM supplier_transactions 
                WHERE type = 'payment'
            """)
            total_payments = db.cursor.fetchone()[0] or 0
            
            # Balance
            balance = total_purchases - total_payments
            
            # Last purchase date
            db.cursor.execute("""
                SELECT date FROM supplier_transactions 
                WHERE type = 'purchase' 
                ORDER BY date DESC LIMIT 1
            """)
            last_purchase = db.cursor.fetchone()
            last_purchase = last_purchase[0] if last_purchase else None
            
            return {
                'total_purchases': total_purchases,
                'total_payments': total_payments,
                'balance': balance,
                'last_purchase': last_purchase
            }
        except Exception as e:
            print(f"Stats error: {e}")
            return {'total_purchases': 0, 'total_payments': 0, 'balance': 0, 'last_purchase': None}
    
    def create_action_buttons(self):
        """Create action buttons"""
        btn_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)
        
        actions = [
            ("+ New Purchase", "#3498DB", self.show_purchase_form),
            ("+ Make Payment", "#2ECC71", self.show_payment_form),
            ("📜 View History", "#9B59B6", self.show_full_history),
            ("📊 Statement", "#E67E22", self.show_statement),
        ]
        
        for text, color, command in actions:
            btn = ctk.CTkButton(
                btn_frame,
                text=text,
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color=color,
                hover_color=self.darken_color(color),
                command=command,
                width=180,
                height=45
            )
            btn.pack(side="left", padx=10)
    
    def create_recent_transactions(self):
        """Show recent transactions"""
        frame = ctk.CTkFrame(self.scroll_frame)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 10))
        
        ctk.CTkLabel(header, text="Recent Transactions", 
                    font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")
        
        # View All button
        ctk.CTkButton(header, text="View All →", 
                     command=self.show_full_history,
                     width=100, height=30).pack(side="right")
        
        # Table headers
        headers = ["Date", "Invoice", "Type", "Details", "Amount", "Balance"]
        header_row = ctk.CTkFrame(frame, fg_color=("gray85", "gray25"))
        header_row.pack(fill="x", padx=20, pady=5)
        
        widths = [100, 120, 100, 200, 120, 120]
        for i, (h, w) in enumerate(zip(headers, widths)):
            ctk.CTkLabel(header_row, text=h, font=ctk.CTkFont(size=12, weight="bold"), 
                        width=w).grid(row=0, column=i, padx=5, pady=8)
        
        # Get recent transactions with running balance
        transactions = self.get_transaction_history(limit=10)
        
        # Scrollable list
        list_frame = ctk.CTkScrollableFrame(frame, height=250)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        for trans in transactions:
            row = ctk.CTkFrame(list_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            
            type_color = "#E74C3C" if trans['type'] == 'purchase' else "#2ECC71"
            
            values = [
                trans['date'],
                trans['invoice_no'],
                trans['type'].title(),
                trans['details'][:30],
                f"Rs. {trans['amount']:,.0f}",
                f"Rs. {trans['running_balance']:,.0f}"
            ]
            
            for i, (v, w) in enumerate(zip(values, widths)):
                color = type_color if i == 2 else "gray10"
                ctk.CTkLabel(row, text=v, font=ctk.CTkFont(size=11), 
                           width=w, text_color=color).grid(row=0, column=i, padx=5)
    
    def get_transaction_history(self, limit=None):
        """Get transaction history with running balance"""
        try:
            query = """
                SELECT date, invoice_no, type, amount, details, payment_type
                FROM supplier_transactions
                ORDER BY date ASC, id ASC
            """
            if limit:
                query += f" LIMIT {limit}"
            
            db.cursor.execute(query)
            rows = db.cursor.fetchall()
            
            # Calculate running balance
            transactions = []
            balance = 0
            
            for row in rows:
                date, invoice_no, trans_type, amount, details, payment_type = row
                
                if trans_type == 'purchase':
                    if payment_type == 'credit':
                        balance += amount
                    trans_details = details or "Purchase"
                else:
                    balance -= amount
                    trans_details = details or "Payment"
                
                transactions.append({
                    'date': date,
                    'invoice_no': invoice_no,
                    'type': trans_type,
                    'amount': amount,
                    'details': trans_details,
                    'running_balance': balance
                })
            
            # Reverse for descending order display
            return list(reversed(transactions))
        except Exception as e:
            print(f"History error: {e}")
            return []
    
    def show_purchase_form(self):
        """Show form to record new purchase from supplier"""
        supplier = self.get_current_supplier()
        if not supplier:
            messagebox.showwarning("Supplier Required", "Please add a supplier profile first.")
            return

        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("New Supplier Purchase")
        dialog.transient(self.parent)
        dialog.grab_set()
        center_window(dialog, 560, 700)
        
        ctk.CTkLabel(dialog, text="📦 New Purchase from Supplier", 
                    font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
        
        # Form frame
        form = ctk.CTkScrollableFrame(dialog)
        form.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Date
        ctk.CTkLabel(form, text="Date:", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(5, 5))
        date_entry = ctk.CTkEntry(form, placeholder_text="YYYY-MM-DD")
        date_entry.pack(fill="x")
        date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        # Invoice Number (Auto-generated)
        ctk.CTkLabel(form, text="Invoice Number:", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 5))
        invoice_entry = ctk.CTkEntry(form)
        invoice_entry.pack(fill="x")
        invoice_entry.insert(0, self.generate_invoice_number('SUP'))
        invoice_entry.configure(state="disabled")
        
        # Product Selection
        ctk.CTkLabel(form, text="Product:", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 5))
        
        # Get products from inventory (optional for suggestions only)
        db.cursor.execute("SELECT id, name, stock FROM flavors ORDER BY name")
        products = db.cursor.fetchall()

        product_names = [p[1] for p in products]

        ctk.CTkLabel(form, text="Product Name:", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 5))
        product_entry = ctk.CTkEntry(form, placeholder_text="Type product name")
        product_entry.pack(fill="x")

        if product_names:
            product_combo = ctk.CTkComboBox(form, values=product_names, width=400)
            product_combo.pack(fill="x", pady=(5, 0))
            product_combo.set(product_names[0])
            product_entry.insert(0, product_names[0])

            def on_product_select(choice):
                product_entry.delete(0, "end")
                product_entry.insert(0, choice)

            product_combo.configure(command=on_product_select)
        
        # Quantity
        ctk.CTkLabel(form, text="Quantity:", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 5))
        qty_entry = ctk.CTkEntry(form, placeholder_text="Enter quantity")
        qty_entry.pack(fill="x")
        
        # Purchase Price
        ctk.CTkLabel(form, text="Purchase Price (per unit):", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 5))
        price_entry = ctk.CTkEntry(form, placeholder_text="Enter price")
        price_entry.pack(fill="x")

        # Sale Price (for new items)
        ctk.CTkLabel(form, text="Sale Price (for new items):", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 5))
        sale_price_entry = ctk.CTkEntry(form, placeholder_text="Enter sale price")
        sale_price_entry.pack(fill="x")

        # # Category (for new items)
        # ctk.CTkLabel(form, text="Category (for new items):", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 5))
        # category_entry = ctk.CTkEntry(form, placeholder_text="e.g., Citrus")
        # category_entry.pack(fill="x")
        
        # Payment Type
        ctk.CTkLabel(form, text="Payment Type:", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 5))
        payment_combo = ctk.CTkComboBox(form, values=["Credit", "Cash"])
        payment_combo.pack(fill="x")
        payment_combo.set("Credit")
        
        # Total Amount (Calculated)
        ctk.CTkLabel(form, text="Total Amount:", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 5))
        total_label = ctk.CTkLabel(form, text="Rs. 0", font=ctk.CTkFont(size=16, weight="bold"))
        total_label.pack(anchor="w")
        
        def calculate_total(*args):
            try:
                qty = int(qty_entry.get() or 0)
                price = float(price_entry.get() or 0)
                total = qty * price
                total_label.configure(text=f"Rs. {total:,.0f}")
            except:
                total_label.configure(text="Rs. 0")
        
        qty_entry.bind("<KeyRelease>", calculate_total)
        price_entry.bind("<KeyRelease>", calculate_total)
        
        # Buttons
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=20)
        
        def save_purchase():
            try:
                date = date_entry.get()
                invoice = invoice_entry.get()
                product_name = product_entry.get().strip()
                qty = int(qty_entry.get())
                price = float(price_entry.get())
                payment_type = payment_combo.get().lower()
                
                if not all([date, invoice, product_name, qty, price]):
                    messagebox.showerror("Error", "Please fill all fields!")
                    return
                
                if qty <= 0 or price <= 0:
                    messagebox.showerror("Error", "Quantity and price must be greater than 0!")
                    return
                
                total = qty * price

                # Find or create inventory item
                db.cursor.execute(
                    "SELECT id FROM flavors WHERE LOWER(name) = LOWER(?)",
                    (product_name,)
                )
                row = db.cursor.fetchone()
                if row:
                    flavor_id = row[0]
                else:
                    try:
                        sale_price = float(sale_price_entry.get())
                    except ValueError:
                        messagebox.showerror("Error", "Enter a valid sale price for new items!")
                        return

                    category = "General"
                    db.cursor.execute("""
                        INSERT INTO flavors (name, category, sale_price, cost_price, stock, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (product_name, category, sale_price, price, 0, datetime.now()))
                    flavor_id = db.cursor.lastrowid

                supplier_id = supplier[0]

                # Save transaction
                db.cursor.execute("""
                    INSERT INTO supplier_transactions 
                    (supplier_id, date, invoice_no, type, amount, payment_type, 
                     details, flavor_id, quantity, purchase_price)
                    VALUES (?, ?, ?, 'purchase', ?, ?, ?, ?, ?, ?)
                """, (supplier_id, date, invoice, total, payment_type, 
                      f"Purchased {qty} units of {product_name}", flavor_id, qty, price))

                # Update inventory stock
                db.cursor.execute("""
                    UPDATE flavors SET stock = stock + ? WHERE id = ?
                """, (qty, flavor_id))
                
                db.conn.commit()
                
                messagebox.showinfo("Success", "Purchase recorded successfully!")
                dialog.destroy()
                self.setup_ui()  # Refresh dashboard
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {str(e)}")
        
        ctk.CTkButton(btn_frame, text="💾 Save Purchase", 
                     fg_color="#2ECC71", hover_color="#27AE60",
                     command=save_purchase, height=40).pack(side="left", padx=5)
        
        ctk.CTkButton(btn_frame, text="❌ Cancel", 
                     fg_color="#95A5A6", hover_color="#7F8C8D",
                     command=dialog.destroy, height=40).pack(side="left", padx=5)
    
    def show_payment_form(self):
        """Show form to make payment to supplier"""
        supplier = self.get_current_supplier()
        if not supplier:
            messagebox.showwarning("Supplier Required", "Please add a supplier profile first.")
            return

        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Make Payment to Supplier")
        dialog.transient(self.parent)
        dialog.grab_set()
        center_window(dialog, 450, 700)
        
        ctk.CTkLabel(dialog, text="💰 Make Payment", 
                    font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)
        
        # Show current balance
        stats = self.get_supplier_stats()
        balance_frame = ctk.CTkFrame(dialog, fg_color="#FFF3E0")
        balance_frame.pack(fill="x", padx=30, pady=10)
        
        ctk.CTkLabel(balance_frame, text="Current Outstanding Balance", 
                    font=ctk.CTkFont(size=12)).pack(pady=(10, 5))
        ctk.CTkLabel(balance_frame, text=f"Rs. {stats['balance']:,.0f}", 
                    font=ctk.CTkFont(size=24, weight="bold"), 
                    text_color="#E67E22").pack(pady=(5, 10))
        
        # Form
        form = ctk.CTkFrame(dialog, fg_color="transparent")
        form.pack(fill="x", padx=30, pady=10)
        
        # Date
        ctk.CTkLabel(form, text="Payment Date:", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 5))
        date_entry = ctk.CTkEntry(form)
        date_entry.pack(fill="x")
        date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        # Amount
        ctk.CTkLabel(form, text="Payment Amount:", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 5))
        amount_entry = ctk.CTkEntry(form, placeholder_text="Enter amount")
        amount_entry.pack(fill="x")
        
        # Payment Method
        ctk.CTkLabel(form, text="Payment Method:", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 5))
        method_combo = ctk.CTkComboBox(form, values=["Cash", "Bank Transfer", "Cheque", "Online"])
        method_combo.pack(fill="x")
        method_combo.set("Cash")
        
        # Notes
        ctk.CTkLabel(form, text="Notes:", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 5))
        notes_entry = ctk.CTkEntry(form, placeholder_text="Optional notes")
        notes_entry.pack(fill="x")
        
        # Buttons
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=20)
        
        def save_payment():
            try:
                date = date_entry.get()
                amount = float(amount_entry.get())
                method = method_combo.get()
                notes = notes_entry.get()
                
                if not date or amount <= 0:
                    messagebox.showerror("Error", "Please enter valid date and amount!")
                    return
                
                # Check if payment exceeds balance
                if amount > stats['balance']:
                    messagebox.showwarning("Warning", "Payment amount exceeds outstanding balance!")
                
                # Generate payment reference
                payment_ref = self.generate_invoice_number('PAY-SUP')
                
                supplier_id = supplier[0]
                
                # Save payment
                db.cursor.execute("""
                    INSERT INTO supplier_transactions 
                    (supplier_id, date, invoice_no, type, amount, payment_type, details)
                    VALUES (?, ?, ?, 'payment', ?, 'cash', ?)
                """, (supplier_id, date, payment_ref, amount, 
                      f"Payment via {method}. {notes}"))
                
                db.conn.commit()
                
                messagebox.showinfo("Success", f"Payment of Rs. {amount:,.0f} recorded successfully!")
                dialog.destroy()
                self.setup_ui()  # Refresh dashboard
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {str(e)}")
        
        ctk.CTkButton(btn_frame, text="💾 Save Payment", 
                     fg_color="#2ECC71", hover_color="#27AE60",
                     command=save_payment, height=40).pack(side="left", padx=5)
        
        ctk.CTkButton(btn_frame, text="❌ Cancel", 
                     fg_color="#95A5A6", hover_color="#7F8C8D",
                     command=dialog.destroy, height=40).pack(side="left", padx=5)
    
    def show_full_history(self):
        """Show full transaction history"""
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Supplier Transaction History")
        dialog.transient(self.parent)
        dialog.grab_set()
        center_window(dialog, 950, 700)
        
        ctk.CTkLabel(dialog, text="📜 Supplier Transaction History", 
                    font=ctk.CTkFont(size=22, weight="bold")).pack(pady=20)
        
        # Summary
        stats = self.get_supplier_stats()
        summary = ctk.CTkFrame(dialog)
        summary.pack(fill="x", padx=30, pady=10)
        
        ctk.CTkLabel(summary, text=f"Total Purchases: Rs. {stats['total_purchases']:,.0f}", 
                    font=ctk.CTkFont(size=14)).pack(side="left", padx=20, pady=15)
        ctk.CTkLabel(summary, text=f"Total Payments: Rs. {stats['total_payments']:,.0f}", 
                    font=ctk.CTkFont(size=14), text_color="#2ECC71").pack(side="left", padx=20, pady=15)
        ctk.CTkLabel(summary, text=f"Balance: Rs. {stats['balance']:,.0f}", 
                    font=ctk.CTkFont(size=14, weight="bold"), 
                    text_color="#E74C3C" if stats['balance'] > 0 else "#27AE60").pack(side="left", padx=20, pady=15)
        
        # Table
        headers = ["Date", "Invoice", "Type", "Details", "Amount", "Running Balance"]
        header_frame = ctk.CTkFrame(dialog, fg_color=("gray85", "gray25"))
        header_frame.pack(fill="x", padx=30, pady=10)
        
        widths = [100, 130, 100, 250, 130, 130]
        for i, (h, w) in enumerate(zip(headers, widths)):
            ctk.CTkLabel(header_frame, text=h, font=ctk.CTkFont(size=12, weight="bold"), 
                        width=w).grid(row=0, column=i, padx=5, pady=8)
        
        # Scrollable list
        list_frame = ctk.CTkScrollableFrame(dialog, height=400)
        list_frame.pack(fill="both", expand=True, padx=30, pady=10)
        
        transactions = self.get_transaction_history()
        
        for trans in transactions:
            row = ctk.CTkFrame(list_frame, fg_color="transparent", cursor="hand2", height=30)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)
            
            type_color = "#E74C3C" if trans['type'] == 'purchase' else "#2ECC71"
            
            values = [
                trans['date'],
                trans['invoice_no'],
                trans['type'].title(),
                trans['details'][:35],
                f"Rs. {trans['amount']:,.0f}",
                f"Rs. {trans['running_balance']:,.0f}"
            ]
            
            for i, (v, w) in enumerate(zip(values, widths)):
                color = type_color if i == 2 else "gray10"
                lbl = ctk.CTkLabel(row, text=v, font=ctk.CTkFont(size=11), 
                                  width=w, text_color=color, anchor="w")
                lbl.grid(row=0, column=i, padx=5, pady=3, sticky="w")
        
        # Close button
        ctk.CTkButton(dialog, text="Close", command=dialog.destroy, 
                     width=120, height=35).pack(pady=15)
    
    def show_statement(self):
        """Show supplier statement with PDF save option"""
        supplier_profile = self.get_current_supplier()
        if not supplier_profile:
            messagebox.showwarning("Supplier Required", "Please add a supplier profile first.")
            return

        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Supplier Statement")
        dialog.transient(self.parent)
        dialog.grab_set()
        dialog.resizable(True, True)
        center_window(dialog, 950, 700)
        
        # Header
        header = ctk.CTkFrame(dialog, fg_color="#2C3E50")
        header.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(header, text="🏭 JUGO SWAT", 
                    font=ctk.CTkFont(size=24, weight="bold"), text_color="white").pack(pady=(15, 5))
        ctk.CTkLabel(header, text="Supplier Statement", 
                    font=ctk.CTkFont(size=16), text_color="#BDC3C7").pack(pady=(0, 15))
        
        # Supplier Info
        supplier = (
            supplier_profile[1],
            supplier_profile[2],
            supplier_profile[4],
        )
        
        info_frame = ctk.CTkFrame(dialog)
        info_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(info_frame, text=f"Supplier: {supplier[0]}", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=20, pady=(15, 5))
        ctk.CTkLabel(info_frame, text=f"Phone: {supplier[1]}", 
                    font=ctk.CTkFont(size=12)).pack(anchor="w", padx=20)
        ctk.CTkLabel(info_frame, text=f"Address: {supplier[2]}", 
                    font=ctk.CTkFont(size=12)).pack(anchor="w", padx=20, pady=(0, 15))
        
        # Statement Date
        ctk.CTkLabel(info_frame, text=f"Statement Date: {datetime.now().strftime('%Y-%m-%d')}", 
                    font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="w", padx=20, pady=(0, 15))
        
        # Summary Cards
        stats = self.get_supplier_stats()
        summary = ctk.CTkFrame(dialog, fg_color="transparent")
        summary.pack(fill="x", padx=20, pady=15)
        
        cards = [
            ("Total Purchases", stats['total_purchases'], "#3498DB"),
            ("Total Paid", stats['total_payments'], "#2ECC71"),
            ("Remaining", stats['balance'], "#E74C3C" if stats['balance'] > 0 else "#27AE60"),
        ]
        
        for i, (title, value, color) in enumerate(cards):
            card = ctk.CTkFrame(summary)
            card.grid(row=0, column=i, padx=10, pady=5, sticky="nsew")
            summary.grid_columnconfigure(i, weight=1)
            
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=12), text_color="gray").pack(pady=(10, 5))
            ctk.CTkLabel(card, text=f"Rs. {value:,.0f}", 
                        font=ctk.CTkFont(size=18, weight="bold"), text_color=color).pack(pady=(5, 10))
        
        # Transaction Table
        ctk.CTkLabel(dialog, text="Transaction Details", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(20, 10))
        
        # Headers
        headers = ["Date", "Invoice", "Description", "Type", "Amount", "Balance"]
        header_row = ctk.CTkFrame(dialog, fg_color=("gray85", "gray25"))
        header_row.pack(fill="x", padx=20, pady=5)
        
        col_widths = [100, 120, 200, 80, 120, 120]
        for i, (h, w) in enumerate(zip(headers, col_widths)):
            ctk.CTkLabel(header_row, text=h, font=ctk.CTkFont(size=11, weight="bold"), 
                        width=w).grid(row=0, column=i, padx=5, pady=8)
        
        transactions = self.get_transaction_history()

        # Buttons (pin at bottom so always visible)
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20, side="bottom")

        ctk.CTkButton(btn_frame, text="Save as PDF",
                     fg_color="#E67E22", hover_color="#D35400",
                     command=lambda: self.save_statement_pdf(supplier, stats, transactions),
                     width=140, height=40).pack(side="left", padx=5)

        ctk.CTkButton(btn_frame, text="Close",
                     fg_color="#95A5A6", hover_color="#7F8C8D",
                     command=dialog.destroy, width=120, height=40).pack(side="left", padx=5)

        # List
        list_frame = ctk.CTkScrollableFrame(dialog, height=250)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)

        for trans in transactions:
            row = ctk.CTkFrame(list_frame, fg_color="transparent")
            row.pack(fill="x", pady=1)

            values = [
                trans['date'],
                trans['invoice_no'],
                trans['details'][:25],
                "Dr" if trans['type'] == 'purchase' else "Cr",
                f"Rs. {trans['amount']:,.0f}",
                f"Rs. {trans['running_balance']:,.0f}"
            ]

            for i, (v, w) in enumerate(zip(values, col_widths)):
                ctk.CTkLabel(row, text=v, font=ctk.CTkFont(size=10), width=w).grid(row=0, column=i, padx=5)

    def save_statement_pdf(self, supplier, stats, transactions):
        """Save supplier statement as PDF"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"Supplier_Statement_{datetime.now().strftime('%Y%m%d')}"
        )
        
        if not filename:
            return
        
        try:
            doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=50, bottomMargin=50)
            elements = []
            styles = getSampleStyleSheet()
            
            # Shop Header
            shop_style = ParagraphStyle('Shop', parent=styles['Heading1'], 
                                       fontSize=22, textColor=colors.HexColor("#2C3E50"), 
                                       alignment=1, spaceAfter=10)
            elements.append(Paragraph("🥤 JUGO SWAT", shop_style))
            elements.append(Paragraph("Supplier Statement", 
                                     ParagraphStyle('Sub', parent=styles['Normal'], 
                                                   fontSize=14, textColor=colors.gray, alignment=1)))
            elements.append(Spacer(1, 20))
            
            # Supplier Info
            info_style = ParagraphStyle('Info', parent=styles['Normal'], fontSize=11, spaceAfter=5)
            elements.append(Paragraph(f"<b>Supplier:</b> {supplier[0]}", info_style))
            elements.append(Paragraph(f"<b>Phone:</b> {supplier[1]}", info_style))
            elements.append(Paragraph(f"<b>Address:</b> {supplier[2]}", info_style))
            elements.append(Paragraph(f"<b>Statement Date:</b> {datetime.now().strftime('%Y-%m-%d')}", info_style))
            elements.append(Spacer(1, 20))
            
            # Summary Table
            summary_data = [
                ["Total Purchases", f"Rs. {stats['total_purchases']:,.0f}"],
                ["Total Payments", f"Rs. {stats['total_payments']:,.0f}"],
                ["Remaining Balance", f"Rs. {stats['balance']:,.0f}"],
            ]
            
            summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#ECF0F1")),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ]))
            elements.append(summary_table)
            elements.append(Spacer(1, 30))
            
            # Transactions Table
            elements.append(Paragraph("Transaction History", 
                                     ParagraphStyle('TableTitle', parent=styles['Heading2'], 
                                                   fontSize=14, spaceAfter=10)))
            
            table_data = [["Date", "Invoice", "Description", "Type", "Amount", "Balance"]]
            for t in transactions:
                table_data.append([
                    t['date'], t['invoice_no'], t['details'][:30],
                    "Purchase" if t['type'] == 'purchase' else "Payment",
                    f"Rs. {t['amount']:,.0f}", f"Rs. {t['running_balance']:,.0f}"
                ])
            
            trans_table = Table(table_data, colWidths=[1*inch, 1.2*inch, 2*inch, 0.8*inch, 1*inch, 1*inch])
            trans_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#34495E")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F9FA")]),
            ]))
            elements.append(trans_table)
            
            # Footer
            elements.append(Spacer(1, 30))
            elements.append(Paragraph("This is a computer generated statement from JUGO SWAT.", 
                                     ParagraphStyle('Footer', parent=styles['Normal'], 
                                                   fontSize=9, textColor=colors.gray, alignment=1)))
            
            doc.build(elements)
            messagebox.showinfo("Success", f"Statement saved to:\n{filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save PDF: {str(e)}")
    
    def generate_invoice_number(self, prefix):
        """Generate auto-incrementing invoice number"""
        try:
            db.cursor.execute(f"""
                SELECT MAX(CAST(SUBSTR(invoice_no, {len(prefix)+2}) AS INTEGER))
                FROM supplier_transactions
                WHERE invoice_no LIKE '{prefix}-%'
            """)
            max_num = db.cursor.fetchone()[0] or 0
            return f"{prefix}-{max_num + 1:04d}"
        except:
            return f"{prefix}-0001"
    
    def darken_color(self, hex_color):
        color_map = {
            "#3498DB": "#2980B9",
            "#2ECC71": "#27AE60",
            "#9B59B6": "#8E44AD",
            "#E67E22": "#D35400",
        }
        return color_map.get(hex_color, hex_color)
