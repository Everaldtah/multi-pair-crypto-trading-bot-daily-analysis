#!/usr/bin/env python3
"""
Multi-Pair Bot Insight Generator
Analyzes historical data from the repo to generate strategy improvement recommendations
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

REPO_DIR = "/root/multi-pair-crypto-trading-bot-daily-analysis"
ANALYTICS_FILE = Path(REPO_DIR) / "analytics" / "performance_history.json"

def load_history():
    if not ANALYTICS_FILE.exists():
        return []
    with open(ANALYTICS_FILE, 'r') as f:
        return json.load(f)

def calculate_win_rate(trades):
    if not trades:
        return 0.0
    wins = sum(1 for t in trades if float(t['pnl_pct'].replace('%', '')) > 0)
    return (wins / len(trades)) * 100

def generate_insights():
    history = load_history()
    if len(history) < 2:
        return "Need more historical data for meaningful insights."
    
    insights = []
    
    # Trend analysis
    values = [h['total_value'] for h in history]
    pnls = [h['total_pnl'] for h in history]
    
    if values:
        avg_value = sum(values) / len(values)
        max_value = max(values)
        min_value = min(values)
        
        insights.append(f"**Historical Range**: Portfolio has traded between £{min_value:.2f} and £{max_value:.2f} (avg: £{avg_value:.2f})")
        
        if values[-1] >= max_value * 0.98:
            insights.append("🚀 **Peak Performance**: Current portfolio is near all-time highs.")
        elif values[-1] <= min_value * 1.05:
            insights.append("⚠️ **Drawdown Territory**: Portfolio is near historical lows. Review risk parameters.")
    
    # Activity analysis
    total_buys = sum(h['buys'] for h in history)
    total_sells = sum(h['sells'] for h in history)
    
    if total_buys > 0:
        close_ratio = total_sells / total_buys
        insights.append(f"**Trade Closure Rate**: {close_ratio:.2f} ({total_sells}/{total_buys} positions closed)")
        
        if close_ratio < 0.3:
            insights.append("📝 **Holding Pattern**: Most positions remain open. Consider if take-profit levels are too optimistic for current market conditions.")
    
    # Pair performance analysis
    monitor_state_file = Path("/root/multi_bot_monitor_state.json")
    if monitor_state_file.exists():
        with open(monitor_state_file, 'r') as f:
            monitor = json.load(f)
        
        pair_performance = defaultdict(list)
        for trade in monitor.get('closed_trades', []):
            pnl = float(trade['pnl_pct'].replace('%', ''))
            pair_performance[trade['pair']].append(pnl)
        
        if pair_performance:
            insights.append("\n**Pair Performance (Closed Trades):**")
            for pair, pnls in sorted(pair_performance.items(), key=lambda x: sum(x[1]), reverse=True):
                avg_pnl = sum(pnls) / len(pnls)
                win_rate = (sum(1 for p in pnls if p > 0) / len(pnls)) * 100
                insights.append(f"  • {pair}: {len(pnls)} trades, avg {avg_pnl:+.2f}%, win rate {win_rate:.0f}%")
    
    # Recommendations
    insights.append("\n**Strategy Recommendations:**")
    
    recent_pnls = pnls[-7:] if len(pnls) >= 7 else pnls
    if recent_pnls and all(p <= 0 for p in recent_pnls[-3:]):
        insights.append("🔴 **3+ days of flat/negative P&L**: Market may be unfavorable. Consider reducing position size or taking a break until conditions improve.")
    
    if total_buys > 20 and total_sells < 5:
        insights.append("🟡 **Low Closure Rate**: Many entries but few exits. Review whether TP levels are realistic. Consider trailing stops to lock in smaller gains.")
    
    if max_value - min(values[-7:] if len(values) >= 7 else values) > 20:
        insights.append("📉 **High Volatility Detected**: Portfolio swings exceeding £20. Consider tightening stop-losses or reducing max positions from 5 to 3.")
    
    insights.append("✅ **Continue Data Collection**: More closed trades are needed for statistically significant insights. Maintain dry-run mode.")
    
    return "\n\n".join(insights)

def save_insights():
    content = generate_insights()
    today = datetime.now().strftime("%Y-%m-%d")
    
    insight_file = Path(REPO_DIR) / "insights" / f"{today}-strategy-insights.md"
    with open(insight_file, 'w') as f:
        f.write(f"# 🧠 Strategy Insights — {today}\n\n{content}\n")
    
    print(f"Insights saved to {insight_file}")
    return str(insight_file)

if __name__ == "__main__":
    save_insights()
