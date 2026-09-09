#!/usr/bin/env python3
"""
Helper to update metacognitive_state.json for self_learn project.

Usage:
    python update_metacognitive_state.py "state_key" "new value"
    python update_metacognitive_state.py --file  # Show current file
"""

import json
import sys
from pathlib import Path
from datetime import datetime

METACOGNITIVE_STATE_FILE = Path(__file__).resolve().parent.parent.parent / "metacognitive_state.json"


def load_state():
    """Load the metacognitive state JSON."""
    if not METACOGNITIVE_STATE_FILE.exists():
        return {"migrated_from": "manual_entry", "migration_date": datetime.now().isoformat(),
                "project": "self_learn", "entries": {}, "notes": ""}
    
    with open(METACOGNITIVE_STATE_FILE) as f:
        return json.load(f)


def save_state(data):
    """Save the metacognitive state JSON."""
    with open(METACOGNITIVE_STATE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def update_entry(key, value, category=None, confidence=None, provenance=None):
    """Update or create a metacognitive state entry."""
    data = load_state()
    
    entry = {"value": value, "updated_at": datetime.now().isoformat()}
    if category:
        entry["category"] = category
    if confidence is not None:
        entry["confidence"] = confidence
    if provenance:
        entry["provenance"] = provenance
    
    data["entries"][key] = entry
    data["migration_date"] = datetime.now().isoformat()
    save_state(data)
    print(f"✅ Updated '{key}' at {entry['updated_at']}")


def show_state():
    """Show current state entries."""
    data = load_state()
    print("=== Metacognitive State (JSON) ===")
    for key, entry in data.get("entries", {}).items():
        print(f"\n{key}:")
        print(f"  value: {entry.get('value', '')[:60]}...")
        print(f"  category: {entry.get('category', 'unknown')}")
        if entry.get('confidence'):
            print(f"  confidence: {entry['confidence']}")
        print(f"  updated_at: {entry.get('updated_at')}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Update metacognitive_state.json")
    parser.add_argument("key", nargs="?", help="State key to update")
    parser.add_argument("value", nargs="?", help="State value")
    parser.add_argument("--category", help="Category for the entry")
    parser.add_argument("--confidence", type=float, help="Confidence value (0-1)")
    parser.add_argument("--provenance", help="Provenance source")
    parser.add_argument("--file", action="store_true", help="Show current file")
    
    args = parser.parse_args()
    
    if args.file:
        if METACOGNITIVE_STATE_FILE.exists():
            print(METACOGNITIVE_STATE_FILE)
        else:
            print("File does not exist")
        return
    
    if args.key and args.value:
        update_entry(args.key, args.value, args.category, args.confidence, args.provenance)
    else:
        show_state()


if __name__ == "__main__":
    main()