import os
from datetime import datetime

from reportlab.lib.pagesizes import A5
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


def generate_invoice(
    invoice_num,
    customer_name,
    customer_contact,
    items,
    subtotal,
    discount,
    grand_total,
    payment,
    output_dir="invoices"
):
    # Create output directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    pdf_path = os.path.join(output_dir, f"{invoice_num}.pdf")
    
    # A5 size
    width, height = A5
    
    # Create canvas
    c = canvas.Canvas(pdf_path, pagesize=A5)
    
    # Date
    today = datetime.now().strftime("%d-%m-%Y %H:%M")
    customer_contact = customer_contact or "N/A"
    customer_name = customer_name or "Walk-in Customer"

    # ==========================================
    # 1. LEFT SIDE: Shop Name & Location
    # ==========================================
    c.setFont("Helvetica-Bold", 16)
    c.drawString(30, height - 40, "SM ENTERPRISES")
    
    c.setFont("Helvetica", 10)
    c.drawString(30, height - 55, "Fresh Juice Distribution")
    c.drawString(30, height - 68, "Swat, KP, Pakistan")
    c.drawString(30, height - 81, "Contact: 0348-0906263")

    # ==========================================
    # 2. RIGHT SIDE: Invoice No & Date
    # ==========================================
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(width - 30, height - 40, f"Invoice #: {invoice_num}")
    
    c.setFont("Helvetica", 10)
    c.drawRightString(width - 30, height - 55, f"Date: {today}")
    c.drawRightString(width - 30, height - 70, f"Payment: {payment}")

    # ==========================================
    # 3. BILL TO: Customer Info (Right Side)
    # ==========================================
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(width - 30, height - 95, "BILL TO:")
    
    c.setFont("Helvetica", 10)
    c.drawRightString(width - 30, height - 110, f"Name: {customer_name}")
    c.drawRightString(width - 30, height - 125, f"Contact: {customer_contact}")

    # Line divider
    c.line(20, height - 140, width - 20, height - 140)

    # ==========================================
    # 4. TABLE HEADERS
    # ==========================================
    y_position = height - 165
    
    # Header background
    c.setFillColor(colors.lightgrey)
    c.rect(20, y_position - 5, width - 40, 20, fill=1)
    c.setFillColor(colors.black)
    
    # Header text
    c.setFont("Helvetica-Bold", 10)
    c.drawString(30, y_position, "S.No")
    c.drawString(70, y_position, "Description")
    c.drawString(200, y_position, "Price")
    c.drawString(250, y_position, "Qty")
    c.drawRightString(width - 30, y_position, "Total")

    # ==========================================
    # 5. ITEMS (Loop)
    # ==========================================
    y_position -= 25
    c.setFont("Helvetica", 10)
    
    for i, item in enumerate(items, 1):
        item_total = float(item["price"]) * int(item["qty"])
        
        c.drawString(35, y_position, str(i))
        c.drawString(70, y_position, item["name"][:25])
        c.drawString(200, y_position, f"{float(item['price']):,.0f}")
        c.drawString(255, y_position, str(item["qty"]))
        c.drawRightString(width - 30, y_position, f"{item_total:,.0f}")
        
        y_position -= 20
        
        # Page break if needed
        if y_position < 100:
            break

    # ==========================================
    # 6. SUBTOTAL, DISCOUNT, GRAND TOTAL
    # ==========================================
    # Line before totals
    c.line(20, y_position + 10, width - 20, y_position + 10)
    y_position -= 5
    
    # Subtotal
    c.setFont("Helvetica", 10)
    c.drawString(200, y_position, "Subtotal:")
    c.drawRightString(width - 30, y_position, f"Rs. {subtotal:,.0f}/-")
    y_position -= 15
    
    # Discount
    c.drawString(200, y_position, "Discount:")
    c.drawRightString(width - 30, y_position, f"Rs. {discount:,.0f}/-")
    y_position -= 15
    
    # Line before grand total
    c.line(20, y_position + 5, width - 20, y_position + 5)
    y_position -= 5
    
    # Grand Total
    c.setFont("Helvetica-Bold", 12)
    c.drawString(200, y_position, "Grand Total:")
    c.drawRightString(width - 30, y_position, f"Rs. {grand_total:,.0f}/-")

    # ==========================================
    # 7. FOOTER - Thank You
    # ==========================================
    c.setFont("Helvetica-Oblique", 9)
    c.drawCentredString(width/2, 40, "Thank you for choosing JUGO SWAT!")
    c.drawCentredString(width/2, 25, "Fresh Juice - Swat")

    # Save PDF
    c.save()
    
    # Generate text receipt also
    invoice_text = generate_text_receipt(
        invoice_num, today, customer_name, customer_contact,
        items, subtotal, discount, grand_total, payment
    )
    
    print(f"Invoice '{pdf_path}' generated successfully!")
    return invoice_text, pdf_path


def generate_text_receipt(invoice_num, date_str, customer_name, customer_contact,
                          items, subtotal, discount, grand_total, payment):
    """Generate simple text receipt for display"""
    
    text = f"""
{'='*50}
              SM ENTERPRISES
        Fresh Juice Distribution
{'='*50}

Invoice #: {invoice_num}
Date: {date_str}
Customer: {customer_name}
Contact: {customer_contact}
Payment: {payment}

{'-'*50}
Items:
{'-'*50}
"""
    for i, item in enumerate(items, 1):
        line = (
            f"{i}. {item['name'][:25]:<25} {item['qty']} x Rs.{int(item['price'])} "
            f"= Rs.{int(item['price'] * item['qty'])}"
        )
        text += line + "\n"

    text += f"""
{'-'*50}
Subtotal:        Rs. {int(subtotal):,}
Discount:        Rs. {int(discount):,}
{'='*50}
GRAND TOTAL:     Rs. {int(grand_total):,}
{'='*50}

      Thank you for your business!
           JUGO SWAT - Swat
"""
    return text


# Test function
if __name__ == "__main__":
    test_items = [
        {"name": "Apple Juice", "price": 500, "qty": 2},
        {"name": "Mango Juice", "price": 600, "qty": 1},
        {"name": "Orange Juice", "price": 450, "qty": 3}
    ]
    
    generate_invoice(
        invoice_num="JUGO-001",
        customer_name="Test Customer",
        customer_contact="0312-1234567",
        items=test_items,
        subtotal=2950,
        discount=100,
        grand_total=2850,
        payment="Cash"
    )