"""Regional sales breakdown: NA / EU / JP / Other."""
import streamlit as st
import plotly.express as px
from utils.auth import login_form
from utils.data_loader import merged_view

if not login_form():
    st.stop()

st.title("🌍 Regional Sales")
df = merged_view()

regions = ["na_sales", "eu_sales", "jp_sales", "other_sales"]
labels = {"na_sales": "North America", "eu_sales": "Europe",
          "jp_sales": "Japan", "other_sales": "Other"}

# ---- Region totals --------------------------------------------------------
totals = df[regions].sum().rename(labels).reset_index()
totals.columns = ["region", "sales_M"]
c1, c2 = st.columns(2)
with c1:
    st.subheader("Total by Region")
    st.plotly_chart(px.bar(totals, x="region", y="sales_M", color="region"),
                    use_container_width=True)
with c2:
    st.subheader("Region Share")
    st.plotly_chart(px.pie(totals, names="region", values="sales_M", hole=.4),
                    use_container_width=True)

# ---- Top genre per region -------------------------------------------------
st.subheader("Top Genres per Region")
sel = st.selectbox("Region", list(labels.values()))
col = [k for k, v in labels.items() if v == sel][0]
top = (df.groupby("genre", as_index=False)[col]
         .sum().sort_values(col, ascending=False).head(10))
st.plotly_chart(px.bar(top, x=col, y="genre", orientation="h",
                       color=col, color_continuous_scale="Plasma"),
                use_container_width=True)

# ---- Heatmap: Genre × Region ---------------------------------------------
st.subheader("Heatmap — Genre × Region")
hm = df.groupby("genre")[regions].sum().rename(columns=labels)
st.plotly_chart(px.imshow(hm, aspect="auto", color_continuous_scale="Viridis"),
                use_container_width=True)
