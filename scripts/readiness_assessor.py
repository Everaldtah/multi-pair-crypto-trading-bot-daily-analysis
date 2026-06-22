#!/usr/bin/env python3
"""
Multi-Pair Bot Live Trading Readiness Assessor
Tracks market conditions, bot performance, and strategy confidence
to determine optimal timing for £500 live capital deployment.
Target window: April 20 - May 1, 2026
"""

import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import statistics

# Configuration
REPO_DIR = "/root/multi-pair-crypto-trading-bot-daily-analysis"
ASSESSMENT_FILE = Path(REPO_DIR) / "analytics" / "readiness_assessment.json"
CONFIDENCE_DB = Path(REPO_DIR) / "analytics" / "confidence_database.json"
MULTI_BOT_LOG = "/root/dry_run_bot.log"
MONITOR_STATE = "/root/multi_bot_monitor_state.json"

# Target deployment window
DEPLOY_WINDOW_START = datetime(2026, 4, 20)
DEPLOY_WINDOW_END = datetime(2026, 5, 1)

# Minimum data requirements for confidence
MIN_DAYS_DATA = 7  # At least 7 days of dry-run data
MIN_CLOSED_TRADES = 5  # At least 5 completed trades
MIN_WIN_RATE = 40  # Minimum 40% win rate
MAX_ACCEPTABLE_DRAWDOWN = 10  # Max 10% from peak

# Confidence scoring weights
WEIGHTS = {
    "data_sufficiency": 15,      # Enough days of data
    "trade_sample": 15,          # Enough closed trades
    "win_rate": 20,              # Historical win rate
    "profit_consistency": 20,    # Consistent profit trend
    "drawdown_control": 15,      # Acceptable drawdown levels
    "market_conditions": 15      # Favorable market regime
}

class ReadinessAssessor:
    def __init__(self):
        self.assessment = self.load_assessment()
        self.confidence_db = self.load_confidence_db()
        
    def load_assessment(self):
        if ASSESSMENT_FILE.exists():
            with open(ASSESSMENT_FILE, 'r') as f:
                return json.load(f)
        return {
            "first_run_date": datetime.now().isoformat(),
            "assessments": [],
            "current_confidence": 0,
            "ready_date": None,
            "recommended_capital": 500,
            "status": "COLLECTING_DATA"
        }
    
    def load_confidence_db(self):
        if CONFIDENCE_DB.exists():
            with open(CONFIDENCE_DB, 'r') as f:
                return json.load(f)
        return {
            "daily_snapshots": [],
            "market_regimes": [],
            "pair_performance": {},
            "volatility_history": []
        }
    
    def save_assessment(self):
        with open(ASSESSMENT_FILE, 'w') as f:
            json.dump(self.assessment, f, indent=2)
    
    def save_confidence_db(self):
        with open(CONFIDENCE_DB, 'w') as f:
            json.dump(self.confidence_db, f, indent=2)
    
    def parse_bot_data(self):
        """Extract current performance data from bot logs"""
        if not Path(MULTI_BOT_LOG).exists():
            return None
        
        with open(MULTI_BOT_LOG, 'r') as f:
            content = f.read()
        
        # Get latest summary
        summary_pattern = r'Portfolio Summary:\s+Open Positions:\s+(\d+).*?Available Cash:\s+£([\d.]+).*?Total P&L:\s+£([\d.-]+).*?Total Value:\s+£([\d.]+)'
        summaries = re.findall(summary_pattern, content, re.DOTALL)
        
        # Get all position P&L history
        position_pattern = r'📊\s+(\w+-USDT):\s+\$([\d.]+)\s+\|\s+P&L:\s+([+-]?[\d.]+%)'
        positions = re.findall(position_pattern, content)
        
        # Get buy/sell counts
        buy_pattern = r'🟢\s+BUY\s+(\w+-USDT)'
        sell_pattern = r'🔴\s+SELL\s+(\w+-USDT)'
        buys = re.findall(buy_pattern, content)
        sells = re.findall(sell_pattern, content)
        
        if not summaries:
            return None
        
        latest = summaries[-1]
        return {
            "open_positions": int(latest[0]),
            "available_cash": float(latest[1]),
            "total_pnl": float(latest[2]),
            "total_value": float(latest[3]),
            "total_buys": len(buys),
            "total_sells": len(sells),
            "current_positions": positions[-5:] if positions else []
        }
    
    def load_monitor_data(self):
        if not Path(MONITOR_STATE).exists():
            return {"closed_trades": [], "highest_balance": 500.0}
        with open(MONITOR_STATE, 'r') as f:
            return json.load(f)
    
    def calculate_scores(self, bot_data, monitor_data, analytics_history):
        """Calculate confidence scores across all criteria"""
        scores = {}
        
        # 1. Data Sufficiency Score
        days_running = len(analytics_history)
        if days_running >= MIN_DAYS_DATA:
            scores["data_sufficiency"] = WEIGHTS["data_sufficiency"]
        else:
            scores["data_sufficiency"] = (days_running / MIN_DAYS_DATA) * WEIGHTS["data_sufficiency"]
        
        # 2. Trade Sample Score
        closed_trades = len(monitor_data.get("closed_trades", []))
        if closed_trades >= MIN_CLOSED_TRADES:
            scores["trade_sample"] = WEIGHTS["trade_sample"]
        else:
            scores["trade_sample"] = (closed_trades / MIN_CLOSED_TRADES) * WEIGHTS["trade_sample"]
        
        # 3. Win Rate Score
        if closed_trades > 0:
            wins = sum(1 for t in monitor_data["closed_trades"] 
                      if float(t['pnl_pct'].replace('%', '')) > 0)
            win_rate = (wins / closed_trades) * 100
            if win_rate >= MIN_WIN_RATE:
                scores["win_rate"] = WEIGHTS["win_rate"]
            else:
                scores["win_rate"] = (win_rate / MIN_WIN_RATE) * WEIGHTS["win_rate"]
        else:
            scores["win_rate"] = 0
        
        # 4. Profit Consistency Score
        if len(analytics_history) >= 3:
            pnls = [d['total_pnl'] for d in analytics_history[-7:]]  # Last 7 days
            if len(pnls) >= 3:
                # Check if generally positive or improving
                positive_days = sum(1 for p in pnls if p >= 0)
                consistency = positive_days / len(pnls)
                scores["profit_consistency"] = consistency * WEIGHTS["profit_consistency"]
            else:
                scores["profit_consistency"] = 0
        else:
            scores["profit_consistency"] = 0
        
        # 5. Drawdown Control Score
        if bot_data:
            peak = monitor_data.get("highest_balance", 500.0)
            current = bot_data["total_value"]
            drawdown = ((peak - current) / peak) * 100 if peak > 0 else 0
            if drawdown <= MAX_ACCEPTABLE_DRAWDOWN:
                scores["drawdown_control"] = WEIGHTS["drawdown_control"]
            else:
                scores["drawdown_control"] = max(0, 
                    (1 - (drawdown - MAX_ACCEPTABLE_DRAWDOWN) / MAX_ACCEPTABLE_DRAWDOWN) * WEIGHTS["drawdown_control"])
        else:
            scores["drawdown_control"] = 0
        
        # 6. Market Conditions Score
        if bot_data:
            # Check if bot is actively finding opportunities
            has_activity = bot_data["total_buys"] > 0 or bot_data["total_sells"] > 0
            # Check portfolio is healthy
            portfolio_healthy = bot_data["total_value"] >= 490  # Within 2% of start
            
            if has_activity and portfolio_healthy:
                scores["market_conditions"] = WEIGHTS["market_conditions"]
            elif has_activity or portfolio_healthy:
                scores["market_conditions"] = WEIGHTS["market_conditions"] * 0.5
            else:
                scores["market_conditions"] = 0
        else:
            scores["market_conditions"] = 0
        
        return scores
    
    def generate_readiness_report(self):
        """Generate comprehensive readiness assessment"""
        bot_data = self.parse_bot_data()
        monitor_data = self.load_monitor_data()
        
        # Load analytics history
        analytics_file = Path(REPO_DIR) / "analytics" / "performance_history.json"
        analytics_history = []
        if analytics_file.exists():
            with open(analytics_file, 'r') as f:
                analytics_history = json.load(f)
        
        scores = self.calculate_scores(bot_data, monitor_data, analytics_history)
        total_confidence = sum(scores.values())
        
        now = datetime.now()
        
        # Determine status
        if total_confidence >= 80:
            if DEPLOY_WINDOW_START <= now <= DEPLOY_WINDOW_END:
                status = "READY_TO_DEPLOY"
                if not self.assessment.get("ready_date"):
                    self.assessment["ready_date"] = now.strftime("%Y-%m-%d")
            else:
                status = "READY_BUT_WAITING_FOR_WINDOW"
        elif total_confidence >= 60:
            status = "APPROACHING_READY"
        elif total_confidence >= 40:
            status = "BUILDING_CONFIDENCE"
        else:
            status = "COLLECTING_DATA"
        
        # Create assessment entry
        assessment_entry = {
            "date": now.strftime("%Y-%m-%d %H:%M:%S"),
            "confidence_score": round(total_confidence, 1),
            "status": status,
            "component_scores": {k: round(v, 1) for k, v in scores.items()},
            "bot_snapshot": bot_data,
            "closed_trades": len(monitor_data.get("closed_trades", [])),
            "days_of_data": len(analytics_history)
        }
        
        self.assessment["assessments"].append(assessment_entry)
        self.assessment["current_confidence"] = round(total_confidence, 1)
        self.assessment["status"] = status
        
        self.save_assessment()
        
        return assessment_entry, total_confidence, status
    
    def should_notify_user(self):
        """Determine if user should be notified about readiness"""
        now = datetime.now()
        
        # Only notify if within deployment window
        if not (DEPLOY_WINDOW_START <= now <= DEPLOY_WINDOW_END):
            return False, "Outside deployment window (Apr 20 - May 1)"
        
        # Check if already notified
        if self.assessment.get("user_notified"):
            return False, "User already notified"
        
        # Check confidence threshold
        if self.assessment["current_confidence"] >= 75:
            return True, "Confidence >= 75% and within deployment window"
        
        return False, f"Confidence at {self.assessment['current_confidence']}% (need 75%)"
    
    def generate_notification_message(self):
        """Generate the notification message for the user"""
        ready_date = self.assessment.get("ready_date", datetime.now().strftime("%Y-%m-%d"))
        confidence = self.assessment["current_confidence"]
        
        # Get latest assessment details
        latest = self.assessment["assessments"][-1] if self.assessment["assessments"] else None
        
        message = f"""🎯 <b>LIVE TRADING READY — CONFIDENCE CONFIRMED</b>

📅 <b>Recommended Date:</b> {ready_date}
📊 <b>Confidence Score:</b> {confidence}%
💰 <b>Recommended Capital:</b> £500

<b>Readiness Breakdown:</b>
"""
        if latest:
            for component, score in latest["component_scores"].items():
                emoji = "🟢" if score >= WEIGHTS[component] * 0.8 else "🟡" if score >= WEIGHTS[component] * 0.5 else "🔴"
                message += f"  {emoji} {component.replace('_', ' ').title()}: {score:.1f}/{WEIGHTS[component]}\n"
        
        message += f"""
<b>Current Bot Status:</b>
• Days of Data: {latest['days_of_data'] if latest else 'N/A'}
• Closed Trades: {latest['closed_trades'] if latest else 'N/A'}
• Portfolio Value: £{latest['bot_snapshot']['total_value'] if latest and latest['bot_snapshot'] else 'N/A'}

<b>🚀 RECOMMENDATION:</b>
You are cleared to deploy £500 in LIVE trading mode.

<b>Next Steps:</b>
1. Review the full analysis: https://github.com/Everaldtah/multi-pair-crypto-trading-bot-daily-analysis
2. Switch simple_multi_bot.py from DRY_RUN=True to DRY_RUN=False
3. Ensure your KuCoin balance has £500 USDT available
4. Start the bot and monitor first few trades closely

<b>Risk Reminder:</b>
Even with high confidence, crypto trading carries risk. Never invest more than you can afford to lose.

<i>This recommendation is based on {latest['days_of_data'] if latest else 0} days of dry-run data and {latest['closed_trades'] if latest else 0} completed trades.</i>
"""
        return message
    
    def run_assessment(self):
        """Main assessment run"""
        print("=" * 60)
        print("🎯 MULTI-PAIR BOT READINESS ASSESSMENT")
        print("=" * 60)
        print(f"Deployment Window: {DEPLOY_WINDOW_START.strftime('%Y-%m-%d')} to {DEPLOY_WINDOW_END.strftime('%Y-%m-%d')}")
        print(f"Current Date: {datetime.now().strftime('%Y-%m-%d')}")
        print()
        
        assessment, confidence, status = self.generate_readiness_report()
        
        print(f"Status: {status}")
        print(f"Confidence Score: {confidence:.1f}%")
        print()
        print("Component Scores:")
        for component, score in assessment["component_scores"].items():
            print(f"  • {component.replace('_', ' ').title()}: {score:.1f}/{WEIGHTS[component]}")
        print()
        
        should_notify, reason = self.should_notify_user()
        print(f"Should Notify User: {should_notify}")
        print(f"Reason: {reason}")
        
        if should_notify:
            message = self.generate_notification_message()
            print("\n" + "=" * 60)
            print("🚨 NOTIFICATION READY TO SEND")
            print("=" * 60)
            print(message)
            
            # Mark as notified
            self.assessment["user_notified"] = True
            self.assessment["notification_sent_at"] = datetime.now().isoformat()
            self.save_assessment()
            
            return True, message
        
        return False, None

def main():
    assessor = ReadinessAssessor()
    should_notify, message = assessor.run_assessment()
    
    if should_notify and message:
        # Send notification
        import urllib.request
        import urllib.parse
        
        token = os.getenv("TELEGRAM_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN", "")
        if not token:
            # Try to read from env files
            for env_file in ["/root/.env", os.path.expanduser("~/.hermes/.env")]:
                if Path(env_file).exists():
                    with open(env_file) as f:
                        for line in f:
                            # SECURITY FIX: Removed hardcoded credential
                            # if line.startswith("TELEGRAM_TOKEN="):
                            # TODO: Use environment variable instead
                                token = line.strip().split("=", 1)[1].strip('"\'')
                                break
                    if token:
                        break
        
        if token:
            chat_id = "5836707779"
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = urllib.parse.urlencode({
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML"
            }).encode()
            
            try:
                req = urllib.request.Request(url, data=data, method="POST")
                req.add_header("Content-Type", "application/x-www-form-urlencoded")
                with urllib.request.urlopen(req, timeout=10) as resp:
                    print(f"\n✅ Telegram notification sent: {resp.status}")
            except Exception as e:
                print(f"\n⚠️ Failed to send Telegram notification: {e}")
        else:
            print("\n⚠️ No Telegram token found, notification not sent")
    
    print("\n✅ Assessment complete")

if __name__ == "__main__":
    main()
