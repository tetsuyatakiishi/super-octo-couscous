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


def iter_files(target: Path, recursive: bool) -> list[Path]:
    """Return the files under *target* that should be organized.

    In the default (non-recursive) mode only top-level files are returned.
    In recursive mode files in nested subdirectories are included too, but
    anything already living inside one of the category folders is skipped so
    that the operation stays idempotent (safe to run more than once).
    """
    category_names = set(CATEGORIES) | {OTHERS}

    if not recursive:
        return [entry for entry in sorted(target.iterdir()) if entry.is_file()]

    files: list[Path] = []
    for entry in sorted(target.rglob("*")):
        if not entry.is_file():
            continue
        # Leave files that are already sorted into a category folder alone.
        if entry.relative_to(target).parts[0] in category_names:
            continue
        files.append(entry)
    return files


def organize(
    target: Path, dry_run: bool = False, recursive: bool = False
) -> dict[str, int]:
    """Sort files in *target* into category subfolders.

    Top-level files are always considered; with *recursive* enabled, files in
    nested subdirectories are pulled up into the top-level category folders as
    well. Existing category folders and (in non-recursive mode) other
    directories are left untouched. Returns a mapping of category name to the
    number of files moved (or that would be moved).
    """
    moved: dict[str, int] = {}

    for entry in iter_files(target, recursive):
        category = category_for(entry)
        destination_dir = target / category
        destination = destination_dir / entry.name

        # Show the path relative to the target so recursive moves are clear.
        display = entry.relative_to(target)
        action = "Would move" if dry_run else "Moving"
        print(f"{action}: {display} -> {category}/")

        if not dry_run:
            destination_dir.mkdir(exist_ok=True)
            # Avoid clobbering an existing file at the destination.
            if destination.exists():
                print(f"  Skipped (already exists at destination): {destination}")
                continue
            shutil.move(str(entry), str(destination))

        moved[category] = moved.get(category, 0) + 1

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
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Also organize files inside nested subdirectories.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    target = Path(args.directory).expanduser().resolve()

    if not target.is_dir():
        print(f"Error: {target} is not a directory.", file=sys.stderr)
        return 1

    print(f"Organizing: {target}")
    if args.recursive:
        print("(recursive - nested subdirectories included)")
    if args.dry_run:
        print("(dry run - no changes will be made)")
    print()

    moved = organize(target, dry_run=args.dry_run, recursive=args.recursive)
    print_summary(moved, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
