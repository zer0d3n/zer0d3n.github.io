#!/usr/bin/env python3
"""Keeps the weekly rhythm: opens a «Weekly post pending» issue when the last post is too old,
and closes it as soon as a new post is published.

The pipeline runs it every morning and after every deploy. Only one reminder is open at a time.
REMINDER_DAYS sets the gap that triggers it (default 8 days; 0 turns reminders off).

Local run, without touching GitHub:  python3 tools/weekly_reminder.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime
from zoneinfo import ZoneInfo

import yaml

from linkedin import ROOT, published_posts

LABEL = "weekly-post"
TITLE = "Weekly post pending"


def gh(*args: str) -> str:
    return subprocess.run(["gh", *args], text=True, capture_output=True, check=True).stdout


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--dry-run", action="store_true", help="print what would happen without touching GitHub")
    args = p.parse_args()

    days_limit = int(os.environ.get("REMINDER_DAYS", "8"))
    if days_limit <= 0:
        print("Weekly reminders are off (REMINDER_DAYS=0)")
        return
    config = yaml.safe_load((ROOT / "_config.yml").read_text(encoding="utf-8"))
    now = datetime.now(ZoneInfo(config.get("timezone") or "UTC"))
    latest = max(((when, fm, url) for _, fm, url, when in published_posts(config, now, with_date=True)),
                 key=lambda x: x[0], default=None)
    overdue = latest is None or (now - latest[0]).days >= days_limit

    if args.dry_run:
        last = f"{latest[1].get('title')} ({(now - latest[0]).days} days ago)" if latest else "none yet"
        print(f"Last post: {last}. {'Reminder needed.' if overdue else 'Up to date.'}")
        return

    gh("label", "create", LABEL, "--color", "FBCA04", "--description", "No blog post for a week", "--force")
    open_issues = json.loads(gh("issue", "list", "--label", LABEL, "--state", "open", "--json", "number"))
    if overdue and not open_issues:
        last = (f"The last post, [{latest[1].get('title')}]({latest[2]}), went out {(now - latest[0]).days} days ago."
                if latest else "There are no posts yet.")
        body = "\n".join([
            last,
            "",
            "In the study plan repo, ask Claude Code for `/entrada-blog`, or run "
            "`python3 tools/borrador_blog.py` and then `python3 tools/publicar_blog.py <draft>`.",
            "",
            "This issue closes itself when the next post is published.",
        ])
        cmd = ["issue", "create", "--title", TITLE, "--label", LABEL, "--body", body]
        if os.environ.get("ASSIGNEE"):
            cmd += ["--assignee", os.environ["ASSIGNEE"]]
        print(gh(*cmd).strip())
    elif not overdue:
        for issue in open_issues:
            gh("issue", "close", str(issue["number"]), "--comment",
               f"Published: [{latest[1].get('title')}]({latest[2]}). See you next week.")
            print(f"Closed reminder #{issue['number']}")
    else:
        print("Reminder already open")


if __name__ == "__main__":
    main()
