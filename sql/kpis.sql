-- kpis.sql
-- Core KPIs for Trading Performance Dashboard
-- Assumes a table named trades_fact with one row per trade and column pnl_net.

-- Win rate, avg win/loss, expectancy, profit factor, net PnL
WITH
base AS (
    SELECT pnl_net
    FROM trades_fact
),

wins AS (
    SELECT pnl_net FROM base
    WHERE pnl_net > 0
),

losses AS (
    SELECT pnl_net FROM base
    WHERE pnl_net < 0
),

agg AS (
    SELECT
        (SELECT COUNT(*) FROM base) AS total_trades,
        (SELECT COUNT(*) FROM wins) AS wins,
        (SELECT COUNT(*) FROM losses) AS losses,
        (SELECT SUM(pnl_net) FROM base) AS net_pnl_usd,
        (SELECT AVG(pnl_net) FROM wins) AS avg_win_usd,
        (SELECT ABS(AVG(pnl_net)) FROM losses) AS avg_loss_usd,
        (SELECT SUM(pnl_net) FROM wins) AS gross_profit_usd,
        (SELECT ABS(SUM(pnl_net)) FROM losses) AS gross_loss_usd
)

SELECT
    total_trades,
    wins,
    losses,
    avg_win_usd,
    avg_loss_usd,
    net_pnl_usd,
    -- Expectancy per trade = (win_rate * avg_win) - (loss_rate * avg_loss)
    CAST(wins AS REAL) / NULLIF(total_trades, 0) AS win_rate,
    (
        (CAST(wins AS REAL) / NULLIF(total_trades, 0)) * avg_win_usd
        - (1 - (CAST(wins AS REAL) / NULLIF(total_trades, 0))) * avg_loss_usd
    ) AS expectancy_usd_per_trade,
    gross_profit_usd / NULLIF(gross_loss_usd, 0) AS profit_factor
FROM agg;
