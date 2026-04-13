#!/bin/bash
# Claude Code Morning Health Check
# Runs at 8AM AWST daily

DATE=$(date '+%Y-%m-%d %H:%M AWST')
LOG="/home/dusk/mission-control/logs/health.log"

echo "[$DATE] Running health check..." >> $LOG

# Check n8n
if pgrep -f "n8n" > /dev/null; then
    echo "  n8n: RUNNING" >> $LOG
else
    echo "  n8n: DOWN - restarting..." >> $LOG
    cd /home/dusk && nohup n8n start --host 0.0.0.0 --port 5678 > /home/dusk/n8n.log 2>&1 &
    sleep 3
    echo "  n8n: restarted" >> $LOG
fi

# Check OpenClaw
if pgrep -f "openclaw" > /dev/null; then
    echo "  OpenClaw: RUNNING" >> $LOG
else
    echo "  OpenClaw: DOWN - alerting..." >> $LOG
    # Could send Telegram alert here
fi

# Check disk space
DISK=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK" -gt 80 ]; then
    echo "  Disk: WARNING ${DISK}% used" >> $LOG
else
    echo "  Disk: OK ${DISK}% used" >> $LOG
fi

# Check memory
MEM=$(free -h | awk 'NR==2 {print $3 "/" $2}')
echo "  Memory: $MEM" >> $LOG

# Check mission control
if curl -s --max-time 5 http://localhost:8080 > /dev/null; then
    echo "  Mission Control: OK" >> $LOG
else
    echo "  Mission Control: DOWN - restarting..." >> $LOG
    cd /home/dusk/mission-control && nohup python3 -m http.server 8080 > /tmp/dash.log 2>&1 &
fi

# Check agent workspaces git status
cd ~/.openclaw
for ws in workspace-*/; do
    if [ -d "$ws/.git" ]; then
        cd "$ws"
        git status --short 2>/dev/null | head -1
        cd ~
    fi
done >> $LOG 2>&1

echo "  Agent workspaces: checked" >> $LOG
echo "[$DATE] Health check complete" >> $LOG
