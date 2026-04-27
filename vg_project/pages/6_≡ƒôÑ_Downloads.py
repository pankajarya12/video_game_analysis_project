"""Export hub — cleaned CSV, SQLite DB, PDF and Excel reports."""
from pathlib import Path
import streamlit as st
from utils.auth import login_form
from utils.data_loader import load_raw, clean, merged_view, DB_PATH
from utils.reports import to_excel_bytes, to_pdf_bytes
from utils.insights import stat_insights

if not login_form():
    st.stop()

st.title("📥 Downloads & Reports")

# ---- Cleaned CSVs ---------------------------------------------------------
st.subheader("Cleaned datasets")
g, v = clean(*load_raw())
c1, c2 = st.columns(2)
c1.download_button("⬇️ games_clean.csv",
                   g.to_csv(index=False).encode(),
                   "games_clean.csv", "text/csv")
c2.download_button("⬇️ vgsales_clean.csv",
                   v.to_csv(index=False).encode(),
                   "vgsales_clean.csv", "text/csv")

# ---- SQLite DB ------------------------------------------------------------
st.subheader("SQLite database")
if Path(DB_PATH).exists():
    st.download_button("⬇️ videogames.db",
                       Path(DB_PATH).read_bytes(),
                       "videogames.db", "application/x-sqlite3")

st.divider()

# ---- Excel + PDF reports --------------------------------------------------
st.subheader("Analytical reports")
df = st.session_state.get("filtered_df")
if df is None or df.empty:
    df = merged_view()

# Multi-sheet Excel
sheets = {
    "merged": df,
    "top_games": df.groupby("name", as_index=False)["global_sales"].sum()
                   .sort_values("global_sales", ascending=False).head(50),
    "by_genre": df.groupby("genre", as_index=False)["global_sales"].sum(),
    "by_platform": df.groupby("platform", as_index=False)["global_sales"].sum(),
}
st.download_button("⬇️ report.xlsx",
                   to_excel_bytes(sheets),
                   "report.xlsx",
                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# One-page PDF summary
kpis = {
    "Rows": f"{len(df):,}",
    "Total global sales (M)": f"{df['global_sales'].sum():,.1f}",
    "Unique games":  f"{df['name'].nunique():,}",
    "Platforms":     f"{df['platform'].nunique():,}",
}
narrative = " ".join(stat_insights(df))
top = (df.groupby("name", as_index=False)["global_sales"].sum()
         .sort_values("global_sales", ascending=False).head(15))
pdf_bytes = to_pdf_bytes("Video Game Sales — Snapshot", kpis, top, narrative)
st.download_button("⬇️ report.pdf", pdf_bytes, "report.pdf", "application/pdf")
