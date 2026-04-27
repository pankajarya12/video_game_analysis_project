"""
insights.py — model-assisted insights.

Two layers:
1. **Statistical insights** (always available, no API key required):
   - top movers, correlation flags, anomaly detection (IQR), trend slope.
2. **LLM narrative** (optional): if OPENAI_API_KEY or LOVABLE_API_KEY is set,
   generates a natural-language summary of the filtered dataset.

The LLM call is wrapped in try/except so the dashboard never breaks.
"""

from __future__ import annotations
import os
import json
import numpy as np
import pandas as pd

try:
    import requests
except ImportError:
    requests = None


# ---------------------------------------------------------------- statistical
def stat_insights(df: pd.DataFrame) -> list[str]:
    out: list[str] = []
    if df.empty:
        return ["No data in current filter."]

    # Top platform / genre / publisher
    for col, label in [("platform", "platform"),
                       ("genre", "genre"),
                       ("publisher", "publisher")]:
        if col in df.columns:
            top = df.groupby(col)["global_sales"].sum().sort_values(ascending=False)
            if len(top):
                share = top.iloc[0] / top.sum() * 100
                out.append(
                    f"🏆 Top {label}: **{top.index[0]}** "
                    f"({top.iloc[0]:.1f}M, {share:.1f}% share)"
                )

    # Trend
    if "release_year" in df.columns:
        yr = df.groupby("release_year")["global_sales"].sum().sort_index()
        yr = yr[(yr.index > 1970) & (yr.index < 2030)]
        if len(yr) > 3:
            slope = np.polyfit(yr.index, yr.values, 1)[0]
            direction = "rising 📈" if slope > 0 else "falling 📉"
            out.append(f"Sales trend across years is **{direction}** "
                       f"(slope = {slope:+.2f}M/yr)")

    # Anomaly: blockbuster outliers (IQR rule)
    s = df["global_sales"].dropna()
    if len(s) > 10:
        q1, q3 = s.quantile([.25, .75])
        hi = q3 + 1.5 * (q3 - q1)
        outliers = df[df["global_sales"] > hi].sort_values(
            "global_sales", ascending=False).head(3)
        if not outliers.empty:
            names = ", ".join(outliers["name"].astype(str).head(3))
            out.append(f"💥 Blockbuster outliers: {names}")

    # Critic vs sales correlation
    if {"critic_score", "global_sales"}.issubset(df.columns):
        sub = df[["critic_score", "global_sales"]].dropna()
        if len(sub) > 20:
            r = sub.corr().iloc[0, 1]
            out.append(f"Critic score ↔ global sales correlation: **r = {r:+.2f}**")

    return out


# ----------------------------------------------------------------------- LLM
def llm_summary(df: pd.DataFrame, max_rows: int = 50) -> str | None:
    """Optional LLM narrative. Returns None when no API key/library available."""
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("LOVABLE_API_KEY")
    if not api_key or requests is None or df.empty:
        return None

    # Compact summary the model can reason on (don't ship raw rows)
    summary = {
        "rows": int(len(df)),
        "global_sales_total_M": round(float(df["global_sales"].sum()), 2),
        "by_genre": df.groupby("genre")["global_sales"].sum()
                      .sort_values(ascending=False).head(5).round(2).to_dict()
            if "genre" in df else {},
        "by_platform": df.groupby("platform")["global_sales"].sum()
                         .sort_values(ascending=False).head(5).round(2).to_dict()
            if "platform" in df else {},
        "year_range": [int(df["release_year"].min()),
                       int(df["release_year"].max())]
            if "release_year" in df and df["release_year"].notna().any() else None,
    }

    prompt = (
        "You are a data analyst. In 4-6 short bullet points, summarize the "
        "video-game-sales snapshot below. Highlight leaders, trends, and any "
        "interesting tensions. Be concrete, no fluff.\n\n"
        f"{json.dumps(summary, indent=2)}"
    )

    # Lovable AI Gateway (preferred when available)
    try:
        url = "https://ai.gateway.lovable.dev/v1/chat/completions"
        r = requests.post(
            url,
            headers={"Authorization": f"Bearer {api_key}",
                     "Content-Type": "application/json"},
            json={"model": "google/gemini-2.5-flash",
                  "messages": [{"role": "user", "content": prompt}]},
            timeout=30,
        )
        if r.ok:
            return r.json()["choices"][0]["message"]["content"]
    except Exception as e:  # noqa: BLE001
        return f"_LLM call failed: {e}_"
    return None
