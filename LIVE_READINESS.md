# 🎯 Live Trading Readiness Tracker

> **Target Deployment:** £1000 real capital into Multi-Pair Bot v5  
> **Assessment Window:** April 20, 2026 → May 1, 2026  
> **Minimum Confidence Required:** 75%

---

## 📊 Current Readiness Status

**Last Updated:** Auto-generated daily at 09:00 UTC  
**Current Confidence:** See latest assessment in `analytics/readiness_assessment.json`  
**Target Investment:** £1000 (changed from £500)

### Confidence Score Breakdown

| Component | Weight | Description |
|-----------|--------|-------------|
| Data Sufficiency | 15 pts | Minimum 7 days of dry-run data |
| Trade Sample | 15 pts | Minimum 5 completed trades |
| Win Rate | 20 pts | At least 40% profitable trades |
| Profit Consistency | 20 pts | Positive/improving P&L trend |
| Drawdown Control | 15 pts | Less than 10% from peak balance |
| Market Conditions | 15 pts | Bot finding healthy opportunities |

**Total Possible:** 100 points  
**Ready Threshold:** 75+ points

---

## 🚦 Status Levels

| Status | Confidence | Meaning |
|--------|------------|---------|
| 🟢 **READY_TO_DEPLOY** | 80%+ | Cleared to go live within Apr 20 - May 1 |
| 🟡 **APPROACHING_READY** | 60-79% | Getting close, monitor closely |
| 🟠 **BUILDING_CONFIDENCE** | 40-59% | Need more data/trades |
| 🔴 **COLLECTING_DATA** | <40% | Too early, keep running dry-run |

---

## 📅 Deployment Window

```
April 2026
Su Mo Tu We Th Fr Sa
 1  2  3  4
 5  6  7  8  9 10 11
12 13 14 15 16 17 18
19 [20][21][22][23][24][25]
[26][27][28][29][30] [May 1]
```

**Assessment period:** Bold dates in brackets  
If confidence hits 75%+ during this window, you will receive a Telegram notification with my recommendation.

**Decision Date:** May 1, 2026 (latest) - If readiness isn't achieved by then, reassess strategy.

---

## 🧠 How the Decision Is Made

The readiness assessor runs **daily at 9 AM UTC** and evaluates:

1. **Historical performance** from `analytics/performance_history.json`
2. **Closed trade statistics** from the bot monitor
3. **Current market conditions** from live bot logs
4. **Risk metrics** (drawdown, volatility, position management)
5. **Obsidian vault sync** - All assessments are saved to Obsidian for building historical dataset

It will **only notify you** if:
- Confidence score is **≥ 75%**
- We are within **April 20 - May 1**
- You haven't already been notified

---

## 🔄 Obsidian Vault Integration

**Critical:** Each daily assessment is automatically saved to the Obsidian vault:

- **Location:** `HermesVault/Trading Bot/Daily Readiness/YYYY-MM-DD-Readiness-Assessment.md`
- **Sync:** Every 5 minutes via systemd → GitHub → Web app
- **Purpose:** Build complete timeline from April 14 to May 1 for historical analysis

This ensures we have a full dataset to review before making the £1000 investment decision.

---

## 📝 What Happens When Ready

When I notify you, the message will include:
- ✅ Exact recommended deployment date
- ✅ Confidence breakdown with component scores
- ✅ Current bot snapshot (trades, P&L, days of data)
- ✅ Step-by-step instructions to switch to live mode
- ✅ £1000 position sizing recommendations
- ⚠️ Risk reminder and capital allocation advice

---

## 💰 £1000 Investment Configuration

When deploying £1000:
- **Max Concurrent Positions:** 5 pairs (increased from 3)
- **Position Size:** £200 per pair (20% allocation)
- **Risk Per Trade:** 2% (£20 stop-loss per position)
- **Kelly Criterion:** Apply for optimal sizing
- **Portfolio Stop:** 8% total drawdown (£80 max loss)

---

## 📈 Projected Timeline

| Date | Target | Status |
|------|--------|--------|
| Apr 14 | £1000 config deployed | ✅ In Progress |
| Apr 15-19 | 5+ days dry-run data | 🔄 Collecting |
| Apr 20 | Decision window opens | ⏳ Waiting |
| Apr 20-30 | Daily assessments | ⏳ Pending |
| May 1 | Final decision / Deploy | ⏳ Target |

---

## 🔗 Auto-Updated Files

- `analytics/readiness_assessment.json` — Daily confidence scores and status
- `analytics/confidence_database.json` — Accumulating market regime data
- `insights/strategy_upgrades.md` — Parameter recommendations from historical analysis
- `HermesVault/Trading Bot/Daily Readiness/*.md` — Obsidian timeline for historical review

---

*This system is automated. I will only message you when I have enough evidence to be confident in the £1000 deployment recommendation.*
*All data syncs to Obsidian vault for complete timeline tracking from April 14 → May 1.*
