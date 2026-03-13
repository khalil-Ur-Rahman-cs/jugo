import customtkinter as ctk
from tkinter import messagebox, filedialog
from database import db
import shutil
import os
import sys
from datetime import datetime
from ui_utils import center_window


class SettingsManager:
    def __init__(self, parent_frame):
        self.parent = parent_frame
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        # Clear parent
        for widget in self.parent.winfo_children():
            widget.destroy()
        
        # Title
        ctk.CTkLabel(
            self.parent,
            text="⚙️ Settings & Backup",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(pady=(20, 10))
        
        # Create tabs
        tab_frame = ctk.CTkFrame(self.parent)
        tab_frame.pack(fill="x", padx=20, pady=10)
        
        self.tab_buttons = []
        tabs = [
            ("Business Info", self.show_business_info),
            ("Security", self.show_security),
            ("Backup & Restore", self.show_backup),
        ]
        
        for i, (text, command) in enumerate(tabs):
            btn = ctk.CTkButton(
                tab_frame,
                text=text,
                font=ctk.CTkFont(size=12),
                width=150,
                height=35,
                command=lambda c=command, idx=i: self.switch_tab(c, idx)
            )
            btn.pack(side="left", padx=5, pady=10)
            self.tab_buttons.append(btn)
        
        # Content frame
        self.content_frame = ctk.CTkFrame(self.parent)
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Show first tab
        self.switch_tab(self.show_business_info, 0)
    
    def switch_tab(self, command, active_idx):
        # Update button colors
        for i, btn in enumerate(self.tab_buttons):
            if i == active_idx:
                btn.configure(fg_color="#2ECC71", text_color="white")
            else:
                btn.configure(fg_color=("gray85", "gray25"), text_color=("gray10", "gray90"))
        
        # Show content
        command()
    
    def show_business_info(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        ctk.CTkLabel(
            self.content_frame,
            text="Business Information",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(20, 10))
        
        # Form
        form_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        form_frame.pack(padx=40, pady=0, fill="x")
        
        # Business Name
        ctk.CTkLabel(form_frame, text="Business Name", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(15, 5))
        self.business_name = ctk.CTkEntry(form_frame, height=35)
        self.business_name.pack(fill="x")
        
        # Address
        ctk.CTkLabel(form_frame, text="Address", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(15, 5))
        self.business_address = ctk.CTkEntry(form_frame, height=35)
        self.business_address.pack(fill="x")
        
        # Phone
        ctk.CTkLabel(form_frame, text="Phone", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(15, 5))
        self.business_phone = ctk.CTkEntry(form_frame, height=35)
        self.business_phone.pack(fill="x")
        
        # Email
        ctk.CTkLabel(form_frame, text="Email", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(15, 5))
        self.business_email = ctk.CTkEntry(form_frame, height=35)
        self.business_email.pack(fill="x")
        
        # Invoice Prefix
        ctk.CTkLabel(form_frame, text="Invoice Prefix", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(15, 5))
        self.invoice_prefix = ctk.CTkEntry(form_frame, height=35)
        self.invoice_prefix.pack(fill="x")
        
        # Save Button
        ctk.CTkButton(
            self.content_frame,
            text="💾 Save Changes",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2ECC71",
            hover_color="#27AE60",
            command=self.save_business_info,
            width=150,
            height=40
        ).pack(pady=10)
    
    def show_security(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        ctk.CTkLabel(
            self.content_frame,
            text="Change Password",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(20, 10))
        
        # Form
        form_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        form_frame.pack(padx=40, pady=20, fill="x")
        
        # Current Password
        ctk.CTkLabel(form_frame, text="Current Password", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(15, 5))
        self.current_pass = ctk.CTkEntry(form_frame, height=35, show="●")
        self.current_pass.pack(fill="x")
        
        # New Password
        ctk.CTkLabel(form_frame, text="New Password", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(15, 5))
        self.new_pass = ctk.CTkEntry(form_frame, height=35, show="●")
        self.new_pass.pack(fill="x")
        
        # Confirm Password
        ctk.CTkLabel(form_frame, text="Confirm New Password", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(15, 5))
        self.confirm_pass = ctk.CTkEntry(form_frame, height=35, show="●")
        self.confirm_pass.pack(fill="x")
        
        # Change Button
        ctk.CTkButton(
            self.content_frame,
            text="🔒 Change Password",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#3498DB",
            hover_color="#2980B9",
            command=self.change_password,
            width=150,
            height=40
        ).pack(pady=30)
    
    def show_backup(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        scroll_frame = ctk.CTkScrollableFrame(self.content_frame)
        scroll_frame.pack(fill="both", expand=True)
        
        ctk.CTkLabel(
            scroll_frame,
            text="Backup & Restore",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(20, 10))
        
        # Backup Section
        backup_frame = ctk.CTkFrame(scroll_frame)
        backup_frame.pack(fill="x", padx=40, pady=20)
        
        ctk.CTkLabel(
            backup_frame,
            text="💾 Create Backup",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(20, 10))
        
        ctk.CTkLabel(
            backup_frame,
            text="Create a backup of your database file.\nKeep it safe for data recovery.",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(pady=5)
        
        ctk.CTkButton(
            backup_frame,
            text="📥 Backup Now",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2ECC71",
            hover_color="#27AE60",
            command=self.create_backup,
            width=150,
            height=40
        ).pack(pady=20)
        
        # Restore Section
        restore_frame = ctk.CTkFrame(scroll_frame)
        restore_frame.pack(fill="x", padx=40, pady=20)
        
        ctk.CTkLabel(
            restore_frame,
            text="🔄 Restore Backup",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(20, 10))
        
        ctk.CTkLabel(
            restore_frame,
            text="⚠️ Warning: This will replace all current data!\nMake sure you have a current backup first.",
            font=ctk.CTkFont(size=12),
            text_color="#E74C3C"
        ).pack(pady=5)
        
        ctk.CTkButton(
            restore_frame,
            text="📤 Restore from Backup",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#E74C3C",
            hover_color="#C0392B",
            command=self.restore_backup,
            width=180,
            height=40
        ).pack(pady=20)
        
        # Export Section
        export_frame = ctk.CTkFrame(scroll_frame)
        export_frame.pack(fill="x", padx=40, pady=20)
        
        ctk.CTkLabel(
            export_frame,
            text="📤 Export Data",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(20, 10))
        
        btn_frame = ctk.CTkFrame(export_frame, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(
            btn_frame,
            text="Export Sales (CSV)",
            command=lambda: self.export_data("sales"),
            width=150,
            height=35
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="Export Inventory (CSV)",
            command=lambda: self.export_data("inventory"),
            width=150,
            height=35
        ).pack(side="left", padx=10)

        # Factory Reset Section
        reset_frame = ctk.CTkFrame(scroll_frame)
        reset_frame.pack(fill="x", padx=40, pady=20)

        ctk.CTkLabel(
            reset_frame,
            text="Factory Reset",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#E74C3C"
        ).pack(pady=(20, 10))

        ctk.CTkLabel(
            reset_frame,
            text="Delete all business data and restart the software like a fresh installation.\nAdmin account and business settings will remain safe.",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(pady=5)

        ctk.CTkButton(
            reset_frame,
            text="Factory Reset",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#E74C3C",
            hover_color="#C0392B",
            command=self.show_factory_reset_password_dialog,
            width=160,
            height=40
        ).pack(pady=20)
    
    def load_settings(self):
        try:
            db.cursor.execute("SELECT business_name, address, phone, email, invoice_prefix FROM settings WHERE id=1")
            settings = db.cursor.fetchone()
            
            if settings:
                self.business_name.insert(0, settings[0] or "")
                self.business_address.insert(0, settings[1] or "")
                self.business_phone.insert(0, settings[2] or "")
                self.business_email.insert(0, settings[3] or "")
                self.invoice_prefix.insert(0, settings[4] or "JUGO-")
        except:
            pass

    def show_factory_reset_password_dialog(self):
        dialog = ctk.CTkToplevel(self.parent.winfo_toplevel())
        dialog.title("Enter Admin Password")
        dialog.transient(self.parent.winfo_toplevel())
        dialog.grab_set()
        center_window(dialog, 420, 240)

        ctk.CTkLabel(
            dialog,
            text="Enter Admin Password",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(25, 10))

        ctk.CTkLabel(
            dialog,
            text="Password is required before factory reset.",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(pady=(0, 15))

        password_entry = ctk.CTkEntry(dialog, height=40, width=300, show="*")
        password_entry.pack(pady=10)
        password_entry.focus()
        password_entry.bind(
            "<Return>",
            lambda e: self.verify_factory_reset_password(dialog, password_entry)
        )

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            width=120,
            height=38,
            fg_color="#95A5A6",
            hover_color="#7F8C8D",
            command=dialog.destroy
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            btn_frame,
            text="Verify",
            width=120,
            height=38,
            fg_color="#3498DB",
            hover_color="#2980B9",
            command=lambda: self.verify_factory_reset_password(dialog, password_entry)
        ).pack(side="left", padx=8)

    def verify_factory_reset_password(self, dialog, password_entry):
        password = password_entry.get().strip()

        if not db.verify_login("admin", password):
            messagebox.showerror("Error", "Incorrect password. Reset not allowed.")
            password_entry.delete(0, "end")
            password_entry.focus()
            return

        dialog.destroy()
        self.show_factory_reset_confirmation()

    def show_factory_reset_confirmation(self):
        dialog = ctk.CTkToplevel(self.parent.winfo_toplevel())
        dialog.title("Factory Reset")
        dialog.transient(self.parent.winfo_toplevel())
        dialog.grab_set()
        center_window(dialog, 560, 300)

        ctk.CTkLabel(
            dialog,
            text="Factory Reset Warning",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#E74C3C"
        ).pack(pady=(25, 15))

        ctk.CTkLabel(
            dialog,
            text="WARNING: This will delete all data including customers, sales, inventory, suppliers, and reports. This action cannot be undone.",
            font=ctk.CTkFont(size=13),
            wraplength=480,
            justify="left",
            text_color="#E74C3C"
        ).pack(padx=30, pady=10)

        ctk.CTkLabel(
            dialog,
            text="Admin account and business settings will remain available.",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(pady=(0, 15))

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=15)

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            width=130,
            height=40,
            fg_color="#95A5A6",
            hover_color="#7F8C8D",
            command=dialog.destroy
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="Confirm Reset",
            width=150,
            height=40,
            fg_color="#E74C3C",
            hover_color="#C0392B",
            command=lambda: self.perform_factory_reset(dialog)
        ).pack(side="left", padx=10)

    def perform_factory_reset(self, dialog):
        dialog.destroy()

        try:
            db.reset_business_data()
            self.delete_generated_invoice_files()
            messagebox.showinfo("Success", "System has been reset successfully.")
            self.restart_application()
        except Exception as e:
            messagebox.showerror("Error", f"Factory reset failed: {str(e)}")

    def delete_generated_invoice_files(self):
        invoices_dir = os.path.join(os.path.dirname(__file__), "invoices")

        if not os.path.isdir(invoices_dir):
            return

        for entry in os.scandir(invoices_dir):
            if entry.is_file():
                os.remove(entry.path)

    def restart_application(self):
        root = self.parent.winfo_toplevel()
        main_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "main.py"))

        try:
            db.close()
        except Exception:
            pass

        root.destroy()
        os.execl(sys.executable, sys.executable, main_script)

    def save_business_info(self):
        try:
            db.cursor.execute("""
                UPDATE settings 
                SET business_name=?, address=?, phone=?, email=?, invoice_prefix=?
                WHERE id=1
            """, (
                self.business_name.get(),
                self.business_address.get(),
                self.business_phone.get(),
                self.business_email.get(),
                self.invoice_prefix.get()
            ))
            db.conn.commit()
            
            messagebox.showinfo("Success", "Business information saved!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {str(e)}")
    
    def change_password(self):
        current = self.current_pass.get()
        new = self.new_pass.get()
        confirm = self.confirm_pass.get()
        
        if not current or not new or not confirm:
            messagebox.showerror("Error", "Please fill all fields!")
            return
        
        if new != confirm:
            messagebox.showerror("Error", "New passwords do not match!")
            return
        
        if len(new) < 4:
            messagebox.showerror("Error", "Password must be at least 4 characters!")
            return
        
        # Verify current password
        if not db.verify_login("admin", current):
            messagebox.showerror("Error", "Current password is incorrect!")
            return
        
        try:
            db.change_password("admin", new)
            messagebox.showinfo("Success", "Password changed successfully!")
            
            # Clear fields
            self.current_pass.delete(0, "end")
            self.new_pass.delete(0, "end")
            self.confirm_pass.delete(0, "end")
        except Exception as e:
            messagebox.showerror("Error", f"Failed: {str(e)}")
    
    def create_backup(self):
        try:
            # Choose location
            filename = filedialog.asksaveasfilename(
                defaultextension=".db",
                filetypes=[("Database files", "*.db"), ("All files", "*.*")],
                initialfile=f"jugo_swat_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            )
            
            if not filename:
                return
            
            # Copy database
            shutil.copy('database/jugo_swat.db', filename)
            
            messagebox.showinfo("Success", f"Backup created successfully!\nSaved to: {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Backup failed: {str(e)}")
    
    def restore_backup(self):
        if not messagebox.askyesno("Confirm", "This will replace ALL current data!\nAre you sure?"):
            return
        
        try:
            # Choose file
            filename = filedialog.askopenfilename(
                filetypes=[("Database files", "*.db"), ("All files", "*.*")]
            )
            
            if not filename:
                return
            
            # Verify it's a valid database
            import sqlite3
            test_conn = sqlite3.connect(filename)
            test_cursor = test_conn.cursor()
            
            # Check if required tables exist
            test_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [t[0] for t in test_cursor.fetchall()]
            
            required_tables = ['admin', 'flavors', 'customers', 'sales', 'settings']
            for table in required_tables:
                if table not in tables:
                    test_conn.close()
                    messagebox.showerror("Error", f"Invalid backup file! Missing table: {table}")
                    return
            
            test_conn.close()
            
            # Restore
            shutil.copy(filename, 'database/jugo_swat.db')
            
            messagebox.showinfo("Success", "Database restored successfully!\nPlease restart the application.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Restore failed: {str(e)}")
    
    def export_data(self, data_type):
        try:
            if data_type == "sales":
                filename = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    filetypes=[("CSV files", "*.csv")],
                    initialfile=f"sales_{datetime.now().strftime('%Y%m%d')}.csv"
                )
                
                if not filename:
                    return
                
                db.cursor.execute("""
                    SELECT invoice_number, customer_name, grand_total, payment_mode, created_at 
                    FROM sales ORDER BY created_at DESC
                """)
                data = db.cursor.fetchall()
                
                with open(filename, 'w') as f:
                    f.write("Invoice,Customer,Amount,Payment,Date\n")
                    for row in data:
                        f.write(f"{row[0]},{row[1]},{row[2]},{row[3]},{row[4]}\n")
            
            elif data_type == "inventory":
                filename = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    filetypes=[("CSV files", "*.csv")],
                    initialfile=f"inventory_{datetime.now().strftime('%Y%m%d')}.csv"
                )
                
                if not filename:
                    return
                
                db.cursor.execute("SELECT name, category, stock, sale_price, cost_price FROM flavors")
                data = db.cursor.fetchall()
                
                with open(filename, 'w') as f:
                    f.write("Name,Category,Stock,Sale Price,Cost Price\n")
                    for row in data:
                        f.write(f"{row[0]},{row[1]},{row[2]},{row[3]},{row[4]}\n")
            
            messagebox.showinfo("Success", f"Data exported to: {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {str(e)}")
