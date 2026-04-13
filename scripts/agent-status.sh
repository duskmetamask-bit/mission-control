#!/bin/bash
# Usage: agent-status.sh karma "Running email sequence" active

AGENT=$1
TASK="$2"
STATUS=${3:-"active"}
DATE=$(date '+%I:%M%p' | tr '[:upper:]' '[:lower]')

# Read existing agents.json or create new
JSON_FILE="/home/dusk/mission-control/data/agents.json"
if [ -f "$JSON_FILE" ]; then
    # Simple update - just update this agent's entry
    # For production, this should use jq but keeping it simple
    echo "{\"agent\":\"$AGENT\",\"task\":\"$TASK\",\"status\":\"$STATUS\",\"updated\":\"$DATE\"}" > "/home/dusk/mission-control/data/agent-$AGENT.json"
else
    echo "{\"agent\":\"$AGENT\",\"task\":\"$TASK\",\"status\":\"$STATUS\",\"updated\":\"$DATE\"}" > "/home/dusk/mission-control/data/agent-$AGENT.json"
fi

echo "Updated $AGENT status: $STATUS - $TASK"
