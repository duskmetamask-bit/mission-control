#!/usr/bin/env python3
"""
Mission Control — AI Income Opportunities Daily Scan
Run daily via cron. Searches for new AI capabilities that can be leveraged for monetization.
"""

import json
import os
from datetime import datetime, timedelta
import re

DATA_FILE = '/home/dusk/mission-control/data.json'
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
GITHUB_REPO = 'duskwun/mission-control'
BRANCH = 'main'

def load_current_data():
    """Load existing opportunities from data.json"""
    if not os.path.exists(DATA_FILE):
        return {'opportunities': [], 'lastUpdated': None, 'nextScan': None}
    with open(DATA_FILE) as f:
        return json.load(f)

def save_data(data):
    """Save updated opportunities to data.json"""
    data['lastUpdated'] = datetime.utcnow().isoformat() + 'Z'
    data['nextScan'] = (datetime.utcnow() + timedelta(days=1)).isoformat() + 'Z'
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"[Mission Control] Saved {len(data['opportunities'])} opportunities to {DATA_FILE}")

def is_recent(entry_date_str, days=7):
    """Check if entry was found within last N days"""
    try:
        entry_date = datetime.strptime(entry_date_str, '%Y-%m-%d')
        return (datetime.now() - entry_date).days <= days
    except:
        return False

def generate_opportunity_id(existing_ids):
    """Generate a new unique ID"""
    if not existing_ids:
        return '1'
    max_id = max(int(re.sub(r'\D', '', eid)) for eid in existing_ids)
    return str(max_id + 1)

def build_entry(category, name, description, leverage, source, source_name, relevance, tags):
    """Build a standardized opportunity entry"""
    existing_ids = [o['id'] for o in load_current_data().get('opportunities', [])]
    return {
        'id': generate_opportunity_id(existing_ids),
        'category': category,
        'name': name,
        'description': description,
        'leverage': leverage,
        'source': source,
        'sourceName': source_name,
        'dateFound': datetime.now().strftime('%Y-%m-%d'),
        'relevance': relevance,
        'tags': tags
    }

def main():
    print("[Mission Control] Starting daily AI opportunities scan...")

    data = load_current_data()
    existing = data.get('opportunities', [])

    new_entries = []

    # =====================================================================
    # RESEARCH SOURCES — Add new capabilities here as they're discovered
    # =====================================================================

    # Example new entry format (uncomment to add):
    #
    # new_entries.append(build_entry(
    #     category='api',           # api | framework | automation | integration | monetization
    #     name='Capability Name',
    #     description='What it does and why it matters',
    #     leverage='How to monetize this - be specific about the business model',
    #     source='https://source.url',
    #     source_name='Source Name',
    #     relevance=4,               # 1-5 scale
    #     tags=['saas', 'b2b', 'automation']
    # ))

    # =====================================================================
    # DEDUP — Remove entries older than 30 days (stale)
    # =====================================================================

    cutoff = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    updated_opportunities = [o for o in existing if o.get('dateFound', '') >= cutoff]

    # =====================================================================
    # MERGE — Add new entries
    # =====================================================================

    updated_opportunities.extend(new_entries)

    # Sort by relevance descending
    updated_opportunities.sort(key=lambda x: x.get('relevance', 0), reverse=True)

    data['opportunities'] = updated_opportunities
    save_data(data)

    print(f"[Mission Control] Scan complete. {len(new_entries)} new entries added. "
          f"Total: {len(updated_opportunities)} opportunities.")

if __name__ == '__main__':
    main()
