import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime, date
from database import db


class ExpensesManager:
    def __init__(self, parent_frame=None, main_window=None):
        self.parent = parent_frame
        self.main_window = main_window
        
        # Colors - Same as JUGO dashboard
        self.colors = {
            "primary": "#F58220",
            "secondary": "#D63366",
            "sidebar_bg": "#1E293B",
            "content_bg": "#F1F5F9",
            "card_bg": "#FFFFFF",
            "border": "#E2E8F0",
            "text_primary": "#0F172A",
            "text_secondary": "#64748B",
            "success": "#2ECC71",
            "error": "#E74C3C",
            "warning": "#F39C12",
            "hover": "#27AE60"
        }
        
        # Default expense categories
        self.categories = [
            "Petrol",
            "Food",
            "Electricity",
            "Rent",
            "Maintenance",
            "Staff Salary",
            "Other"
        ]
        
        self.expenses = self.load_expenses()
        
        if parent_frame:
            self.setup_ui()
            
    def load_expenses(self):
        """Load expenses from database"""
        try:
            db.cursor.execute("""
                SELECT id, date, category, amount, notes, created_at
                FROM expenses
                ORDER BY date DESC, id DESC
            """)
            rows = db.cursor.fetchall()
            expenses = []
            for row in rows:
                exp_id, date_str, category, amount, notes, created_at = row
                expenses.append({
                    "id": exp_id,
                    "date": date_str or "",
                    "category": category or "",
                    "description": notes or "-",
                    "amount": float(amount or 0),
                    "created_at": created_at,
                })
            return expenses
        except Exception:
            return []
            
    def setup_ui(self):
        """Setup the expenses page UI"""
        # Clear parent frame
        for widget in self.parent.winfo_children():
            widget.destroy()
            
        self.parent.configure(fg_color=self.colors["content_bg"])
        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_rowconfigure(1, weight=1)
        
        # Header Section
        self.setup_header()
        
        # Main Content
        self.setup_content()
        
        # Refresh display
        self.refresh_expenses_list()
        
    def setup_header(self):
        """Setup page header with summary cards"""
        header_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        header_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        # Get today's stats
        today = date.today().isoformat()
        today_expenses = self.get_total_for_date(today)
        month_expenses = self.get_month_total()
        total_expenses = sum(float(e["amount"]) for e in self.expenses)
        
        # Card 1: Today's Expenses
        self.create_summary_card(
            header_frame, 
            "Today's Expenses", 
            f"Rs. {today_expenses:,.0f}", 
            self.colors["error"],
            0, 0
        )
        
        # Card 2: This Month
        self.create_summary_card(
            header_frame, 
            "This Month", 
            f"Rs. {month_expenses:,.0f}", 
            self.colors["warning"],
            0, 1
        )
        
        # Card 3: Total All Time
        self.create_summary_card(
            header_frame, 
            "Total Expenses", 
            f"Rs. {total_expenses:,.0f}", 
            self.colors["primary"],
            0, 2
        )
        
        # Card 4: Net Profit (placeholder - will be updated from sales)
        self.net_profit_label = self.create_summary_card(
            header_frame, 
            "Net Profit (Est.)", 
            "Rs. 0", 
            self.colors["success"],
            0, 3,
            is_profit=True
        )
        
    def create_summary_card(self, parent, title, value, color, row, col, is_profit=False):
        """Create a summary card"""
        card = ctk.CTkFrame(
            parent,
            fg_color="white",
            corner_radius=15,
            border_width=1,
            border_color=self.colors["border"]
        )
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_secondary"]
        ).pack(anchor="w", padx=20, pady=(20, 5))
        
        label = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=color
        )
        label.pack(anchor="w", padx=20, pady=(5, 20))
        
        if is_profit:
            return label
        return None
        
    def setup_content(self):
        """Setup main content area"""
        content_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        content_frame.grid_columnconfigure(0, weight=2)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        
        # Left: Expenses List
        self.setup_expenses_list(content_frame)
        
        # Right: Add Expense Form
        self.setup_add_form(content_frame)
        
    def setup_expenses_list(self, parent):
        """Setup the expenses list/table"""
        list_frame = ctk.CTkFrame(
            parent,
            fg_color="white",
            corner_radius=15,
            border_width=1,
            border_color=self.colors["border"]
        )
        list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        list_frame.grid_rowconfigure(1, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Header with filter and View All button
        header = ctk.CTkFrame(list_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        
        ctk.CTkLabel(
            header,
            text="Expenses List",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors["text_primary"]
        ).pack(side="left")
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(header, fg_color="transparent")
        buttons_frame.pack(side="right")
        
        # View All Button
        ctk.CTkButton(
            buttons_frame,
            text="View All →",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=self.colors["primary"],
            hover_color=self.colors["hover"],
            width=120,
            height=35,
            corner_radius=8,
            command=self.open_view_all_window
        ).pack(side="left", padx=(0, 10))
        
        # Filter by date
        self.date_filter = ctk.CTkOptionMenu(
            buttons_frame,
            values=["All Time", "Today", "This Week", "This Month"],
            font=ctk.CTkFont(size=12),
            width=150,
            command=self.filter_expenses
        )
        self.date_filter.pack(side="left")
        self.date_filter.set("All Time")
        
        # Treeview for expenses
        columns = ("date", "category", "description", "amount", "actions")
        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=15
        )
        
        # Style the treeview
        style = ttk.Style()
        style.configure("Expenses.Treeview",
                       background="white",
                       foreground=self.colors["text_primary"],
                       rowheight=40,
                       fieldbackground="white")
        style.configure("Expenses.Treeview.Heading",
                       background=self.colors["sidebar_bg"],
                       foreground="white",
                       font=('Segoe UI', 11, 'bold'))
        style.map("Expenses.Treeview",
                 background=[('selected', self.colors["primary"])],
                 foreground=[('selected', 'white')])
        
        self.tree.configure(style="Expenses.Treeview")
        
        # Define columns
        self.tree.heading("date", text="Date")
        self.tree.heading("category", text="Category")
        self.tree.heading("description", text="Description")
        self.tree.heading("amount", text="Amount")
        self.tree.heading("actions", text="Actions")
        
        self.tree.column("date", width=100)
        self.tree.column("category", width=120)
        self.tree.column("description", width=200)
        self.tree.column("amount", width=100)
        self.tree.column("actions", width=80, anchor="center")
        
        self.tree.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        
        # Scrollbar
        scrollbar = ctk.CTkScrollbar(list_frame, command=self.tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns", pady=(0, 20))
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # ✅ NEW: Bind click event for delete button only
        self.tree.bind('<ButtonRelease-1>', self.on_item_click)
        
    def on_item_click(self, event):
        """Handle click - only delete when clicking on actions column"""
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
            
        column = self.tree.identify_column(event.x)
        item = self.tree.identify_row(event.y)
        
        # Column #5 is "actions" column (Delete button)
        if column == "#5" and item:
            try:
                item_id = self.tree.item(item, "tags")[0]
                self.delete_expense(item_id)
            except IndexError:
                pass
    
    def delete_expense(self, item_id):
        """Delete expense with confirmation"""
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this expense?"):
            try:
                db.cursor.execute("DELETE FROM expenses WHERE id = ?", (item_id,))
                db.conn.commit()
                
                # Reload and refresh
                self.expenses = self.load_expenses()
                self.refresh_expenses_list()
                self.setup_header()  # Refresh totals
                self.notify_dashboard_refresh()
                
                messagebox.showinfo("Success", "Expense deleted successfully!")
                return True
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete expense: {str(e)}")
                return False
        return False
        
    def open_view_all_window(self):
        """Open new window with all expenses"""
        view_window = ctk.CTkToplevel(self.parent)
        view_window.title("All Expenses - JUGO SWAT")
        view_window.geometry("1000x700")
        view_window.configure(fg_color=self.colors["content_bg"])
        
        # Header
        header = ctk.CTkFrame(view_window, fg_color="white", corner_radius=0)
        header.pack(fill="x", padx=0, pady=0)
        
        ctk.CTkLabel(
            header,
            text="All Expenses History",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.colors["text_primary"]
        ).pack(pady=20)
        
        # Summary label
        total_count = len(self.expenses)
        total_amount = sum(float(e["amount"]) for e in self.expenses)
        
        ctk.CTkLabel(
            header,
            text=f"Total Records: {total_count}  |  Total Amount: Rs. {total_amount:,.0f}",
            font=ctk.CTkFont(size=14),
            text_color=self.colors["text_secondary"]
        ).pack(pady=(0, 20))
        
        # Treeview frame
        tree_frame = ctk.CTkFrame(view_window, fg_color="white", corner_radius=15)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Columns
        columns = ("date", "category", "description", "amount", "actions")
        tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            height=20
        )
        
        # Style
        style = ttk.Style()
        style.configure("ViewAll.Treeview",
                       background="white",
                       foreground=self.colors["text_primary"],
                       rowheight=40,
                       fieldbackground="white")
        style.configure("ViewAll.Treeview.Heading",
                       background=self.colors["sidebar_bg"],
                       foreground="white",
                       font=('Segoe UI', 11, 'bold'))
        style.map("ViewAll.Treeview",
                 background=[('selected', self.colors["primary"])],
                 foreground=[('selected', 'white')])
        
        tree.configure(style="ViewAll.Treeview")
        
        # Headings
        tree.heading("date", text="Date")
        tree.heading("category", text="Category")
        tree.heading("description", text="Description")
        tree.heading("amount", text="Amount")
        tree.heading("actions", text="Delete")
        
        tree.column("date", width=120)
        tree.column("category", width=150)
        tree.column("description", width=300)
        tree.column("amount", width=120)
        tree.column("actions", width=100, anchor="center")
        
        # Add all expenses sorted by date
        sorted_expenses = sorted(self.expenses, key=lambda x: x["date"], reverse=True)
        
        for exp in sorted_expenses:
            tree.insert("", "end", values=(
                exp["date"],
                exp["category"],
                exp["description"],
                f"Rs. {float(exp['amount']):,.0f}",
                "🗑️ Delete"
            ), tags=(str(exp["id"]),))
        
        tree.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Scrollbar
        scrollbar = ctk.CTkScrollbar(tree_frame, command=tree.yview)
        scrollbar.pack(side="right", fill="y", padx=(0, 20), pady=20)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Bind delete for this tree
        tree.bind('<ButtonRelease-1>', 
                 lambda e, t=tree, w=view_window: self.on_view_all_click(e, t, w))
        
        # Close button
        ctk.CTkButton(
            view_window,
            text="Close",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.colors["error"],
            hover_color="#C0392B",
            width=150,
            height=40,
            corner_radius=10,
            command=view_window.destroy
        ).pack(pady=(0, 20))
        
    def on_view_all_click(self, event, tree, window):
        """Handle delete in view all window"""
        region = tree.identify("region", event.x, event.y)
        if region != "cell":
            return
            
        column = tree.identify_column(event.x)
        item = tree.identify_row(event.y)
        
        if column == "#5" and item:
            try:
                item_id = tree.item(item, "tags")[0]
                if self.delete_expense(item_id):
                    tree.delete(item)  # Remove from view window
                    
                    # Update summary
                    window.destroy()
                    self.open_view_all_window()  # Refresh window
            except IndexError:
                pass
        
    def setup_add_form(self, parent):
        """Setup the add expense form"""
        form_frame = ctk.CTkFrame(
            parent,
            fg_color="white",
            corner_radius=15,
            border_width=1,
            border_color=self.colors["border"]
        )
        form_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        ctk.CTkLabel(
            form_frame,
            text="Add New Expense",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors["text_primary"]
        ).pack(anchor="w", padx=20, pady=20)
        
        # Date
        ctk.CTkLabel(
            form_frame,
            text="Date",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_secondary"]
        ).pack(anchor="w", padx=20, pady=(10, 5))
        
        self.date_entry = ctk.CTkEntry(
            form_frame,
            font=ctk.CTkFont(size=14),
            height=40,
            placeholder_text="YYYY-MM-DD"
        )
        self.date_entry.pack(fill="x", padx=20)
        self.date_entry.insert(0, date.today().isoformat())
        
        # Category
        ctk.CTkLabel(
            form_frame,
            text="Category",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_secondary"]
        ).pack(anchor="w", padx=20, pady=(15, 5))
        
        self.category_combo = ctk.CTkOptionMenu(
            form_frame,
            values=self.categories,
            font=ctk.CTkFont(size=14),
            height=40
        )
        self.category_combo.pack(fill="x", padx=20)
        
        # Description
        ctk.CTkLabel(
            form_frame,
            text="Description",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_secondary"]
        ).pack(anchor="w", padx=20, pady=(15, 5))
        
        self.desc_entry = ctk.CTkEntry(
            form_frame,
            font=ctk.CTkFont(size=14),
            height=40,
            placeholder_text="Enter details..."
        )
        self.desc_entry.pack(fill="x", padx=20)
        
        # Amount
        ctk.CTkLabel(
            form_frame,
            text="Amount (Rs.)",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_secondary"]
        ).pack(anchor="w", padx=20, pady=(15, 5))
        
        self.amount_entry = ctk.CTkEntry(
            form_frame,
            font=ctk.CTkFont(size=14),
            height=40,
            placeholder_text="0.00"
        )
        self.amount_entry.pack(fill="x", padx=20)
        
        # Add Button
        ctk.CTkButton(
            form_frame,
            text="➕ Add Expense",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.colors["success"],
            hover_color=self.colors["hover"],
            height=45,
            corner_radius=10,
            command=self.add_expense
        ).pack(fill="x", padx=20, pady=30)
        
        # Quick Add Buttons
        quick_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        quick_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkLabel(
            quick_frame,
            text="Quick Add:",
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text_secondary"]
        ).pack(anchor="w", pady=(0, 10))
        
        quick_expenses = [
            ("🛵 Petrol", "Petrol"),
            ("🍔 Food", "Food"),
            ("⚡ Electric", "Electricity")
        ]
        
        for text, cat in quick_expenses:
            btn = ctk.CTkButton(
                quick_frame,
                text=text,
                font=ctk.CTkFont(size=12),
                fg_color=self.colors["content_bg"],
                text_color=self.colors["text_primary"],
                hover_color=self.colors["border"],
                height=35,
                corner_radius=8,
                command=lambda c=cat: self.quick_add(c)
            )
            btn.pack(fill="x", pady=3)
            
    def add_expense(self):
        """Add new expense"""
        try:
            date_str = self.date_entry.get().strip()
            category = self.category_combo.get()
            description = self.desc_entry.get().strip()
            amount = self.amount_entry.get().strip()
            
            # Validation
            if not all([date_str, category, amount]):
                messagebox.showerror("Error", "Please fill all required fields!")
                return
                
            try:
                float(amount)
            except ValueError:
                messagebox.showerror("Error", "Amount must be a number!")
                return

            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD.")
                return

            # Save to database
            db.cursor.execute(
                """
                INSERT INTO expenses (date, category, amount, payment_mode, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (date_str, category, float(amount), "Cash", description or "-", datetime.now()),
            )
            db.conn.commit()
            
            # Clear form
            self.desc_entry.delete(0, 'end')
            self.amount_entry.delete(0, 'end')
            
            # Refresh display
            self.expenses = self.load_expenses()
            self.refresh_expenses_list()
            self.setup_header()  # Refresh totals
            self.notify_dashboard_refresh()
            
            messagebox.showinfo("Success", "Expense added successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add expense: {str(e)}")
            
    def quick_add(self, category):
        """Quick add with preset category"""
        self.category_combo.set(category)
        self.desc_entry.focus()
        
    def refresh_expenses_list(self, filter_type="All Time"):
        """Refresh the expenses treeview"""
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Filter expenses
        filtered = self.get_filtered_expenses(filter_type)
        
        # Sort by date (newest first)
        filtered.sort(key=lambda x: x["date"], reverse=True)
        
        # Add to treeview
        for exp in filtered:
            self.tree.insert("", "end", values=(
                exp["date"],
                exp["category"],
                exp["description"],
                f"Rs. {float(exp['amount']):,.0f}",
                "🗑️ Delete"
            ), tags=(str(exp["id"]),))
            
    def get_filtered_expenses(self, filter_type):
        """Get filtered expenses based on filter type"""
        if filter_type == "All Time":
            return self.expenses
            
        today = date.today()
        
        if filter_type == "Today":
            today_str = today.isoformat()
            return [e for e in self.expenses if e["date"] == today_str]
            
        elif filter_type == "This Week":
            from datetime import timedelta
            week_ago = (today - timedelta(days=7)).isoformat()
            return [e for e in self.expenses if e["date"] >= week_ago]
            
        elif filter_type == "This Month":
            month_start = today.replace(day=1).isoformat()
            return [e for e in self.expenses if e["date"] >= month_start]
            
        return self.expenses
        
    def filter_expenses(self, choice):
        """Handle filter change"""
        self.refresh_expenses_list(choice)
            
    def get_total_for_date(self, date_str):
        """Get total expenses for a specific date"""
        total = sum(float(e["amount"]) for e in self.expenses if e["date"] == date_str)
        return total
        
    def get_month_total(self):
        """Get total for current month"""
        today = date.today()
        month_start = today.replace(day=1).isoformat()
        total = sum(float(e["amount"]) for e in self.expenses if e["date"] >= month_start)
        return total
        
    def get_today_total(self):
        """Get today's total expenses"""
        today = date.today().isoformat()
        return self.get_total_for_date(today)
        
    def update_net_profit(self, today_sales):
        """Update net profit display (call this from dashboard with today's sales)"""
        today_expenses = self.get_today_total()
        net_profit = today_sales - today_expenses
        
        if hasattr(self, 'net_profit_label'):
            color = self.colors["success"] if net_profit >= 0 else self.colors["error"]
            self.net_profit_label.configure(
                text=f"Rs. {net_profit:,.0f}",
                text_color=color
            )
            
        return net_profit
        
    def get_expenses_summary(self, date_str=None):
        """Get summary for a date (for dashboard integration)"""
        if date_str is None:
            date_str = date.today().isoformat()
            
        day_expenses = self.get_total_for_date(date_str)
        month_expenses = self.get_month_total()
        
        return {
            "today": day_expenses,
            "month": month_expenses,
            "total": sum(float(e["amount"]) for e in self.expenses),
            "count": len([e for e in self.expenses if e["date"] == date_str])
        }


# Standalone test
if __name__ == "__main__":
    root = ctk.CTk()
    root.title("Expenses Manager - JUGO SWAT")
    root.geometry("1200x900")
    
    # Main container
    main_frame = ctk.CTkFrame(root, fg_color="#F1F5F9")
    main_frame.pack(fill="both", expand=True)
    
    app = ExpensesManager(parent_frame=main_frame)
    root.mainloop()