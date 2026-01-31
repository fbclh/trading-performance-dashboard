# Trading Performance Dashboard (Python + SQL + Tableau)

This portfolio project turns raw trade logs into a clean, repeatable analytics pipeline and a Tableau-ready dataset.

## What it does
1. **Ingest**: reads the Excel trade report (`Replay_Trading_CME_MINI_ES1!_2025-09-27_79f2b.xlsx`, sheet: `List of trades`)
2. **Transform**: pairs Entry/Exit rows into a single trade record (one row per trade)
3. **Model**: produces a `trades_fact` dataset suitable for BI tools
4. **Metrics**: computes core trading KPIs (win rate, expectancy, profit factor, max drawdown)
5. **Output**: exports CSV files for Tableau dashboarding

## Outputs (for Tableau)
- `trades_fact.csv` — one row per trade (timestamps, prices, size, net PnL, run-up, drawdown)
- `equity_curve.csv` — equity and drawdown over time
- `kpis_summary.csv` — summary KPI table (single row)

## Core KPIs included
- Win Rate
- Average Win / Average Loss
- Expectancy (per trade)
- Profit Factor
- Net PnL
- Max Drawdown (from equity curve)

## How to run
```bash
pip install -r requirements.txt
python etl_from_excel.py
```

## Tableau dashboard suggestion
**Dashboard 1 — Overview**
- KPI tiles (Net PnL, Win Rate, Profit Factor, Expectancy, Max Drawdown)
- Equity curve line chart

**Dashboard 2 — Trade Quality**
- PnL distribution (histogram)
- Run-up vs Drawdown scatter

**Dashboard 3 — Drilldowns**
- PnL by week/month
- PnL by side (Long/Short)
