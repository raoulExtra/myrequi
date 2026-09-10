#!/usr/bin/env python3
"""
Test script to send queries to the current session's LLM via the helper_for_db.py helper.

The helper_for_db.py provides a CLI interface that can be used
to send queries to the underlying system. This script demonstrates how to invoke
that functionality programmatically.
"""

from helper_for_db import (
    connect,
    cmd_research_create,
    cmd_self_check,
    cmd_list,
    cmd_show,
)
import sys
import json


def send_query(query: str) -> dict:
    """Send a query to the system and return the result."""
    # Connect to the continuity.db
    con = connect(sys.argv[1] if len(sys.argv) > 1 else "/home/peter/xmyrequi/myrequi/continuity.db")
    
    # Create a research job with the query
    # This effectively sends the query to the system's LLM
    job = cmd_research_create(query=query)
    
    # Close the connection
    con.close()
    
    return job


def main():
    if len(sys.argv) < 2:
        print("Usage: test_query.py <query>", file=sys.stderr)
        print("Example queries:", file=sys.stderr)
        print("  - 'What is the current status of the continuity database locking issue?'", file=sys.stderr)
        print("  - 'Explain the difference between continuous and discrete thinking models.'", file=sys.stderr)
        print("  - 'Summarize the recent research on memory architectures.'", file=sys.stderr)
        sys.exit(1)
    
    query = sys.argv[1]
    result = send_query(query)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
