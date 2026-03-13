import customtkinter as ctk
from tkinter import messagebox, ttk
from database import db
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import os
from ui_utils import center_window


class CustomersManager:
    def __init__(self, parent_frame):
        self.parent = parent_frame
        self.setup_ui()
        self.load_customers()
    
    def setup_ui(self):
        # Clear parent
        for widget in self.parent.winfo_children():
            widget.destroy()
        
        # Title
        title_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(
            title_frame,
            text="👥 Customer Management",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(side="left")
        
        # Add New Button
        add_btn = ctk.CTkButton(
            title_frame,
            text="+ Add New Customer",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2ECC71",
            hover_color="#27AE60",
            command=self.show_add_customer_dialog,
            width=160,
            height=35
        )
        add_btn.pack(side="right")
        
        # Search Frame
        search_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=10)
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Search by name or phone...",
            width=300,
            height=35,
            font=ctk.CTkFont(size=12)
        )
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", lambda e: self.search_customers())
        
        ctk.CTkButton(
            search_frame,
            text="🔍 Search",
            width=100,
            height=35,
            command=self.search_customers
        ).pack(side="left")
        
        # Stats Frame
        stats_frame = ctk.CTkFrame(self.parent)
        stats_frame.pack(fill="x", padx=20, pady=10)
        
        self.total_label = ctk.CTkLabel(
            stats_frame,
            text="Total Customers: 0",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.total_label.pack(side="left", padx=20, pady=10)
        
        self.credit_label = ctk.CTkLabel(
            stats_frame,
            text="Credit Customers: 0",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#E74C3C"
        )
        self.credit_label.pack(side="left", padx=20, pady=10)
        
        # Table Frame
        table_frame = ctk.CTkFrame(self.parent)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Treeview
        columns = ("ID", "Name", "Phone", "Shop", "Address", "Credit Limit", "Action")
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=15
        )
        
        # Column headings
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")
        
        self.tree.column("Name", width=150)
        self.tree.column("Phone", width=120)
        self.tree.column("Shop", width=150)
        self.tree.column("Address", width=200)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Double click to view invoice
        self.tree.bind("<Double-1>", self.on_item_double_click)
        
        # Action Buttons Frame
        action_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        action_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(
            action_frame,
            text="✏️ Edit",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#3498DB",
            hover_color="#2980B9",
            command=self.edit_selected,
            width=80,
            height=35
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            action_frame,
            text="📋 History",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#9B59B6",
            hover_color="#8E44AD",
            command=self.view_history,
            width=90,
            height=35
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            action_frame,
            text="💵 Receive\nPayment",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#2ECC71",
            hover_color="#27AE60",
            command=self.receive_payment,
            width=90,
            height=40
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            action_frame,
            text="🗑️ Delete",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#E74C3C",
            hover_color="#C0392B",
            command=self.delete_selected,
            width=80,
            height=35
        ).pack(side="left", padx=5)
    
    def get_customer_totals(self, cust_id):
        """Calculate Total Spent, Total Paid, and Credit for a customer"""
        # Get all transactions
        db.cursor.execute("""
            SELECT grand_total, is_credit
            FROM sales
            WHERE customer_id = ? AND grand_total != 0
        """, (cust_id,))
        transactions = db.cursor.fetchall()
        
        total_spent = 0  # All purchases (credit + cash)
        total_paid = 0   # All payments + cash purchases
        
        for grand_total, is_credit in transactions:
            if grand_total > 0:
                # Purchase
                total_spent += grand_total
                if not is_credit:
                    # Cash purchase = paid immediately
                    total_paid += grand_total
            else:
                # Payment received (negative value)
                total_paid += abs(grand_total)
        
        current_credit = total_spent - total_paid
        
        return total_spent, total_paid, current_credit
    
    def get_next_invoice_number(self, prefix="JUGO"):
        """Get next auto-increment invoice number"""
        try:
            db.cursor.execute("""
                SELECT invoice_number FROM sales 
                WHERE invoice_number LIKE ?
                ORDER BY id DESC LIMIT 1
            """, (f"{prefix}-%",))
            
            result = db.cursor.fetchone()
            if result:
                last_num = int(result[0].split('-')[1])
                return f"{prefix}-{last_num + 1:04d}"
            else:
                return f"{prefix}-0001"
        except:
            return f"{prefix}-0001"
    
    def load_customers(self):
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Load from database
        db.cursor.execute("""
            SELECT id, name, phone, shop_name, address, credit_limit 
            FROM customers 
            ORDER BY name
        """)
        customers = db.cursor.fetchall()
        
        credit_customers = 0
        
        for customer in customers:
            cust_id, name, phone, shop, address, credit_limit = customer
            
            # Calculate totals
            total_spent, total_paid, current_credit = self.get_customer_totals(cust_id)
            
            # Determine status and tag
            if current_credit > 0:
                status = f"Credit: Rs. {current_credit:,.0f}"
                credit_customers += 1
                tag = "credit"
            else:
                status = "No Credit"
                tag = "no_credit"
            
            item_id = self.tree.insert("", "end", values=(
                cust_id, name, phone, shop or "-", address or "-", 
                f"Rs. {credit_limit:,.0f}", status
            ), tags=(tag,))
        
        # Configure tag colors - RED for credit customers
        self.tree.tag_configure("credit", foreground="#E74C3C", font=('TkDefaultFont', 9, 'bold'))
        self.tree.tag_configure("no_credit", foreground="black")
        
        # Update stats
        self.total_label.configure(text=f"Total Customers: {len(customers)}")
        self.credit_label.configure(text=f"Credit Customers: {credit_customers}")
    
    def search_customers(self):
        search_term = self.search_entry.get().strip().lower()
        
        for item in self.tree.get_children():
            values = self.tree.item(item)["values"]
            name = str(values[1]).lower()
            phone = str(values[2]).lower()
            
            if search_term in name or search_term in phone:
                self.tree.selection_set(item)
                self.tree.see(item)
                return
        
        if search_term:
            messagebox.showinfo("Search", f"No customer found: {search_term}")
    
    def show_add_customer_dialog(self):
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Add New Customer")
        dialog.transient(self.parent)
        dialog.grab_set()
        center_window(dialog, 450, 600)
        
        # Scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(dialog, width=400, height=450)
        scroll_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        ctk.CTkLabel(
            scroll_frame,
            text="Add New Customer",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(0, 20))
        
        # Form fields
        ctk.CTkLabel(scroll_frame, text="Full Name *", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 5))
        name_entry = ctk.CTkEntry(scroll_frame, height=35)
        name_entry.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(scroll_frame, text="Phone Number *", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 5))
        phone_entry = ctk.CTkEntry(scroll_frame, height=35)
        phone_entry.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(scroll_frame, text="Shop/Business Name", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 5))
        shop_entry = ctk.CTkEntry(scroll_frame, height=35)
        shop_entry.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(scroll_frame, text="Address", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 5))
        address_entry = ctk.CTkEntry(scroll_frame, height=35)
        address_entry.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(scroll_frame, text="Credit Limit (Rs.)", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 5))
        credit_entry = ctk.CTkEntry(scroll_frame, height=35)
        credit_entry.pack(fill="x", pady=(0, 20))
        credit_entry.insert(0, "0")
        
        def save_customer():
            name = name_entry.get().strip()
            phone = phone_entry.get().strip()
            shop = shop_entry.get().strip()
            address = address_entry.get().strip()
            
            try:
                credit_limit = float(credit_entry.get() or 0)
            except ValueError:
                credit_limit = 0
            
            if not name or not phone:
                messagebox.showerror("Error", "Name and Phone are required!", parent=dialog)
                return
            
            try:
                db.cursor.execute('''
                    INSERT INTO customers (name, phone, shop_name, address, credit_limit, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (name, phone, shop, address, credit_limit, datetime.now()))
                db.conn.commit()
                
                messagebox.showinfo("Success", f"Customer '{name}' added successfully!", parent=dialog)
                dialog.destroy()
                self.load_customers()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add customer: {str(e)}", parent=dialog)
        
        # Buttons frame at bottom
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(
            btn_frame,
            text="💾 Save",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2ECC71",
            hover_color="#27AE60",
            command=save_customer,
            width=120,
            height=40
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="❌ Cancel",
            font=ctk.CTkFont(size=14),
            fg_color="#95A5A6",
            hover_color="#7F8C8D",
            command=dialog.destroy,
            width=120,
            height=40
        ).pack(side="left", padx=10)
    
    def on_item_double_click(self, event):
        # Show invoice for selected item
        selected = self.tree.selection()
        if selected:
            self.show_invoice()
    
    def show_invoice(self, sale_id=None):
        """Show detailed invoice with credit info"""
        selected = self.tree.selection()
        if not sale_id and not selected:
            return
        
        if not sale_id:
            # Get latest sale for selected customer
            item = self.tree.item(selected[0])
            cust_id = item["values"][0]
            cust_name = item["values"][1]
            
            db.cursor.execute("""
                SELECT id, invoice_number, grand_total, payment_mode, is_credit, created_at
                FROM sales 
                WHERE customer_id = ? AND grand_total != 0
                ORDER BY created_at DESC LIMIT 1
            """, (cust_id,))
            result = db.cursor.fetchone()
            
            if not result:
                messagebox.showinfo("Info", "No transactions found for this customer")
                return
            
            sale_id, invoice_num, amount, payment_mode, is_credit, date = result
        else:
            db.cursor.execute("""
                SELECT s.id, s.invoice_number, s.grand_total, s.payment_mode, s.is_credit, s.created_at,
                       c.name, c.id
                FROM sales s
                JOIN customers c ON s.customer_id = c.id
                WHERE s.id = ?
            """, (sale_id,))
            result = db.cursor.fetchone()
            if not result:
                return
            sale_id, invoice_num, amount, payment_mode, is_credit, date, cust_name, cust_id = result
        
        # Get customer totals
        total_spent, total_paid, current_credit = self.get_customer_totals(cust_id)
        
        # Get previous credit before this transaction
        db.cursor.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN grand_total > 0 THEN grand_total ELSE 0 END), 0) -
                COALESCE(SUM(CASE WHEN grand_total < 0 THEN ABS(grand_total) 
                                  WHEN is_credit = 0 AND grand_total > 0 THEN grand_total 
                                  ELSE 0 END), 0) as prev_credit
            FROM sales
            WHERE customer_id = ? AND created_at < ?
        """, (cust_id, date))
        
        prev_credit_result = db.cursor.fetchone()
        previous_credit = prev_credit_result[0] if prev_credit_result and prev_credit_result[0] else 0
        
        # Determine transaction type and amounts
        if amount < 0:
            # Payment transaction
            trans_type = "PAYMENT"
            purchase_amount = 0
            payment_amount = abs(amount)
            credit_from_this = 0
        elif is_credit:
            # Credit purchase
            trans_type = "CREDIT"
            purchase_amount = amount
            payment_amount = 0
            credit_from_this = amount
        else:
            # Cash purchase
            trans_type = "CASH"
            purchase_amount = amount
            payment_amount = amount
            credit_from_this = 0
        
        # Create Invoice Dialog
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title(f"Invoice - {invoice_num}")
        dialog.transient(self.parent)
        dialog.grab_set()
        center_window(dialog, 500, 750)
        
        # Invoice Frame
        invoice_frame = ctk.CTkFrame(dialog, fg_color="white", border_width=2, border_color="gray")
        invoice_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        ctk.CTkLabel(
            invoice_frame,
            text="🧾 INVOICE",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#2C3E50"
        ).pack(pady=(20, 10))
        
        ctk.CTkLabel(
            invoice_frame,
            text=f"Invoice #: {invoice_num}",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack()
        
        # Customer Details
        details_frame = ctk.CTkFrame(invoice_frame, fg_color="transparent")
        details_frame.pack(fill="x", padx=30, pady=20)
        
        ctk.CTkLabel(details_frame, text=f"Customer: {cust_name}", 
                    font=ctk.CTkFont(size=14, weight="bold"), anchor="w").pack(fill="x")
        ctk.CTkLabel(details_frame, text=f"Date: {date[:10] if isinstance(date, str) else date.strftime('%Y-%m-%d')}", 
                    font=ctk.CTkFont(size=12), anchor="w").pack(fill="x")
        
        # Transaction Type Badge
        if trans_type == "CREDIT":
            badge_color = "#E74C3C"
            badge_text = "⭐ CREDIT SALE"
        elif trans_type == "CASH":
            badge_color = "#2ECC71"
            badge_text = "💰 CASH SALE"
        else:
            badge_color = "#3498DB"
            badge_text = "💵 PAYMENT RECEIVED"
        
        ctk.CTkLabel(details_frame, text=badge_text, 
                    font=ctk.CTkFont(size=14, weight="bold"), 
                    text_color=badge_color).pack(fill="x", pady=(10, 0))
        
        # Line
        ctk.CTkFrame(invoice_frame, height=2, fg_color="gray").pack(fill="x", padx=30, pady=10)
        
        # Transaction Details
        trans_frame = ctk.CTkFrame(invoice_frame, fg_color="transparent")
        trans_frame.pack(fill="x", padx=30, pady=10)
        
        ctk.CTkLabel(trans_frame, text="TRANSACTION DETAILS:", 
                    font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        
        if trans_type != "PAYMENT":
            ctk.CTkLabel(trans_frame, text=f"Purchase Amount: Rs. {purchase_amount:,.2f}", 
                        font=ctk.CTkFont(size=13)).pack(anchor="w", pady=(5, 0))
        
        if payment_amount > 0:
            ctk.CTkLabel(trans_frame, text=f"Payment Received: Rs. {payment_amount:,.2f}", 
                        font=ctk.CTkFont(size=13), text_color="#2ECC71").pack(anchor="w", pady=(5, 0))
        
        if trans_type == "CREDIT":
            ctk.CTkLabel(trans_frame, text=f"Credit from this bill: Rs. {credit_from_this:,.2f}", 
                        font=ctk.CTkFont(size=13), text_color="#E74C3C").pack(anchor="w", pady=(5, 0))
        
        # Credit Summary
        ctk.CTkFrame(invoice_frame, height=2, fg_color="gray").pack(fill="x", padx=30, pady=10)
        
        summary_frame = ctk.CTkFrame(invoice_frame, fg_color="transparent")
        summary_frame.pack(fill="x", padx=30, pady=10)
        
        ctk.CTkLabel(summary_frame, text="CREDIT SUMMARY:", 
                    font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        
        ctk.CTkLabel(summary_frame, text=f"Previous Credit: Rs. {previous_credit:,.2f}", 
                    font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(5, 0))
        
        if trans_type == "CREDIT":
            ctk.CTkLabel(summary_frame, text=f"+ New Credit: Rs. {credit_from_this:,.2f}", 
                        font=ctk.CTkFont(size=12), text_color="#E74C3C").pack(anchor="w")
        elif trans_type == "PAYMENT":
            ctk.CTkLabel(summary_frame, text=f"- Payment: Rs. {payment_amount:,.2f}", 
                        font=ctk.CTkFont(size=12), text_color="#2ECC71").pack(anchor="w")
        
        ctk.CTkFrame(summary_frame, height=1, fg_color="gray").pack(fill="x", pady=5)
        
        ctk.CTkLabel(summary_frame, text=f"TOTAL OUTSTANDING CREDIT: Rs. {current_credit:,.2f}", 
                    font=ctk.CTkFont(size=14, weight="bold"),
                    text_color="#E74C3C" if current_credit > 0 else "#2ECC71").pack(anchor="w")
        
        # Footer
        ctk.CTkLabel(invoice_frame, text="Thank you for your business!", 
                    font=ctk.CTkFont(size=12),
                    text_color="gray").pack(pady=30)
        
        # Buttons Frame
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        ctk.CTkButton(
            btn_frame,
            text="🖨️ Print",
            font=ctk.CTkFont(size=12),
            width=100,
            height=35,
            command=lambda: messagebox.showinfo("Print", "Print functionality would be implemented here")
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="Close",
            font=ctk.CTkFont(size=12),
            width=100,
            height=35,
            command=dialog.destroy
        ).pack(side="left", padx=5)
    
    def edit_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select", "Please select a customer to edit!")
            return
        
        item = self.tree.item(selected[0])
        values = item["values"]
        cust_id = values[0]
        
        # Get full details
        db.cursor.execute("SELECT * FROM customers WHERE id=?", (cust_id,))
        customer = db.cursor.fetchone()
        
        if not customer:
            messagebox.showerror("Error", "Customer not found!")
            return
        
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title(f"Edit: {customer[1]}")
        dialog.transient(self.parent)
        dialog.grab_set()
        center_window(dialog, 450, 650)
        
        # Scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(dialog, width=400, height=450)
        scroll_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        ctk.CTkLabel(
            scroll_frame,
            text="✏️ Edit Customer",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(0, 20))
        
        # Form fields
        ctk.CTkLabel(scroll_frame, text="Full Name", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 5))
        name_entry = ctk.CTkEntry(scroll_frame, height=35)
        name_entry.pack(fill="x", pady=(0, 10))
        name_entry.insert(0, customer[1])
        
        ctk.CTkLabel(scroll_frame, text="Phone Number", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 5))
        phone_entry = ctk.CTkEntry(scroll_frame, height=35)
        phone_entry.pack(fill="x", pady=(0, 10))
        phone_entry.insert(0, customer[2])
        
        ctk.CTkLabel(scroll_frame, text="Shop/Business Name", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 5))
        shop_entry = ctk.CTkEntry(scroll_frame, height=35)
        shop_entry.pack(fill="x", pady=(0, 10))
        shop_entry.insert(0, customer[4] or "")
        
        ctk.CTkLabel(scroll_frame, text="Address", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 5))
        address_entry = ctk.CTkEntry(scroll_frame, height=35)
        address_entry.pack(fill="x", pady=(0, 10))
        address_entry.insert(0, customer[3] or "")
        
        ctk.CTkLabel(scroll_frame, text="Credit Limit (Rs.)", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 5))
        credit_entry = ctk.CTkEntry(scroll_frame, height=35)
        credit_entry.pack(fill="x", pady=(0, 20))
        credit_entry.insert(0, str(customer[6]))
        
        def save_changes():
            name = name_entry.get().strip()
            phone = phone_entry.get().strip()
            
            if not name or not phone:
                messagebox.showerror("Error", "Name and Phone are required!", parent=dialog)
                return
            
            try:
                credit_limit = float(credit_entry.get() or 0)
            except ValueError:
                credit_limit = 0
            
            try:
                db.cursor.execute('''
                    UPDATE customers 
                    SET name=?, phone=?, shop_name=?, address=?, credit_limit=?
                    WHERE id=?
                ''', (name, phone, shop_entry.get(), address_entry.get(), credit_limit, cust_id))
                db.conn.commit()
                
                messagebox.showinfo("Success", "Customer updated successfully!", parent=dialog)
                dialog.destroy()
                self.load_customers()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed: {str(e)}", parent=dialog)
        
        # Buttons frame
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(
            btn_frame,
            text="💾 Save Changes",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2ECC71",
            command=save_changes,
            width=140,
            height=40
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=dialog.destroy,
            width=100,
            height=40
        ).pack(side="left", padx=10)
    
    def receive_payment(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select", "Please select a customer!")
            return
        
        item = self.tree.item(selected[0])
        cust_id = item["values"][0]
        cust_name = item["values"][1]
        
        # Get customer totals
        total_spent, total_paid, current_credit = self.get_customer_totals(cust_id)
        
        if current_credit <= 0:
            messagebox.showinfo("No Credit", f"{cust_name} has no outstanding credit!")
            return
        
        # Show payment dialog
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title(f"Receive Payment - {cust_name}")
        dialog.transient(self.parent)
        dialog.grab_set()
        center_window(dialog, 400, 650)
        
        ctk.CTkLabel(
            dialog,
            text=f"💵 Receive Payment",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=20)
        
        # Customer Info
        info_frame = ctk.CTkFrame(dialog)
        info_frame.pack(fill="x", padx=30, pady=10)
        
        ctk.CTkLabel(
            info_frame,
            text=f"Customer: {cust_name}",
            font=ctk.CTkFont(size=14)
        ).pack(pady=5)
        
        ctk.CTkLabel(
            info_frame,
            text=f"Total Spent: Rs. {total_spent:,.0f}",
            font=ctk.CTkFont(size=12),
            text_color="#2ECC71"
        ).pack(pady=2)
        
        ctk.CTkLabel(
            info_frame,
            text=f"Total Paid: Rs. {total_paid:,.0f}",
            font=ctk.CTkFont(size=12),
            text_color="#3498DB"
        ).pack(pady=2)
        
        ctk.CTkLabel(
            info_frame,
            text=f"Credit Due: Rs. {current_credit:,.0f}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#E74C3C"
        ).pack(pady=5)
        
        # Payment Amount
        ctk.CTkLabel(
            dialog,
            text="Amount Received (Rs.):",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", padx=30, pady=(20, 5))
        
        amount_entry = ctk.CTkEntry(
            dialog,
            placeholder_text="e.g., 500",
            width=250,
            height=35,
            font=ctk.CTkFont(size=14)
        )
        amount_entry.pack(padx=30, pady=5)
        
        # Quick amount buttons
        quick_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        quick_frame.pack(padx=30, pady=5)
        
        def set_amount(amt):
            amount_entry.delete(0, "end")
            amount_entry.insert(0, str(amt))
        
        # Common amounts
        for amt in [500, 1000, 2000]:
            ctk.CTkButton(
                quick_frame,
                text=f"Rs. {amt}",
                width=70,
                height=25,
                font=ctk.CTkFont(size=10),
                command=lambda a=amt: set_amount(a)
            ).pack(side="left", padx=3)
        
        # Pay Full Button
        ctk.CTkButton(
            quick_frame,
            text="Full",
            width=60,
            height=25,
            font=ctk.CTkFont(size=10),
            fg_color="#E67E22",
            command=lambda: set_amount(int(current_credit))
        ).pack(side="left", padx=3)
        
        # Payment Mode
        ctk.CTkLabel(
            dialog,
            text="Payment Mode:",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", padx=30, pady=(15, 5))
        
        payment_mode = ctk.CTkComboBox(
            dialog,
            values=["Cash", "Online Transfer", "Cheque"],
            width=250,
            height=35
        )
        payment_mode.pack(padx=30, pady=5)
        payment_mode.set("Cash")
        
        # Notes
        ctk.CTkLabel(
            dialog,
            text="Notes (Optional):",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", padx=30, pady=(15, 5))
        
        notes_entry = ctk.CTkEntry(
            dialog,
            placeholder_text="e.g., Partial payment",
            width=300,
            height=35
        )
        notes_entry.pack(padx=30, pady=5)
        
        def save_payment():
            try:
                amount = float(amount_entry.get().strip())
                if amount <= 0:
                    messagebox.showerror("Error", "Please enter valid amount!", parent=dialog)
                    return
                
            except ValueError:
                messagebox.showerror("Error", "Please enter valid number!", parent=dialog)
                return
            
            # Calculate new credit
            new_credit = current_credit - amount
            
            # Confirm
            msg = f"Receive Rs. {amount:,.0f} from {cust_name}?\n\nRemaining Credit: Rs. {new_credit:,.0f}"
            
            if not messagebox.askyesno("Confirm", msg, parent=dialog):
                return
            
            try:
                # Get next payment invoice number
                payment_invoice = self.get_next_invoice_number("PAY")
                
                # Create a payment record (negative sale = payment received)
                db.cursor.execute("""
                    INSERT INTO sales (invoice_number, customer_id, customer_name, total_amount, 
                                      discount, grand_total, payment_mode, is_credit, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    payment_invoice,
                    cust_id,
                    cust_name,
                    0,
                    0,
                    -amount,  # Negative amount = payment received
                    payment_mode.get(),
                    0,  # Not credit
                    datetime.now()
                ))
                
                db.conn.commit()
                
                success_msg = f"✅ Payment Received!\n\nAmount: Rs. {amount:,.0f}\nInvoice: {payment_invoice}\nRemaining Credit: Rs. {new_credit:,.0f}"
                messagebox.showinfo("Success", success_msg, parent=dialog)
                dialog.destroy()
                self.load_customers()  # Refresh the list
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save payment: {str(e)}", parent=dialog)
        
        # Buttons
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=30)
        
        ctk.CTkButton(
            btn_frame,
            text="💾 Save Payment",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2ECC71",
            command=save_payment,
            width=140,
            height=40
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=dialog.destroy,
            width=100,
            height=40
        ).pack(side="left", padx=10)
    
    def view_history(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select", "Please select a customer!")
            return
        
        item = self.tree.item(selected[0])
        cust_id = item["values"][0]
        cust_name = item["values"][1]
        
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title(f"Purchase History - {cust_name}")
        dialog.transient(self.parent)
        dialog.grab_set()
        center_window(dialog, 950, 650)
        
        ctk.CTkLabel(
            dialog,
            text=f"📋 Purchase History: {cust_name}",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=20)
        
        try:
            # Get all sales for this customer
            db.cursor.execute("""
                SELECT id, invoice_number, grand_total, payment_mode, is_credit, created_at
                FROM sales
                WHERE customer_id = ? AND grand_total != 0
                ORDER BY created_at ASC
            """, (cust_id,))
            sales = db.cursor.fetchall()
            
            if not sales:
                ctk.CTkLabel(dialog, text="No purchase history found.", text_color="gray").pack(pady=50)
                
                ctk.CTkButton(
                    dialog,
                    text="Close",
                    command=dialog.destroy,
                    width=100,
                    height=35
                ).pack(pady=15)
                return
            
            # Calculate totals using the same logic
            total_spent, total_paid, current_credit = self.get_customer_totals(cust_id)
            
            # Count purchases (positive amounts)
            total_purchases = len([s for s in sales if s[2] > 0])
            
            # Summary Frame
            summary_frame = ctk.CTkFrame(dialog)
            summary_frame.pack(fill="x", padx=20, pady=10)
            
            ctk.CTkLabel(summary_frame, text=f"Total Transactions: {len(sales)}", 
                        font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=15, pady=10)
            ctk.CTkLabel(summary_frame, text=f"Purchases: {total_purchases}", 
                        font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=15, pady=10)
            ctk.CTkLabel(summary_frame, text=f"Total Spent: Rs. {total_spent:,.0f}", 
                        font=ctk.CTkFont(size=14, weight="bold"), text_color="#2ECC71").pack(side="left", padx=15, pady=10)
            ctk.CTkLabel(summary_frame, text=f"Total Paid: Rs. {total_paid:,.0f}", 
                        font=ctk.CTkFont(size=14, weight="bold"), text_color="#3498DB").pack(side="left", padx=15, pady=10)
            ctk.CTkLabel(summary_frame, text=f"Current Credit: Rs. {current_credit:,.0f}", 
                        font=ctk.CTkFont(size=14, weight="bold"), 
                        text_color="#E74C3C" if current_credit > 0 else "#2ECC71").pack(side="left", padx=15, pady=10)
            
            # Create Treeview for detailed history
            columns = ("Date", "Invoice", "Details", "Type", "Amount", "Running Balance")
            history_tree = ttk.Treeview(dialog, columns=columns, show="headings", height=14)
            
            # Configure columns
            history_tree.heading("Date", text="Date")
            history_tree.heading("Invoice", text="Invoice #")
            history_tree.heading("Details", text="Details")
            history_tree.heading("Type", text="Type")
            history_tree.heading("Amount", text="Amount")
            history_tree.heading("Running Balance", text="Running Balance")
            
            history_tree.column("Date", width=100, anchor="center")
            history_tree.column("Invoice", width=120, anchor="center")
            history_tree.column("Details", width=280, anchor="w")
            history_tree.column("Type", width=80, anchor="center")
            history_tree.column("Amount", width=100, anchor="e")
            history_tree.column("Running Balance", width=120, anchor="e")
            
            # Scrollbar
            scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=history_tree.yview)
            history_tree.configure(yscrollcommand=scrollbar.set)
            
            # Pack
            history_tree.pack(side="left", fill="both", expand=True, padx=(20, 0), pady=10)
            scrollbar.pack(side="left", fill="y", pady=10)
            
            # Calculate running balance chronologically
            running_spent = 0
            running_paid = 0
            transactions = []
            
            for sale in sales:  # Process in chronological order (oldest first)
                sale_id, invoice, amount, payment, is_credit, date = sale
                date_str = date[:10] if isinstance(date, str) else date.strftime('%Y-%m-%d')
                
                # Determine type and update running totals
                if amount < 0:
                    # Payment received
                    running_paid += abs(amount)
                    type_text = "PAYMENT"
                    type_color = "#3498DB"
                    amount_text = f"Rs. {abs(amount):,.0f}"
                    details = "Payment Received"
                elif is_credit:
                    # Credit purchase
                    running_spent += amount
                    type_text = "CREDIT"
                    type_color = "#E74C3C"
                    amount_text = f"Rs. {amount:,.0f}"
                    details = "Purchase on Credit"
                else:
                    # Cash purchase
                    running_spent += amount
                    running_paid += amount  # Cash = paid immediately
                    type_text = "CASH"
                    type_color = "#2ECC71"
                    amount_text = f"Rs. {amount:,.0f}"
                    details = "Cash Purchase"
                
                # Calculate running balance (credit)
                running_balance = running_spent - running_paid
                
                transactions.append({
                    'date': date_str,
                    'invoice': invoice,
                    'details': details,
                    'type': type_text,
                    'amount': amount_text,
                    'balance': f"Rs. {running_balance:,.0f}",
                    'tag': type_text,
                    'sale_id': sale_id
                })
            
            # Display in reverse order (newest first)
            for trans in reversed(transactions):
                history_tree.insert("", "end", values=(
                    trans['date'],
                    trans['invoice'],
                    trans['details'],
                    trans['type'],
                    trans['amount'],
                    trans['balance']
                ), tags=(trans['tag'],))
            
            # Color tags
            history_tree.tag_configure("CREDIT", foreground="#E74C3C")
            history_tree.tag_configure("CASH", foreground="#2ECC71")
            history_tree.tag_configure("PAYMENT", foreground="#3498DB")
            
            # Double click to view invoice
            def on_history_click(event):
                selected = history_tree.selection()
                if selected:
                    item = history_tree.item(selected[0])
                    invoice_num = item["values"][1]
                    # Find sale data and show invoice
                    for sale in sales:
                        if sale[1] == invoice_num:
                            self.show_invoice(sale_id=sale[0])
                            break
            
            history_tree.bind("<Double-1>", on_history_click)
            
            # Buttons Frame
            btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
            btn_frame.pack(pady=15)
            
            # Save as PDF Button
            ctk.CTkButton(
                btn_frame,
                text="📄 Save as PDF",
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="#E67E22",
                hover_color="#D35400",
                command=lambda: self.save_credit_bill(cust_id, cust_name, transactions, current_credit),
                width=120,
                height=35
            ).pack(side="left", padx=5)
            
            ctk.CTkButton(
                btn_frame,
                text="Close",
                command=dialog.destroy,
                width=100,
                height=35
            ).pack(side="left", padx=5)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load history: {str(e)}", parent=dialog)
            dialog.destroy()
    
    def save_credit_bill(self, cust_id, cust_name, transactions, total_credit):
        """Generate and save PDF credit bill/statement"""
        if total_credit <= 0:
            messagebox.showinfo("Info", "No credit balance to save!")
            return
        
        # Ask for save location
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"Credit_Bill_{cust_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}"
        )
        
        if not filename:
            return
        
        try:
            # Create PDF
            doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=50, bottomMargin=50)
            elements = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor("#2C3E50"),
                spaceAfter=30,
                alignment=1  # Center
            )
            
            # Title
            elements.append(Paragraph("CREDIT STATEMENT", title_style))
            elements.append(Spacer(1, 20))
            
            # Customer Info
            info_data = [
                ["Customer Name:", cust_name],
                ["Statement Date:", datetime.now().strftime("%Y-%m-%d %H:%M")],
                ["Total Credit Due:", f"Rs. {total_credit:,.2f}"]
            ]
            
            info_table = Table(info_data, colWidths=[2*inch, 4*inch])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#ECF0F1")),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#BDC3C7")),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            elements.append(info_table)
            elements.append(Spacer(1, 30))
            
            # Transactions Table
            elements.append(Paragraph("Transaction Details", styles['Heading2']))
            elements.append(Spacer(1, 10))
            
            # Table headers
            table_data = [["Date", "Invoice #", "Description", "Type", "Amount", "Balance"]]
            
            # Add transactions (already in reverse order - newest first)
            for trans in transactions:
                table_data.append([
                    trans['date'],
                    trans['invoice'],
                    trans['details'],
                    trans['type'],
                    trans['amount'],
                    trans['balance']
                ])
            
            # Create table
            trans_table = Table(table_data, colWidths=[0.9*inch, 1.1*inch, 2.2*inch, 0.8*inch, 1*inch, 1*inch])
            trans_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#34495E")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),
                ('ALIGN', (1, 1), (1, -1), 'CENTER'),
                ('ALIGN', (2, 1), (2, -1), 'LEFT'),
                ('ALIGN', (3, 1), (3, -1), 'CENTER'),
                ('ALIGN', (4, 1), (5, -1), 'RIGHT'),
                
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F9FA")]),
            ]))
            
            elements.append(trans_table)
            elements.append(Spacer(1, 30))
            
            # Total Due Box
            total_data = [["TOTAL AMOUNT DUE:", f"Rs. {total_credit:,.2f}"]]
            total_table = Table(total_data, colWidths=[4*inch, 2*inch])
            total_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#E74C3C")),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
                ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 14),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ]))
            elements.append(total_table)
            
            # Footer
            elements.append(Spacer(1, 50))
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.gray,
                alignment=1
            )
            elements.append(Paragraph("Generated by JUDO Swat.", footer_style))
            
            # Build PDF
            doc.build(elements)
            
            messagebox.showinfo("Success", f"Credit bill saved successfully!\n\nLocation: {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save PDF: {str(e)}")
    
    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select", "Please select a customer to delete!")
            return
        
        item = self.tree.item(selected[0])
        cust_id = item["values"][0]
        cust_name = item["values"][1]
        
        # Check if customer has sales
        db.cursor.execute("SELECT COUNT(*) FROM sales WHERE customer_id=? AND grand_total != 0", (cust_id,))
        sale_count = db.cursor.fetchone()[0]
        
        if sale_count > 0:
            messagebox.showerror(
                "Cannot Delete", 
                f"'{cust_name}' has {sale_count} transaction(s).\nCannot delete customer with history."
            )
            return
        
        if messagebox.askyesno("Confirm", f"Delete customer '{cust_name}'?"):
            try:
                db.cursor.execute("DELETE FROM customers WHERE id=?", (cust_id,))
                db.conn.commit()
                messagebox.showinfo("Success", "Customer deleted!")
                self.load_customers()
            except Exception as e:
                messagebox.showerror("Error", f"Failed: {str(e)}")
