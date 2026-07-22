#!/bin/bash
# =============================================================================
# SCRIPT NAME: run_bloomberg_keepalive.sh
# =============================================================================
#
# DESCRIPTION:
#   Shell wrapper that launches the Bloomberg robust keepalive service inside
#   the OpusBloomberg conda environment. Designed to be called by launchd
#   so that the keepalive runs forever with automatic restart on crash.
#
#   The script waits 5 seconds before starting (to let the system settle after
#   login) and then execs into the Python process so launchd can manage it
#   directly (correct PID tracking).
#
# INPUT FILES:
#   - /Users/arjundivecha/Dropbox/AAA Backup/A Working/BloombergGPT/bloomberg_keepalive.py
#     (the keepalive Python program)
#
# OUTPUT FILES:
#   (none directly — stdout/stderr are captured by launchd)
#
# USAGE:
#   Direct:  ./run_bloomberg_keepalive.sh
#   Via launchd: launchctl load ~/Library/LaunchAgents/com.arjundivecha.bloomberg-keepalive.plist
#
# VERSION: 1.0
# LAST UPDATED: 2026-06-10
# AUTHOR: Arjun Divecha
# =============================================================================

set -euo pipefail

CONDA_ENV="/Users/arjundivecha/Dropbox/AAA Backup/A Working/OpusBloomberg/.venv"
SCRIPT="/Users/arjundivecha/Dropbox/AAA Backup/A Working/BloombergGPT/bloomberg_keepalive.py"

# Give the system a moment to settle after login/boot before hitting Bloomberg
sleep 5

# Ensure output directory exists
mkdir -p "/Users/arjundivecha/Dropbox/AAA Backup/A Working/BloombergGPT/outputs"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting Bloomberg Robust Keepalive..."

# exec into the Python process so launchd tracks the correct PID
exec conda run -p "$CONDA_ENV" python "$SCRIPT"
