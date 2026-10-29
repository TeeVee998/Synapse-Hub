#!/usr/bin/env bash
# Enterprise Single-Command DoD Verification Wrapper
set -e
python3 "$(dirname "$0")/verify_all.py" "$@"
