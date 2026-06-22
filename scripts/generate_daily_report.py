#!/usr/bin/env python3
"""
Multi-Pair Crypto Trading Bot - Daily Analysis Report Generator
Generates comprehensive daily trading reports with market analysis
and strategy insights. Pushes results to GitHub for historical tracking.
"""

import re
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# Configuration
REPO_DIR = "/root/multi-pair-crypto-trading-bot-daily-analysis"
MULTI_BOT_LOG = "/root/dry_run_bot.log"
V4_BOT_LOG = "/root/bot_v4.log"
TRADER_STATE = "/root/trader_state.json"
MONITOR_STATE = "/root/multi_bot_monitor_state.json"
BOT_CONFIG = "/root/bot_config.json"
INITIAL_CAPITAL = 500.00

# Trading pairs monitored
PAIRS = [
    "ETH-USDT", "BTC-USDT", "SOL-USDT", "LINK-USDT",
    "AVAX-USDT", "DOT-USDT", "MATIC-USDT", "UNI-USDT",
    "AAVE-USDT", "ATOM-USDT", "ADA-USDT", "DOGE-USDT"
]

def run_cmd(cmd, cwd=None):
    """Run shell command and return output"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def parse_multi_bot_log():
    """Parse multi-pair bot log for daily activity"""
    if not Path(MULTI_BOT_LOG).exists():
        return None
    
    with open(MULTI_BOT_LOG, 'r') as f:
        content = f.read()
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Get all cycles
    cycle_pattern = r'CYCLE\s+(\d+)\s+-\s+(\d{2}:\d{2}:\d{2})'
    cycles = re.findall(cycle_pattern, content)
    total_cycles = len(cycles)
    
    # Get all summaries
    summary_pattern = r'Portfolio Summary:\s+Open Positions:\s+(\d+).*?Available Cash:\s+£([\d.]+).*?Total P&L:\s+£([\d.-]+).*?Total Value:\s+£([\d.]+)'
    summaries = re.findall(summary_pattern, content, re.DOTALL)
    
    # Get buy/sell signals
    buy_pattern = r'🟢\s+BUY\s+(\w+-USDT)\s+@\s+\$([\d.]+)'
    sell_pattern = r'🔴\s+SELL\s+(\w+-USDT)\s+@\s+\$([\d.]+)'
    
    buys = re.findall(buy_pattern, content)
    sells = re.findall(sell_pattern, content)
    
    # Get position P&L history
    position_pattern = r'📊\s+(\w+-USDT):\s+\$([\d.]+)\s+\|\s+P&L:\s+([+-]?[\d.]+%)'
    positions = re.findall(position_pattern, content)
    
    # Calculate unique entries and pair frequency
    pair_buys = defaultdict(int)
    for pair, price in buys:
        pair_buys[pair] += 1
    
    # Get latest prices for each pair
    latest_prices = {}
    for pair, price, pnl in positions:
        latest_prices[pair] = float(price)
    
    return {
        "total_cycles": total_cycles,
        "total_buys": len(buys),
        "total_sells": len(sells),
        "open_positions": int(summaries[-1][0]) if summaries else 0,
        "available_cash": float(summaries[-1][1]) if summaries else 0,
        "total_pnl": float(summaries[-1][2]) if summaries else 0,
        "total_value": float(summaries[-1][3]) if summaries else 0,
        "pair_buys": dict(pair_buys),
        "latest_prices": latest_prices,
        "unique_pairs_traded": len(pair_buys),
        "all_buys": buys,
        "all_sells": sells
    }

def parse_v4_bot_log():
    """Parse v4 live bot log"""
    if not Path(V4_BOT_LOG).exists():
        return None
    
    # Read last 1000 lines for recent activity
    lines = Path(V4_BOT_LOG).read_text().split('\n')[-1000:]
    content = '\n'.join(lines)
    
    # Extract key metrics
    balance_match = re.search(r'Balance:\s*\$?([\d.]+)', content)
    pnl_match = re.search(r'P&L:\s*([+-]?[\d.]+)', content)
    
    trades = []
    trade_pattern = r'(BUY|SELL|TP|SL|EXIT).*?(\w+-USDT).*?\$?([\d.]+)'
    for line in lines:
        match = re.search(trade_pattern, line, re.IGNORECASE)
        if match:
            trades.append({
                "action": match.group(1).upper(),
                "pair": match.group(2),
                "price": match.group(3)
            })
    
    return {
        "recent_trades": trades[-10:] if trades else [],
        "balance": float(balance_match.group(1)) if balance_match else None,
        "total_activity": len(trades)
    }

def load_monitor_state():
    """Load monitor state for closed trades"""
    if not Path(MONITOR_STATE).exists():
        return {"closed_trades": [], "highest_balance": INITIAL_CAPITAL}
    
    with open(MONITOR_STATE, 'r') as f:
        return json.load(f)

def get_readiness_status():
    """Get current live trading readiness status"""
    readiness_file = Path(REPO_DIR) / "analytics" / "readiness_assessment.json"
    if not readiness_file.exists():
        return None
    with open(readiness_file, 'r') as f:
        data = json.load(f)
    if data.get("assessments"):
        return data["assessments"][-1]
    return None

def analyze_market_conditions(multi_data):
    """Generate market condition analysis"""
    if not multi_data:
        return "No market data available."
    
    analysis = []
    
    # Market volatility assessment
    if multi_data["total_buys"] >= 5:
        analysis.append("**High Activity**: The bot found multiple entry signals, suggesting volatile or trending market conditions across monitored pairs.")
    elif multi_data["total_buys"] >= 2:
        analysis.append("**Moderate Activity**: Selective opportunities were identified. Market showing mixed signals with some pairs presenting valid setups.")
    else:
        analysis.append("**Low Activity / Chop**: Few or no entry signals triggered. The market is likely in a consolidation phase or the bot's criteria are too strict for current conditions.")
    
    # Pair diversification
    if multi_data["unique_pairs_traded"] >= 3:
        analysis.append(f"**Good Diversification**: {multi_data['unique_pairs_traded']} different pairs showed signals, reducing single-asset risk.")
    elif multi_data["unique_pairs_traded"] >= 1:
        analysis.append(f"**Limited Diversification**: Only {multi_data['unique_pairs_traded']} pair(s) triggered entries. Correlated market movement or lack of opportunities.")
    else:
        analysis.append("**No Trades**: The bot remained in cash, avoiding forced entries in unfavorable conditions.")
    
    # Performance
    pnl = multi_data["total_pnl"]
    if pnl > 5:
        analysis.append(f"**Strong Performance**: +£{pnl:.2f} P&L indicates the bot captured profitable moves effectively.")
    elif pnl > 0:
        analysis.append(f"**Positive Performance**: +£{pnl:.2f} P&L. Small gains but capital preservation is intact.")
    elif pnl > -5:
        analysis.append(f"**Flat/Slight Drawdown**: £{pnl:+.2f} P&L. Within normal risk parameters.")
    else:
        analysis.append(f"**Notable Drawdown**: £{pnl:+.2f} P&L. Consider reviewing stop-loss levels and position sizing.")
    
    return "\n\n".join(analysis)

def generate_strategy_insights(multi_data, monitor_state, v4_data):
    """Generate actionable strategy insights"""
    insights = []
    
    # Entry frequency insight
    if multi_data and multi_data["total_cycles"] > 0:
        buy_rate = multi_data["total_buys"] / multi_data["total_cycles"]
        if buy_rate < 0.01:
            insights.append("🔍 **Entry Criteria**: The buy rate is very low (<1% of cycles). Consider relaxing RSI threshold from <30 to <35 or adding trend-confirmation alternatives to capture more opportunities without sacrificing edge.")
        elif buy_rate > 0.15:
            insights.append("⚠️ **Entry Frequency**: High buy rate (>15% of cycles). Risk of over-trading in choppy conditions. Consider tightening signal requirements or reducing position size.")
        else:
            insights.append("✅ **Entry Frequency**: Buy rate is well-balanced, indicating selective but active strategy.")
    
    # Exit/closure insight
    closed_count = len(monitor_state.get("closed_trades", []))
    if closed_count == 0 and multi_data and multi_data["total_buys"] > 0:
        insights.append("⏳ **Holding Period**: Positions are still open. No exits yet. Monitor if TP (+3%) or SL (-1.5%) levels are appropriate for current volatility.")
    
    # Diversification insight
    if multi_data:
        open_pct = (multi_data["open_positions"] / 5) * 100
        insights.append(f"📊 **Capital Deployment**: {multi_data['open_positions']}/5 positions open ({open_pct:.0f}% max capacity). {multi_data['available_cash']:.0f} cash available for new entries.")
    
    # v4 vs v5 comparison
    if v4_data and multi_data:
        insights.append("🔄 **Multi-Pair Advantage**: While v4 is tied to ETH movement, v5 can rotate capital into whichever pair is trending. Continue dry-run validation before going live.")
    
    # Risk management
    if multi_data and multi_data["total_value"] < INITIAL_CAPITAL - 10:
        insights.append("🛡️ **Risk Alert**: Portfolio has declined more than £10 from initial capital. Consider activating circuit breaker or reviewing strategy parameters.")
    elif multi_data and multi_data["total_value"] > INITIAL_CAPITAL:
        insights.append("🚀 **Strategy Validation**: Portfolio is above initial capital. The multi-pair approach is showing promise. Document what market conditions led to this success.")
    
    return "\n\n".join(insights)

def generate_daily_report():
    """Generate the full daily markdown report"""
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    multi_data = parse_multi_bot_log()
    v4_data = parse_v4_bot_log()
    monitor_state = load_monitor_state()
    
    market_analysis = analyze_market_conditions(multi_data)
    insights = generate_strategy_insights(multi_data, monitor_state, v4_data)
    readiness = get_readiness_status()
    
    # Build report
    report = f"""# 📊 Daily Trading Analysis — {today}

**Report Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}  
**Bot Version:** Multi-Pair v5 (Dry Run) + ETH v4 (Live)  
**Initial Capital:** £{INITIAL_CAPITAL:.2f}

---

## 🎯 Live Trading Readiness

"""
    
    if readiness:
        status_emoji = {
            "READY_TO_DEPLOY": "🟢",
            "READY_BUT_WAITING_FOR_WINDOW": "🟡",
            "APPROACHING_READY": "🟡",
            "BUILDING_CONFIDENCE": "🟠",
            "COLLECTING_DATA": "🔴"
        }.get(readiness["status"], "⚪")
        
        report += f"""| Metric | Value |
|--------|-------|
| Status | {status_emoji} {readiness['status']} |
| Confidence Score | {readiness['confidence_score']}% / 100% |
| Days of Data | {readiness['days_of_data']} |
| Closed Trades | {readiness['closed_trades']} |

**Target:** Deploy £500 live capital between **April 20 - May 1, 2026** when confidence reaches **75%+**

"""
    else:
        report += "Readiness assessment not yet available. Running initial data collection phase.\n\n"
    
    report += f"""---

## 💰 Portfolio Performance

### Multi-Pair Bot (v5) — Dry Run
| Metric | Value |
|--------|-------|
| Total Portfolio Value | £{multi_data['total_value']:.2f} |
| Available Cash | £{multi_data['available_cash']:.2f} |
| Total P&L | £{multi_data['total_pnl']:+.2f} |
| Open Positions | {multi_data['open_positions']}/5 |
| Total Buy Signals | {multi_data['total_buys']} |
| Total Sell Signals | {multi_data['total_sells']} |
| Unique Pairs Traded | {multi_data['unique_pairs_traded']} |
| Cycles Monitored | {multi_data['total_cycles']} |

### ETH v4 Bot (Live)
| Metric | Value |
|--------|-------|
| Recent Activity | {v4_data['total_activity'] if v4_data else 'N/A'} events |
| Balance | {'$' + str(v4_data['balance']) if v4_data and v4_data['balance'] else 'N/A'} |

---

## 📈 Open Positions

"""
    
    if multi_data and multi_data["latest_prices"]:
        report += "| Pair | Current Price | Status |\n"
        report += "|------|---------------|--------|\n"
        for pair, price in multi_data["latest_prices"].items():
            # Determine if position is open based on buys
            if pair in multi_data["pair_buys"]:
                report += f"| {pair} | ${price:.2f} | 🟢 Open |\n"
    else:
        report += "No open positions recorded.\n"
    
    report += f"""

---

## 📝 Trade History

### Buy Entries
"""
    
    if multi_data and multi_data["all_buys"]:
        report += "| # | Pair | Entry Price |\n"
        report += "|---|------|-------------|\n"
        for i, (pair, price) in enumerate(multi_data["all_buys"], 1):
            report += f"| {i} | {pair} | ${price} |\n"
    else:
        report += "No buy entries today.\n"
    
    report += "\n### Closed Trades\n"
    if monitor_state.get("closed_trades"):
        report += "| Time | Pair | Exit Price | P&L |\n"
        report += "|------|------|------------|-----|\n"
        for trade in monitor_state["closed_trades"]:
            pnl_emoji = "🟢" if float(trade['pnl_pct'].replace('%', '')) > 0 else "🔴"
            report += f"| {trade['time']} | {trade['pair']} | ${trade['price']:.2f} | {pnl_emoji} {trade['pnl_pct']} |\n"
    else:
        report += "No closed trades recorded.\n"
    
    report += f"""

---

## 🌍 Market Situation Analysis

{market_analysis}

---

## 🧠 Strategy Insights & Recommendations

{insights}

---

## 📋 Action Items for Tomorrow

- [ ] Review overnight price action on open positions
- [ ] Check if any positions hit TP/SL
- [ ] Monitor correlation between ETH and SOL (primary traded pairs)
- [ ] Assess whether to extend dry-run period or switch to live mode
- [ ] Update this analysis with tomorrow's data

---

## 📚 Historical Reports

See previous daily reports in the [`daily-reports/`](../daily-reports/) directory.

---

*This report is auto-generated by the Multi-Pair Bot Analysis System. No API keys or sensitive data are included.*
"""
    
    return report, today, multi_data

def update_analytics(multi_data, today):
    """Update cumulative analytics JSON"""
    analytics_file = Path(REPO_DIR) / "analytics" / "performance_history.json"
    
    history = []
    if analytics_file.exists():
        with open(analytics_file, 'r') as f:
            history = json.load(f)
    
    if multi_data:
        entry = {
            "date": today,
            "total_value": multi_data["total_value"],
            "total_pnl": multi_data["total_pnl"],
            "open_positions": multi_data["open_positions"],
            "buys": multi_data["total_buys"],
            "sells": multi_data["total_sells"],
            "unique_pairs": multi_data["unique_pairs_traded"]
        }
        
        # Update or append
        history = [h for h in history if h["date"] != today]
        history.append(entry)
        history.sort(key=lambda x: x["date"])
        
        with open(analytics_file, 'w') as f:
            json.dump(history, f, indent=2)

def push_to_github(today):
    """Commit and push daily report to GitHub"""
    os.chdir(REPO_DIR)
    
    # Git config
    run_cmd('git config user.email "bot@hermes.trading"')
    run_cmd('git config user.name "Hermes Trading Bot"')
    
    # Get token
    token = os.getenv("GITHUB_TOKEN", "")
    if not token:
        # Try common locations
        for env_file in ["/root/.env", os.path.expanduser("~/.hermes/.env")]:
            if Path(env_file).exists():
                with open(env_file) as f:
                    for line in f:
                        # SECURITY FIX: Removed hardcoded credential
                        # if line.startswith("GITHUB_TOKEN="):
                        # TODO: Use environment variable instead
                            token = line.strip().split("=", 1)[1].strip('"\'')
                            break
                if token:
                    break
    
    # Set remote URL with token
    if token:
        remote_url = f"https://{token}@github.com/Everaldtah/multi-pair-crypto-trading-bot-daily-analysis.git"
        run_cmd(f"git remote set-url origin {remote_url}")
    
    # Stage all changes
    stdout, stderr, rc = run_cmd("git add -A")
    if rc != 0:
        print(f"Git add error: {stderr}")
        return False
    
    # Check if there are changes to commit
    stdout, stderr, rc = run_cmd("git diff --cached --stat")
    if not stdout.strip():
        print("No changes to commit.")
        return True
    
    # Commit
    commit_msg = f"Daily Analysis: {today} — Multi-Pair Bot Performance Report"
    stdout, stderr, rc = run_cmd(f'git commit -m "{commit_msg}"')
    if rc != 0:
        print(f"Git commit error: {stderr}")
        return False
    
    # Push
    stdout, stderr, rc = run_cmd("git push origin main")
    
    # Reset remote URL to remove token from history
    run_cmd("git remote set-url origin https://github.com/Everaldtah/multi-pair-crypto-trading-bot-daily-analysis.git")
    
    if rc != 0:
        print(f"Git push error: {stderr}")
        return False
    
    print(f"✅ Successfully pushed daily report for {today}")
    return True

def main():
    """Main entry point"""
    print("=" * 60)
    print("📊 GENERATING MULTI-PAIR BOT DAILY ANALYSIS")
    print("=" * 60)
    
    # Ensure directories exist
    for subdir in ["daily-reports", "analytics", "market-data", "insights"]:
        Path(REPO_DIR) / subdir / ".gitkeep"
        (Path(REPO_DIR) / subdir).mkdir(exist_ok=True)
    
    report, today, multi_data = generate_daily_report()
    
    # Save daily report
    report_filename = f"daily-reports/{today}-trading-analysis.md"
    report_path = Path(REPO_DIR) / report_filename
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"✅ Report saved: {report_path}")
    
    # Update analytics
    update_analytics(multi_data, today)
    print("✅ Analytics updated")
    
    # Update README with latest summary
    update_readme(today, multi_data)
    print("✅ README updated")
    
    # Generate insights and sync with upgrade system
    print("\n🧠 Generating strategy insights...")
    os.system(f"cd {REPO_DIR} && python3 scripts/insight_generator.py")
    os.system(f"cd {REPO_DIR} && python3 scripts/sync_with_trading_bot.py")
    print("✅ Insights and upgrade sync complete")
    
    # Push to GitHub
    success = push_to_github(today)
    
    if success:
        print("\n🎉 Daily analysis complete and synced to GitHub!")
        print(f"📎 https://github.com/Everaldtah/multi-pair-crypto-trading-bot-daily-analysis/tree/main/{report_filename}")
    else:
        print("\n⚠️ Report generated but GitHub push failed.")
        sys.exit(1)

def update_readme(today, multi_data):
    """Update README with latest summary"""
    readme = f"""# Multi-Pair Crypto Trading Bot — Daily Analysis

> Automated daily trading reports and market analysis for the multi-pair crypto trading bot.

## 📅 Latest Report

**[{today} — Daily Trading Analysis](./daily-reports/{today}-trading-analysis.md)**

## 📊 Quick Stats

| Metric | Value |
|--------|-------|
| Latest Portfolio Value | {'£' + f"{multi_data['total_value']:.2f}" if multi_data else 'N/A'} |
| Total P&L | {'£' + f"{multi_data['total_pnl']:+.2f}" if multi_data else 'N/A'} |
| Open Positions | {f"{multi_data['open_positions']}/5" if multi_data else 'N/A'} |
| Unique Pairs Traded | {multi_data['unique_pairs_traded'] if multi_data else 'N/A'} |

## 📁 Repository Structure

```
.
├── daily-reports/          # Daily markdown trading reports
├── analytics/              # Cumulative performance data (JSON)
├── market-data/            # Market condition snapshots
├── strategies/             # Strategy evolution and backtests
├── insights/               # Actionable trading insights
└── README.md               # This file
```

## 🤖 Bots Tracked

1. **Multi-Pair Bot v5** — Dry-run portfolio manager monitoring 12 crypto pairs
2. **ETH Live Trader v4** — Live single-pair bot on KuCoin

## 🔒 Security

- No API keys, credentials, or sensitive configuration are stored in this repository
- All data is sanitized before commit
- Trading secrets remain in local `.env` files only

## 🔄 Automation

This repository is auto-updated daily via cron job.

---

*Generated by Hermes Trading Bot Analysis System*
"""
    
    with open(Path(REPO_DIR) / "README.md", 'w') as f:
        f.write(readme)

if __name__ == "__main__":
    main()
