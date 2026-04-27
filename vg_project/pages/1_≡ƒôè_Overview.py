"""Overview KPIs + top games + yearly trend."""
import streamlit as st
import plotly.express as px
from utils.auth import login_form
from utils.data_loader import merged_view

if not login_form():
    st.stop()

st.title("📊 Overview")
df = merged_view()

# --- Filters ---------------------------------------------------------------
with st.sidebar:
    st.header("Filters")
    years = sorted(df["release_year"].dropna().astype(int).unique())
    if years:
        y0, y1 = st.select_slider("Year range",
                                  options=years,
                                  value=(min(years), max(years)))
        df = df[(df["release_year"] >= y0) & (df["release_year"] <= y1)]
    plat = st.multiselect("Platform", sorted(df["platform"].dropna().unique()))
    if plat: df = df[df["platform"].isin(plat)]
    gen = st.multiselect("Genre", sorted(df["genre"].dropna().unique()))
    if gen: df = df[df["genre"].isin(gen)]

# --- KPIs ------------------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Games", f"{df['name'].nunique():,}")
c2.metric("Global Sales (M)", f"{df['global_sales'].sum():,.1f}")
c3.metric("Platforms", f"{df['platform'].nunique():,}")
c4.metric("Publishers", f"{df['publisher'].nunique():,}")

st.divider()

# --- Top 10 games ----------------------------------------------------------
st.subheader("🏆 Top 10 Games by Global Sales")
top10 = (df.groupby("name", as_index=False)["global_sales"]
           .sum().sort_values("global_sales", ascending=False).head(10))
st.plotly_chart(
    px.bar(top10, x="global_sales", y="name", orientation="h",
           color="global_sales", color_continuous_scale="Viridis"),
    use_container_width=True,
)

# --- Yearly trend ----------------------------------------------------------
st.subheader("📈 Global Sales by Year")
yr = (df.groupby("release_year", as_index=False)["global_sales"].sum()
        .sort_values("release_year"))
yr = yr[(yr["release_year"] > 1970) & (yr["release_year"] < 2030)]
st.plotly_chart(px.area(yr, x="release_year", y="global_sales"),
                use_container_width=True)

# --- Genre share -----------------------------------------------------------
st.subheader("🎯 Sales by Genre")
g = df.groupby("genre", as_index=False)["global_sales"].sum() \
      .sort_values("global_sales", ascending=False)
st.plotly_chart(px.pie(g, names="genre", values="global_sales", hole=.4),
                use_container_width=True)

# Persist filtered df for other pages (Downloads / AI Insights)
st.session_state["filtered_df"] = df
