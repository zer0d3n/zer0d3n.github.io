#!/usr/bin/env python3
"""Opens an issue with the LinkedIn text for every published post that doesn't have one yet.

The pipeline runs it right after deploying the site, so the link in the issue already works.
- Each post gets a single issue, even if you edit it and push again: it is recognised by its
  file name, hidden in the issue body.
- Scheduled posts (future date) wait for their day, just like Jekyll does.
- `linkedin: false` in a post's front matter leaves it out.

Local run, without touching GitHub:  python3 tools/linkedin.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from datetime import date, datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

ROOT = Path(__file__).resolve().parents[1]
LABEL = "linkedin"
FILENAME = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+)\.(md|markdown)$")
MARKER = "<!-- post: {} -->"


def front_matter(path: Path) -> dict:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", path.read_text(encoding="utf-8"), re.S)
    return (yaml.safe_load(m.group(1)) or {}) if m else {}


def publish_date(value, fallback: str, zone: ZoneInfo) -> datetime:
    """The publish date as Jekyll sees it: no time means midnight, no zone means the site's zone."""
    if isinstance(value, str):  # Chirpy's «2026-09-27 10:00:00 +0200» arrives as a string
        for fmt in ("%Y-%m-%d %H:%M:%S %z", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                value = datetime.strptime(value.strip(), fmt)
                break
            except ValueError:
                continue
        else:
            raise SystemExit(f"Can't parse the date of a post: {value!r}")
    if value is None:
        value = date.fromisoformat(fallback)
    if not isinstance(value, datetime):
        value = datetime.combine(value, time())
    return value if value.tzinfo else value.replace(tzinfo=zone)


def hashtags(tags) -> str:
    clean = [re.sub(r"[^0-9A-Za-z]", "", str(t)) for t in (tags or [])]
    return " ".join(f"#{t}" for t in clean[:5] if t)


def published_posts(config: dict, now: datetime):
    zone = ZoneInfo(config.get("timezone") or "UTC")
    base = (config.get("url") or "").rstrip("/") + (config.get("baseurl") or "")
    for p in sorted((ROOT / "_posts").glob("*.md")):
        m = FILENAME.match(p.name)
        if not m:
            continue
        fm = front_matter(p)
        if fm.get("published") is False or fm.get("linkedin") is False:
            continue
        if publish_date(fm.get("date"), m.group(1), zone) > now:
            continue  # scheduled: not on the site yet
        slug = fm.get("slug") or m.group(2)
        url = base + (fm.get("permalink") or f"/posts/{slug}/")
        yield p, fm, url


def issue_body(p: Path, fm: dict, url: str) -> str:
    title = fm.get("title") or p.stem
    text = (fm.get("linkedin") or "").strip()
    generic = not text
    if generic:
        text = f"{title}\n\n{(fm.get('description') or '').strip()}".strip()
    tags = hashtags(fm.get("tags"))
    if tags and "#" not in text:
        text += f"\n\n{tags}"
    lines = [
        f"**{title}** is live: {url}",
        "",
        "Paste this text into a new LinkedIn post (the copy button is at the top right of the block):",
        "",
        "````text",
        f"{text}\n\n{url}",
        "````",
        "",
    ]
    if generic:
        lines += ["> The post had no `linkedin:` field in its front matter, so this is a generic text. "
                  "One written for LinkedIn (what you did, what you learned, a question at the end) works much better.", ""]
    lines += ["Close this issue once it's posted.", "", MARKER.format(p.relative_to(ROOT).as_posix())]
    return "\n".join(lines)


def gh(*args: str, stdin: str | None = None) -> str:
    return subprocess.run(["gh", *args], input=stdin, text=True, capture_output=True, check=True).stdout


def already_notified() -> set:
    issues = json.loads(gh("issue", "list", "--label", LABEL, "--state", "all", "--limit", "1000", "--json", "body"))
    return {m.group(1) for i in issues for m in [re.search(r"<!-- post: (.+?) -->", i.get("body") or "")] if m}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--dry-run", action="store_true", help="print the issues without creating anything on GitHub")
    args = p.parse_args()

    config = yaml.safe_load((ROOT / "_config.yml").read_text(encoding="utf-8"))
    now = datetime.now(ZoneInfo(config.get("timezone") or "UTC"))
    done = set() if args.dry_run else already_notified()
    if not args.dry_run:
        gh("label", "create", LABEL, "--color", "0A66C2", "--description", "Post ready to share on LinkedIn", "--force")

    created = 0
    for post, fm, url in published_posts(config, now):
        path = post.relative_to(ROOT).as_posix()
        if path in done:
            continue
        title = f"LinkedIn: {fm.get('title') or post.stem}"
        body = issue_body(post, fm, url)
        created += 1
        if args.dry_run:
            print(f"--- {title}\n{body}\n")
            continue
        cmd = ["issue", "create", "--title", title, "--label", LABEL, "--body-file", "-"]
        if os.environ.get("ASSIGNEE"):
            cmd += ["--assignee", os.environ["ASSIGNEE"]]
        print(gh(*cmd, stdin=body).strip())

    summary = f"New LinkedIn issues: {created}"
    print(summary)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(summary + "\n")


if __name__ == "__main__":
    main()
