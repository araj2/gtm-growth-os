from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans


def greedy_balance_territories(accounts: pd.DataFrame, rep_count: int, region: str | None = None, segment: str | None = None) -> pd.DataFrame:
    """Assign accounts to reps by balancing weighted opportunity value.

    This is deliberately transparent: high-potential accounts are assigned first to the rep
    with the lowest current book, preserving a simple story for interviews.
    """
    scoped = accounts.copy()
    if region and region != "All":
        scoped = scoped[scoped["region"] == region]
    if segment and segment != "All":
        scoped = scoped[scoped["segment"] == segment]
    scoped = scoped.sort_values("priority_score", ascending=False).reset_index(drop=True)
    reps = {f"Rep {i+1:02d}": 0.0 for i in range(rep_count)}
    assignments: list[str] = []
    for _, row in scoped.iterrows():
        rep = min(reps, key=reps.get)
        assignments.append(rep)
        reps[rep] += float(row["whitespace_arr"]) * (float(row["propensity_to_buy"]) / 100)
    scoped["territory_owner"] = assignments
    scoped["weighted_book_value"] = scoped["whitespace_arr"] * scoped["propensity_to_buy"] / 100
    return scoped


def territory_summary(territories: pd.DataFrame) -> pd.DataFrame:
    if territories.empty:
        return pd.DataFrame()
    return (
        territories.groupby("territory_owner", as_index=False)
        .agg(
            accounts=("account_id", "count"),
            whitespace_arr=("whitespace_arr", "sum"),
            weighted_book_value=("weighted_book_value", "sum"),
            avg_fit=("fit_score", "mean"),
            avg_intent=("intent_score", "mean"),
            customers=("current_customer", "sum"),
        )
        .assign(balance_index=lambda d: d["weighted_book_value"] / d["weighted_book_value"].mean())
        .sort_values("weighted_book_value", ascending=False)
    )


def cluster_accounts(accounts: pd.DataFrame, clusters: int = 6) -> pd.DataFrame:
    features = accounts[["fit_score", "intent_score", "data_maturity_score", "whitespace_arr", "employees"]].copy()
    features["whitespace_arr"] = np.log1p(features["whitespace_arr"])
    features["employees"] = np.log1p(features["employees"])
    model = KMeans(n_clusters=clusters, random_state=7, n_init="auto")
    out = accounts.copy()
    out["micro_market_cluster"] = model.fit_predict(features)
    return out
