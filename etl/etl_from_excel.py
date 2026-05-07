"""
ETL pipeline for Trading Performance Dashboard (Portfolio Project).

Reads an Excel trade report, pairs Entry/Exit rows by Trade #, and outputs
Tableau-ready CSVs: trades fact table, equity curve, and KPI summary.

Input:
    Excel file with sheet "List of trades" (see README for expected columns).

Outputs (under `data/` at project root):
    - trades_fact.csv   — one row per completed trade
    - equity_curve.csv  — equity and drawdown over time
    - kpis_summary.csv  — win rate, expectancy, profit factor, max drawdown

Usage (from project root):
    python etl/etl_from_excel.py

Notes:
    - Entry/Exit are paired by Trade # (first entry, last exit per trade).
    - KPIs use net P&L per trade (pnl_net). Break-even trades (pnl_net == 0)
      are excluded from win/loss counts.
"""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pandas as pd

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

INPUT_XLSX = r"/mnt/data/Replay_Trading_CME_MINI_ES1!_2025-09-27_79f2b.xlsx"
SHEET_NAME = "List of trades"

OUT_TRADES_FACT = DATA_DIR / "trades_fact.csv"
OUT_EQUITY_CURVE = DATA_DIR / "equity_curve.csv"
OUT_KPIS = DATA_DIR / "kpis_summary.csv"


# -----------------------------------------------------------------------------
# Transform: raw rows → one row per trade
# -----------------------------------------------------------------------------


def build_trades_fact(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build the trades fact table from raw Excel rows.

    Classifies rows by Type (entry/exit, long/short), groups by Trade #,
    and joins first entry with last exit per trade. Computes equity curve
    and trade duration.

    Args:
        df: Raw DataFrame from Excel (sheet "List of trades").

    Returns:
        DataFrame with one row per trade: entry/exit times and prices,
        P&L, run-up, drawdown, equity, and duration.
    """
    # Normalize and classify rows
    raw = df.copy()
    raw["Type"] = raw["Type"].astype(str).str.strip().str.lower()
    raw["is_entry"] = raw["Type"].str.contains("entry")
    raw["is_exit"] = raw["Type"].str.contains("exit")
    is_long = raw["Type"].str.contains("long")
    is_short = raw["Type"].str.contains("short")
    raw["side"] = pd.Series(pd.NA, index=raw.index, dtype="string")
    raw.loc[is_short, "side"] = "SHORT"
    raw.loc[is_long, "side"] = "LONG"

    entries = cast(pd.DataFrame, raw[raw["is_entry"]]).sort_values(
        by=["Trade #", "Date/Time"],
    )
    exits = cast(pd.DataFrame, raw[raw["is_exit"]]).sort_values(
        by=["Trade #", "Date/Time"],
    )

    # One entry and one exit per trade (first entry, last exit)
    entries_g = entries.groupby("Trade #").first()
    exits_g = exits.groupby("Trade #").last()

    # Build fact from entry columns (cast so .rename(columns=...) matches DataFrame stubs)
    fact = cast(
        pd.DataFrame,
        entries_g[
            [
                "Date/Time",
                "Price USD",
                "Position size (qty)",
                "Position size (value)",
                "side",
            ]
        ],
    ).rename(
        columns={
            "Date/Time": "entry_time",
            "Price USD": "entry_price",
            "Position size (qty)": "quantity",
            "Position size (value)": "position_value",
        }
    )

    # Join exit columns (times, P&L, run-up, drawdown)
    exit_block = cast(
        pd.DataFrame,
        exits_g[
            [
                "Date/Time",
                "Price USD",
                "Net P&L USD",
                "Net P&L %",
                "Run-up USD",
                "Run-up %",
                "Drawdown USD",
                "Drawdown %",
                "Cumulative P&L USD",
                "Cumulative P&L %",
            ]
        ],
    ).rename(
        columns={
            "Date/Time": "exit_time",
            "Price USD": "exit_price",
            "Net P&L USD": "pnl_net",
            "Net P&L %": "pnl_net_pct",
            "Run-up USD": "runup_usd",
            "Run-up %": "runup_pct",
            "Drawdown USD": "drawdown_usd",
            "Drawdown %": "drawdown_pct",
            "Cumulative P&L USD": "cum_pnl_usd",
            "Cumulative P&L %": "cum_pnl_pct",
        }
    )
    fact = fact.join(exit_block)

    fact = cast(pd.DataFrame, fact.reset_index()).rename(
        columns={"Trade #": "trade_id"},
    )

    # Parse datetimes and sort by exit time (for equity curve order)
    fact["entry_time"] = pd.to_datetime(fact["entry_time"])
    fact["exit_time"] = pd.to_datetime(fact["exit_time"])
    fact = fact.sort_values("exit_time").reset_index(drop=True)

    # Equity curve from cumulative P&L
    fact["equity"] = fact["pnl_net"].cumsum()
    fact["peak_equity"] = fact["equity"].cummax()
    fact["equity_drawdown"] = fact["equity"] - fact["peak_equity"]

    # Trade duration in minutes
    fact["trade_duration_min"] = (
        (fact["exit_time"] - fact["entry_time"]).dt.total_seconds() / 60.0
    )

    return fact


def compute_kpis(trades_fact: pd.DataFrame) -> pd.DataFrame:
    """
    Compute summary KPIs from the trades fact table.

    Win rate, average win/loss, expectancy, profit factor, net P&L,
    and max drawdown. Break-even trades (pnl_net == 0) are not counted
    as wins or losses.

    Args:
        trades_fact: Output of build_trades_fact (must include pnl_net,
                     equity_drawdown).

    Returns:
        DataFrame with one row and columns: total_trades, wins, losses,
        win_rate, avg_win_usd, avg_loss_usd, expectancy_usd_per_trade,
        profit_factor, net_pnl_usd, max_drawdown_usd.
    """
    pnl = trades_fact["pnl_net"].astype(float)
    total = len(trades_fact)
    wins = trades_fact[trades_fact["pnl_net"] > 0]
    losses = trades_fact[trades_fact["pnl_net"] < 0]

    win_rate = (len(wins) / total) if total else 0.0
    avg_win = float(wins["pnl_net"].mean()) if len(wins) else 0.0
    avg_loss = float(abs(losses["pnl_net"].mean())) if len(losses) else 0.0
    loss_rate = 1.0 - win_rate

    expectancy = (win_rate * avg_win) - (loss_rate * avg_loss)

    if len(losses):
        profit_factor = float(wins["pnl_net"].sum()) / float(abs(losses["pnl_net"].sum()))
    else:
        profit_factor = float("inf")

    max_drawdown = float(trades_fact["equity_drawdown"].min()) if total else 0.0

    kpis = {
        "total_trades": int(total),
        "wins": int(len(wins)),
        "losses": int(len(losses)),
        "win_rate": float(win_rate),
        "avg_win_usd": float(avg_win),
        "avg_loss_usd": float(avg_loss),
        "expectancy_usd_per_trade": float(expectancy),
        "profit_factor": float(profit_factor),
        "net_pnl_usd": float(pnl.sum()) if total else 0.0,
        "max_drawdown_usd": float(max_drawdown),
    }

    return pd.DataFrame([kpis])


# -----------------------------------------------------------------------------
# Main: load → transform → export
# -----------------------------------------------------------------------------


def main() -> None:
    """Load Excel, build fact table and KPIs, write CSVs and print summary."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    df_raw = pd.read_excel(INPUT_XLSX, sheet_name=SHEET_NAME)
    trades_fact = build_trades_fact(df_raw)

    trades_fact.to_csv(OUT_TRADES_FACT, index=False)

    equity_curve = trades_fact[
        ["trade_id", "exit_time", "pnl_net", "equity", "peak_equity", "equity_drawdown"]
    ].copy()
    equity_curve.to_csv(OUT_EQUITY_CURVE, index=False)

    kpis = compute_kpis(trades_fact)
    kpis.to_csv(OUT_KPIS, index=False)

    print("Wrote outputs:")
    print(" -", OUT_TRADES_FACT)
    print(" -", OUT_EQUITY_CURVE)
    print(" -", OUT_KPIS)
    print()
    print("KPIs:")
    print(kpis.to_string(index=False))


if __name__ == "__main__":
    main()
