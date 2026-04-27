"""Data quality + validation report."""
import streamlit as st
from utils.auth import login_form
from utils.data_loader import load_raw, clean
from utils.validation import validate

if not login_form():
    st.stop()

st.title("🧪 Data Quality Report")

raw_g, raw_v = load_raw()
games, vg = clean(raw_g.copy(), raw_v.copy())
report = validate(games, vg)

# ---- Score badge ----------------------------------------------------------
score = report["score"]
color = "🟢" if score >= 85 else "🟡" if score >= 60 else "🔴"
st.metric("Overall data-quality score", f"{color}  {score} / 100")

# ---- Summary --------------------------------------------------------------
st.subheader("Summary")
st.json(report["summary"])

# ---- Issues ---------------------------------------------------------------
st.subheader("Issues detected")
if report["issues"]:
    for i in report["issues"]:
        st.warning(i)
else:
    st.success("No major issues found 🎉")

# ---- Null reports ---------------------------------------------------------
c1, c2 = st.columns(2)
with c1:
    st.subheader("games.csv — null & dtype report")
    st.dataframe(report["games_nulls"], use_container_width=True)
with c2:
    st.subheader("vgsales.csv — null & dtype report")
    st.dataframe(report["sales_nulls"], use_container_width=True)
