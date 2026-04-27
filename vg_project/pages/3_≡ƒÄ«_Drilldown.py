"""
Drill-down navigation:
    Platform → Genre → Publisher → Individual game.
Each step filters the next, ending in a per-game detail card.
"""
import streamlit as st
import plotly.express as px
from utils.auth import login_form
from utils.data_loader import merged_view

if not login_form():
    st.stop()

st.title("🎮 Drill-down Explorer")
df = merged_view()

# Step 1 — Platform
platform = st.selectbox(
    "1️⃣  Choose a platform",
    ["(all)"] + sorted(df["platform"].dropna().unique().tolist()),
)
if platform != "(all)":
    df = df[df["platform"] == platform]

# Step 2 — Genre
genre = st.selectbox(
    "2️⃣  Choose a genre",
    ["(all)"] + sorted(df["genre"].dropna().unique().tolist()),
)
if genre != "(all)":
    df = df[df["genre"] == genre]

# Step 3 — Publisher
publisher = st.selectbox(
    "3️⃣  Choose a publisher",
    ["(all)"] + sorted(df["publisher"].dropna().unique().tolist()),
)
if publisher != "(all)":
    df = df[df["publisher"] == publisher]

st.caption(f"{len(df):,} matching rows")

# Aggregated chart at current level
if not df.empty:
    agg_col = ("name" if publisher != "(all)" else
               "publisher" if genre != "(all)" else
               "genre" if platform != "(all)" else "platform")
    top = (df.groupby(agg_col, as_index=False)["global_sales"]
             .sum().sort_values("global_sales", ascending=False).head(15))
    st.plotly_chart(
        px.bar(top, x="global_sales", y=agg_col, orientation="h",
               color="global_sales", color_continuous_scale="Turbo",
               title=f"Top {agg_col}s in current selection"),
        use_container_width=True,
    )

# Step 4 — Game detail
st.divider()
st.subheader("4️⃣  Game detail")
games = sorted(df["name"].dropna().unique().tolist())
if not games:
    st.info("No games match the current filters.")
else:
    pick = st.selectbox("Pick a game", games)
    rows = df[df["name"] == pick]
    row = rows.iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Global", f"{rows['global_sales'].sum():.2f} M")
    c2.metric("NA",     f"{rows['na_sales'].sum():.2f} M")
    c3.metric("EU",     f"{rows['eu_sales'].sum():.2f} M")
    c4.metric("JP",     f"{rows['jp_sales'].sum():.2f} M")

    with st.expander("More details"):
        st.write({
            "Platform":   row["platform"],
            "Genre":      row["genre"],
            "Publisher":  row["publisher"],
            "Year":       row["release_year"],
            "User score": row.get("user_score"),
            "Critic score": row.get("critic_score"),
            "Rating":     row.get("rating"),
            "Developer":  row.get("developer"),
        })
    st.dataframe(rows, use_container_width=True)
