"""AI-assisted insights: statistical bullets + optional LLM narrative."""
import streamlit as st
from utils.auth import login_form
from utils.data_loader import merged_view
from utils.insights import stat_insights, llm_summary

if not login_form():
    st.stop()

st.title("🤖 AI Insights")
df = st.session_state.get("filtered_df")
if df is None or df.empty:
    df = merged_view()

st.caption(f"Analyzing {len(df):,} rows from current selection")

st.subheader("📌 Statistical highlights")
for line in stat_insights(df):
    st.markdown(f"- {line}")

st.divider()
st.subheader("🧠 LLM narrative (optional)")
st.caption(
    "Set `OPENAI_API_KEY` or `LOVABLE_API_KEY` as an environment variable "
    "to enable. Falls back gracefully if unavailable."
)
if st.button("Generate narrative"):
    with st.spinner("Calling model…"):
        text = llm_summary(df)
    if text:
        st.markdown(text)
        st.session_state["llm_narrative"] = text
    else:
        st.warning("No API key found — showing stats only.")
