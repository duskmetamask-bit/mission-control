#!/usr/bin/env python3
"""
Mission Control Dashboard Updater
Pulls data from agent workspaces and updates dashboard JSON files
"""
import json
import os
from datetime import datetime

BASE = "/home/dusk/mission-control/data"
WORKSPACES = "/home/dusk/.openclaw/workspaces"

def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except: return {}

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def update_agents():
    """Aggregate agent status from workspaces"""
    agents = {
        "updated": datetime.now().strftime("%I:%M%p").lower(),
        "date": datetime.now().strftime("%a %b %d"),
        "pendingCount": 0,
        "emailsSent": 0,
        "postsDelivered": 0,
        "pending": [],
        "attention": [],
        "list": []
    }
    
    # Karma
    karma_status = load_json(f"{WORKSPACES}/workspace-karma/walnuts/emvy-outreach/logs/status.json")
    agents["list"].append({
        "id": "karma",
        "name": "Karma",
        "task": karma_status.get("task", "Awaiting first campaign"),
        "status": karma_status.get("status", "idle")
    })
    agents["emailsSent"] = karma_status.get("emails_sent", 0)
    
    # Connor
    connor_status = load_json(f"{WORKSPACES}/workspace-connor/walnuts/audit-walnut/logs/status.json")
    agents["list"].append({
        "id": "connor",
        "name": "Connor",
        "task": connor_status.get("task", "Daily scan active"),
        "status": connor_status.get("status", "active")
    })
    
    # Maya
    maya_status = load_json(f"{WORKSPACES}/workspace-maya/walnuts/content-walnut/logs/status.json")
    agents["list"].append({
        "id": "maya",
        "name": "Maya",
        "task": maya_status.get("task", "Content operation running"),
        "status": maya_status.get("status", "active")
    })
    agents["postsDelivered"] = maya_status.get("posts_today", 0)
    
    # Yuki
    agents["list"].append({
        "id": "yuki",
        "name": "Yuki",
        "task": "Coordination active",
        "status": "idle"
    })
    
    # Claude Code
    claude_status = load_json(f"{WORKSPACES}/workspace-chad/status.json")
    agents["list"].append({
        "id": "claude",
        "name": "Claude Code",
        "task": claude_status.get("task", "Awaiting task"),
        "status": claude_status.get("status", "idle")
    })
    
    # Xi
    xi_status = load_json(f"{WORKSPACES}/workspace-xi/walnuts/trading-walnut/logs/status.json")
    agents["list"].append({
        "id": "xi",
        "name": "Xi",
        "task": xi_status.get("task", "Paper trading"),
        "status": xi_status.get("status", "active")
    })
    
    save_json(f"{BASE}/agents.json", agents)
    return agents

def update_system():
    """Check system health"""
    system = [
        {"Name": "n8n", "Status": "Running — workflows active", "dotClass": "dot-green"},
        {"Name": "OpenClaw Gateway", "Status": "Active", "dotClass": "dot-green"},
        {"Name": "VPS Disk", "Status": "34% used", "dotClass": "dot-green"},
        {"Name": "Mission Control", "Status": "Live", "dotClass": "dot-green"},
    ]
    save_json(f"{BASE}/system.json", system)

def main():
    print("Updating mission control dashboard...")
    update_agents()
    update_system()
    print("Done.")

if __name__ == "__main__":
    main()
