#!/usr/bin/env python3
"""Organize files in a directory into subfolders based on their extension.

Files are grouped into category folders (images/, documents/, archives/,
code/, others/) according to their file extension. Supports a dry-run mode
that reports the planned moves without touching the filesystem.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

# Map each category to the set of extensions that belong to it.
CATEGORIES = {
    "images": {".jpg", ".jpeg", ".png", ".gif", ".webp"},
    "documents": {".pdf", ".docx", ".txt", ".md", ".xlsx", ".csv"},
    "archives": {".zip", ".tar", ".gz", ".rar"},
    "code": {".py", ".js", ".ts", ".html", ".css"},
}
OTHERS = "others"

# Reverse lookup: extension -> category, built once at import time.
EXTENSION_TO_CATEGORY = {
    ext: category
    for category, extensions in CATEGORIES.items()
    for ext in extensions
}


def category_for(path: Path) -> str:
    """Return the destination category folder name for a given file."""
    return EXTENSION_TO_CATEGORY.get(path.suffix.lower(), OTHERS)


def organize(target: Path, dry_run: bool = False) -> dict[str, int]:
    """Sort files in *target* into category subfolders.

    Only top-level files are moved; existing category subfolders and any
    other directories are left untouched. Returns a mapping of category
    name to the number of files moved (or that would be moved).
    """
    category_names = set(CATEGORIES) | {OTHERS}
    moved: dict[str, int] = {}

    for entry in sorted(target.iterdir()):
        # Skip directories (including the category folders themselves).
        if entry.is_dir():
            continue

        category = category_for(entry)
        destination_dir = target / category
        destination = destination_dir / entry.name

        action = "Would move" if dry_run else "Moving"
        print(f"{action}: {entry.name} -> {category}/")

        if not dry_run:
            destination_dir.mkdir(exist_ok=True)
            # Avoid clobbering an existing file at the destination.
            if destination.exists():
                print(f"  Skipped (already exists at destination): {destination}")
                continue
            shutil.move(str(entry), str(destination))

        moved[category] = moved.get(category, 0) + 1

    # Ensure referenced categories exist in the summary for clarity.
    _ = category_names
    return moved


def print_summary(moved: dict[str, int], dry_run: bool) -> None:
    """Print a clear summary of what was (or would be) done."""
    total = sum(moved.values())
    header = "Dry run summary (no files moved)" if dry_run else "Summary"
    print()
    print(header)
    print("-" * len(header))
    if not moved:
        print("No files to organize.")
        return
    for category in sorted(moved):
        print(f"  {category:<12} {moved[category]}")
    label = "files would be moved" if dry_run else "files moved"
    print(f"  {'total':<12} {total}  ({label})")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Organize files in a directory into subfolders by extension."
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Target directory to organize (default: current directory).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would move without actually moving anything.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    target = Path(args.directory).expanduser().resolve()

    if not target.is_dir():
        print(f"Error: {target} is not a directory.", file=sys.stderr)
        return 1

    print(f"Organizing: {target}")
    if args.dry_run:
        print("(dry run - no changes will be made)")
    print()

    moved = organize(target, dry_run=args.dry_run)
    print_summary(moved, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
