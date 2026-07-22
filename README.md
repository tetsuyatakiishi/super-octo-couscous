# organize.py

A small command-line tool that tidies a directory by sorting its files into
category subfolders based on their file extension.

## What it does

It scans the top-level files in a target directory and moves each one into a
subfolder chosen by its extension:

| Category     | Extensions                                   |
|--------------|----------------------------------------------|
| `images/`    | `.jpg` `.jpeg` `.png` `.gif` `.webp`         |
| `documents/` | `.pdf` `.docx` `.txt` `.md` `.xlsx` `.csv`   |
| `archives/`  | `.zip` `.tar` `.gz` `.rar`                    |
| `code/`      | `.py` `.js` `.ts` `.html` `.css`             |
| `others/`    | anything that doesn't match the above        |

Subdirectories (including the category folders themselves) are left untouched,
so it's safe to run more than once. If a file with the same name already exists
at the destination, it is skipped rather than overwritten.

## Requirements

- Python 3.9+ (standard library only, no dependencies)

## Usage

```bash
# Organize the current directory
python3 organize.py

# Organize a specific directory
python3 organize.py ~/Downloads

# Preview the changes without moving anything
python3 organize.py ~/Downloads --dry-run
```

## Example

```bash
$ python3 organize.py ~/Downloads --dry-run
Organizing: /home/you/Downloads
(dry run - no changes will be made)

Would move: photo.png -> images/
Would move: report.pdf -> documents/
Would move: archive.zip -> archives/
Would move: script.py -> code/
Would move: mystery.xyz -> others/

Dry run summary (no files moved)
--------------------------------
  archives     1
  code         1
  documents    1
  images       1
  others       1
  total        5  (files would be moved)
```

Drop the `--dry-run` flag to actually move the files.
