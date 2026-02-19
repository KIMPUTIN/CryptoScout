
from datetime import datetime, timedelta
from database.db import get_connection
import math


def backtest_top_n(days_ago: int = 7, hold_days: int = 7, top_n: int = 10):

    conn = get_connection()
    cursor = conn.cursor()

    # Entry snapshot
    cursor.execute("""
    SELECT * FROM project_history
    WHERE snapshot_time <= datetime('now', ?)
    ORDER BY snapshot_time DESC
    """, (f"-{days_ago} days",))

    historical = cursor.fetchall()

    if not historical:
        conn.close()
        return {"error": "Not enough historical data"}

    sorted_hist = sorted(
        historical,
        key=lambda x: x["combined_score"],
        reverse=True
    )

    selected = sorted_hist[:top_n]

    returns = []
    wins = 0

    for coin in selected:

        entry_price = coin["current_price"]
        entry_time = datetime.fromisoformat(coin["snapshot_time"])
        exit_time = entry_time + timedelta(days=hold_days)

        cursor.execute("""
        SELECT current_price FROM project_history
        WHERE symbol=? AND snapshot_time >= ?
        ORDER BY snapshot_time ASC
        LIMIT 1
        """, (coin["symbol"], exit_time.isoformat()))

        exit_data = cursor.fetchone()

        if not exit_data:
            continue

        exit_price = exit_data["current_price"]

        if entry_price > 0:

            return_pct = (exit_price - entry_price) / entry_price
            returns.append(return_pct)

            if return_pct > 0:
                wins += 1

    conn.close()

    if not returns:
        return {"error": "No valid exit data"}

    # ==========================
    # PERFORMANCE METRICS
    # ==========================

    avg_return = sum(returns) / len(returns)
    win_rate = (wins / len(returns)) * 100

    # --- Equity Curve ---
    equity = 1.0
    equity_curve = []

    for r in returns:
        equity *= (1 + r)
        equity_curve.append(equity)

    # --- Max Drawdown ---
    peak = equity_curve[0]
    max_drawdown = 0

    for value in equity_curve:
        if value > peak:
            peak = value

        drawdown = (peak - value) / peak
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    # --- Volatility (std deviation) ---
    mean_return = avg_return
    variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
    volatility = math.sqrt(variance)

    return {
        "entry_days_ago": days_ago,
        "holding_period_days": hold_days,
        "top_n": top_n,
        "trades_evaluated": len(returns),
        "average_return_percent": round(avg_return * 100, 2),
        "win_rate_percent": round(win_rate, 2),
        "max_drawdown_percent": round(max_drawdown * 100, 2),
        "volatility_percent": round(volatility * 100, 2)
    }
