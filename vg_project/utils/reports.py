"""
reports.py — exportable PDF + Excel reports.
"""

from io import BytesIO
import pandas as pd
from fpdf import FPDF


def to_excel_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    """Build a multi-sheet .xlsx in memory."""
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        for name, df in sheets.items():
            df.to_excel(w, sheet_name=name[:31], index=False)
    return buf.getvalue()


class _PDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "Video Game Sales - Report",
                  new_x="LMARGIN", new_y="NEXT", align="C")
        self.ln(2)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 8, f"Page {self.page_no()}", align="C")


def to_pdf_bytes(title: str, kpis: dict, top_table: pd.DataFrame,
                 narrative: str | None = None) -> bytes:
    """Compact one-page summary PDF (ASCII-safe for built-in fonts)."""
    def _safe(s):
        return str(s).encode("latin-1", "ignore").decode("latin-1")

    pdf = _PDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, _safe(title), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    # KPIs
    pdf.set_font("Helvetica", "", 10)
    for k, v in kpis.items():
        pdf.cell(0, 6, _safe(f"- {k}: {v}"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # Narrative
    if narrative:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, "AI Insights", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        # ASCII-safe (FPDF default font has no full unicode)
        safe = narrative.encode("latin-1", "ignore").decode("latin-1")
        pdf.multi_cell(0, 5, safe)
        pdf.ln(2)

    # Top table
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Top Rows", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 8)
    cols = list(top_table.columns)[:5]
    col_w = 190 / max(len(cols), 1)
    for c in cols:
        pdf.cell(col_w, 6, str(c)[:18], border=1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 8)
    for _, row in top_table.head(15).iterrows():
        for c in cols:
            val = str(row[c])[:18].encode("latin-1", "ignore").decode("latin-1")
            pdf.cell(col_w, 6, val, border=1)
        pdf.ln()

    return bytes(pdf.output())
