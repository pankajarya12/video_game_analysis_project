"""
validation.py — dataset validation + data-quality report.

Checks performed:
    - required columns present
    - dtype correctness
    - null-rate per column
    - duplicate rows
    - out-of-range values (years, scores, sales)
    - referential integrity between games and sales

Returns a structured dict consumed by the Streamlit "Data Quality" page.
"""

from __future__ import annotations
import pandas as pd
import numpy as np

REQUIRED_GAMES = {"name", "platform", "genre", "publisher", "release_year"}
REQUIRED_SALES = {"name", "platform", "release_year", "global_sales"}


def _null_report(df: pd.DataFrame) -> pd.DataFrame:
    n = len(df)
    return pd.DataFrame({
        "column": df.columns,
        "null_count": df.isna().sum().values,
        "null_pct": (df.isna().mean().values * 100).round(2),
        "dtype": [str(t) for t in df.dtypes.values],
        "n_unique": [df[c].nunique(dropna=True) for c in df.columns],
    })


def validate(games: pd.DataFrame, vg: pd.DataFrame) -> dict:
    issues: list[str] = []
    score = 100.0  # start perfect, deduct per issue category

    # 1. required columns
    miss_g = REQUIRED_GAMES - set(games.columns)
    miss_v = REQUIRED_SALES - set(vg.columns)
    if miss_g:
        issues.append(f"games.csv missing columns: {sorted(miss_g)}")
        score -= 15
    if miss_v:
        issues.append(f"vgsales.csv missing columns: {sorted(miss_v)}")
        score -= 15

    # 2. duplicates
    dup_g = int(games.duplicated().sum())
    dup_v = int(vg.duplicated().sum())
    if dup_g:
        issues.append(f"{dup_g} duplicate rows in games")
        score -= min(10, dup_g / max(len(games), 1) * 100)
    if dup_v:
        issues.append(f"{dup_v} duplicate rows in vgsales")
        score -= min(10, dup_v / max(len(vg), 1) * 100)

    # 3. year range sanity
    bad_years = 0
    if "release_year" in vg.columns:
        bad_years = int(((vg["release_year"] < 1970) |
                         (vg["release_year"] > 2030)).sum())
        if bad_years:
            issues.append(f"{bad_years} sales rows with implausible release_year")
            score -= 5

    # 4. negative sales
    neg_sales = 0
    for c in ["na_sales", "eu_sales", "jp_sales", "other_sales", "global_sales"]:
        if c in vg.columns:
            neg_sales += int((vg[c] < 0).sum())
    if neg_sales:
        issues.append(f"{neg_sales} negative sales values")
        score -= 5

    # 5. score range
    bad_scores = 0
    if "user_score" in games.columns:
        bad_scores += int(((games["user_score"] < 0) |
                           (games["user_score"] > 10)).sum())
    if "critic_score" in games.columns:
        bad_scores += int(((games["critic_score"] < 0) |
                           (games["critic_score"] > 100)).sum())
    if bad_scores:
        issues.append(f"{bad_scores} out-of-range score values")
        score -= 5

    # 6. referential integrity (games ↔ sales by name+platform)
    orphan_pct = None
    if {"name", "platform"}.issubset(games.columns) and \
       {"name", "platform"}.issubset(vg.columns):
        gk = set(zip(games["name"].str.lower(), games["platform"].str.lower()))
        sk = list(zip(vg["name"].str.lower(), vg["platform"].str.lower()))
        orphans = sum(1 for k in sk if k not in gk)
        orphan_pct = round(orphans / max(len(sk), 1) * 100, 2)
        if orphan_pct > 50:
            issues.append(
                f"{orphan_pct}% of sales rows have no match in games "
                "(low referential integrity)"
            )
            score -= 10

    score = max(0, round(score, 1))

    return {
        "score": score,
        "issues": issues,
        "games_nulls": _null_report(games),
        "sales_nulls": _null_report(vg),
        "summary": {
            "games_rows": len(games),
            "sales_rows": len(vg),
            "duplicates_games": dup_g,
            "duplicates_sales": dup_v,
            "bad_years": bad_years,
            "negative_sales": neg_sales,
            "bad_scores": bad_scores,
            "orphan_sales_pct": orphan_pct,
        },
    }
