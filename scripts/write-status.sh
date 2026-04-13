#!/bin/bash
# Usage: write-status.sh karma "Running email sequence" active
# Writes agent status to mission control data dir

AGENT=$1
TASK="$2"
STATUS=${3:-"active"}
UPDATED=$(date '+%I:%M%p' | tr '[:upper:]' '[:lower]')

STATUS_FILE="/home/dusk/mission-control/data/agent-$AGENT.json"

cat > "$STATUS_FILE" << EOF
{
  "agent": "$AGENT",
  "task": "$TASK",
  "status": "$STATUS",
  "updated": "$UPDATED"
}
EOF

echo "[$(date)] $AGENT status updated: $STATUS - $TASK" >> /home/dusk/mission-control/logs/agent-updates.log
