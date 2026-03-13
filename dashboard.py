from fileinput import filename
import tkinter as tk
from tkinter import dialog
from PIL import Image
from analytical_review import AnalyticsReview
import customtkinter as ctk
from tkinter import messagebox, filedialog
from database import db
from PIL import Image as PILImage, ImageTk
import os
from datetime import datetime
from functools import partial 
from reportlab.lib.pagesizes import A4

from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from expenses import ExpensesManager
from ui_utils import center_window



from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage, HRFlowable

from reportlab.lib.units import inch, cm




class Dashboard:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("JUGO SWAT - Dashboard")
        self.root.geometry("1400x900")
        self.root.resizable(True, True)
        self.brand_logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo2.png")
        self.sidebar_logo_image = None
        self._profit_refresh_active = False
        
        # Center window
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 1400) // 2
        y = (screen_height - 900) // 2
        self.root.geometry(f"1400x900+{x}+{y}")
        
        self.setup_ui()
        self.root.after(0, self.maximize_window)

    def maximize_window(self):
        self.root.update_idletasks()
        windowing_system = self.root.tk.call("tk", "windowingsystem")

        try:
            if windowing_system == "win32":
                self.root.state("zoomed")
            else:
                self.root.attributes("-zoomed", True)
        except tk.TclError:
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            self.root.geometry(f"{screen_width}x{screen_height}+0+0")
    
    def setup_ui(self):
        # Main Layout
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # Sidebar
        self.sidebar = ctk.CTkFrame(self.root, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Branding Text + Logo
        brand_text_label = ctk.CTkLabel(
            self.sidebar,
            text="SM ENTERPRISES",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=("gray10", "gray90"),
        )
        brand_text_label.grid(row=0, column=0, padx=20, pady=(20, 6))

        try:
            logo_image = PILImage.open(self.brand_logo_path).convert("RGBA")
            target_width = 170
            target_height = max(1, int(logo_image.height * (target_width / logo_image.width)))
            self.sidebar_logo_image = ctk.CTkImage(
                light_image=logo_image,
                dark_image=logo_image,
                size=(target_width, target_height),
            )
            logo_label = ctk.CTkLabel(self.sidebar, text="", image=self.sidebar_logo_image)
        except Exception:
            logo_label = ctk.CTkLabel(
                self.sidebar,
                text="JUGO SWAT",
                font=ctk.CTkFont(size=24, weight="bold"),
                text_color="#2ECC71"
            )
        logo_label.grid(row=1, column=0, padx=20, pady=(0, 30))
        
        # Menu Buttons
        menu_items = [
            ("🏠 Dashboard", self.show_dashboard),
            ("📦 Inventory", self.show_inventory),
            ("💰 Sales", self.show_sales),
            ("💸 Expenses", self.show_expenses),
            ("👥 Customers", self.show_customers),
            ("🏭 Supplier", self.show_supplier),
            ("📈 Analytics", self.show_analytics), 
            ("📊 Reports", self.show_reports),
            ("⚙️ Settings", self.show_settings),
        ]

        spacer_row = len(menu_items) + 2
        logout_row = len(menu_items) + 3
        self.sidebar.grid_rowconfigure(spacer_row, weight=1)

        for i, (text, command) in enumerate(menu_items, start=2):
            btn = ctk.CTkButton(
                self.sidebar,
                text=text,
                font=ctk.CTkFont(size=14),
                anchor="w",
                height=40,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
                command=command
            )
            btn.grid(row=i, column=0, padx=10, pady=5, sticky="ew")
        
        # Logout Button
        logout_btn = ctk.CTkButton(
            self.sidebar,
            text="🚪 Logout",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#E74C3C",
            hover_color="#C0392B",
            command=self.logout
        )
        logout_btn.grid(row=logout_row, column=0, padx=20, pady=20, sticky="ew")
        
        # Main Content Area
        self.main_frame = ctk.CTkFrame(self.root, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        # Header
        self.header = ctk.CTkLabel(
            self.main_frame,
            text="Dashboard",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        self.header.grid(row=0, column=0, sticky="w", pady=(0, 20))
        
        # Content Frame
        self.content_frame = ctk.CTkFrame(self.main_frame)
        self.content_frame.grid(row=1, column=0, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        self.show_dashboard()
    
    def show_dashboard(self):
        self.clear_content()
        self.header.configure(text="Dashboard")
        
        # ===== BACKGROUND IMAGE =====
        try:
            # Load and resize image
            image_path = "assets/jugo.jpeg"  # Image should be in assets folder
            if os.path.exists(image_path):
                img = PILImage.open(image_path)
                # Resize to low resolution (200x150)
                img = img.resize((200, 150), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                
                # Background label
                bg_label = ctk.CTkLabel(self.content_frame, image=photo, text="")
                bg_label.image = photo  # Keep reference
                bg_label.place(relx=0.95, rely=0.02, anchor="ne")  # Top right corner
        except Exception as e:
            print(f"Background image error: {e}")
        
        # ===== FINANCIAL SUMMARY CARDS (ROW 0) =====
        finance_frame = ctk.CTkFrame(self.content_frame)
        finance_frame.pack(fill="x", padx=10, pady=10)
        
        # Get data from database
        # Get data from database
        today_gross_profit = db.get_today_profit()  # Gross profit from sales

        # Get today's expenses
        exp_manager = ExpensesManager()
        today_expenses = exp_manager.get_today_total()

        # Calculate NET PROFIT = Gross Profit - Expenses
        net_profit_value = today_gross_profit['profit'] - today_expenses

        # Prepare display data
        today_profit = {
        'profit': net_profit_value,
        'revenue': today_gross_profit['revenue']
}
        investment = db.get_total_investment()
        monthly_gross = db.get_monthly_summary()
        month_expenses = exp_manager.get_month_total()
        monthly_net = monthly_gross['profit'] - month_expenses
        credit = db.get_outstanding_credit()
        
        # Financial Cards Data
        finance_cards = [
            ("📈 Today's Net Profit", f"Rs. {today_profit['profit']:,.0f}", 
             "#2ECC71" if today_profit['profit'] >= 0 else "#E74C3C",
             f"Revenue: Rs. {today_profit['revenue']:,.0f} | Expenses: Rs. {today_expenses:,.0f}"),
            
            ("💰 Total Investment", f"Rs. {investment['investment']:,.0f}", 
             "#3498DB",
             f"{investment['BOX']} BOX in stock"),
            
            ("📊 This Month Profit", f"Rs. {monthly_net:,.0f}", 
             "#9B59B6" if monthly_net >= 0 else "#E74C3C",
             f"{monthly_gross['sales_count']} sales | Expenses: Rs. {month_expenses:,.0f}"),
            
            ("💳 Outstanding Credit", f"Rs. {credit:,.0f}", 
             "#E67E22",
             "To be collected"),
        ]
        
        for i, (title, value, color, subtitle) in enumerate(finance_cards):
            card = ctk.CTkFrame(finance_frame, corner_radius=10)
            card.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")
            finance_frame.grid_columnconfigure(i, weight=1)
            
            lbl_title = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=12), text_color="gray")
            lbl_title.pack(pady=(15, 5))
            
            lbl_value = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=22, weight="bold"), text_color=color)
            lbl_value.pack()
            
            lbl_sub = ctk.CTkLabel(card, text=subtitle, font=ctk.CTkFont(size=10), text_color="gray")
            lbl_sub.pack(pady=(5, 15))

            if i == 0:  # First card = Today's Profit
                self.today_profit_label = lbl_value
                
                hidden_state = {"hidden": False}
                
                def toggle_value(value_label=lbl_value, original_value=value, state=hidden_state):
                    state["hidden"] = not state["hidden"]
                    value_label.configure(text="****" if state["hidden"] else original_value)
                
                eye_btn = ctk.CTkButton(
                    card,
                    text="👁",
                    width=28,
                    height=28,
                    font=ctk.CTkFont(size=14),
                    fg_color="transparent",
                    text_color="gray",
                    hover_color=("gray85", "gray25"),
                    corner_radius=6,
                    command=toggle_value
                )
                eye_btn.place(relx=1.0, rely=0.0, x=-8, y=8, anchor="ne")
            elif i == 2:  # Third card = This Month Profit
                self.month_profit_label = lbl_value
            elif i == 3:  # Fourth card = Outstanding Credit
                self.credit_label = lbl_value

        # ===== BUSINESS STATS CARDS (ROW 1) - CLICKABLE =====
        stats_frame = ctk.CTkFrame(self.content_frame)
        stats_frame.pack(fill="x", padx=10, pady=10)
        
        # Get basic stats
        db.cursor.execute("SELECT COUNT(*) FROM flavors")
        total_flavors = db.cursor.fetchone()[0]
        
        db.cursor.execute("SELECT SUM(stock) FROM flavors")
        total_stock = db.cursor.fetchone()[0] or 0
        
        db.cursor.execute("SELECT COUNT(*) FROM customers")
        total_customers = db.cursor.fetchone()[0]
        
        db.cursor.execute("SELECT COUNT(*) FROM flavors WHERE stock < 4")
        low_stock = db.cursor.fetchone()[0]
        
        # Stats cards with click commands
        stats_cards = [
            ("🥤 Total Flavors", str(total_flavors), "#1ABC9C", self.show_inventory),
            ("📦 Stock Available", f"{total_stock} BOX", "#3498DB", self.show_inventory),
            ("👥 Total Customers", str(total_customers), "#9B59B6", self.show_customers),
            ("⚠️ Low Stock Items", str(low_stock), "#E74C3C" if low_stock > 0 else "#27AE60", self.show_low_stock),
        ]
        
        for i, (title, value, color, command) in enumerate(stats_cards):
            card = ctk.CTkFrame(stats_frame, corner_radius=10, cursor="hand2")
            card.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")
            stats_frame.grid_columnconfigure(i, weight=1)
            
            # Make clickable
            card.bind("<Button-1>", lambda e, cmd=command: cmd())
            
            lbl_value = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=28, weight="bold"), text_color=color)
            lbl_value.pack(pady=(20, 5))
            lbl_value.bind("<Button-1>", lambda e, cmd=command: cmd())
            
            lbl_title = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=12), text_color="gray")
            lbl_title.pack(pady=(5, 20))
            lbl_title.bind("<Button-1>", lambda e, cmd=command: cmd())
        
        # ===== QUICK ACTIONS (ROW 2) =====
        actions_frame = ctk.CTkFrame(self.content_frame)
        actions_frame.pack(fill="x", padx=10, pady=20)
        
        ctk.CTkLabel(
            actions_frame,
            text="Quick Actions",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(15, 10), padx=20, anchor="w")
        
        actions_btn_frame = ctk.CTkFrame(actions_frame, fg_color="transparent")
        actions_btn_frame.pack(pady=10, padx=20, fill="x")
        
        actions = [
            ("+ New Sale", "#2ECC71", self.show_sales),
            ("+ Add Stock", "#3498DB", self.show_inventory),
            ("+ Add Customer", "#9B59B6", self.show_customers),
            ("📊 View Reports", "#E67E22", self.show_reports),
        ]
        
        for text, color, command in actions:
            btn = ctk.CTkButton(
                actions_btn_frame,
                text=text,
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color=color,
                hover_color=self.darken_color(color),
                command=command,
                width=150,
                height=45
            )
            btn.pack(side="left", padx=10)

        # Start auto refresh for profit cards
        self.start_profit_refresh()
        
        # ===== RECENT SALES (ROW 3) WITH VIEW ALL BUTTON =====
        activity_frame = ctk.CTkFrame(self.content_frame)
        activity_frame.pack(fill="both", expand=True, padx=10, pady=20)
        
        # Header with View All button
        header_frame = ctk.CTkFrame(activity_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(15, 10))
        
        ctk.CTkLabel(
            header_frame,
            text="Recent Sales",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(side="left")
        
        # VIEW ALL BUTTON - NEW
        ctk.CTkButton(
            header_frame,
            text="View All →",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#3498DB",
            hover_color="#2980B9",
            command=self.show_all_sales,
            width=100,
            height=30
        ).pack(side="right")
        
        # Table headers
        headers = ["Invoice", "Customer", "Amount", "Payment", "Date"]
        header_frame = ctk.CTkFrame(activity_frame, fg_color=("gray85", "gray25"))
        header_frame.pack(fill="x", padx=20, pady=5)
        
        for i, header in enumerate(headers):
            ctk.CTkLabel(
                header_frame,
                text=header,
                font=ctk.CTkFont(size=12, weight="bold"),
                width=150
            ).grid(row=0, column=i, padx=5, pady=8)
        
        # SCROLLABLE FRAME for sales
        sales_scroll = ctk.CTkScrollableFrame(activity_frame, height=250)
        sales_scroll.pack(fill="both", expand=True, padx=20, pady=10)
        self.recent_sales_scroll = sales_scroll
        self.load_recent_sales(sales_scroll)
        self.start_sales_refresh()

    def start_sales_refresh(self):
        """Auto refresh recent sales every 10 seconds"""
        try:
            # Only refresh if still on dashboard
            if self.header.cget("text") == "Dashboard":
                self.refresh_recent_sales()
                self.root.after(10000, self.start_sales_refresh)  # 10 sec
        except Exception:
            pass

    def refresh_recent_sales(self):
        """Refresh only recent sales list"""
        try:
            sales_scroll = getattr(self, "recent_sales_scroll", None)
            if not sales_scroll:
                return
            for child in sales_scroll.winfo_children():
                child.destroy()
            self.load_recent_sales(sales_scroll)
        except Exception as e:
            print(f"Sales refresh error: {e}")

    def load_recent_sales(self, sales_scroll):
        """Load recent sales into scrollable frame"""
        # Get recent sales from database
        db.cursor.execute("""
            SELECT invoice_number, customer_name, grand_total, payment_mode, created_at 
            FROM sales 
            WHERE grand_total > 0
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        recent_sales = db.cursor.fetchall()
        
        if recent_sales:
            for sale in recent_sales:
                invoice, customer, amount, payment, date = sale
                
                # Create clickable row
                row_frame = ctk.CTkFrame(sales_scroll, fg_color="transparent", cursor="hand2", height=30)
                row_frame.pack(fill="x", pady=2)
                row_frame.pack_propagate(False)
                
                for i in range(5):
                    row_frame.grid_columnconfigure(i, weight=1)
                
                row_frame.bind("<Button-1>", partial(self.on_row_click, invoice))
                
                values = [
                    invoice,
                    customer[:20] if customer else "Walk-in",
                    f"Rs. {amount:,.0f}",
                    payment,
                    date[:10] if isinstance(date, str) else date.strftime('%Y-%m-%d')
                ]
                
                widths = [150, 150, 150, 150, 150]
                for i, (cell, w) in enumerate(zip(values, widths)):
                    lbl = ctk.CTkLabel(
                        row_frame,
                        text=str(cell),
                        font=ctk.CTkFont(size=11),
                        width=w,
                        anchor="w"
                    )
                    lbl.grid(row=0, column=i, padx=5, pady=3, sticky="w")
                    lbl.bind("<Button-1>", partial(self.on_row_click, invoice))
                
                # Hover effect
                def on_enter(e, rf=row_frame):
                    rf.configure(fg_color=("gray90", "gray20"))
                
                def on_leave(e, rf=row_frame):
                    rf.configure(fg_color="transparent")
                
                row_frame.bind("<Enter>", on_enter)
                row_frame.bind("<Leave>", on_leave)
        else:
            ctk.CTkLabel(
                sales_scroll,
                text="No sales yet. Start selling! 🚀",
                font=ctk.CTkFont(size=14),
                text_color="gray"
            ).pack(pady=50)

    def on_row_click(self, invoice, event=None):
            """Handle row click to show bill"""
            self.show_bill_dialog(invoice)
            self.start_profit_refresh()
            self.start_sales_refresh()

    def start_profit_refresh(self):
        """Auto refresh profit every 5 seconds"""
        if self._profit_refresh_active:
            return
        self._profit_refresh_active = True
        self._schedule_profit_refresh()

    def _schedule_profit_refresh(self):
        self.refresh_profit()
        # 5000 ms = 5 seconds baad dobara call karo
        self.root.after(5000, self._schedule_profit_refresh)

    def refresh_profit(self):
        """Recalculate and update today's and monthly profit"""
        try:
            # Get fresh data
            today_gross = db.get_today_profit()
            
            # Import here to avoid circular import
            from expenses import ExpensesManager
            exp_manager = ExpensesManager()
            today_exp = exp_manager.get_today_total()
            month_exp = exp_manager.get_month_total()
            monthly_gross = db.get_monthly_summary()
            
            # Calculate net profit
            net_profit = today_gross['profit'] - today_exp
            monthly_net = monthly_gross['profit'] - month_exp
            
            # Update the profit card (4th card - index 3)
            # Note: You need to store reference to profit label
            if hasattr(self, 'today_profit_label'):
                self.today_profit_label.configure(
                    text=f"Rs. {net_profit:,.0f}",
                    text_color="#2ECC71" if net_profit >= 0 else "#E74C3C"
                )
            if hasattr(self, 'month_profit_label'):
                self.month_profit_label.configure(
                    text=f"Rs. {monthly_net:,.0f}",
                    text_color="#9B59B6" if monthly_net >= 0 else "#E74C3C"
                )
            if hasattr(self, 'credit_label'):
                credit = db.get_outstanding_credit()
                self.credit_label.configure(
                    text=f"Rs. {credit:,.0f}"
                )
        except Exception as e:
            print(f"Refresh error: {e}")

    # ===== BILL DIALOG - NEW FUNCTION =====
    
    def show_bill_dialog(self, invoice_number):
        """Show bill preview dialog - SM Enterprises style"""
        self._profit_refresh_active = False
    
        try:
            # Fetch sale details
            db.cursor.execute("""
                SELECT s.id, s.invoice_number, s.customer_name,
                   s.grand_total, s.payment_mode, s.is_credit, s.created_at,
                   c.name, c.phone, c.credit_limit
                FROM sales s
                LEFT JOIN customers c ON s.customer_id = c.id
                WHERE s.invoice_number = ?
            """, (invoice_number,))
        
            sale = db.cursor.fetchone()
            if not sale:
                messagebox.showerror("Error", "Invoice not found!")

                return
            
            sale_id, invoice, cust_name, grand_total, payment_mode, is_credit, created_at, db_name, db_phone, credit_limit = sale
        
        # Fetch items
            db.cursor.execute("""
                SELECT f.name, si.quantity, si.price, si.total
                FROM sale_items si
                JOIN flavors f ON si.flavor_id = f.id
                WHERE si.sale_id = ?
            """, (sale_id,))
            items = db.cursor.fetchall()
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load invoice: {str(e)}")
            return
    
        # Create dialog
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(f"Invoice #{invoice}")
        dialog.transient(self.root)
        dialog.grab_set()
        center_window(dialog, 450, 700)

        

        #     # ===== SCROLLABLE FRAME FOR BILL CONTENT =====
        # scroll_frame = ctk.CTkScrollableFrame(dialog, fg_color="white", corner_radius=0)
        # scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)
    
        # Scrollable content frame (keeps buttons visible)
        main_frame = ctk.CTkScrollableFrame(dialog, fg_color="white", corner_radius=0)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # ===== TOP SECTION - LEFT & RIGHT =====
        top_frame = ctk.CTkFrame(main_frame, fg_color="white")
        top_frame.pack(fill="x", pady=(5, 0))

        # LEFT: Shop details + BILL TO
        left_frame = ctk.CTkFrame(top_frame, fg_color="white")
        left_frame.pack(side="left", fill="y")

        ctk.CTkLabel(left_frame, text="SM ENTERPRISES", 
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color="#2076E7").pack(anchor="w")

        ctk.CTkLabel(left_frame, text="MINGORA SWAT, PAKISTAN", 
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color="black").pack(anchor="w")
        ctk.CTkLabel(left_frame, text="Contact: 0348-0906263 - 0315-9673621", 
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color="black").pack(anchor="w")

        # BILL TO (left side) - BLUE HEADER STYLE
        bill_to_header = ctk.CTkFrame(left_frame, fg_color="#74AEF9", height=20)
        bill_to_header.pack(fill="x", pady=(5, 5))

        ctk.CTkLabel(bill_to_header, text="BILL TO:", 
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="white").pack(anchor="w", padx=5, pady=2)

        display_name = db_name or cust_name or "Walk-in Customer"
        display_phone = db_phone or "N/A"

        ctk.CTkLabel(left_frame, text=f"{display_name}", 
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color="black").pack(anchor="w")
        ctk.CTkLabel(left_frame, text=f"{display_phone}", 
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color="black").pack(anchor="w")
        
        # RIGHT: Logo (top) + Invoice (bottom, opposite to BILL TO)
        right_frame = ctk.CTkFrame(top_frame, fg_color="white")
        right_frame.pack(side="right", fill="y")

        # LOGO (top right)
        try:
            logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo2.png")
            logo_img = PILImage.open(logo_path).convert("RGBA")
            logo_photo = ctk.CTkImage(logo_img, size=(100, 100))
            logo_label = ctk.CTkLabel(right_frame, image=logo_photo, text="")
            logo_label.image = logo_photo  # Keep reference
            logo_label.pack(anchor="e")
        except Exception as e:
            # If no logo, use text
            ctk.CTkLabel(right_frame, text="🥤 JUGO", font=ctk.CTkFont(size=20)).pack(anchor="e")

# Spacer to push invoice down
        ctk.CTkLabel(right_frame, text="", height=20).pack()

# INVOICE (bottom right, opposite to BILL TO)
        date_str = datetime.now().strftime("%d-%m-%Y %H:%M") if isinstance(created_at, str) else created_at.strftime("%d-%m-%Y %H:%M")

        ctk.CTkLabel(right_frame, text=f"Invoice #: {invoice}", 
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="black").pack(anchor="e")
        ctk.CTkLabel(right_frame, text=f"Date: {date_str}", 
                font=ctk.CTkFont(size=10),
                text_color="gray").pack(anchor="e")
    
        # Line divider
        line = ctk.CTkFrame(main_frame, height=2, fg_color="gray")
        line.pack(fill="x", pady=5)
    
        # ===== TABLE HEADERS =====
        header_frame = ctk.CTkFrame(main_frame, fg_color="#428DEE", height=25)
        header_frame.pack(fill="x", pady=(5, 5))
    
        ctk.CTkLabel(header_frame, text="S.No", 
                font=ctk.CTkFont(size=10, weight="bold"),
                width=40, text_color="white").pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="Description", 
                font=ctk.CTkFont(size=10, weight="bold"),
                width=150, text_color="white").pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="Price", 
                font=ctk.CTkFont(size=10, weight="bold"),
                width=60, text_color="white").pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="Qty", 
                font=ctk.CTkFont(size=10, weight="bold"),
                width=40, text_color="white").pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="Total", 
                font=ctk.CTkFont(size=10, weight="bold"),
                width=60, text_color="white").pack(side="right", padx=5)
    
        # ===== ITEMS =====
        items_frame = ctk.CTkFrame(main_frame, fg_color="white")
        items_frame.pack(fill="x", pady=5)
    
        for i, (item_name, qty, price, total) in enumerate(items, 1):
            row = ctk.CTkFrame(items_frame, fg_color="white")
            row.pack(fill="x", pady=2)
        
            ctk.CTkLabel(row, text=str(i), 
                    font=ctk.CTkFont(size=10, weight="bold"),
                    width=40).pack(side="left", padx=5)
            ctk.CTkLabel(row, text=item_name[:20], 
                    font=ctk.CTkFont(size=10, weight="bold"),
                    width=150).pack(side="left", padx=5)
            ctk.CTkLabel(row, text=f"{int(price)}", 
                    font=ctk.CTkFont(size=10, weight="bold"),
                    width=60).pack(side="left", padx=5)
            ctk.CTkLabel(row, text=str(qty), 
                    font=ctk.CTkFont(size=10, weight="bold"),
                    width=40).pack(side="left", padx=5)
            ctk.CTkLabel(row, text=f"{int(total)}", 
                    font=ctk.CTkFont(size=10, weight="bold"),
                    width=60).pack(side="right", padx=5)
    
        # Line before total
        line2 = ctk.CTkFrame(main_frame, height=1, fg_color="gray")
        line2.pack(fill="x", pady=10)
    
        # ===== TOTALS (Right aligned) =====
        total_frame = ctk.CTkFrame(main_frame, fg_color="white")
        total_frame.pack(fill="x", pady=5)

        # Calculate subtotal from items
        subtotal = sum(float(total) for _, _, _, total in items)

        ctk.CTkLabel(total_frame, text=f"Subtotal:", 
                font=ctk.CTkFont(size=10),
                text_color="gray").pack(anchor="e", padx=60)
        ctk.CTkLabel(total_frame, text=f"Rs. {int(subtotal)}/-", 
                font=ctk.CTkFont(size=10),
                text_color="black").pack(anchor="e", padx=10)

        discount = subtotal - grand_total
        if discount > 0:
            ctk.CTkLabel(total_frame, text=f"Discount:", 
                font=ctk.CTkFont(size=10),
                text_color="gray").pack(anchor="e", padx=60)
            ctk.CTkLabel(total_frame, text=f"Rs. {int(discount)}/-", 
                font=ctk.CTkFont(size=10),
                text_color="black").pack(anchor="e", padx=10)

        # GRAND TOTAL BLUE BAR (Reference image style)
        grand_total_frame = ctk.CTkFrame(main_frame, fg_color="#428DEE", height=30)
        grand_total_frame.pack(fill="x", pady=(10, 5))

        # Left side: TOTAL label
        ctk.CTkLabel(grand_total_frame, text="TOTAL", 
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="white").pack(side="left", padx=10, pady=5)

        # # Center: Total quantity (20)
        # ctk.CTkLabel(grand_total_frame, text="20", 
        #         font=ctk.CTkFont(size=12, weight="bold"),
        #         text_color="white").pack(side="left", padx=50, pady=5)

        # Right side: Grand Total amount
        ctk.CTkLabel(grand_total_frame, text=f"Rs. {int(grand_total)}/-", 
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="white").pack(side="right", padx=10, pady=5)
    
        # ===== FOOTER =====
        footer_frame = ctk.CTkFrame(main_frame, fg_color="white")
        footer_frame.pack(fill="x", pady=20)
    
        ctk.CTkLabel(footer_frame, text="Thank you for choosing JUGO SWAT!", 
                font=ctk.CTkFont(size=10, slant="italic"),
                text_color="gray").pack()
        
        # # ===== BUTTONS FRAME (Top pe fixed) =====
        # btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        # btn_frame.pack(fill="x", padx=10, pady=(10, 5))

        # ctk.CTkButton(
        #     btn_frame,
        #     text="💾 Save PDF",
        #     font=ctk.CTkFont(size=12),
        #     fg_color="#428DEE",
        #     command=lambda: self.save_bill_as_pdf(invoice, sale, items),
        #     width=100
        # ).pack(side="left", padx=5)

        # ctk.CTkButton(
        #     btn_frame,
        #     text="🖨️ Print",
        #     font=ctk.CTkFont(size=12),
        #     fg_color="#428DEE",
        #     command=lambda: self.print_bill(invoice, sale, items),
        #     width=80
        # ).pack(side="left", padx=5)

        # ctk.CTkButton(
        #     btn_frame,
        #     text="❌ Close",
        #     font=ctk.CTkFont(size=12),
        #     fg_color="#95A5A6",
        #     command=lambda: [dialog.destroy(), self.restart_refresh()],
        #     width=80
        # ).pack(side="left", padx=5)

        # ===== BUTTONS =====
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)
    
        ctk.CTkButton(
            btn_frame,
            text="💾 Save PDF",
            font=ctk.CTkFont(size=12),
            fg_color="#428DEE",
            command=lambda: self.save_bill_as_pdf(invoice, sale, items),
            width=100
        ).pack(side="left", padx=5)
    
        ctk.CTkButton(
            btn_frame,
            text="🖨️ Print",
            font=ctk.CTkFont(size=12),
            fg_color="#428DEE",
            command=lambda: self.print_bill(invoice, sale, items),
            width=80
        ).pack(side="left", padx=5)
    
        ctk.CTkButton(
            btn_frame,
            text="❌ Close",
            font=ctk.CTkFont(size=12),
            fg_color="#95A5A6",
            command=lambda: [dialog.destroy(), self.restart_refresh()],
            width=80
        ).pack(side="left", padx=5)
    
    def save_bill_as_pdf(self, invoice, sale, items):
        """Save bill as PDF with exact SM Enterprises design"""
        sale_id, invoice_num, cust_name, grand_total, payment_mode, is_credit, created_at, db_name, db_phone, credit_limit = sale

        # File save dialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"Invoice_{invoice_num}_{datetime.now().strftime('%Y%m%d')}"
        )

        if not filename:
            return

        try:
            doc = SimpleDocTemplate(
                filename,
                pagesize=A4,
                rightMargin=40,
                leftMargin=40,
                topMargin=40,
                bottomMargin=40
            )
            elements = []
            styles = getSampleStyleSheet()

            # Custom styles matching GUI
            shop_title_style = ParagraphStyle(
                'ShopTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.HexColor("#2076E7"),
                fontName='Helvetica-Bold',
                spaceAfter=2
            )

            shop_detail_style = ParagraphStyle(
                'ShopDetail',
                parent=styles['Normal'],
                fontSize=10,
                fontName='Helvetica-Bold',
                textColor=colors.black,
                spaceAfter=2
            )

            bill_to_header_style = ParagraphStyle(
                'BillToHeader',
                parent=styles['Normal'],
                fontSize=11,
                fontName='Helvetica-Bold',
                textColor=colors.white
            )

            customer_style = ParagraphStyle(
                'Customer',
                parent=styles['Normal'],
                fontSize=10,
                fontName='Helvetica-Bold',
                textColor=colors.black,
                spaceAfter=2
            )

            invoice_detail_style = ParagraphStyle(
                'InvoiceDetail',
                parent=styles['Normal'],
                fontSize=11,
                fontName='Helvetica-Bold',
                textColor=colors.black,
                alignment=2,
                spaceAfter=2
            )

            date_style = ParagraphStyle(
                'DateStyle',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.grey,
                alignment=2
            )

            # ===== TOP SECTION: LEFT (Shop Details) & RIGHT (Logo + Invoice) =====

            # Left side: Shop details
            left_content = [
                [Paragraph("SM ENTERPRISES", shop_title_style)],
                [Paragraph("MINGORA SWAT, PAKISTAN", shop_detail_style)],
                [Paragraph("Contact: 0315-9673621", shop_detail_style)],
                [Paragraph("Contact: 0348-0906263", shop_detail_style)],
                [Spacer(1, 8)],
            ]

            # BILL TO Blue Header
            display_name = db_name or cust_name or "Walk-in Customer"
            display_phone = db_phone or "N/A"

            bill_to_data = [[Paragraph("BILL TO:", bill_to_header_style)]]
            bill_to_table = Table(bill_to_data, colWidths=[200], rowHeights=[20])
            bill_to_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#74AEF9")),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ]))
            left_content.append([bill_to_table])
            left_content.append([Spacer(1, 5)])
            left_content.append([Paragraph(display_name, customer_style)])
            left_content.append([Paragraph(display_phone, customer_style)])

            # Right side: Logo + Invoice details
            right_content = []

            # Try to add logo
            try:
                logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo2.png")
                if os.path.exists(logo_path):
                    img = RLImage(logo_path, width=80, height=80)
                    right_content.append([img])
                else:
                    right_content.append([Paragraph("JUGO", shop_title_style)])
            except Exception:
                right_content.append([Paragraph("JUGO", shop_title_style)])

            right_content.append([Spacer(1, 15)])

            date_str = created_at.strftime("%d-%m-%Y %H:%M") if hasattr(created_at, 'strftime') else str(created_at)
            right_content.append([Paragraph(f"Invoice #: {invoice_num}", invoice_detail_style)])
            right_content.append([Paragraph(f"Date: {date_str}", date_style)])

            # Combine left and right in one table
            header_table = Table([
                [Table(left_content, colWidths=[220]), Table(right_content, colWidths=[200])]
            ], colWidths=[220, 200])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ]))
            elements.append(header_table)
            elements.append(Spacer(1, 10))

            # Line divider
            elements.append(HRFlowable(width="100%", thickness=2, color=colors.grey))
            elements.append(Spacer(1, 10))

            # ===== TABLE HEADERS (Blue Background) =====
            table_data = [['S.No', 'Description', 'Price', 'Qty', 'Total']]

            # Add items
            for i, (item_name, qty, price, total) in enumerate(items, 1):
                table_data.append([
                    str(i),
                    item_name[:20],
                    str(int(price)),
                    str(qty),
                    str(int(total))
                ])

            # Create items table
            items_table = Table(table_data, colWidths=[50, 170, 70, 50, 80])
            items_table.setStyle(TableStyle([
                # Header row (Blue background like GUI)
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#428DEE")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),

                # Body rows (White background, bold text like GUI)
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),
                ('ALIGN', (1, 1), (1, -1), 'LEFT'),
                ('ALIGN', (2, 1), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                ('TOPPADDING', (0, 1), (-1, -1), 6),

                # Grid lines
                ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor("#428DEE")),
            ]))
            elements.append(items_table)
            elements.append(Spacer(1, 10))

            # Line before totals
            elements.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
            elements.append(Spacer(1, 10))

            # ===== TOTALS SECTION (Right aligned like GUI) =====
            subtotal = sum(float(total) for _, _, _, total in items)

            totals_data = []
            totals_data.append(['', '', 'Subtotal:', f"Rs. {int(subtotal)}/-"])

            discount = subtotal - grand_total
            if discount > 0:
                totals_data.append(['', '', 'Discount:', f"Rs. {int(discount)}/-"])

            totals_table = Table(totals_data, colWidths=[50, 170, 100, 100])
            totals_table.setStyle(TableStyle([
                ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
                ('FONTNAME', (2, 0), (2, -1), 'Helvetica'),
                ('FONTNAME', (3, 0), (3, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TEXTCOLOR', (2, 0), (2, -1), colors.grey),
                ('TEXTCOLOR', (3, 0), (3, -1), colors.black),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(totals_table)
            elements.append(Spacer(1, 8))

            # ===== GRAND TOTAL BLUE BAR (Like GUI) =====
            grand_total_data = [['TOTAL', '', '', f"Rs. {int(grand_total)}/-"]]
            grand_total_table = Table(grand_total_data, colWidths=[80, 140, 100, 100])
            grand_total_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#428DEE")),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (-1, 0), (-1, 0), 'RIGHT'),
                ('LEFTPADDING', (0, 0), (0, 0), 10),
                ('RIGHTPADDING', (-1, 0), (-1, 0), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            elements.append(grand_total_table)
            elements.append(Spacer(1, 25))

            # ===== FOOTER =====
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.grey,
                alignment=1,
                fontName='Helvetica-Oblique'
            )
            elements.append(Paragraph("Thank you for choosing JUGO!", footer_style))

            # Build PDF
            doc.build(elements)

            messagebox.showinfo("Success", f"Invoice saved successfully!\n\nLocation: {filename}")

            # Open PDF
            try:
                os.startfile(filename)
            except Exception:
                pass

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save PDF: {str(e)}")


    def show_today_profit_details(self):
        """Today's Profit card click handler"""
        self.show_reports()
        # You can add specific report filtering here
    
    def show_investment_details(self):
        """Total Investment card click handler"""
        self.show_inventory()
    
    def show_month_details(self):
        """This Month card click handler"""
        self.show_reports()
    
    def show_credit_details(self):
        """Outstanding Credit card click handler"""
        self.show_customers()
    
    def show_low_stock(self):
        """Low Stock Items card click handler"""
        self.show_inventory()
    
    def show_all_sales(self):
        """View All Sales button click handler - Like Banking Apps"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("All Sales Transactions")
        dialog.transient(self.root)
        dialog.grab_set()
        center_window(dialog, 1000, 750)
        
        # Title
        ctk.CTkLabel(
            dialog,
            text="📋 All Sales Transactions",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(pady=20)
        
        # Summary Frame
        summary_frame = ctk.CTkFrame(dialog)
        summary_frame.pack(fill="x", padx=30, pady=10)
        
        # Get summary stats
        db.cursor.execute("SELECT COUNT(*), SUM(grand_total) FROM sales WHERE grand_total > 0")
        total_sales, total_amount = db.cursor.fetchone()
        total_sales = total_sales or 0
        total_amount = total_amount or 0
        
        db.cursor.execute("SELECT COUNT(*), SUM(ABS(grand_total)) FROM sales WHERE grand_total < 0")
        payment_count, payment_amount = db.cursor.fetchone()
        payment_count = payment_count or 0
        payment_amount = payment_amount or 0

        outstanding_credit = db.get_outstanding_credit()
        
        ctk.CTkLabel(summary_frame, text=f"Total Sales: {total_sales}", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=20, pady=15)
        ctk.CTkLabel(summary_frame, text=f"Total Amount: Rs. {total_amount:,.0f}", 
                    font=ctk.CTkFont(size=14, weight="bold"), text_color="#2ECC71").pack(side="left", padx=20, pady=15)
        ctk.CTkLabel(summary_frame, text=f"Payments: {payment_count} (Rs. {payment_amount:,.0f})", 
                    font=ctk.CTkFont(size=14, weight="bold"), text_color="#3498DB").pack(side="left", padx=20, pady=15)
        ctk.CTkLabel(summary_frame, text=f"Outstanding Credit: Rs. {outstanding_credit:,.0f}", 
                    font=ctk.CTkFont(size=14, weight="bold"), text_color="#E67E22").pack(side="left", padx=20, pady=15)
        
        # Filter Frame
        filter_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        filter_frame.pack(fill="x", padx=30, pady=10)
        
        ctk.CTkLabel(filter_frame, text="Filter:", font=ctk.CTkFont(size=12)).pack(side="left", padx=5)
        
        filter_combo = ctk.CTkComboBox(
            filter_frame,
            values=["All", "Cash", "Credit", "Online Transfer", "Today", "This Week", "This Month"],
            width=150,
            height=30
        )
        filter_combo.pack(side="left", padx=10)
        filter_combo.set("All")
        
        # Transactions List
        list_frame = ctk.CTkScrollableFrame(dialog, height=400)
        list_frame.pack(fill="both", expand=True, padx=30, pady=10)
        
        # Headers
        headers = ["Invoice", "Customer", "Amount", "Payment", "Date", "Status"]
        header_frame = ctk.CTkFrame(list_frame, fg_color=("gray85", "gray25"))
        header_frame.pack(fill="x", pady=5)
        
        # Configure grid columns for header
        for i in range(len(headers)):
            header_frame.grid_columnconfigure(i, weight=1)
        
        col_widths = [130, 130, 100, 100, 120, 100]
        for i, (h, w) in enumerate(zip(headers, col_widths)):
            ctk.CTkLabel(header_frame, text=h, font=ctk.CTkFont(size=12, weight="bold"), width=w).grid(row=0, column=i, padx=5, pady=8, sticky="w")
        
        payment_labels = db.get_credit_payment_labels()

        # Get all sales
        db.cursor.execute("""
            SELECT id, invoice_number, customer_name, grand_total, payment_mode, created_at, is_credit
            FROM sales 
            WHERE grand_total != 0
            ORDER BY created_at DESC
        """)
        all_sales = db.cursor.fetchall()
        
                # Display sales - CLICKABLE ROWS
            
        for sale in all_sales:
            sale_id, invoice, customer, amount, payment, date, is_credit = sale
            is_payment = amount < 0
            payment_type = payment_labels.get(sale_id, "Credit Payment") if is_payment else payment
            
            # Create clickable row frame with explicit width
            row = ctk.CTkFrame(list_frame, fg_color="transparent", cursor="hand2" if not is_payment else "arrow", height=35)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)
            
            # Configure grid columns
            for i in range(len(headers)):
                row.grid_columnconfigure(i, weight=1)
            
            # ========== FIX HERE ==========
            if not is_payment:
                row.bind("<Button-1>", partial(self.on_row_click, invoice))
            
            values = [
                invoice,
                customer[:15] if customer else "Walk-in",
                f"Rs. {abs(amount):,.0f}",
                payment_type,
                date[:10] if isinstance(date, str) else date.strftime('%Y-%m-%d'),
                "Payment" if is_payment else ("Credit Sale" if is_credit else "Paid")
            ]
            
            status_color = "#3498DB" if is_payment else ("#E74C3C" if is_credit else "#2ECC71")
            payment_color = "#3498DB" if is_payment else "gray10"
            colors_text = ["gray10", "gray10", "gray10", payment_color, "gray10", status_color]
            
            for i, (cell, color, w) in enumerate(zip(values, colors_text, col_widths)):
                lbl = ctk.CTkLabel(row, text=str(cell), font=ctk.CTkFont(size=11), 
                           width=w, text_color=color, anchor="w")
                lbl.grid(row=0, column=i, padx=5, pady=5, sticky="w")
                # ========== FIX HERE ==========
                if not is_payment:
                    lbl.bind("<Button-1>", partial(self.on_row_click, invoice))
            
            # Hover effect
            if not is_payment:
                def on_enter(e, r=row):
                    r.configure(fg_color=("gray90", "gray20"))
                
                def on_leave(e, r=row):
                    r.configure(fg_color="transparent")
                
                row.bind("<Enter>", on_enter)
                row.bind("<Leave>", on_leave)
        
        # Close Button
        ctk.CTkButton(
            dialog,
            text="Close",
            command=dialog.destroy,
            width=120,
            height=35
        ).pack(pady=15)
    
    def show_inventory(self):
        self.clear_content()
        self.header.configure(text="Inventory Management")
        
        from inventory import InventoryManager
        InventoryManager(self.content_frame)
    
    def show_sales(self):
        self.clear_content()
        self.header.configure(text="Sales & Billing")
        
        from sales import SalesManager
        SalesManager(self.content_frame)
    
    def show_expenses(self):
        self.clear_content()
        self.header.configure(text="Expenses")
        
        from expenses import ExpensesManager
        ExpensesManager(self.content_frame, main_window=self)

    def show_customers(self):
        self.clear_content()
        self.header.configure(text="Customer Management")
    
        from customers import CustomersManager
        CustomersManager(self.content_frame)
    
    def show_supplier(self):
        self.clear_content()
        self.header.configure(text="Supplier Management")
        try:
            from supplier_management import SupplierManager
            SupplierManager(self.content_frame)
        except Exception as e:
            ctk.CTkLabel(
                self.content_frame,
                text="Supplier screen failed to load.",
                font=ctk.CTkFont(size=20, weight="bold"),
                text_color="#E74C3C"
            ).pack(pady=(80, 10))

            ctk.CTkLabel(
                self.content_frame,
                text=str(e),
                font=ctk.CTkFont(size=13),
                text_color="gray"
            ).pack(pady=5)

            ctk.CTkButton(
                self.content_frame,
                text="Retry",
                width=120,
                command=self.show_supplier
            ).pack(pady=20)

            messagebox.showerror("Supplier Error", f"Failed to open supplier screen:\n\n{str(e)}")

    def show_analytics(self):
        self.clear_content()
        self.header.configure(text="Analytics Review")
    
        from analytical_review import AnalyticsReview
        AnalyticsReview(self.content_frame, main_window=self)

    def show_reports(self):
        self.clear_content()
        self.header.configure(text="Reports")

        # Test - direct button banaein
        test_btn = ctk.CTkButton(
        self.content_frame,
        text="TEST BUTTON",
        fg_color="red",
        command=lambda: print("TEST BUTTON WORKS!")
        )
        
        from reports import ReportsManager
        ReportsManager(self.content_frame)
    
    def show_settings(self):
        self.clear_content()
        self.header.configure(text="Settings")
        
        from settings import SettingsManager
        SettingsManager(self.content_frame)
    
    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def darken_color(self, hex_color):
        color_map = {
            "#2ECC71": "#27AE60",
            "#3498DB": "#2980B9",
            "#9B59B6": "#8E44AD",
            "#E67E22": "#D35400",
            "#1ABC9C": "#16A085",
        }
        return color_map.get(hex_color, hex_color)
    
    def logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.root.destroy()
            from login_screen import LoginWindow
            login = LoginWindow()
            login.run()
    
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = Dashboard()
    app.run()
