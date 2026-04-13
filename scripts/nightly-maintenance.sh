#!/bin/bash
# Claude Code Nightly Maintenance
# Runs at 11PM AWST daily

DATE=$(date '+%Y-%m-%d %H:%M AWST')
LOG="/home/dusk/mission-control/logs/maintenance.log"

echo "[$DATE] Running nightly maintenance..." >> $LOG

# Git sync agent workspaces
cd ~/.openclaw
for ws in workspace-*/; do
    if [ -d "$ws/.git" ]; then
        echo "  Syncing $ws..." >> $LOG
        cd "$ws"
        git add . >> $LOG 2>&1
        git commit -m "auto-sync $(date '+%Y-%m-%d %H:%M')" >> $LOG 2>&1 || true
        cd ~
    fi
done

# Clean old logs (keep last 7 days)
find /home/dusk/mission-control/logs -name "*.log" -mtime +7 -delete 2>/dev/null
echo "  Old logs cleaned" >> $LOG

# Update mission control one final time
/usr/bin/python3 /home/dusk/mission-control/scripts/update-dashboard.py >> $LOG 2>&1
echo "  Mission control updated" >> $LOG

# Trim walnut logs (keep last 30 entries)
for wal in ~/.openclaw/workspace-*/walnuts/*/logs/*.md; do
    if [ -f "$wal" ] && [ "$(wc -l < $wal)" -gt 300 ]; then
        tail -100 "$wal" > /tmp/wal_trim.tmp && mv /tmp/wal_trim.tmp "$wal"
        echo "  Trimmed $wal" >> $LOG
    fi
done 2>/dev/null || true

echo "[$DATE] Nightly maintenance complete" >> $LOG
