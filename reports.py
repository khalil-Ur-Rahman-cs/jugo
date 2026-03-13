from wsgiref import headers

import customtkinter as ctk
from tkinter import messagebox, filedialog

from matplotlib.pyplot import title
from database import db
from datetime import datetime, timedelta
import calendar
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from ui_utils import center_window



class ReportsManager:
    def __init__(self, parent_frame):
        self.parent = parent_frame
        self.current_report_data = None  # Store current report for PDF export
        self.current_report_title = ""
        self.setup_ui()
    
    def setup_ui(self):
        # Clear parent
        for widget in self.parent.winfo_children():
            widget.destroy()
        
        # Create main scrollable frame
        self.main_scroll = ctk.CTkScrollableFrame(self.parent)
        self.main_scroll.pack(fill="both", expand=True)
        
        # Title
        ctk.CTkLabel(
            self.main_scroll,
            text="📊 Business Reports",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(pady=(20, 10))
        
        # Report Types Frame
        types_frame = ctk.CTkFrame(self.main_scroll)
        types_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            types_frame,
            text="Select Report Type:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=20, pady=(15, 10))
        
        self.report_type = ctk.CTkComboBox(
            types_frame,
            values=[
                "Daily Sales Report",
                "Monthly Sales Report", 
                "Stock Report",
                "Profit/Loss Report",
                "Top Selling Flavors",
                "Customer Credit Report"
            ],
            width=300,
            height=35,
            command=self.on_report_type_change
        )
        self.report_type.pack(anchor="w", padx=20, pady=(0, 15))
        self.report_type.set("Daily Sales Report")
        
        # Date Selection Frame
        self.date_frame = ctk.CTkFrame(self.main_scroll)
        self.date_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            self.date_frame,
            text="Select Date:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=20, pady=(15, 10))
        
        # Date entries
        date_inputs = ctk.CTkFrame(self.date_frame, fg_color="transparent")
        date_inputs.pack(anchor="w", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(date_inputs, text="From:").pack(side="left", padx=(0, 10))
        self.from_date = ctk.CTkEntry(date_inputs, width=120, placeholder_text="YYYY-MM-DD")
        self.from_date.pack(side="left", padx=(0, 20))
        self.from_date.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        ctk.CTkLabel(date_inputs, text="To:").pack(side="left", padx=(0, 10))
        self.to_date = ctk.CTkEntry(date_inputs, width=120, placeholder_text="YYYY-MM-DD")
        self.to_date.pack(side="left")
        self.to_date.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        # Generate Button
        ctk.CTkButton(
            self.main_scroll,
            text="📈 Generate Report",
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#2ECC71",
            hover_color="#27AE60",
            command=self.generate_report,
            width=200,
            height=45
        ).pack(pady=20)
        
        # Results Frame - Non-scrollable, inside main scroll
        self.results_frame = ctk.CTkFrame(self.main_scroll)
        self.results_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(
            self.results_frame,
            text="Report will appear here...",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        ).pack(pady=100)
    
    def on_report_type_change(self, choice):
        if choice == "Stock Report":
            self.date_frame.pack_forget()
        else:
            self.date_frame.pack(fill="x", padx=20, pady=10, before=self.results_frame)
    
    def generate_report(self):
        report_type = self.report_type.get()
        
        # Clear results
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        if report_type == "Daily Sales Report":
            self.generate_daily_sales()
        elif report_type == "Monthly Sales Report":
            self.generate_monthly_sales()
        elif report_type == "Stock Report":
            self.generate_stock_report()
        elif report_type == "Profit/Loss Report":
            self.generate_profit_report()
        elif report_type == "Top Selling Flavors":
            self.generate_top_flavors()
        elif report_type == "Customer Credit Report":
            self.generate_credit_report()
    
    def show_view_all_dialog(self, title, headers, all_rows, summary_data=None, is_detailed_sales=False):
        """Show all records in a dialog with View All button and Save PDF"""
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title(f"View All - {title}")
        dialog.transient(self.parent)
        dialog.grab_set()
        center_window(dialog, 1200, 750)
        
        # Main container with scroll
        main_container = ctk.CTkScrollableFrame(dialog, height=650)
        main_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Shop Header
        header_frame = ctk.CTkFrame(main_container, fg_color="#3990E7")
        header_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            header_frame,
            text="SM ENTERPRISES",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="white"
        ).pack(pady=(15, 5))
        
        ctk.CTkLabel(
            header_frame,
            text="JUGO SWAT",
            font=ctk.CTkFont(size=14),
            text_color="#BDC3C7"
        ).pack(pady=(0, 15))
        
        # Title
        ctk.CTkLabel(
            main_container,
            text=f"📋 {title}",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=10)
        
        # Total records
        ctk.CTkLabel(
            main_container,
            text=f"Total Records: {len(all_rows)}",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        ).pack(pady=(0, 10))
        
        # Summary cards if available
        if summary_data:
            summary_frame = ctk.CTkFrame(main_container)
            summary_frame.pack(fill="x", pady=10)
            
            col = 0
            for key, value in summary_data.items():
                self.create_dialog_stat_card(summary_frame, key, str(value), col)
                col += 1
        
        # Scrollable table
        table_container = ctk.CTkScrollableFrame(main_container, height=400)
        table_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Headers
        header_frame = ctk.CTkFrame(table_container, fg_color=("gray85", "gray25"))
        header_frame.pack(fill="x", pady=2)
        
        # Adjust column widths based on content
        col_width = 140 if is_detailed_sales else 120
        
        for i, h in enumerate(headers):
            ctk.CTkLabel(header_frame, text=h, font=ctk.CTkFont(size=12, weight="bold"), width=col_width).grid(row=0, column=i, padx=5, pady=8)
        
        # All rows
        for row_data in all_rows:
            row_frame = ctk.CTkFrame(table_container, fg_color="transparent")
            row_frame.pack(fill="x", pady=1)
            
            for i, cell in enumerate(row_data):
                ctk.CTkLabel(row_frame, text=str(cell), font=ctk.CTkFont(size=11), width=col_width).grid(row=0, column=i, padx=5, pady=5)
        
        # Button frame at bottom
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=15)
        
        # Save as PDF Button (Green)
        ctk.CTkButton(
            btn_frame,
            text="📄 Save as PDF",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#2ECC71",
            hover_color="#27AE60",
            command=lambda: self.save_report_as_pdf(title, headers, all_rows, summary_data),
            width=140,
            height=40
        ).pack(side="left", padx=5)
        
        # Close Button (Gray)
        ctk.CTkButton(
            btn_frame,
            text="❌ Close",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#95A5A6",
            hover_color="#7F8C8D",
            command=dialog.destroy,
            width=120,
            height=40
        ).pack(side="left", padx=5)
    
    def create_dialog_stat_card(self, parent, title, value, column):
        """Create stat card for dialog"""
        card = ctk.CTkFrame(parent)
        card.grid(row=0, column=column, padx=10, pady=10, sticky="nsew")
        parent.grid_columnconfigure(column, weight=1)
        
        ctk.CTkLabel(card, text=str(value), font=ctk.CTkFont(size=18, weight="bold"), text_color="#2ECC71").pack(pady=(10, 5))
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=11), text_color="gray").pack(pady=(5, 10))
    
    def add_action_buttons(self, title, headers, all_rows, summary_data=None, is_detailed_sales=False):
        """Add View All, Save as PDF, and Close buttons"""
    
        # Pehle se existing buttons hataein
        for widget in self.results_frame.winfo_children():
            if hasattr(widget, '_is_button_frame'):
                widget.destroy()
    
        # Naya frame
        btn_frame = ctk.CTkFrame(self.results_frame, fg_color="transparent")
        btn_frame._is_button_frame = True  # Mark for identification
    
        btn_frame.pack(side="bottom", fill="x", padx=20, pady=15)
        
        # View All Button
        ctk.CTkButton(
            btn_frame,
            text="👁️ View All",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#3498DB",
            hover_color="#2980B9",
            command=lambda: self.show_view_all_dialog(title, headers, all_rows, summary_data, is_detailed_sales),
            width=120,
            height=35
        ).pack(side="left", padx=5)
        
        # Save as PDF Button
        ctk.CTkButton(
            btn_frame,
            text="📄 Save as PDF",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#E67E22",
            hover_color="#D35400",
            command=lambda: self.save_report_as_pdf(title, headers, all_rows, summary_data),
            width=120,
            height=35
        ).pack(side="left", padx=5)
        
        # Close Button
        ctk.CTkButton(
            btn_frame,
            text="❌ Close",
            font=ctk.CTkFont(size=12),
            fg_color="#95A5A6",
            hover_color="#7F8C8D",
            command=lambda: self.clear_report(),
            width=100,
            height=35
        ).pack(side="left", padx=5)

        # Force update
        btn_frame.update()
        self.results_frame.update()
    
    def clear_report(self):
        """Clear report and show default message"""
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        ctk.CTkLabel(
            self.results_frame,
            text="Report will appear here...",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        ).pack(pady=100)
    
    def save_report_as_pdf(self, title, headers, rows, summary_data=None):
        """Save report as PDF file with shop branding"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"{title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}"
        )
        
        if not filename:
            return
        
        try:
            doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=40, bottomMargin=40)
            elements = []
            styles = getSampleStyleSheet()
            
            # Shop Header Style
            shop_name_style = ParagraphStyle(
                'ShopName',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor("#5369F7"),
                spaceAfter=5,
                alignment=1,
                fontName='Helvetica-Bold'
            )
            
            shop_tagline_style = ParagraphStyle(
                'ShopTagline',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.HexColor("#7F8C8D"),
                spaceAfter=20,
                alignment=1
            )
            
            # Shop Header
            elements.append(Paragraph("SM INTERPRISES", shop_name_style))
            elements.append(Paragraph("JUGO - SWAT", shop_tagline_style))
            
            # Decorative line
            line_style = ParagraphStyle(
                'Line',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.HexColor("#BDC3C7"),
                alignment=1
            )
            elements.append(Paragraph("─" * 60, line_style))
            elements.append(Spacer(1, 10))
            
            # Report Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading2'],
                fontSize=18,
                textColor=colors.HexColor("#2C3E50"),
                spaceAfter=10,
                alignment=1
            )
            elements.append(Paragraph(title, title_style))
            
            # Date
            date_style = ParagraphStyle(
                'DateStyle',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.gray,
                alignment=1
            )
            elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", date_style))
            elements.append(Spacer(1, 20))
            
            # Summary if available
            if summary_data:
                summary_title_style = ParagraphStyle(
                    'SummaryTitle',
                    parent=styles['Heading3'],
                    fontSize=14,
                    textColor=colors.HexColor("#2C3E50"),
                    spaceAfter=10
                )
                elements.append(Paragraph("Summary", summary_title_style))
                
                summary_table_data = [[k, str(v)] for k, v in summary_data.items()]
                summary_table = Table(summary_table_data, colWidths=[2.5*inch, 2.5*inch])
                summary_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#ECF0F1")),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor("#2C3E50")),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 11),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('LEFTPADDING', (0, 0), (-1, -1), 12),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 12),
                ]))
                elements.append(summary_table)
                elements.append(Spacer(1, 25))
            
            # Main table
            table_title_style = ParagraphStyle(
                'TableTitle',
                parent=styles['Heading3'],
                fontSize=14,
                textColor=colors.HexColor("#2C3E50"),
                spaceAfter=10
            )
            elements.append(Paragraph("Details", table_title_style))
            elements.append(Spacer(1, 5))
            
            # Prepare table data
            table_data = [headers] + [list(row) for row in rows]
            
            # Calculate column widths based on number of columns
            num_cols = len(headers)
            if num_cols <= 4:
                col_widths = [1.4*inch] * num_cols
            elif num_cols <= 6:
                col_widths = [1.0*inch] * num_cols
            else:
                col_widths = [0.8*inch] * num_cols
            
            table = Table(table_data, colWidths=col_widths)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#34495E")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 0), (-1, 0), 12),
                
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F9FA")]),
            ]))
            
            elements.append(table)
            
            # Footer
            elements.append(Spacer(1, 40))
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.gray,
                alignment=1
            )
            # elements.append(Paragraph("This is a computer generated report from JUGO SWAT.", footer_style))
            elements.append(Paragraph("Thank you for your business!", footer_style))
            
            # Build PDF
            doc.build(elements)
            
            messagebox.showinfo("Success", f"Report saved successfully!\n\nLocation: {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save PDF: {str(e)}")
    
    def generate_daily_sales(self):
        from_date = self.from_date.get()
        to_date = self.to_date.get()
        
        try:
            payment_labels = db.get_credit_payment_labels()

            # Include sales and credit payments
            db.cursor.execute("""
                SELECT 
                    s.id,
                    s.invoice_number,
                    c.name as customer_name,
                    DATE(s.created_at) as date,
                    s.grand_total as total_amount,
                    s.is_credit,
                    s.payment_mode
                FROM sales s
                LEFT JOIN customers c ON s.customer_id = c.id
                WHERE DATE(s.created_at) BETWEEN ? AND ?
                  AND s.grand_total != 0
                ORDER BY s.created_at DESC
            """, (from_date, to_date))
            
            detailed_results = db.cursor.fetchall()
            
            if not detailed_results:
                ctk.CTkLabel(self.results_frame, text="No sales data found for selected period.", text_color="gray").pack(pady=50)
                return
            
            # Title
            ctk.CTkLabel(
                self.results_frame,
                text=f"Daily Sales Report ({from_date} to {to_date})",
                font=ctk.CTkFont(size=18, weight="bold")
            ).pack(pady=(20, 10))
            
            # Summary (sales vs payments)
            sales_rows = [r for r in detailed_results if (r[4] or 0) > 0]
            payment_rows = [r for r in detailed_results if (r[4] or 0) < 0]

            total_sales = len(sales_rows)
            total_amount = sum((r[4] or 0) for r in sales_rows)
            total_credit = sum((r[4] or 0) for r in sales_rows if r[5] == 1)
            total_cash = sum((r[4] or 0) for r in sales_rows if r[5] == 0)
            total_payments = sum(abs(r[4] or 0) for r in payment_rows)
            
            summary = ctk.CTkFrame(self.results_frame)
            summary.pack(fill="x", padx=20, pady=10)
            
            self.create_stat_card(summary, "Total Sales", str(total_sales), "#3498DB", 0)
            self.create_stat_card(summary, "Total Amount", f"Rs. {total_amount:,.0f}", "#2ECC71", 1)
            self.create_stat_card(summary, "Cash", f"Rs. {total_cash:,.0f}", "#27AE60", 2)
            self.create_stat_card(summary, "Credit", f"Rs. {total_credit:,.0f}", "#E74C3C", 3)
            self.create_stat_card(summary, "Payments", f"Rs. {total_payments:,.0f}", "#3498DB", 4)
            
            # Configure grid columns
            for i in range(5):
                summary.grid_columnconfigure(i, weight=1)
            
            # Prepare data for table and buttons - Detailed view with Invoice and Customer
            headers = ["Invoice #", "Customer", "Date", "Amount", "Type"]
            all_rows = []
            for row in detailed_results:
                sale_id, invoice, customer_name, date, total_amount, is_credit, _payment_mode = row
                if total_amount < 0:
                    trans_type = payment_labels.get(sale_id, "Credit Payment")
                    amount_display = abs(total_amount)
                else:
                    trans_type = "Credit" if is_credit else "Cash"
                    amount_display = total_amount
                all_rows.append((
                    invoice,
                    customer_name or "Walk-in",
                    date,
                    f"Rs. {amount_display:,.0f}",
                    trans_type
                ))
            
            # Show first 10 rows
            display_rows = all_rows[:10]
            self.create_table(headers, display_rows, is_detailed=True)
            
            # Summary data for PDF
            summary_data = {
                "Total Sales": str(total_sales),
                "Total Amount": f"Rs. {total_amount:,.0f}",
                "Cash": f"Rs. {total_cash:,.0f}",
                "Credit": f"Rs. {total_credit:,.0f}",
                "Payments": f"Rs. {total_payments:,.0f}"
            }
            
            # Add action buttons
            self.add_action_buttons(f"Daily Sales ({from_date} to {to_date})", headers, all_rows, summary_data, is_detailed_sales=True)
            
        except Exception as e:
            ctk.CTkLabel(self.results_frame, text=f"Error: {str(e)}", text_color="red").pack(pady=50)

            
    
    def generate_monthly_sales(self):
        try:
            db.cursor.execute("""
                SELECT 
                    strftime('%Y-%m', created_at) as month,
                    COUNT(*) as total_sales,
                    COALESCE(SUM(grand_total), 0) as total_amount
                FROM sales
                WHERE grand_total > 0
                  AND invoice_number NOT LIKE 'PAY-%'
                GROUP BY strftime('%Y-%m', created_at)
                ORDER BY month DESC
                LIMIT 12
            """)
            
            results = db.cursor.fetchall()
            
            if not results:
                ctk.CTkLabel(self.results_frame, text="No sales data found.", text_color="gray").pack(pady=50)
                return
            
            ctk.CTkLabel(
                self.results_frame,
                text="Monthly Sales Report (Last 12 Months)",
                font=ctk.CTkFont(size=18, weight="bold")
            ).pack(pady=(20, 10))
            
            # Summary
            total_amount = sum((r[2] or 0) for r in results)
            
            summary = ctk.CTkFrame(self.results_frame)
            summary.pack(fill="x", padx=20, pady=10)
            
            ctk.CTkLabel(summary, text=f"Total Revenue: Rs. {total_amount:,.0f}", 
                        font=ctk.CTkFont(size=18, weight="bold"), text_color="#2ECC71").pack(pady=20)
            
            # Prepare data
            headers = ["Month", "Sales Count", "Total Amount"]
            all_rows = [(r[0], r[1], f"Rs. {(r[2] or 0):,.0f}") for r in results]
            
            # Show first 10
            display_rows = all_rows[:10]
            self.create_table(headers, display_rows)
            
            summary_data = {"Total Revenue": f"Rs. {total_amount:,.0f}"}
            self.add_action_buttons("Monthly Sales Report", headers, all_rows, summary_data)
            
        except Exception as e:
            ctk.CTkLabel(self.results_frame, text=f"Error: {str(e)}", text_color="red").pack(pady=50)
    
    def generate_stock_report(self):
        try:
            db.cursor.execute("""
                SELECT 
                    name,
                    category,
                    stock,
                    sale_price,
                    cost_price,
                    (stock * cost_price) as stock_value
                FROM flavors
                ORDER BY stock ASC
            """)
            
            results = db.cursor.fetchall()
            
            if not results:
                ctk.CTkLabel(self.results_frame, text="No stock data found.", text_color="gray").pack(pady=50)
                return
            
            ctk.CTkLabel(
                self.results_frame,
                text="Current Stock Report",
                font=ctk.CTkFont(size=18, weight="bold")
            ).pack(pady=(20, 10))
            
            # Summary
            total_items = len(results)
            total_stock = sum(r[2] for r in results)
            total_value = sum(r[5] for r in results)
            low_stock = sum(1 for r in results if r[2] < 20)
            
            summary = ctk.CTkFrame(self.results_frame)
            summary.pack(fill="x", padx=20, pady=10)
            
            self.create_stat_card(summary, "Total Items", str(total_items), "#3498DB", 0)
            self.create_stat_card(summary, "Total Stock", f"{total_stock} BOX", "#2ECC71", 1)
            self.create_stat_card(summary, "Stock Value", f"Rs. {total_value:,.0f}", "#9B59B6", 2)
            self.create_stat_card(summary, "Low Stock", str(low_stock), "#E74C3C", 3)
            
            # Configure grid columns
            for i in range(4):
                summary.grid_columnconfigure(i, weight=1)
            
            # Prepare data
            headers = ["Flavor", "Category", "Stock", "Sale Price", "Value"]
            all_rows = [(r[0], r[1], r[2], f"Rs. {r[3]}", f"Rs. {r[5]:,.0f}") for r in results]
            
            display_rows = all_rows[:10]
            self.create_table(headers, display_rows)
            
            summary_data = {
                "Total Items": str(total_items),
                "Total Stock": f"{total_stock} BOX",
                "Stock Value": f"Rs. {total_value:,.0f}",
                "Low Stock Items": str(low_stock)
            }
            self.add_action_buttons("Stock Report", headers, all_rows, summary_data)
            
        except Exception as e:
            ctk.CTkLabel(self.results_frame, text=f"Error: {str(e)}", text_color="red").pack(pady=50)
    
    def generate_profit_report(self):
        from_date = self.from_date.get()
        to_date = self.to_date.get()
        
        try:
            # Get sales with cost prices
            db.cursor.execute("""
                SELECT 
                    s.grand_total,
                    SUM(si.quantity * f.cost_price) as total_cost
                FROM sales s
                JOIN sale_items si ON s.id = si.sale_id
                JOIN flavors f ON si.flavor_id = f.id
                WHERE DATE(s.created_at) BETWEEN ? AND ?
                GROUP BY s.id
            """, (from_date, to_date))
            
            results = db.cursor.fetchall()
            
            if not results:
                ctk.CTkLabel(self.results_frame, text="No data found for selected period.", text_color="gray").pack(pady=50)
                return
            
            total_revenue = sum(r[0] for r in results)
            total_cost = sum(r[1] for r in results)
            total_profit = total_revenue - total_cost
            profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
            
            ctk.CTkLabel(
                self.results_frame,
                text=f"Profit/Loss Report ({from_date} to {to_date})",
                font=ctk.CTkFont(size=18, weight="bold")
            ).pack(pady=(20, 10))
            
            # Summary Cards
            summary = ctk.CTkFrame(self.results_frame)
            summary.pack(fill="x", padx=20, pady=10)
            
            self.create_stat_card(summary, "Total Revenue", f"Rs. {total_revenue:,.0f}", "#3498DB", 0)
            self.create_stat_card(summary, "Total Cost", f"Rs. {total_cost:,.0f}", "#E74C3C", 1)
            self.create_stat_card(summary, "Net Profit", f"Rs. {total_profit:,.0f}", "#2ECC71", 2)
            self.create_stat_card(summary, "Margin", f"{profit_margin:.1f}%", "#9B59B6", 3)
            
            # Configure grid columns
            for i in range(4):
                summary.grid_columnconfigure(i, weight=1)
            
            # Profit bar
            bar_frame = ctk.CTkFrame(self.results_frame)
            bar_frame.pack(fill="x", padx=20, pady=20)
            
            ctk.CTkLabel(bar_frame, text="Profit Margin:", font=ctk.CTkFont(size=14)).pack(anchor="w")
            
            progress = ctk.CTkProgressBar(bar_frame, width=400, height=20)
            progress.pack(pady=10)
            progress.set(min(profit_margin / 100, 1.0))
            
            if profit_margin >= 30:
                progress.configure(progress_color="#2ECC71")
            elif profit_margin >= 15:
                progress.configure(progress_color="#F39C12")
            else:
                progress.configure(progress_color="#E74C3C")
            
            # For profit report, create a simple summary for PDF
            summary_data = {
                "Total Revenue": f"Rs. {total_revenue:,.0f}",
                "Total Cost": f"Rs. {total_cost:,.0f}",
                "Net Profit": f"Rs. {total_profit:,.0f}",
                "Profit Margin": f"{profit_margin:.1f}%"
            }
            
            # Empty table for PDF (just summary)
            headers = ["Metric", "Value"]
            all_rows = [(k, v) for k, v in summary_data.items()]
            self.add_action_buttons(f"Profit Report ({from_date} to {to_date})", headers, all_rows, summary_data)
            
        except Exception as e:
            ctk.CTkLabel(self.results_frame, text=f"Error: {str(e)}", text_color="red").pack(pady=50)
    
    def generate_top_flavors(self):
        try:
            db.cursor.execute("""
                SELECT 
                    f.name,
                    SUM(si.quantity) as total_qty,
                    SUM(si.total) as total_revenue
                FROM sale_items si
                JOIN flavors f ON si.flavor_id = f.id
                GROUP BY si.flavor_id
                ORDER BY total_qty DESC
                LIMIT 10
            """)
            
            results = db.cursor.fetchall()
            
            if not results:
                ctk.CTkLabel(self.results_frame, text="No sales data found.", text_color="gray").pack(pady=50)
                return
            
            ctk.CTkLabel(
                self.results_frame,
                text="🏆 Top 10 Selling Flavors",
                font=ctk.CTkFont(size=18, weight="bold")
            ).pack(pady=(20, 10))
            
            # Get all flavors (not just top 10) for View All
            db.cursor.execute("""
                SELECT 
                    f.name,
                    SUM(si.quantity) as total_qty,
                    SUM(si.total) as total_revenue
                FROM sale_items si
                JOIN flavors f ON si.flavor_id = f.id
                GROUP BY si.flavor_id
                ORDER BY total_qty DESC
            """)
            all_results = db.cursor.fetchall()
            
            headers = ["Rank", "Flavor", "Bottles Sold", "Revenue"]
            all_rows = [(i+1, r[0], r[1], f"Rs. {r[2]:,.0f}") for i, r in enumerate(all_results)]
            
            display_rows = all_rows[:10]
            self.create_table(headers, display_rows)
            
            summary_data = {"Total Flavors": str(len(all_results))}
            self.add_action_buttons("Top Selling Flavors", headers, all_rows, summary_data)
            
        except Exception as e:
            ctk.CTkLabel(self.results_frame, text=f"Error: {str(e)}", text_color="red").pack(pady=50)
    
    def generate_credit_report(self):
        try:
            # Get all customers with credit (not just those with credit_used > 0)
            db.cursor.execute("""
                SELECT 
                    c.name,
                    c.phone,
                    c.credit_limit,
                    COALESCE(SUM(CASE WHEN s.is_credit = 1 AND s.grand_total > 0 THEN s.grand_total ELSE 0 END), 0) -
                    COALESCE(SUM(CASE WHEN s.grand_total < 0 THEN ABS(s.grand_total) ELSE 0 END), 0) as credit_used
                FROM customers c
                LEFT JOIN sales s ON c.id = s.customer_id
                GROUP BY c.id
                ORDER BY credit_used DESC
            """)
            
            all_results = db.cursor.fetchall()
            
            # Filter for display (only those with credit)
            results = [r for r in all_results if r[3] > 0]
            
            if not results:
                ctk.CTkLabel(self.results_frame, text="No credit customers found.", text_color="gray").pack(pady=50)
                return
            
            ctk.CTkLabel(
                self.results_frame,
                text="💳 Customer Credit Report",
                font=ctk.CTkFont(size=18, weight="bold")
            ).pack(pady=(20, 10))
            
            total_credit = sum(r[3] for r in results)
            
            summary = ctk.CTkFrame(self.results_frame)
            summary.pack(fill="x", padx=20, pady=10)
            
            ctk.CTkLabel(summary, text=f"Total Outstanding Credit: Rs. {total_credit:,.0f}", 
                        font=ctk.CTkFont(size=18, weight="bold"), text_color="#E74C3C").pack(pady=20)
            
            headers = ["Customer", "Phone", "Credit Limit", "Used", "Remaining"]
            all_rows = [(r[0], r[1], f"Rs. {r[2]:,.0f}", f"Rs. {r[3]:,.0f}", f"Rs. {r[2]-r[3]:,.0f}") for r in all_results if r[3] > 0]
            
            display_rows = all_rows[:10]
            self.create_table(headers, display_rows)
            
            summary_data = {
                "Total Credit Customers": str(len(results)),
                "Total Outstanding": f"Rs. {total_credit:,.0f}"
            }
            self.add_action_buttons("Customer Credit Report", headers, all_rows, summary_data)
            
        except Exception as e:
            ctk.CTkLabel(self.results_frame, text=f"Error: {str(e)}", text_color="red").pack(pady=50)
    
    def create_stat_card(self, parent, title, value, color, column):
        card = ctk.CTkFrame(parent)
        card.grid(row=0, column=column, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=20, weight="bold"), text_color=color).pack(pady=(15, 5))
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=12), text_color="gray").pack(pady=(5, 15))
    
    def create_table(self, headers, rows, is_detailed=False):
        table_container = ctk.CTkScrollableFrame(self.results_frame, height=250)
        table_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Headers
        header_frame = ctk.CTkFrame(table_container, fg_color=("gray85", "gray25"))
        header_frame.pack(fill="x", pady=2)
        
        # Adjust column width based on table type
        col_width = 140 if is_detailed else 120
        
        for i, h in enumerate(headers):
            ctk.CTkLabel(header_frame, text=h, font=ctk.CTkFont(size=12, weight="bold"), width=col_width).grid(row=0, column=i, padx=5, pady=8)
        
        # Rows
        for row_data in rows:
            row_frame = ctk.CTkFrame(table_container, fg_color="transparent")
            row_frame.pack(fill="x", pady=1)
            
            for i, cell in enumerate(row_data):
                ctk.CTkLabel(row_frame, text=str(cell), font=ctk.CTkFont(size=11), width=col_width).grid(row=0, column=i, padx=5, pady=5)
