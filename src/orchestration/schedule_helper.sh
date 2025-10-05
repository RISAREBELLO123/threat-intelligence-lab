#!/bin/bash
# Helper script for cron scheduling
# Add this to crontab for daily runs at 2 AM:
# 0 2 * * * /path/to/threat-aggregation-lab/src/orchestration/schedule_helper.sh

cd "$(dirname "$0")/../.."
source .venv/bin/activate
python -m src.orchestration.daily_run
