from __future__ import annotations

import duckdb
import pandas as pd


def duckdb_market_query(accounts: pd.DataFrame) -> pd.DataFrame:
    con = duckdb.connect(database=":memory:")
    con.register("accounts", accounts)
    return con.execute(
        """
        SELECT
          region,
          segment,
          COUNT(*) AS account_count,
          ROUND(SUM(whitespace_arr), 0) AS whitespace_arr,
          ROUND(AVG(fit_score), 1) AS avg_fit,
          ROUND(AVG(intent_score), 1) AS avg_intent,
          ROUND(SUM(CASE WHEN current_customer THEN expansion_arr ELSE 0 END), 0) AS customer_expansion_pool
        FROM accounts
        GROUP BY 1, 2
        ORDER BY whitespace_arr DESC
        """
    ).df()
