# Trading Performance Dashboard

**Python + SQL + Streamlit + Tableau**

The project analyzes trading strategy performance and risk metrics using historical trade data. It includes data processing, KPI calculation, a dark-themed **Streamlit** dashboard, and **Tableau-ready** CSV exports.

Although the example uses trading data, the same pipeline structure applies to financial, operational, and performance analytics in business environments.

**Repository:** [github.com/fbclh/trading-performance-dashboard](https://github.com/fbclh/trading-performance-dashboard)

## Project layout

```
├── app/              # Streamlit dashboard
├── data/             # Generated CSVs (ETL output; sample files included for the demo)
├── etl/              # Excel → CSV pipeline
├── sql/              # Ad hoc SQL (e.g. KPIs)
├── screenshots/
├── .streamlit/       # Theme (dark)
├── requirements.txt
├── pyproject.toml
└── README.md
```

## What it does

1. **Ingest** — Reads structured trade reports (Excel: sheet `List of trades` — path is configurable in `etl/etl_from_excel.py`).
2. **Transform** — Pairs entry and exit rows into one row per trade.
3. **Model** — Builds a `trades_fact`-style dataset for BI tools.
4. **Metrics** — Computes win rate, expectancy, profit factor, net PnL, max drawdown, and related KPIs.
5. **Output** — Writes CSVs under `data/` for Tableau or other tools, and powers the Streamlit app.

> **Note:** Raw proprietary exports are not required to explore the repo; sample CSV outputs are included so the dashboard runs without running the ETL.

## Outputs (Tableau / BI)

Written to `data/` by the ETL:

| File | Description |
|------|-------------|
| `data/trades_fact.csv` | One row per trade (timestamps, prices, size, net PnL, run-up, drawdown) |
| `data/equity_curve.csv` | Equity progression and drawdown over time |
| `data/kpis_summary.csv` | Single-row KPI snapshot |

## Core KPIs

- Win rate  
- Average win vs. average loss  
- Expectancy (per trade)  
- Profit factor  
- Net PnL  
- Maximum drawdown (from equity curve)  

## How to run

From the **project root**:

```bash
pip install -r requirements.txt
python etl/etl_from_excel.py
```

### Streamlit dashboard

```bash
streamlit run app/dashboard_app.py
```

(Optional) Create a virtual environment first: `python -m venv .venv` and activate it, then `pip install -r requirements.txt`.

## Linting and formatting

Config is in `pyproject.toml` (Ruff).

```bash
pip install ruff
ruff check .
ruff format .
```

### SQL (`sql/kpis.sql`)

Optional formatting with a [SQL Formatter](https://marketplace.visualstudio.com/items?itemName=adpyke.vscode-sql-formatter) extension; optional linting with [SQLFluff](https://marketplace.visualstudio.com/items?itemName=dorzey.vscode-sqlfluff).

## Tableau ideas

- **Overview** — KPI tiles, equity curve, drawdown  
- **Trade quality** — PnL distribution, run-up vs drawdown  
- **Drilldowns** — PnL by period, by side (long/short)  

## License

See [LICENSE](LICENSE) (MIT).
