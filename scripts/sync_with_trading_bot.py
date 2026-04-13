#!/usr/bin/env python3
"""
Sync daily analysis insights with trading bot upgrade system
Reads GitHub repo analytics and generates strategy improvement patches
for the KuCoin-autonomous-crypto-trader repository
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path

ANALYTICS_FILE = "/root/multi-pair-crypto-trading-bot-daily-analysis/analytics/performance_history.json"
MONITOR_STATE = "/root/multi_bot_monitor_state.json"
TRADING_BOT_REPO = "/root/KuCoin-autonomous-crypto-trader"
UPGRADE_LOG = "/root/multi-pair-crypto-trading-bot-daily-analysis/insights/strategy_upgrades.md"

def load_analytics():
    if not Path(ANALYTICS_FILE).exists():
        return []
    with open(ANALYTICS_FILE, 'r') as f:
        return json.load(f)

def load_monitor():
    if not Path(MONITOR_STATE).exists():
        return {"closed_trades": [], "highest_balance": 500.0}
    with open(MONITOR_STATE, 'r') as f:
        return json.load(f)

def evaluate_strategy_adjustments(history, monitor):
    """Analyze data and recommend bot parameter changes"""
    recommendations = []
    
    if len(history) < 3:
        recommendations.append("📊 **Insufficient Data**: Need at least 3 days of history before suggesting parameter adjustments.")
        return recommendations
    
    # Analyze recent performance trend
    recent = history[-7:]
    pnls = [d['total_pnl'] for d in recent]
    values = [d['total_value'] for d in recent]
    
    # Trend detection
    if len(pnls) >= 3:
        if all(pnls[i] < pnls[i+1] for i in range(len(pnls)-1)):
            recommendations.append("🚀 **Uptrend Confirmed**: P&L improving consistently. Consider increasing position size by 2-5% or reducing cash reserve.")
        elif all(pnls[i] > pnls[i+1] for i in range(len(pnls)-1)):
            recommendations.append("🔴 **Downtrend Detected**: P&L declining for 3+ days. Suggest reducing position size or tightening stop-losses.")
    
    # Volatility-based recommendations
    if values:
        volatility = max(values) - min(values)
        if volatility > 25:
            recommendations.append(f"⚠️ **High Volatility**: Portfolio swung £{volatility:.2f}. Recommend reducing max positions from 5 to 3 or tightening SL from -1.5% to -1.0%.")
        elif volatility < 5 and len(history) > 5:
            recommendations.append("🟡 **Low Volatility/Chop**: Portfolio stagnant for multiple days. Consider lowering RSI entry threshold to capture more opportunities.")
    
    # Closure rate analysis
    total_buys = sum(d['buys'] for d in history)
    total_sells = sum(d['sells'] for d in history)
    
    if total_buys > 10:
        close_rate = total_sells / total_buys
        if close_rate < 0.25:
            recommendations.append(f"⏳ **Low Exit Rate**: Only {close_rate*100:.0f}% of positions closed. Take-profit (+3%) may be too high for current market. Consider trailing stops or TP at +2%.")
        elif close_rate > 0.8:
            recommendations.append(f"✅ **Healthy Turnover**: {close_rate*100:.0f}% close rate. Strategy is actively capturing moves. Maintain current parameters.")
    
    # Drawdown analysis
    peak = monitor.get('highest_balance', 500.0)
    current = values[-1] if values else 500.0
    drawdown = ((peak - current) / peak) * 100
    
    if drawdown > 5:
        recommendations.append(f"📉 **Drawdown Alert**: Currently {drawdown:.1f}% below peak (£{peak:.2f}). Activate circuit breaker or pause new entries until trend recovers.")
    
    # Pair-specific insights
    pair_pnls = {}
    for trade in monitor.get('closed_trades', []):
        pair = trade['pair']
        pnl = float(trade['pnl_pct'].replace('%', ''))
        if pair not in pair_pnls:
            pair_pnls[pair] = []
        pair_pnls[pair].append(pnl)
    
    for pair, pnls in pair_pnls.items():
        avg_pnl = sum(pnls) / len(pnls)
        win_rate = (sum(1 for p in pnls if p > 0) / len(pnls)) * 100
        
        if len(pnls) >= 3:
            if win_rate >= 66 and avg_pnl > 1:
                recommendations.append(f"🟢 **{pair} is High-Performing**: {win_rate:.0f}% win rate, avg +{avg_pnl:.2f}%. Consider increasing allocation for this pair.")
            elif win_rate <= 33 and avg_pnl < -0.5:
                recommendations.append(f"🔴 **{pair} Underperforming**: {win_rate:.0f}% win rate, avg {avg_pnl:.2f}%. Consider removing from watchlist or tightening entry criteria.")
    
    return recommendations

def generate_upgrade_log():
    """Generate strategy upgrade recommendations log"""
    history = load_analytics()
    monitor = load_monitor()
    today = datetime.now().strftime("%Y-%m-%d")
    
    recommendations = evaluate_strategy_adjustments(history, monitor)
    
    log_entry = f"""# 🔄 Strategy Upgrade Recommendations — {today}

## Performance Snapshot
- **Days of Data**: {len(history)}
- **Highest Balance**: £{monitor.get('highest_balance', 500.0):.2f}
- **Closed Trades**: {len(monitor.get('closed_trades', []))}
- **Current P&L**: £{history[-1]['total_pnl'] if history else 0:+.2f}

## Recommended Adjustments

"""
    
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            log_entry += f"{i}. {rec}\n\n"
    else:
        log_entry += "No adjustments recommended at this time. Continue current strategy.\n\n"
    
    log_entry += f"""---

## Implementation Notes

To apply any of these changes:
1. Modify bot parameters in `/root/simple_multi_bot.py` or `/root/live_eth_trader_v4.py`
2. Test in dry-run mode first
3. Use the `trading-bot-github-sync` skill to commit changes
4. Update this log with the applied changes

*Generated automatically from daily analysis data.*
"""
    
    Path(UPGRADE_LOG).parent.mkdir(exist_ok=True)
    with open(UPGRADE_LOG, 'w') as f:
        f.write(log_entry)
    
    print(f"✅ Strategy upgrade log saved: {UPGRADE_LOG}")
    return log_entry

def sync_to_upgrade_system():
    """Push upgrade recommendations to trading bot upgrade tracking"""
    # Read current upgrade log
    if not Path(UPGRADE_LOG).exists():
        generate_upgrade_log()
    
    with open(UPGRADE_LOG, 'r') as f:
        content = f.read()
    
    # This can be extended to automatically create GitHub issues
    # or modify the trading bot source code based on recommendations
    print("=" * 60)
    print("📡 SYNC WITH TRADING BOT UPGRADE SYSTEM")
    print("=" * 60)
    print(content[:500] + "...")
    print("\n✅ Sync complete. Review recommendations above before applying.")

if __name__ == "__main__":
    generate_upgrade_log()
    sync_to_upgrade_system()
