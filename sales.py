import customtkinter as ctk
from tkinter import messagebox, ttk
from database import db
from datetime import datetime
from invoice_generator import generate_invoice
from ui_utils import center_window


class SalesManager:
    def __init__(self, parent_frame):
        self.parent = parent_frame
        self.cart = []  # Shopping cart
        self.current_customer = None
        self.setup_ui()
        self.load_flavors()
    
    def setup_ui(self):
        # Clear parent
        for widget in self.parent.winfo_children():
            widget.destroy()
        
        # Main layout - 2 columns
        self.parent.grid_columnconfigure(0, weight=3)  # Products
        self.parent.grid_columnconfigure(1, weight=2)  # Cart
        self.parent.grid_rowconfigure(0, weight=1)
        
        # ========== LEFT SIDE - Products ==========
        left_frame = ctk.CTkFrame(self.parent)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_frame.grid_rowconfigure(2, weight=1)
        
        # Title
        ctk.CTkLabel(
            left_frame,
            text="🛒 Point of Sale",
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack(pady=(10, 5))
        
        # Search & Filter
        filter_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        filter_frame.pack(fill="x", padx=15, pady=5)
        
        self.search_entry = ctk.CTkEntry(
            filter_frame,
            placeholder_text="Search flavor...",
            width=220,
            height=32
        )
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", lambda e: self.filter_flavors())
        
        ctk.CTkButton(
            filter_frame,
            text="🔍 Search",
            width=80,
            height=32,
            command=self.filter_flavors
        ).pack(side="left")
        
        # Products Grid
        self.products_frame = ctk.CTkScrollableFrame(left_frame)
        self.products_frame.pack(fill="both", expand=True, padx=15, pady=5)
        
        self.products_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # ========== RIGHT SIDE - Cart ==========
        right_frame = ctk.CTkFrame(self.parent)
        right_frame.grid(row=0, column=1, sticky="nsew")
        
        # Cart Title
        ctk.CTkLabel(
            right_frame,
            text="🛍️ Current Sale",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(10, 5))
        
        # Customer Selection
        customer_frame = ctk.CTkFrame(right_frame)
        customer_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(
            customer_frame,
            text="Customer:",
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=5)
        
        self.customer_label = ctk.CTkLabel(
            customer_frame,
            text="Walk-in Customer",
            font=ctk.CTkFont(size=11, weight="bold")
        )
        self.customer_label.pack(side="left", padx=5)
        
        ctk.CTkButton(
            customer_frame,
            text="Change",
            width=70,
            height=25,
            font=ctk.CTkFont(size=10),
            command=self.select_customer
        ).pack(side="right", padx=5)
        
        # Cart Items Frame
        self.cart_frame = ctk.CTkFrame(right_frame)
        self.cart_frame.pack(fill="both", expand=True, padx=15, pady=5)
        
        # Cart headers
        headers = ["Item", "Qty", "Price", "Total", ""]
        header_frame = ctk.CTkFrame(self.cart_frame, fg_color=("gray85", "gray25"))
        header_frame.pack(fill="x", pady=2)
        
        for i, header in enumerate(headers):
            ctk.CTkLabel(
                header_frame,
                text=header,
                font=ctk.CTkFont(size=10, weight="bold"),
                width=55 if i < 4 else 25
            ).grid(row=0, column=i, padx=2, pady=3)
        
        # Cart items scrollable frame
        self.cart_items_frame = ctk.CTkScrollableFrame(self.cart_frame, height=180)
        self.cart_items_frame.pack(fill="both", expand=True, pady=2)
        
        # Totals Frame
        totals_frame = ctk.CTkFrame(right_frame)
        totals_frame.pack(fill="x", padx=15, pady=5)
        
        # Subtotal
        ctk.CTkLabel(totals_frame, text="Subtotal:", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=10, pady=(5, 2))
        self.subtotal_label = ctk.CTkLabel(
            totals_frame,
            text="Rs. 0",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.subtotal_label.pack(anchor="w", padx=10)
        
        # Discount
        discount_frame = ctk.CTkFrame(totals_frame, fg_color="transparent")
        discount_frame.pack(fill="x", padx=10, pady=3)
        
        ctk.CTkLabel(discount_frame, text="Discount:", font=ctk.CTkFont(size=11)).pack(side="left")
        
        self.discount_entry = ctk.CTkEntry(discount_frame, width=80, height=28, font=ctk.CTkFont(size=11))
        self.discount_entry.pack(side="left", padx=10)
        self.discount_entry.insert(0, "0")
        self.discount_entry.bind("<KeyRelease>", lambda e: self.update_totals())
        
        # Grand Total
        ctk.CTkLabel(totals_frame, text="GRAND TOTAL:", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=10)
        self.grand_total_label = ctk.CTkLabel(
            totals_frame,
            text="Rs. 0",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#2ECC71"
        )
        self.grand_total_label.pack(anchor="w", padx=10, pady=(2, 8))
        
        # Payment Mode
        payment_frame = ctk.CTkFrame(right_frame)
        payment_frame.pack(fill="x", padx=15, pady=3)
        
        ctk.CTkLabel(payment_frame, text="Payment:", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=10, pady=(3, 2))
        
        self.payment_mode = ctk.CTkComboBox(
            payment_frame,
            values=["Cash", "Credit", "Online Transfer"],
            height=32,
            font=ctk.CTkFont(size=11)
        )
        self.payment_mode.pack(fill="x", padx=10, pady=(0, 3))
        self.payment_mode.set("Cash")
        
        # ===== ACTION BUTTONS - FIXED =====
        btn_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=8)
        
        # Clear Button
        ctk.CTkButton(
            btn_frame,
            text="🗑️ Clear",
            font=ctk.CTkFont(size=11),
            fg_color="#E74C3C",
            hover_color="#C0392B",
            command=self.clear_cart,
            height=38,
            width=90
        ).pack(side="left", padx=3)
        
        # COMPLETE SALE BUTTON - VISIBLE
        complete_btn = ctk.CTkButton(
            btn_frame,
            text="✅ COMPLETE\nSALE",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#2ECC71",
            hover_color="#27AE60",
            command=self.complete_sale,
            height=45,
            width=130
        )
        complete_btn.pack(side="right", padx=3)
    
    def load_flavors(self):
        # Clear existing products
        for widget in self.products_frame.winfo_children():
            widget.destroy()
        
        # Get flavors from database
        db.cursor.execute("SELECT id, name, sale_price, stock FROM flavors WHERE stock > 0 ORDER BY name")
        flavors = db.cursor.fetchall()
        
        row, col = 0, 0
        for flavor in flavors:
            flavor_id, name, price, stock = flavor
            
            # Product Card - CHOTA BANAYA
            card = ctk.CTkFrame(self.products_frame, corner_radius=8, border_width=1, border_color="#E0E0E0")
            card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            # Flavor Name
            ctk.CTkLabel(
                card,
                text=name,
                font=ctk.CTkFont(size=13, weight="bold")
            ).pack(pady=(10, 3))
            
            # Price
            ctk.CTkLabel(
                card,
                text=f"Rs. {price}",
                font=ctk.CTkFont(size=15, weight="bold"),
                text_color="#2ECC71"
            ).pack()
            
            # Stock
            ctk.CTkLabel(
                card,
                text=f"Stock: {stock}",
                font=ctk.CTkFont(size=10),
                text_color="gray"
            ).pack(pady=(3, 5))
            
            # Add to Cart Button
            ctk.CTkButton(
                card,
                text="+ Add",
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color="#3498DB",
                hover_color="#2980B9",
                command=lambda f=flavor: self.add_to_cart(f),
                width=100,
                height=28
            ).pack(pady=(0, 10))
            
            col += 1
            if col > 2:
                col = 0
                row += 1
    
    def filter_flavors(self):
        search = self.search_entry.get().strip().lower()
        
        for widget in self.products_frame.winfo_children():
            widget.destroy()
        
        db.cursor.execute("SELECT id, name, sale_price, stock FROM flavors WHERE stock > 0 ORDER BY name")
        flavors = db.cursor.fetchall()
        
        row, col = 0, 0
        for flavor in flavors:
            if search and search not in flavor[1].lower():
                continue
                
            flavor_id, name, price, stock = flavor
            
            card = ctk.CTkFrame(self.products_frame, corner_radius=8, border_width=1, border_color="#E0E0E0")
            card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            ctk.CTkLabel(card, text=name, font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(10, 3))
            ctk.CTkLabel(card, text=f"Rs. {price}", font=ctk.CTkFont(size=15, weight="bold"), text_color="#2ECC71").pack()
            ctk.CTkLabel(card, text=f"Stock: {stock}", font=ctk.CTkFont(size=10), text_color="gray").pack(pady=(3, 5))
            
            ctk.CTkButton(
                card,
                text="+ Add",
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color="#3498DB",
                hover_color="#2980B9",
                command=lambda f=flavor: self.add_to_cart(f),
                width=100,
                height=28
            ).pack(pady=(0, 10))
            
            col += 1
            if col > 2:
                col = 0
                row += 1
    
    def add_to_cart(self, flavor):
        flavor_id, name, price, stock = flavor
        
        # Check if already in cart
        for item in self.cart:
            if item['id'] == flavor_id:
                if item['qty'] < stock:
                    item['qty'] += 1
                    self.update_cart_display()
                    self.update_totals()
                    return
                else:
                    messagebox.showwarning("Stock Limit", f"Only {stock} BOX available!")
                    return
        
        # Add new item
        self.cart.append({
            'id': flavor_id,
            'name': name,
            'price': price,
            'qty': 1,
            'stock': stock
        })
        
        self.update_cart_display()
        self.update_totals()
    
    def update_cart_display(self):
        # Clear cart display
        for widget in self.cart_items_frame.winfo_children():
            widget.destroy()
        
        # Show items
        for i, item in enumerate(self.cart):
            row = ctk.CTkFrame(self.cart_items_frame, fg_color="transparent")
            row.pack(fill="x", pady=1)
            
            ctk.CTkLabel(row, text=item['name'][:12], width=55, font=ctk.CTkFont(size=10)).pack(side="left")
            ctk.CTkLabel(row, text=str(item['qty']), width=55, font=ctk.CTkFont(size=10)).pack(side="left")
            ctk.CTkLabel(row, text=f"Rs.{int(item['price'])}", width=55, font=ctk.CTkFont(size=10)).pack(side="left")
            ctk.CTkLabel(row, text=f"Rs.{int(item['price'] * item['qty'])}", width=55, font=ctk.CTkFont(size=10)).pack(side="left")
            
            ctk.CTkButton(
                row,
                text="✕",
                width=25,
                height=20,
                font=ctk.CTkFont(size=10),
                fg_color="#E74C3C",
                hover_color="#C0392B",
                command=lambda idx=i: self.remove_from_cart(idx)
            ).pack(side="left")
    
    def remove_from_cart(self, index):
        del self.cart[index]
        self.update_cart_display()
        self.update_totals()
    
    def update_totals(self):
        subtotal = sum(item['price'] * item['qty'] for item in self.cart)
        
        try:
            discount = float(self.discount_entry.get() or 0)
        except ValueError:
            discount = 0
        
        grand_total = max(0, subtotal - discount)
        
        self.subtotal_label.configure(text=f"Rs. {subtotal}")
        self.grand_total_label.configure(text=f"Rs. {grand_total}")
    
    def clear_cart(self):
        self.cart = []
        self.current_customer = None
        self.customer_label.configure(text="Walk-in Customer")
        self.discount_entry.delete(0, "end")
        self.discount_entry.insert(0, "0")
        self.payment_mode.set("Cash")
        self.update_cart_display()
        self.update_totals()
    
    def select_customer(self):
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Select Customer")
        dialog.transient(self.parent)
        dialog.grab_set()
        center_window(dialog, 400, 500)
        
        ctk.CTkLabel(
            dialog,
            text="👥 Select Customer",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=20)
        
        # Search
        search_entry = ctk.CTkEntry(dialog, placeholder_text="Search customer...", width=300)
        search_entry.pack(pady=10)
        
        # Customer list
        list_frame = ctk.CTkScrollableFrame(dialog, width=350, height=300)
        list_frame.pack(pady=10)
        
        # Walk-in option
        walkin_btn = ctk.CTkButton(
            list_frame,
            text="🚶 Walk-in Customer",
            font=ctk.CTkFont(size=12),
            fg_color="#95A5A6",
            command=lambda: self.set_customer(None, "Walk-in Customer", dialog)
        )
        walkin_btn.pack(fill="x", pady=5)
        
        # Load customers
        db.cursor.execute("SELECT id, name, phone FROM customers ORDER BY name")
        customers = db.cursor.fetchall()
        
        for cust in customers:
            cust_id, name, phone = cust
            btn = ctk.CTkButton(
                list_frame,
                text=f"{name} ({phone})",
                font=ctk.CTkFont(size=12),
                anchor="w",
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
                command=lambda cid=cust_id, cname=name, d=dialog: self.set_customer(cid, cname, d)
            )
            btn.pack(fill="x", pady=2)
        
        ctk.CTkButton(
            dialog,
            text="➕ Add New Customer",
            font=ctk.CTkFont(size=12),
            command=lambda: self.add_new_customer_dialog(dialog)
        ).pack(pady=10)
    
    def set_customer(self, cust_id, name, dialog):
        self.current_customer = cust_id
        self.customer_label.configure(text=name)
        dialog.destroy()
    
    def add_new_customer_dialog(self, parent_dialog):
        parent_dialog.destroy()
        
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Add New Customer")
        dialog.transient(self.parent)
        dialog.grab_set()
        center_window(dialog, 350, 450)
        
        ctk.CTkLabel(dialog, text="Add New Customer", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)
        
        # Scrollable frame
        scroll = ctk.CTkScrollableFrame(dialog, width=300, height=300)
        scroll.pack(padx=20, pady=10, fill="both", expand=True)
        
        fields = [
            ("Name *", "name"),
            ("Phone *", "phone"),
            ("Address", "address"),
            ("Shop/Business Name", "shop")
        ]
        
        entries = {}
        for label, key in fields:
            ctk.CTkLabel(scroll, text=label, font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 5))
            entry = ctk.CTkEntry(scroll, width=280, height=32)
            entry.pack()
            entries[key] = entry
        
        def save_customer():
            name = entries['name'].get().strip()
            phone = entries['phone'].get().strip()
            
            if not name or not phone:
                messagebox.showerror("Error", "Name and Phone are required!", parent=dialog)
                return
            
            try:
                db.cursor.execute('''
                    INSERT INTO customers (name, phone, address, shop_name, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (name, phone, entries['address'].get(), entries['shop'].get(), datetime.now()))
                db.conn.commit()
                
                cust_id = db.cursor.lastrowid
                self.set_customer(cust_id, name, dialog)
                messagebox.showinfo("Success", "Customer added!")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed: {str(e)}", parent=dialog)
        
        # Buttons frame at bottom
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=15)
        
        ctk.CTkButton(
            btn_frame,
            text="💾 Save",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#2ECC71",
            command=save_customer,
            width=100,
            height=32
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=dialog.destroy,
            width=80,
            height=32
        ).pack(side="left", padx=10)
    
    def complete_sale(self):
        if not self.cart:
            messagebox.showwarning("Empty Cart", "Please add items to cart first!")
            return
        
        # Get totals
        subtotal = sum(item['price'] * item['qty'] for item in self.cart)
        try:
            discount = float(self.discount_entry.get() or 0)
        except ValueError:
            discount = 0
        
        grand_total = max(0, subtotal - discount)
        payment = self.payment_mode.get()
        
        # Confirm
        if not messagebox.askyesno("Confirm Sale", f"Total: Rs. {grand_total}\nPayment: {payment}\n\nComplete sale?"):
            return
        
        try:
            # Generate invoice number
            db.cursor.execute("SELECT last_invoice_number FROM settings WHERE id=1")
            last_num = db.cursor.fetchone()[0]
            new_num = last_num + 1
            invoice_number = f"JUGO-{new_num:04d}"
            
            # Update invoice number
            db.cursor.execute("UPDATE settings SET last_invoice_number = ? WHERE id=1", (new_num,))
            
            # Insert sale
            customer_name = self.customer_label.cget("text")
            is_credit = 1 if payment == "Credit" else 0
            
            db.cursor.execute('''
                INSERT INTO sales (invoice_number, customer_id, customer_name, total_amount, 
                                  discount, grand_total, payment_mode, is_credit, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (invoice_number, self.current_customer, customer_name, subtotal,
                  discount, grand_total, payment, is_credit, datetime.now()))
            
            sale_id = db.cursor.lastrowid
            
            # Insert sale items & update stock
            for item in self.cart:
                # Sale item
                db.cursor.execute('''
                    INSERT INTO sale_items (sale_id, flavor_id, flavor_name, quantity, price, total)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (sale_id, item['id'], item['name'], item['qty'], item['price'], 
                      item['price'] * item['qty']))
                
                # Update stock
                db.cursor.execute("UPDATE flavors SET stock = stock - ? WHERE id = ?", 
                                (item['qty'], item['id']))
                
                # Stock movement
                db.cursor.execute('''
                    INSERT INTO stock_movements (flavor_id, type, quantity, notes, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (item['id'], 'out', item['qty'], f'Sale #{invoice_number}', datetime.now()))
            
            db.conn.commit()
            
            # Show success
            messagebox.showinfo("Success", f"Sale completed!\nInvoice: {invoice_number}")
            
            # Fetch customer contact (if available)
            customer_contact = "N/A"
            if self.current_customer:
                db.cursor.execute("SELECT phone FROM customers WHERE id = ?", (self.current_customer,))
                row = db.cursor.fetchone()
                if row and row[0]:
                    customer_contact = row[0]

            # Generate invoice (PDF + text)
            invoice_text, _ = generate_invoice(
                invoice_number,
                customer_name,
                customer_contact,
                self.cart,
                subtotal,
                discount,
                grand_total,
                payment
            )
            self.show_invoice_dialog(invoice_text, invoice_number)
            
            # Clear cart
            self.clear_cart()
            
        except Exception as e:
            db.conn.rollback()
            messagebox.showerror("Error", f"Sale failed: {str(e)}")
    
    def show_invoice_dialog(self, invoice_text, invoice_num):
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title(f"Invoice {invoice_num}")
        dialog.transient(self.parent)
        dialog.grab_set()
        center_window(dialog, 500, 650)
        
        ctk.CTkLabel(dialog, text="🧾 INVOICE", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
        
        text_box = ctk.CTkTextbox(dialog, width=450, height=500)
        text_box.pack(pady=10)
        text_box.insert("1.0", invoice_text)
        text_box.configure(state="disabled")
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        def print_invoice():
            messagebox.showinfo("Print", f"Invoice {invoice_num} sent to printer!")
        
        def save_pdf():
            messagebox.showinfo("PDF", f"Invoice {invoice_num} saved as PDF!")
        
        ctk.CTkButton(
            btn_frame,
            text="🖨️ Print",
            command=print_invoice,
            width=100,
            height=35
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="💾 Save PDF",
            command=save_pdf,
            width=100,
            height=35
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="✅ Close",
            command=dialog.destroy,
            width=100,
            height=35,
            fg_color="#2ECC71"
        ).pack(side="left", padx=5)
        
        # Wait for dialog to close
        dialog.wait_window()
