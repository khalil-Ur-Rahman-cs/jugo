import customtkinter as ctk
from tkinter import messagebox, ttk
from database import db
from datetime import datetime
from ui_utils import center_window


class InventoryManager:
    def __init__(self, parent_frame):
        self.parent = parent_frame
        self.setup_ui()
        self.load_flavors()
    
    def setup_ui(self):
        # Clear parent frame
        for widget in self.parent.winfo_children():
            widget.destroy()
        
        # Title
        title_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(
            title_frame,
            text="🥤 Juice Flavors Inventory",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(side="left")
        
        # Search Frame
        search_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=10)
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Search flavor...",
            width=300,
            height=35,
            font=ctk.CTkFont(size=12)
        )
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", lambda e: self.search_flavors())
        
        ctk.CTkButton(
            search_frame,
            text="🔍 Search",
            width=100,
            height=35,
            command=self.search_flavors
        ).pack(side="left")
        
        # Stats Frame
        stats_frame = ctk.CTkFrame(self.parent)
        stats_frame.pack(fill="x", padx=20, pady=10)
        
        self.total_label = ctk.CTkLabel(
            stats_frame,
            text="Total Flavors: 0",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.total_label.pack(side="left", padx=20, pady=10)
        
        self.stock_label = ctk.CTkLabel(
            stats_frame,
            text="Total Stock: 0 BOX",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#3498DB"
        )
        self.stock_label.pack(side="left", padx=20, pady=10)
        
        self.low_stock_label = ctk.CTkLabel(
            stats_frame,
            text="Low Stock: 0",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#E74C3C"
        )
        self.low_stock_label.pack(side="left", padx=20, pady=10)
        
        # Table Frame
        table_frame = ctk.CTkFrame(self.parent)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Treeview (Table)
        columns = ("ID", "Name", "Category", "Sale Price", "Cost Price", "Stock", "Status")
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
        self.tree.column("Category", width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Double click to edit
        self.tree.bind("<Double-1>", self.on_item_double_click)
        
        # Action Buttons Frame
        action_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        action_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(
            action_frame,
            text="📥 Stock In",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#3498DB",
            hover_color="#2980B9",
            command=self.show_stock_in_dialog,
            width=120,
            height=35
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            action_frame,
            text="📤 Stock Out",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#E67E22",
            hover_color="#D35400",
            command=self.show_stock_out_dialog,
            width=120,
            height=35
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            action_frame,
            text="✏️ Edit Selected",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#9B59B6",
            hover_color="#8E44AD",
            command=self.edit_selected,
            width=120,
            height=35
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            action_frame,
            text="🗑️ Delete",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#E74C3C",
            hover_color="#C0392B",
            command=self.delete_selected,
            width=120,
            height=35
        ).pack(side="left", padx=5)
    
    def load_flavors(self):
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Load from database
        db.cursor.execute("SELECT id, name, category, sale_price, cost_price, stock FROM flavors ORDER BY name")
        flavors = db.cursor.fetchall()
        
        total_stock = 0
        low_stock_count = 0
        
        for flavor in flavors:
            id, name, category, sale_price, cost_price, stock = flavor
            
            # Status determine karein
            if stock <= 0:
                status = "❌ Out of Stock"
                tag = "out"
            elif stock < 20:
                status = "⚠️ Low Stock"
                tag = "low"
            else:
                status = "✅ Available"
                tag = "ok"
            
            if stock < 20:
                low_stock_count += 1
            
            total_stock += stock
            
            self.tree.insert("", "end", values=(
                id, name, category, f"Rs. {sale_price}", 
                f"Rs. {cost_price}", f"{stock} BOX", status
            ), tags=(tag,))
        
        # Configure tags for colors
        self.tree.tag_configure("out", foreground="#E74C3C")
        self.tree.tag_configure("low", foreground="#E67E22")
        self.tree.tag_configure("ok", foreground="#27AE60")
        
        # Update stats
        self.total_label.configure(text=f"Total Flavors: {len(flavors)}")
        self.stock_label.configure(text=f"Total Stock: {total_stock} BOX")
        self.low_stock_label.configure(text=f"Low Stock: {low_stock_count}")
    
    def search_flavors(self):
        search_term = self.search_entry.get().strip().lower()
        
        for item in self.tree.get_children():
            values = self.tree.item(item)["values"]
            if search_term in str(values[1]).lower():  # Name column
                self.tree.selection_set(item)
                self.tree.see(item)
                return
        
        if search_term:
            messagebox.showinfo("Search", f"No flavor found with name: {search_term}")
    
    def show_add_flavor_dialog(self):
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Add New Flavor")
        dialog.transient(self.parent)
        dialog.grab_set()
        center_window(dialog, 400, 600)
        
        ctk.CTkLabel(
            dialog,
            text="Add New Juice Flavor",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=20)
        
        # Form fields
        fields_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        fields_frame.pack(padx=30, fill="x")
        
        # Name
        ctk.CTkLabel(fields_frame, text="Flavor Name *", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 5))
        name_entry = ctk.CTkEntry(fields_frame, placeholder_text="e.g., Mango", height=35)
        name_entry.pack(fill="x")
        
        # Category
        ctk.CTkLabel(fields_frame, text="Category", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 5))
        category_combo = ctk.CTkComboBox(
            fields_frame,
            values=["Citrus", "Tropical", "Berry", "Classic", "Seasonal", "Special"],
            height=35
        )
        category_combo.pack(fill="x")
        category_combo.set("Tropical")
        
        # Sale Price
        ctk.CTkLabel(fields_frame, text="Sale Price (Rs.) *", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 5))
        sale_price_entry = ctk.CTkEntry(fields_frame, placeholder_text="e.g., 120", height=35)
        sale_price_entry.pack(fill="x")
        
        # Cost Price
        ctk.CTkLabel(fields_frame, text="Cost Price (Rs.) *", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 5))
        cost_price_entry = ctk.CTkEntry(fields_frame, placeholder_text="e.g., 80", height=35)
        cost_price_entry.pack(fill="x")
        
        # Initial Stock
        ctk.CTkLabel(fields_frame, text="Initial Stock (BOX)", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 5))
        stock_entry = ctk.CTkEntry(fields_frame, placeholder_text="e.g., 50", height=35)
        stock_entry.pack(fill="x")
        stock_entry.insert(0, "0")
        
        def save_flavor():
            name = name_entry.get().strip()
            category = category_combo.get()
            sale_price = sale_price_entry.get().strip()
            cost_price = cost_price_entry.get().strip()
            stock = stock_entry.get().strip()
            
            # Validation
            if not name or not sale_price or not cost_price:
                messagebox.showerror("Error", "Please fill all required fields!", parent=dialog)
                return
            
            try:
                sale_price = float(sale_price)
                cost_price = float(cost_price)
                stock = int(stock) if stock else 0
            except ValueError:
                messagebox.showerror("Error", "Please enter valid numbers!", parent=dialog)
                return
            
            # Insert to database
            try:
                db.cursor.execute('''
                    INSERT INTO flavors (name, category, sale_price, cost_price, stock, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (name, category, sale_price, cost_price, stock, datetime.now()))
                db.conn.commit()
                
                # Stock movement record
                if stock > 0:
                    flavor_id = db.cursor.lastrowid
                    db.cursor.execute('''
                        INSERT INTO stock_movements (flavor_id, type, quantity, notes, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (flavor_id, 'in', stock, 'Initial stock', datetime.now()))
                    db.conn.commit()
                
                messagebox.showinfo("Success", f"Flavor '{name}' added successfully!", parent=dialog)
                dialog.destroy()
                self.load_flavors()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add flavor: {str(e)}", parent=dialog)
        
        # Buttons
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=30)
        
        ctk.CTkButton(
            btn_frame,
            text="💾 Save",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2ECC71",
            hover_color="#27AE60",
            command=save_flavor,
            width=120,
            height=35
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="❌ Cancel",
            font=ctk.CTkFont(size=14),
            fg_color="#95A5A6",
            hover_color="#7F8C8D",
            command=dialog.destroy,
            width=120,
            height=35
        ).pack(side="left", padx=10)
    
    def show_stock_in_dialog(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select", "Please select a flavor first!")
            return
        
        item = self.tree.item(selected[0])
        flavor_id = item["values"][0]
        flavor_name = item["values"][1]
        current_stock = int(item["values"][5].split()[0])
        
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Stock In")
        dialog.transient(self.parent)
        dialog.grab_set()
        center_window(dialog, 350, 400)
        
        ctk.CTkLabel(
            dialog,
            text=f"📥 Stock In: {flavor_name}",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=20)
        
        ctk.CTkLabel(dialog, text=f"Current Stock: {current_stock} BOX").pack()
        
        ctk.CTkLabel(dialog, text="Quantity to Add *", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=30, pady=(20, 5))
        qty_entry = ctk.CTkEntry(dialog, placeholder_text="e.g., 50", height=35, width=250)
        qty_entry.pack()
        
        ctk.CTkLabel(dialog, text="Notes", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=30, pady=(15, 5))
        notes_entry = ctk.CTkEntry(dialog, placeholder_text="e.g., New production", height=35, width=250)
        notes_entry.pack()
        
        def add_stock():
            try:
                qty = int(qty_entry.get().strip())
                if qty <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Please enter valid quantity!", parent=dialog)
                return
            
            notes = notes_entry.get().strip() or "Stock added"
            
            try:
                # Update stock
                db.cursor.execute("UPDATE flavors SET stock = stock + ? WHERE id = ?", (qty, flavor_id))
                
                # Record movement
                db.cursor.execute('''
                    INSERT INTO stock_movements (flavor_id, type, quantity, notes, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (flavor_id, 'in', qty, notes, datetime.now()))
                
                db.conn.commit()
                
                messagebox.showinfo("Success", f"Added {qty} BOX to {flavor_name}!", parent=dialog)
                dialog.destroy()
                self.load_flavors()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed: {str(e)}", parent=dialog)
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=30)
        
        ctk.CTkButton(
            btn_frame,
            text="➕ Add Stock",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2ECC71",
            command=add_stock,
            width=120,
            height=35
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=dialog.destroy,
            width=100,
            height=35
        ).pack(side="left", padx=10)
    
    def show_stock_out_dialog(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select", "Please select a flavor first!")
            return
        
        item = self.tree.item(selected[0])
        flavor_id = item["values"][0]
        flavor_name = item["values"][1]
        current_stock = int(item["values"][5].split()[0])
        
        if current_stock <= 0:
            messagebox.showerror("Error", "No stock available!")
            return
        
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Stock Out")
        dialog.transient(self.parent)
        dialog.grab_set()
        center_window(dialog, 350, 400)
        
        ctk.CTkLabel(
            dialog,
            text=f"📤 Stock Out: {flavor_name}",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=20)
        
        ctk.CTkLabel(dialog, text=f"Current Stock: {current_stock} BOX", text_color="#3498DB").pack()
        
        ctk.CTkLabel(dialog, text="Quantity to Remove *", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=30, pady=(20, 5))
        qty_entry = ctk.CTkEntry(dialog, placeholder_text="e.g., 10", height=35, width=250)
        qty_entry.pack()
        
        ctk.CTkLabel(dialog, text="Reason", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=30, pady=(15, 5))
        reason_entry = ctk.CTkEntry(dialog, placeholder_text="e.g., Damaged, Expired", height=35, width=250)
        reason_entry.pack()
        
        def remove_stock():
            try:
                qty = int(qty_entry.get().strip())
                if qty <= 0:
                    raise ValueError
                if qty > current_stock:
                    messagebox.showerror("Error", f"Cannot remove more than {current_stock} BOX!", parent=dialog)
                    return
            except ValueError:
                messagebox.showerror("Error", "Please enter valid quantity!", parent=dialog)
                return
            
            reason = reason_entry.get().strip() or "Stock removed"
            
            try:
                # Update stock
                db.cursor.execute("UPDATE flavors SET stock = stock - ? WHERE id = ?", (qty, flavor_id))
                
                # Record movement
                db.cursor.execute('''
                    INSERT INTO stock_movements (flavor_id, type, quantity, notes, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (flavor_id, 'out', qty, reason, datetime.now()))
                
                db.conn.commit()
                
                messagebox.showinfo("Success", f"Removed {qty} BOX from {flavor_name}!", parent=dialog)
                dialog.destroy()
                self.load_flavors()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed: {str(e)}", parent=dialog)
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=30)
        
        ctk.CTkButton(
            btn_frame,
            text="➖ Remove Stock",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#E67E22",
            command=remove_stock,
            width=130,
            height=35
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=dialog.destroy,
            width=100,
            height=35
        ).pack(side="left", padx=10)
    
    def on_item_double_click(self, event):
        self.edit_selected()
    
    def edit_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select", "Please select a flavor to edit!")
            return
        
        item = self.tree.item(selected[0])
        values = item["values"]
        flavor_id = values[0]
        
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title(f"Edit: {values[1]}")
        dialog.transient(self.parent)
        dialog.grab_set()
        center_window(dialog, 400, 600)
        
        ctk.CTkLabel(
            dialog,
            text=f"✏️ Edit Flavor",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=20)
        
        fields_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        fields_frame.pack(padx=30, fill="x")
        
        # Name
        ctk.CTkLabel(fields_frame, text="Flavor Name", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 5))
        name_entry = ctk.CTkEntry(fields_frame, height=35)
        name_entry.pack(fill="x")
        name_entry.insert(0, values[1])
        
        # Category
        ctk.CTkLabel(fields_frame, text="Category", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 5))
        category_combo = ctk.CTkComboBox(
            fields_frame,
            values=["Citrus", "Tropical", "Berry", "Classic", "Seasonal", "Special"],
            height=35
        )
        category_combo.pack(fill="x")
        category_combo.set(values[2])
        
        # Sale Price
        ctk.CTkLabel(fields_frame, text="Sale Price (Rs.)", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 5))
        sale_price_entry = ctk.CTkEntry(fields_frame, height=35)
        sale_price_entry.pack(fill="x")
        sale_price_entry.insert(0, values[3].replace("Rs. ", ""))
        
        # Cost Price
        ctk.CTkLabel(fields_frame, text="Cost Price (Rs.)", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 5))
        cost_price_entry = ctk.CTkEntry(fields_frame, height=35)
        cost_price_entry.pack(fill="x")
        cost_price_entry.insert(0, values[4].replace("Rs. ", ""))
        
        def save_changes():
            name = name_entry.get().strip()
            category = category_combo.get()
            sale_price = sale_price_entry.get().strip()
            cost_price = cost_price_entry.get().strip()
            
            if not name or not sale_price or not cost_price:
                messagebox.showerror("Error", "Please fill all fields!", parent=dialog)
                return
            
            try:
                sale_price = float(sale_price)
                cost_price = float(cost_price)
            except ValueError:
                messagebox.showerror("Error", "Please enter valid prices!", parent=dialog)
                return
            
            try:
                db.cursor.execute('''
                    UPDATE flavors 
                    SET name=?, category=?, sale_price=?, cost_price=?
                    WHERE id=?
                ''', (name, category, sale_price, cost_price, flavor_id))
                db.conn.commit()
                
                messagebox.showinfo("Success", "Flavor updated successfully!", parent=dialog)
                dialog.destroy()
                self.load_flavors()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed: {str(e)}", parent=dialog)
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=30)
        
        ctk.CTkButton(
            btn_frame,
            text="💾 Save Changes",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2ECC71",
            command=save_changes,
            width=140,
            height=35
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=dialog.destroy,
            width=100,
            height=35
        ).pack(side="left", padx=10)
    
    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select", "Please select a flavor to delete!")
            return
        
        item = self.tree.item(selected[0])
        flavor_id = item["values"][0]
        flavor_name = item["values"][1]
        
        if messagebox.askyesno("Confirm", f"Are you sure you want to delete '{flavor_name}'?\n\nThis action cannot be undone!"):
            try:
                db.cursor.execute("DELETE FROM flavors WHERE id=?", (flavor_id,))
                db.conn.commit()
                messagebox.showinfo("Success", f"'{flavor_name}' deleted successfully!")
                self.load_flavors()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete: {str(e)}")
