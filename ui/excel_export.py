import os
import time
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from database import get_working_directory, backup_file


def export_ledger_excel(rows, d_from, d_to):
    wb = Workbook()
    ws = wb.active
    ws.title = "Ledger"
    ws.append(["Weigh Lock - Ledger", f"{d_from} to {d_to}", time.strftime('%Y-%m-%d %H:%M')])
    ws.append(["ID", "Truck", "Challan", "Slip", "Material", "Gross", "Tare", "Net", "Amount", "Paid", "Due", "Date"])
    for c in ws[2]:
        c.font = Font(bold=True)
    for r in rows:
        # report_range rows: id, truck, challan, material, gross, tare, net, ts, amount, paid, due (+slip missing -> '-')
        if len(r) >= 11:
            _id, truck, challan, mat, g, t, n, ts, amt, paid, due = r[:11]
            slip = "-"
        else:
            _id, truck, challan, mat, g, t, n, ts = r[:8]
            amt = paid = due = 0
            slip = "-"
        ws.append([_id, truck, challan, slip, mat, g, t, n, amt or 0, paid or 0, due or 0, ts])
    for col in "ABCDEFGHIJKL":
        try:
            ws.column_dimensions[col].width = 14
        except Exception:
            pass
    out = os.path.join(get_working_directory(), "Receipts", f"Ledger_{d_from}_to_{d_to}_{int(time.time())}.xlsx")
    wb.save(out)
    try:
        backup_file(out)
    except Exception:
        pass
    return out
