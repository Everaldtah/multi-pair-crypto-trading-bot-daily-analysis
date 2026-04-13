#!/bin/bash
# Daily Multi-Pair Bot Analysis Cron Job
# Generates and pushes trading reports to GitHub

set -e

# Export GitHub token for git operations
export GITHUB_TOKEN="${GITHUB_TOKEN:-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}"

# Change to repo directory
cd /root/multi-pair-crypto-trading-bot-daily-analysis

# Configure git credentials for push
git remote set-url origin "https://Everaldtah:${GITHUB_TOKEN}@github.com/Everaldtah/multi-pair-crypto-trading-bot-daily-analysis.git" 2>/dev/null || true

# Run the analysis script
/usr/bin/python3 scripts/generate_daily_report.py >> /var/log/multi-pair-analysis.log 2>&1

# Clean up credentials from remote URL after push
git remote set-url origin "https://github.com/Everaldtah/multi-pair-crypto-trading-bot-daily-analysis.git" 2>/dev/null || true

echo "Daily analysis completed at $(date)"
