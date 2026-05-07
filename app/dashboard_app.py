"""
Streamlit dashboard for the Trading Performance project.

Shows a multi-chart dashboard based on the CSV outputs produced by
`etl/etl_from_excel.py` under `data/`.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import cast

import altair as alt
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

EQUITY_CSV = DATA_DIR / "equity_curve.csv"
KPIS_CSV = DATA_DIR / "kpis_summary.csv"
TRADES_CSV = DATA_DIR / "trades_fact.csv"

# Reference palette (dark theme — readable on Streamlit dark background)
CLR_BLUE = "#5B8FF9"
CLR_BLUE_DIM = "#8EB8FF"
CLR_GREEN = "#2ECC71"
CLR_RED = "#E74C3C"
CLR_NEUTRAL = "#B0B0B0"
CLR_GRID = "#3A3A45"
CLR_AXIS = "#DCDCDC"


def _apply_chart_theme(
    chart: alt.Chart | alt.LayerChart,
    *,
    height: int,
) -> alt.Chart | alt.LayerChart:
    return (
        chart.properties(height=height, background="transparent")
        .configure_axis(
            labelColor=CLR_AXIS,
            titleColor=CLR_AXIS,
            gridColor=CLR_GRID,
            domainColor=CLR_GRID,
        )
        .configure_view(strokeWidth=0)
        .configure_legend(labelColor=CLR_AXIS, titleColor=CLR_AXIS)
    )


@st.cache_data
def load_equity() -> pd.DataFrame:
    """Load equity curve data."""
    _require_csv(EQUITY_CSV)
    return pd.read_csv(EQUITY_CSV, parse_dates=["exit_time"])


@st.cache_data
def load_kpis() -> pd.DataFrame | None:
    """Load KPIs summary, if available."""
    if KPIS_CSV.exists():
        return pd.read_csv(KPIS_CSV)
    return None


@st.cache_data
def load_trades() -> pd.DataFrame:
    """Load trade-level facts."""
    _require_csv(TRADES_CSV)
    return pd.read_csv(TRADES_CSV, parse_dates=["entry_time", "exit_time"])


def _require_csv(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(
            f"Could not find {path}. "
            "From the project root, run: python etl/etl_from_excel.py"
        )


def derive_kpis(trades_df: pd.DataFrame, kpis_df: pd.DataFrame | None) -> dict[str, float]:
    """Build KPI values, preferring `kpis_summary.csv` when available."""
    if kpis_df is not None and not kpis_df.empty:
        row = kpis_df.iloc[0]
        return {
            "net_pnl_usd": float(row.get("net_pnl_usd", 0.0)),
            "max_drawdown_usd": float(row.get("max_drawdown_usd", 0.0)),
            "profit_factor": float(row.get("profit_factor", 0.0)),
            "win_rate": float(row.get("win_rate", 0.0)),
            "avg_win_usd": float(row.get("avg_win_usd", 0.0)),
            "avg_loss_usd": float(row.get("avg_loss_usd", 0.0)),
            "total_trades": float(row.get("total_trades", len(trades_df))),
        }

    pnl = trades_df["pnl_net"].astype(float)
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    win_rate = len(wins) / len(trades_df) if len(trades_df) else 0.0
    avg_win = float(wins.mean()) if len(wins) else 0.0
    avg_loss = float(abs(losses.mean())) if len(losses) else 0.0
    profit_factor = float(wins.sum() / abs(losses.sum())) if len(losses) else float("inf")
    max_drawdown = float(trades_df["equity_drawdown"].min()) if len(trades_df) else 0.0

    return {
        "net_pnl_usd": float(pnl.sum()),
        "max_drawdown_usd": max_drawdown,
        "profit_factor": profit_factor,
        "win_rate": win_rate,
        "avg_win_usd": avg_win,
        "avg_loss_usd": avg_loss,
        "total_trades": float(len(trades_df)),
    }


def _kpi_html(label: str, value: str, *, value_color: str | None = None) -> str:
    c = value_color or "#FAFAFA"
    return (
        f'<div style="padding:0.75rem 0.5rem;text-align:center;'
        f"border:1px solid {CLR_GRID};border-radius:6px;"
        f'background:rgba(38,39,48,0.6);">'
        f'<div style="font-size:0.8rem;color:{CLR_NEUTRAL};margin-bottom:0.35rem;">{label}</div>'
        f'<div style="font-size:1.35rem;font-weight:600;color:{c};">{value}</div>'
        f"</div>"
    )


def chart_equity_curve(equity_df: pd.DataFrame) -> alt.Chart | alt.LayerChart:
    eq = equity_df.sort_values("exit_time").copy()
    melted = eq.melt(
        id_vars=["exit_time"],
        value_vars=["equity", "peak_equity"],
        var_name="series",
        value_name="usd",
    )
    melted["series"] = melted["series"].replace(
        {"equity": "Equity", "peak_equity": "Peak equity"},
    )
    ch = (
        alt.Chart(melted)
        .mark_line(strokeWidth=2)
        .encode(
            x=alt.X("exit_time:T", title="Date"),
            y=alt.Y("usd:Q", title="Equity ($)"),
            color=alt.Color(
                "series:N",
                title="",
                scale=alt.Scale(domain=["Equity", "Peak equity"], range=[CLR_BLUE, CLR_NEUTRAL]),
            ),
        )
    )
    return _apply_chart_theme(ch, height=320)


def chart_drawdown(equity_df: pd.DataFrame) -> alt.Chart | alt.LayerChart:
    dd = equity_df.sort_values("exit_time")[["exit_time", "equity_drawdown"]].copy()
    ch = (
        alt.Chart(dd)
        .mark_area(
            line={"color": CLR_BLUE_DIM, "strokeWidth": 1.5},
            color=CLR_BLUE,
            opacity=0.35,
        )
        .encode(
            x=alt.X("exit_time:T", title="Date"),
            y=alt.Y("equity_drawdown:Q", title="Drawdown ($)"),
        )
    )
    return _apply_chart_theme(ch, height=320)


def chart_duration_vs_pnl(trades_df: pd.DataFrame) -> alt.Chart | alt.LayerChart:
    base = trades_df[["trade_duration_min", "pnl_net"]].dropna()
    pts = (
        alt.Chart(base)
        .mark_circle(color=CLR_BLUE, size=50, opacity=0.85)
        .encode(
            x=alt.X("trade_duration_min:Q", title="Trade duration (minutes)"),
            y=alt.Y("pnl_net:Q", title="PnL ($)"),
        )
    )
    trend = (
        alt.Chart(base)
        .transform_regression("trade_duration_min", "pnl_net")
        .mark_line(color=CLR_BLUE_DIM, strokeWidth=2)
        .encode(
            x=alt.X("trade_duration_min:Q"),
            y=alt.Y("pnl_net:Q"),
        )
    )
    layered = pts + trend
    return _apply_chart_theme(layered, height=280)


def chart_pnl_distribution(trades_df: pd.DataFrame) -> alt.Chart | alt.LayerChart | None:
    hist_source = trades_df["pnl_net"].dropna().astype(float)
    if len(hist_source) == 0:
        return None
    binned = cast(
        pd.Series,
        pd.Series(pd.cut(hist_source, bins=12), index=hist_source.index),
    )
    hist_df = (
        binned.value_counts()
        .sort_index()
        .rename_axis("pnl_range")
        .reset_index(name="count")
    )
    hist_df["pnl_range"] = hist_df["pnl_range"].astype(str)
    ch = (
        alt.Chart(hist_df)
        .mark_bar(color=CLR_BLUE, cornerRadiusEnd=2)
        .encode(
            x=alt.X("pnl_range:N", title="PnL range ($)", sort=None),
            y=alt.Y("count:Q", title="Number of trades"),
        )
    )
    return _apply_chart_theme(ch, height=280)


def chart_pnl_by_hour(trades_df: pd.DataFrame) -> alt.Chart | alt.LayerChart:
    entry_hour_df = trades_df.copy()
    entry_hour_df["entry_hour"] = entry_hour_df["entry_time"].dt.hour
    grouped = entry_hour_df.groupby("entry_hour", as_index=False).agg(
        pnl_net=("pnl_net", "sum"),
    )
    hour_agg = cast(pd.DataFrame, grouped).sort_values(by="entry_hour", ignore_index=True)
    ch = (
        alt.Chart(hour_agg)
        .mark_bar(cornerRadiusEnd=2)
        .encode(
            x=alt.X("entry_hour:O", title="Entry hour (24h)"),
            y=alt.Y("pnl_net:Q", title="PnL ($)"),
            color=alt.condition(
                alt.datum.pnl_net >= 0,
                alt.value(CLR_GREEN),
                alt.value(CLR_RED),
            ),
        )
    )
    return _apply_chart_theme(ch, height=280)


def chart_pnl_per_trade(trades_df: pd.DataFrame) -> alt.Chart | alt.LayerChart:
    per_trade_df = cast(
        pd.DataFrame,
        trades_df[["trade_id", "pnl_net"]],
    ).sort_values(by="trade_id", ignore_index=True)
    ch = (
        alt.Chart(per_trade_df)
        .mark_bar(cornerRadiusEnd=1)
        .encode(
            x=alt.X("trade_id:O", title="Trade #", sort=None),
            y=alt.Y("pnl_net:Q", title="PnL ($)"),
            color=alt.condition(
                alt.datum.pnl_net >= 0,
                alt.value(CLR_GREEN),
                alt.value(CLR_RED),
            ),
        )
    )
    return _apply_chart_theme(ch, height=300)


def main() -> None:
    st.set_page_config(
        page_title="Trading Performance Dashboard",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    st.markdown(
        "<h1 style='text-align:center;margin-bottom:0.25rem;'>Trading Performance Dashboard</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center;color:#9CA3AF;font-size:0.95rem;margin-top:0;'>"
        "Backtest overview from trade-level ETL outputs.</p>",
        unsafe_allow_html=True,
    )

    try:
        equity_df = load_equity()
        trades_df = load_trades()
    except FileNotFoundError as exc:
        st.error(str(exc))
        return

    kpis_df = load_kpis()
    kpis = derive_kpis(trades_df, kpis_df)

    pf = kpis["profit_factor"]
    pf_str = "∞" if math.isinf(pf) else f"{pf:.2f}"

    kpi_row = (
        _kpi_html("Net PnL", f"${kpis['net_pnl_usd']:,.0f}", value_color=CLR_GREEN)
        + _kpi_html(
            "Max Drawdown",
            f"${kpis['max_drawdown_usd']:,.0f}",
            value_color=CLR_RED,
        )
        + _kpi_html("Profit Factor", pf_str, value_color=None)
        + _kpi_html("Win Rate", f"{kpis['win_rate'] * 100:.1f}%", value_color=None)
        + _kpi_html("Avg Win", f"${kpis['avg_win_usd']:,.0f}", value_color=CLR_GREEN)
        + _kpi_html(
            "Avg Loss",
            f"-${kpis['avg_loss_usd']:,.0f}",
            value_color=CLR_RED,
        )
        + _kpi_html("Total Trades", f"{int(kpis['total_trades'])}", value_color=None)
    )
    st.markdown(
        f'<div style="display:grid;grid-template-columns:repeat(7,1fr);gap:0.5rem;">{kpi_row}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    col_left, col_right = st.columns(2, gap="medium")
    with col_left:
        st.markdown(
            f'<h3 style="color:{CLR_NEUTRAL};font-size:1rem;margin:0 0 0.5rem 0;">Equity Curve</h3>',
            unsafe_allow_html=True,
        )
        st.altair_chart(chart_equity_curve(equity_df), use_container_width=True)
    with col_right:
        st.markdown(
            f'<h3 style="color:{CLR_NEUTRAL};font-size:1rem;margin:0 0 0.5rem 0;">Drawdown</h3>',
            unsafe_allow_html=True,
        )
        st.altair_chart(chart_drawdown(equity_df), use_container_width=True)

    chart_col_1, chart_col_2, chart_col_3 = st.columns(3, gap="medium")

    with chart_col_1:
        st.markdown(
            f'<h3 style="color:{CLR_NEUTRAL};font-size:1rem;margin:0 0 0.5rem 0;">'
            "Duration vs PnL</h3>",
            unsafe_allow_html=True,
        )
        st.altair_chart(chart_duration_vs_pnl(trades_df), use_container_width=True)

    with chart_col_2:
        st.markdown(
            f'<h3 style="color:{CLR_NEUTRAL};font-size:1rem;margin:0 0 0.5rem 0;">'
            "PnL Distribution</h3>",
            unsafe_allow_html=True,
        )
        dist = chart_pnl_distribution(trades_df)
        if dist is not None:
            st.altair_chart(dist, use_container_width=True)
        else:
            st.info("No PnL data available.")

    with chart_col_3:
        st.markdown(
            f'<h3 style="color:{CLR_NEUTRAL};font-size:1rem;margin:0 0 0.5rem 0;">'
            "PnL by Entry Hour</h3>",
            unsafe_allow_html=True,
        )
        st.altair_chart(chart_pnl_by_hour(trades_df), use_container_width=True)

    st.markdown(
        f'<h3 style="color:{CLR_NEUTRAL};font-size:1rem;margin:0.75rem 0 0.5rem 0;">'
        "PnL per Trade</h3>",
        unsafe_allow_html=True,
    )
    st.altair_chart(chart_pnl_per_trade(trades_df), use_container_width=True)


if __name__ == "__main__":
    main()
