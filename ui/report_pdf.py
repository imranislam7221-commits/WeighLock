import os
import time
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from database import get_working_directory, backup_file, report_range
from config import COMPANY_NAME
try:
    from receipt import F_B, F_N
except Exception:
    F_B, F_N = 'Helvetica-Bold', 'Helvetica'


def generate_report_pdf(d_from, d_to, truck_q="", fee_per_slip=0, fee_per_ton=0):
    rows, trips, total_net, total_due = report_range(d_from, d_to, truck_q)
    total_ton = total_net / 1000 if total_net else 0
    try:
        fps = float(fee_per_slip or 0)
    except Exception:
        fps = 0
    try:
        fpt = float(fee_per_ton or 0)
    except Exception:
        fpt = 0
    fee = trips * fps + total_ton * fpt

    pdf_dir = os.path.join(get_working_directory(), "Receipts")
    os.makedirs(pdf_dir, exist_ok=True)
    path = os.path.join(pdf_dir, f"Report_{d_from}_to_{d_to}_{int(time.time())}.pdf")

    c = canvas.Canvas(path, pagesize=A4)
    w, h = A4
    c.setFont(F_B, 15)
    c.drawCentredString(w/2, h-45, f"{COMPANY_NAME.upper()} - HISAB REPORT")
    c.setFont(F_N, 10)
    c.drawCentredString(w/2, h-60, f"Date: {d_from} to {d_to}  |  Truck filter: {truck_q or 'sob'}")
    c.drawCentredString(w/2, h-73, f"Print: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    c.line(30, h-82, w-30, h-82)

    y = h-100
    c.setFont(F_N, 9)
    c.drawString(30, y, "SL  Truck        Challan        Material   Gross    Tare    Net    Date")
    y -= 6
    c.line(30, y, w-30, y)
    y -= 14
    for i, r in enumerate(rows[:80], 1):
        _id, truck, challan, mat, g, t, n, ts = r[:8]
        line = f"{i}. {_id} {str(truck)[:12]:12} {str(challan or '-')[:12]:12} {str(mat or '-')[:8]:8} {g} {t} {n} {str(ts)[:16]}"
        c.drawString(30, y, line[:110])
        y -= 13
        if y < 90:
            c.showPage()
            y = h-50
            c.setFont(F_N, 9)
    if len(rows) > 80:
        c.drawString(30, y, f"... aro {len(rows)-80} trip ache (PDF e 80 ta)")
        y -= 16
    c.line(30, y, w-30, y)
    y -= 18
    c.setFont(F_B, 12)
    c.drawString(30, y, f"Total trip: {trips}  |  Total Net: {total_net} KG ({total_ton:.3f} Ton)")
    y -= 20
    c.setFont(F_N, 11)
    c.drawString(30, y, f"Vara: slip proti {fps} x {trips} + ton proti {fpt} x {total_ton:.3f} = {fee:.0f} Tk")
    y -= 18
    try:
        due = total_due or 0
    except Exception:
        due = 0
    c.drawString(30, y, f"Baki/Due: {due:.0f} Tk")
    y -= 22
    c.setFont(F_B, 13)
    c.drawString(30, y, f"TOTAL VARA: {fee:.0f} Tk")
    c.save()
    try:
        backup_file(path)
    except Exception:
        pass
    return path, trips, total_net, fee
