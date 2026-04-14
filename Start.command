#!/bin/bash
cd "$(dirname "$0")"
echo "🚀 Launching ResQNow Mission Control..."
echo "---------------------------------------"
# Ensure the custom server runs
python3 server.py
