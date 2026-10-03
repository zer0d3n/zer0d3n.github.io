#!/usr/bin/env python3
"""Checks every post before the site is built, so a half-finished draft never goes live.

Fails (exit 1) when a post:
- has a file name that won't make a clean URL (`YYYY-MM-DD-lowercase-words.md`);
- misses title, date, description, categories or tags, or its date doesn't match the file name;
- still has a draft placeholder from tools/borrador_blog.py in the study plan repo;
- has a LinkedIn text that, with hashtags and link, goes over LinkedIn's 3,000 characters;
- contains something that looks like a secret: an AWS account ID, an access key, an ARN with an
  account, or a CTF flag. 123456789012, the account ID from the AWS docs, is allowed.

Usage:  python3 tools/check_posts.py [post.md ...]     (default: every file in _posts/)
"""
from __future__ import annotations

import os
import re
import sys
from datetime import date, datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
FILENAME = re.compile(r"^(\d{4}-\d{2}-\d{2})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md$")
REQUIRED = ("title", "date", "description", "categories", "tags")
LINKEDIN_LIMIT = 3000
URL_ALLOWANCE = 80  # the pipeline appends the post URL to the LinkedIn text

PLACEHOLDERS = [
    "<!-- BORRADOR",
    "(Two sentences to open",
    "(one sentence: the most useful",
    "(sum it up in one line)",
    "(what you learned, explained",
    "(nothing in the diary",
    "(what comes next)",
    "(End with a question for your network",
]
SECRETS = [
    (re.compile(r"(?<![\d-])(?!123456789012)\d{12}(?![\d-])"), "a 12-digit number (an AWS account ID?)"),
    (re.compile(r"\b(AKIA|ASIA)[A-Z0-9]{16}\b"), "an AWS access key"),
    (re.compile(r"arn:aws[\w-]*:[^\s`:]*:[^\s`:]*:(?!123456789012)\d{12}:"), "an ARN with a real account ID"),
    (re.compile(r"\b(CTF|flag)\{[^}]+\}", re.I), "a CTF flag"),
]


def front_matter(text: str):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        return None, 0
    return yaml.safe_load(m.group(1)) or {}, m.group(0).count("\n")


def as_date(value) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value.strip()[:10])
        except ValueError:
            return None
    return None


def check(path: Path) -> list[tuple[int, str]]:
    problems: list[tuple[int, str]] = []
    m = FILENAME.match(path.name)
    if not m:
        problems.append((1, "file name must be YYYY-MM-DD-lowercase-words-with-hyphens.md (it becomes the URL)"))
    text = path.read_text(encoding="utf-8")
    try:
        fm, _ = front_matter(text)
    except yaml.YAMLError as e:
        return problems + [(1, f"front matter is not valid YAML: {e}")]
    if fm is None:
        return problems + [(1, "missing front matter (the block between --- lines)")]

    for key in REQUIRED:
        if not fm.get(key):
            problems.append((1, f"front matter is missing `{key}`"))
    day = as_date(fm.get("date"))
    if fm.get("date") and not day:
        problems.append((1, f"can't read the date {fm.get('date')!r}"))
    if m and day and str(day) != m.group(1):
        problems.append((1, f"the date {day} doesn't match the file name ({m.group(1)})"))

    linkedin = fm.get("linkedin")
    if isinstance(linkedin, str):
        tags = " ".join(f"#{re.sub(r'[^0-9A-Za-z]', '', str(t))}" for t in (fm.get("tags") or [])[:5])
        size = len(linkedin.strip()) + len(tags) + URL_ALLOWANCE
        if size > LINKEDIN_LIMIT:
            problems.append((1, f"the LinkedIn text is too long: about {size} characters with hashtags and link "
                                f"(limit {LINKEDIN_LIMIT})"))

    for n, line in enumerate(text.splitlines(), 1):
        for marker in PLACEHOLDERS:
            if marker in line:
                problems.append((n, f"draft placeholder left: {marker!r}"))
        for pattern, what in SECRETS:
            if pattern.search(line):
                problems.append((n, f"looks like {what}"))
    return problems


def main() -> int:
    paths = [Path(p) for p in sys.argv[1:]] or sorted((ROOT / "_posts").glob("*.md"))
    annotate = bool(os.environ.get("GITHUB_ACTIONS"))
    failed = 0
    for path in paths:
        problems = check(path)
        name = path.resolve().relative_to(ROOT).as_posix() if path.resolve().is_relative_to(ROOT) else str(path)
        for line, message in problems:
            print(f"::error file={name},line={line}::{message}" if annotate else f"{name}:{line}: {message}")
        failed += bool(problems)
    print(f"{len(paths)} post(s) checked, {failed} with problems")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
