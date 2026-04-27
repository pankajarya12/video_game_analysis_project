"""
app.py — main Streamlit entry point.

Pages (multi-page app via /pages folder):
    1_📊_Overview.py
    2_🌍_Regional_Sales.py
    3_🎮_Drilldown.py
    4_🤖_AI_Insights.py
    5_🧪_Data_Quality.py
    6_📥_Downloads.py

Run:
    streamlit run app.py
"""

from pathlib import Path
import streamlit as st

from utils.auth import login_form
from utils.data_loader import DB_PATH, load_raw, clean, build_database

st.set_page_config(
    page_title="Video Game Sales Dashboard",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---- Custom polish on top of theme -----------------------------------------
st.markdown(
    """
    <style>
      .block-container {padding-top: 1.4rem;}
      .stMetric {background: #1e293b; padding: .8rem; border-radius: .6rem;}
      h1, h2, h3 {letter-spacing: -0.01em;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---- Auth gate --------------------------------------------------------------
if not login_form():
    st.stop()

# ---- Auto-build DB on first run --------------------------------------------
if not Path(DB_PATH).exists():
    with st.spinner("Building SQLite database from CSVs…"):
        g, v = load_raw()
        g, v = clean(g, v)
        build_database(g, v)
    st.success("Database ready ✅")

# ---- Landing page -----------------------------------------------------------
st.title("🎮 Video Game Sales & Engagement Analysis")
st.markdown(
    """
    Welcome! Use the **sidebar** to navigate:

    | Page | What's inside |
    |------|---------------|
    | 📊 **Overview**       | KPIs, top games, sales trends |
    | 🌍 **Regional Sales** | NA / EU / JP / Other breakdowns |
    | 🎮 **Drill-down**     | Platform → Genre → Publisher → Game |
    | 🤖 **AI Insights**    | Statistical + LLM-generated narrative |
    | 🧪 **Data Quality**   | Validation report & null analysis |
    | 📥 **Downloads**      | Cleaned CSV, SQLite DB, PDF & Excel reports |
    """
)

st.info(
    "💡 Drop your **games.csv** and **vgsales.csv** into the `data/` folder "
    "and click *Rebuild database* below. Otherwise a synthetic sample is used."
)

if st.button("🔄 Rebuild database from /data"):
    with st.spinner("Rebuilding…"):
        g, v = load_raw()
        g, v = clean(g, v)
        build_database(g, v)
    st.success("Done!")
    st.rerun()
