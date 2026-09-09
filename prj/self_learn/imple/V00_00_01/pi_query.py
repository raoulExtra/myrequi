#!/usr/bin/env python3
"""
Run a single prompt with Pi using subprocess to call the pi CLI.

This is a robust alternative to the async pi_coding_agent module approach,
using the CLI which is always available and properly configured.

Usage:
    python pi_query.py "What do you remember about this project?"
    python pi_query.py "Add error handling to the main function"
    python pi_query.py "list files in plans/" --read-only
    python pi_query.py --status
    python pi_query.py --queue "prompt1" "prompt2" "prompt3"
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def resolve_project_root():
    """Find the project root directory."""
    # Walk up from script location to find project root
    script_dir = Path(__file__).resolve().parent
    for parent in [script_dir] + list(script_dir.parents):
        if (parent / "plans").exists() and (parent / "continuity.db").exists():
            return parent
    return script_dir


def run_pi_query(
    query: str,
    cwd: str = None,
    model: str = None,
    read_only: bool = False,
    timeout: int = 300,
    capture_output: bool = True,
) -> tuple[int, str]:
    """
    Run a Pi query using the CLI.
    
    Args:
        query: The query/prompt to send to Pi
        cwd: Working directory (defaults to project root)
        model: Optional model override
        read_only: If True, restrict to read-only tools
        timeout: Maximum execution time in seconds
        capture_output: If True, capture stdout; if False, print live
    
    Returns:
        Tuple of (return_code, output)
    """
    if cwd is None:
        cwd = str(resolve_project_root())
    
    cmd = ["pi", "-p"]
    
    if read_only:
        cmd.extend(["--exclude-tools", "bash,edit,write,powershell"])
    
    if model:
        cmd.extend(["--model", model])
    
    cmd.append(query)
    
    try:
        if capture_output:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return result.returncode, result.stdout + result.stderr
        else:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                text=True,
                timeout=timeout,
            )
            return result.returncode, ""
            
    except subprocess.TimeoutExpired:
        return 1, f"Error: Query timed out after {timeout} seconds"
    except FileNotFoundError:
        return 1, "Error: 'pi' command not found. Is Pi installed?"
    except Exception as e:
        return 1, f"Error running query: {e}"


def run_status_query() -> dict:
    """Query self for current status using self_query.py."""
    import sqlite3
    from pathlib import Path
    
    # Import self_query from same directory
    script_dir = Path(__file__).parent
    sys.path.insert(0, str(script_dir))
    
    try:
        from self_query import run_self_query
        return run_self_query("status")
    except ImportError:
        # Fallback: direct database query
        db_path = script_dir.parent.parent.parent.parent.parent / "continuity.db"
        if db_path.exists():
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            
            # Get primary goal
            goal_row = conn.execute(
                "SELECT value FROM metacognitive_state WHERE state_key='primary_goal'"
            ).fetchone()
            primary_goal = goal_row["value"] if goal_row else "Not set"
            
            # Get active plans
            plans = conn.execute(
                "SELECT plan_key, title, status FROM work_plans WHERE status='active' LIMIT 5"
            ).fetchall()
            active_plans = [dict(p) for p in plans]
            
            # Get open questions
            questions = conn.execute(
                "SELECT question FROM open_questions WHERE status IN ('open', 'deferred') LIMIT 5"
            ).fetchall()
            open_questions = [q["question"] for q in questions]
            
            conn.close()
            
            return {
                "type": "status",
                "primary_goal": [{"state_key": "primary_goal", "value": primary_goal}],
                "active_plans": active_plans,
                "open_questions": [{"question": q} for q in open_questions],
            }
        
        return {"type": "status", "error": "Could not find continuity.db"}


def queue_prompts(prompts: list, output_dir: Path = None):
    """
    Queue prompts for batch processing using pi_queue.py.
    
    Args:
        prompts: List of prompts to queue
        output_dir: Optional output directory for results
    """
    if output_dir is None:
        output_dir = Path.home() / ".pi" / "pending_queries"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    queue_file = output_dir / "query_queue.json"
    
    # Load existing queue
    if queue_file.exists():
        with open(queue_file) as f:
            data = json.load(f)
    else:
        data = {"queries": [], "completed": []}
    
    # Add new prompts
    for prompt in prompts:
        data["queries"].append({
            "prompt": prompt,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
        })
    
    # Save queue
    with open(queue_file, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Queued {len(prompts)} prompt(s)")
    return queue_file


def process_queue(queue_file: Path, max_items: int = None):
    """Process queued prompts."""
    with open(queue_file) as f:
        data = json.load(f)
    
    pending = data.get("queries", [])
    if max_items:
        pending = pending[:max_items]
    
    results = []
    for i, query in enumerate(pending):
        print(f"\n[{i+1}/{len(pending)}] Processing: {query['prompt'][:50]}...")
        
        retcode, output = run_pi_query(query["prompt"])
        
        query["status"] = "completed" if retcode == 0 else "failed"
        query["output"] = output[:2000] if output else ""  # Truncate long outputs
        query["completed_at"] = datetime.now().isoformat()
        
        results.append(query)
        print(f"  Status: {'✅' if retcode == 0 else '❌'}")
    
    data["completed"].extend(results)
    with open(queue_file, "w") as f:
        json.dump(data, f, indent=2)
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Run Pi queries from command line",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python pi_query.py "what do you know"
    python pi_query.py "list plans/" --read-only
    python pi_query.py --status
    python pi_query.py --queue "prompt1" "prompt2"
    python pi_query.py --process-queue 5
        """
    )
    
    parser.add_argument("query", nargs="?", help="Query to run")
    parser.add_argument("--read-only", action="store_true", 
                       help="Restrict to read-only tools only")
    parser.add_argument("--model", "-m", help="Override model (e.g., gpt-4o-mini)")
    parser.add_argument("--timeout", "-t", type=int, default=300,
                       help="Timeout in seconds (default: 300)")
    parser.add_argument("--status", action="store_true",
                       help="Query self-status from local database")
    parser.add_argument("--queue", nargs="*", dest="queue",
                       help="Queue prompts for batch processing")
    parser.add_argument("--process-queue", type=int, nargs="?", const=10,
                       metavar="MAX", help="Process queued prompts (limit to first N)")
    parser.add_argument("--json", action="store_true",
                       help="Output in JSON format")
    
    args = parser.parse_args()
    
    if args.status:
        status = run_status_query()
        if args.json:
            print(json.dumps(status, indent=2, default=str))
        else:
            if status.get("type") == "status":
                goal = status.get("primary_goal", [{}])[0].get("value", "Unknown")
                print(f"🎯 Primary Goal: {goal}")
                plans = status.get("active_plans", [])
                if plans:
                    print(f"📋 Active Plans: {len(plans)}")
                    for p in plans[:3]:
                        print(f"   - {p.get('title', p.get('plan_key', 'Unknown'))}")
                q = status.get("open_questions", [])
                if q:
                    print(f"❓ Open Questions: {len(q)}")
            else:
                print(json.dumps(status, indent=2))
        return 0
    
    if args.queue:
        queue_file = queue_prompts(args.queue)
        print(f"Queue file: {queue_file}")
        print("Run with: python pi_query.py --process-queue")
        return 0
    
    if args.process_queue:
        queue_file = Path.home() / ".pi" / "pending_queries" / "query_queue.json"
        if not queue_file.exists():
            print("No queue file found. Use --queue to add prompts.")
            return 1
        results = process_queue(queue_file, args.process_queue)
        print(f"\nProcessed {len(results)} prompts")
        return 0
    
    if not args.query:
        parser.print_help()
        return 1
    
    retcode, output = run_pi_query(args.query, read_only=args.read_only)
    print(output)
    return retcode


if __name__ == "__main__":
    sys.exit(main())