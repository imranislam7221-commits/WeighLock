import os
import re
import time
import logging
from reportlab.lib.pagesizes import A5
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from database import get_working_directory, backup_file
from config import COMPANY_NAME
from logger import get_logger

log = get_logger("receipt")

def _find_bangla_font():
    # Windows fonts + common Linux paths + bundled
    candidates = [
        r"C:\Windows\Fonts\Nirmala.ttf",
        r"C:\Windows\Fonts\NirmalaB.ttf",
        r"C:\Windows\Fonts\NirmalaS.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansBengali-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansBengali-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        os.path.join(os.path.dirname(__file__), "fonts", "NotoSansBengali-Regular.ttf"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


_BN = False
_font_path = _find_bangla_font()
try:
    if _font_path:
        pdfmetrics.registerFont(TTFont('Nirmala', _font_path))
        _BN = True
        log.info("Bangla font loaded: %s", _font_path)
    else:
        log.warning("No Bangla font found, using Helvetica fallback")
except Exception as e:
    log.warning("Bangla font load failed: %s", e)
    _BN = False

F_B = 'Nirmala' if _BN else 'Helvetica-Bold'
F_N = 'Nirmala' if _BN else 'Helvetica'
F_I = 'Nirmala' if _BN else 'Helvetica-Oblique'


def _safe(s):
    s = (s or "NA").strip() or "NA"
    return re.sub(r'[\\/:*?"<>| ]+', "_", s)[:30]


def generate_pdf_receipt(truck_no, material, gross, tare, net,
                         driver="", supplier="", slip_no="", mobile="",
                         challan_no="", product="", owner="", address="", reprint=False,
                         amount=0, paid=0, due=0, operator=""):
    if not truck_no or not str(truck_no).strip():
        raise ValueError("Truck number din")
    gross = float(gross); tare = float(tare); net = float(net)

    pdf_dir = os.path.join(get_working_directory(), "Receipts")
    os.makedirs(pdf_dir, exist_ok=True)
    if not slip_no:
        slip_no = f"{int(time.time())}"
    tag = "_REPRINT" if reprint else ""
    path = os.path.join(pdf_dir, f"Slip_{_safe(truck_no)}_{slip_no}{tag}.pdf")

    c = canvas.Canvas(path, pagesize=A5)
    w, h = A5
    c.setFont(F_B, 16)
    c.drawCentredString(w/2, h-50, COMPANY_NAME.upper())
    c.setFont(F_B, 11)
    if reprint:
        c.drawCentredString(w/2, h-62, "DUPLICATE / REPRINT COPY")
        c.setFont(F_N, 10)
        c.drawCentredString(w/2, h-74, "ডিজিটাল ওয়েইব্রিজ রশিদ - Digital Receipt")
        c.line(30, h-82, w-30, h-82)
        y = h-107
    else:
        c.setFont(F_N, 10)
        c.drawCentredString(w/2, h-65, "ডিজিটাল ওয়েইব্রিজ রশিদ - Digital Receipt")
        c.line(30, h-75, w-30, h-75)
        y = h-100
    c.setFont(F_N, 11)
    c.drawString(30, y, f"Slip No: {slip_no}"); y -= 18
    c.drawString(30, y, f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}"); y -= 18
    c.drawString(30, y, f"ট্রাক / Truck: {truck_no}"); y -= 18
    c.drawString(30, y, f"Challan No: {challan_no or '-'}"); y -= 18
    c.drawString(30, y, f"ড্রাইভার / Driver: {driver or '-'}  Mobile: {mobile or '-'}"); y -= 18
    if owner:
        c.drawString(30, y, f"মালিক / Owner: {owner}"); y -= 18
    if address:
        c.drawString(30, y, f"ঠিকানা / Address: {address}"); y -= 18
    c.drawString(30, y, f"Party/Supplier: {supplier or '-'}"); y -= 18
    if product:
        c.drawString(30, y, f"Product: {product}"); y -= 18
    c.drawString(30, y, f"মাল / Material: {material or '-'}"); y -= 22

    c.line(30, y, w-30, y); y -= 20
    c.drawString(30, y, f"Gross (1st): {gross} KG"); y -= 18
    c.drawString(30, y, f"Tare (2nd): {tare} KG"); y -= 18
    c.setFont(F_B, 13)
    c.drawString(30, y, f"NET: {net} KG"); y -= 20
    try:
        amt, pd, du = float(amount or 0), float(paid or 0), float(due or 0)
    except Exception as e:
        log.debug("amount parse failed: %s", e)
        amt = pd = du = 0
    if amt > 0 or pd > 0 or du > 0:
        c.setFont(F_N, 11)
        c.drawString(30, y, f"Vara: {amt:.0f} Tk  Paid: {pd:.0f}  Due: {du:.0f}"); y -= 18
        if operator:
            c.drawString(30, y, f"Operator: {operator}"); y -= 18
    else:
        y -= 22

    c.setFont(F_N, 9)
    c.drawString(30, y, "Operator sign: __________    Driver sign: __________")
    c.setFont(F_I, 9)
    c.drawCentredString(w/2, 50, "ধন্যবাদ। Thank you. Powered by Weigh Lock.")
    c.save()
    try:
        backup_file(path)
    except Exception as e:
        log.debug("backup_file failed: %s", e)
    return path
