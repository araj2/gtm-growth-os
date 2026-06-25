from __future__ import annotations

import numpy as np
import pandas as pd

SEGMENTS = ["SMB", "Mid-Market", "Enterprise", "Strategic"]
REGIONS = ["North America", "EMEA", "APAC", "LATAM"]
INDUSTRIES = [
    "AI Infrastructure", "Fintech", "Cybersecurity", "Healthcare SaaS", "Retail Tech",
    "Data/Analytics", "Developer Tools", "Marketing Tech", "Vertical SaaS", "Logistics Tech",
]
COUNTRIES = {
    "North America": ["US", "Canada"],
    "EMEA": ["UK", "Germany", "France", "Netherlands", "UAE"],
    "APAC": ["India", "Singapore", "Australia", "Japan"],
    "LATAM": ["Brazil", "Mexico", "Chile"],
}


def generate_account_universe(n: int = 2500, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    regions = rng.choice(REGIONS, size=n, p=[0.52, 0.24, 0.16, 0.08])
    countries = [rng.choice(COUNTRIES[r]) for r in regions]
    segments = rng.choice(SEGMENTS, size=n, p=[0.46, 0.30, 0.18, 0.06])
    industries = rng.choice(INDUSTRIES, size=n)

    segment_employee_ranges = {
        "SMB": (50, 500),
        "Mid-Market": (500, 2000),
        "Enterprise": (2000, 10000),
        "Strategic": (10000, 100000),
    }
    segment_revenue_multipliers = {
        "SMB": 0.35,
        "Mid-Market": 0.75,
        "Enterprise": 1.4,
        "Strategic": 2.6,
    }
    employees = np.array([
        int(rng.integers(*segment_employee_ranges[s])) for s in segments
    ])
    est_revenue_m = employees * np.array([segment_revenue_multipliers[s] for s in segments]) * rng.uniform(0.08, 0.22, size=n)

    fit_score = np.clip(rng.normal(72, 14, size=n), 1, 100)
    intent_score = np.clip(rng.normal(54, 22, size=n), 1, 100)
    data_maturity = np.clip(rng.normal(60, 18, size=n), 1, 100)
    current_customer = rng.random(size=n) < np.select(
        [segments == "SMB", segments == "Mid-Market", segments == "Enterprise", segments == "Strategic"],
        [0.04, 0.08, 0.13, 0.18],
        default=0.06,
    )
    segment_acv = {
        "SMB": 18_000,
        "Mid-Market": 55_000,
        "Enterprise": 145_000,
        "Strategic": 330_000,
    }
    base_potential = np.array([segment_acv[s] for s in segments])
    whitespace_arr = base_potential * (fit_score / 70) * (intent_score / 55) * rng.uniform(0.7, 1.7, size=n)
    expansion_arr = np.where(current_customer, whitespace_arr * rng.uniform(0.25, 0.95, size=n), 0)
    propensity_to_buy = np.clip(0.42 * fit_score + 0.38 * intent_score + 0.20 * data_maturity, 1, 100)
    priority_score = np.round(propensity_to_buy * np.log1p(whitespace_arr) / 12, 2)

    return pd.DataFrame(
        {
            "account_id": [f"ACCT-{i:05d}" for i in range(1, n + 1)],
            "account_name": [f"{industries[i].split()[0]}Co {i:04d}" for i in range(n)],
            "region": regions,
            "country": countries,
            "segment": segments,
            "industry": industries,
            "employees": employees,
            "est_revenue_m": np.round(est_revenue_m, 2),
            "fit_score": np.round(fit_score, 1),
            "intent_score": np.round(intent_score, 1),
            "data_maturity_score": np.round(data_maturity, 1),
            "current_customer": current_customer,
            "whitespace_arr": np.round(whitespace_arr, 0),
            "expansion_arr": np.round(expansion_arr, 0),
            "propensity_to_buy": np.round(propensity_to_buy, 1),
            "priority_score": priority_score,
        }
    )


def account_summary(accounts: pd.DataFrame) -> pd.DataFrame:
    return (
        accounts.groupby(["region", "segment"], as_index=False)
        .agg(
            accounts=("account_id", "count"),
            whitespace_arr=("whitespace_arr", "sum"),
            avg_fit=("fit_score", "mean"),
            avg_intent=("intent_score", "mean"),
            customers=("current_customer", "sum"),
        )
        .sort_values("whitespace_arr", ascending=False)
    )
