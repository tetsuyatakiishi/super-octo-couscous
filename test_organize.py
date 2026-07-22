#!/usr/bin/env python3
"""Tests for the file organizer (organize.py).

Run with:  python3 -m unittest -v
"""

import tempfile
import unittest
from pathlib import Path

import organize


class CategoryForTests(unittest.TestCase):
    def test_known_extensions_map_to_categories(self):
        self.assertEqual(organize.category_for(Path("photo.jpg")), "images")
        self.assertEqual(organize.category_for(Path("report.pdf")), "documents")
        self.assertEqual(organize.category_for(Path("backup.zip")), "archives")
        self.assertEqual(organize.category_for(Path("app.py")), "code")

    def test_extension_matching_is_case_insensitive(self):
        self.assertEqual(organize.category_for(Path("PIC.JPG")), "images")

    def test_unknown_and_missing_extensions_fall_back_to_others(self):
        self.assertEqual(organize.category_for(Path("mystery.xyz")), "others")
        self.assertEqual(organize.category_for(Path("noext")), "others")


class OrganizeTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _touch(self, name: str) -> Path:
        path = self.dir / name
        path.write_text("x")
        return path

    def test_real_run_sorts_files_into_categories(self):
        self._touch("a.png")
        self._touch("b.PDF")
        self._touch("c.unknownext")

        counts = organize.organize(self.dir, dry_run=False)

        self.assertEqual(counts, {"images": 1, "documents": 1, "others": 1})
        self.assertTrue((self.dir / "images" / "a.png").exists())
        self.assertTrue((self.dir / "documents" / "b.PDF").exists())
        self.assertTrue((self.dir / "others" / "c.unknownext").exists())
        # Originals no longer at top level.
        self.assertFalse((self.dir / "a.png").exists())

    def test_dry_run_moves_nothing(self):
        self._touch("a.png")
        self._touch("b.txt")

        counts = organize.organize(self.dir, dry_run=True)

        self.assertEqual(counts, {"images": 1, "documents": 1})
        # Files stay exactly where they were; no category folders created.
        self.assertTrue((self.dir / "a.png").exists())
        self.assertTrue((self.dir / "b.txt").exists())
        self.assertFalse((self.dir / "images").exists())

    def test_existing_directories_are_skipped(self):
        (self.dir / "some_subdir").mkdir()
        self._touch("a.png")

        counts = organize.organize(self.dir, dry_run=False)

        self.assertEqual(counts, {"images": 1})
        self.assertTrue((self.dir / "some_subdir").is_dir())

    def test_name_collision_is_not_clobbered(self):
        self._touch("a.png")
        # Pre-create the destination with different content.
        (self.dir / "images").mkdir()
        (self.dir / "images" / "a.png").write_text("original")

        organize.organize(self.dir, dry_run=False)

        # Existing destination file is preserved, not overwritten.
        self.assertEqual((self.dir / "images" / "a.png").read_text(), "original")
        # Source is left in place because the move was skipped.
        self.assertTrue((self.dir / "a.png").exists())

    def test_empty_directory_returns_empty_summary(self):
        self.assertEqual(organize.organize(self.dir, dry_run=False), {})

    def test_non_recursive_ignores_nested_files(self):
        self._touch("top.png")
        nested = self.dir / "sub"
        nested.mkdir()
        (nested / "deep.txt").write_text("x")

        counts = organize.organize(self.dir, dry_run=False, recursive=False)

        self.assertEqual(counts, {"images": 1})
        # The nested file is untouched in non-recursive mode.
        self.assertTrue((nested / "deep.txt").exists())

    def test_recursive_pulls_up_nested_files(self):
        self._touch("top.png")
        nested = self.dir / "sub" / "deeper"
        nested.mkdir(parents=True)
        (nested / "deep.txt").write_text("x")
        (self.dir / "sub" / "photo.gif").write_text("x")

        counts = organize.organize(self.dir, dry_run=False, recursive=True)

        self.assertEqual(counts, {"images": 2, "documents": 1})
        self.assertTrue((self.dir / "images" / "top.png").exists())
        self.assertTrue((self.dir / "images" / "photo.gif").exists())
        self.assertTrue((self.dir / "documents" / "deep.txt").exists())

    def test_recursive_is_idempotent(self):
        nested = self.dir / "sub"
        nested.mkdir()
        (nested / "a.png").write_text("x")

        organize.organize(self.dir, dry_run=False, recursive=True)
        # A second run must not try to re-move already-sorted files.
        second = organize.organize(self.dir, dry_run=False, recursive=True)

        self.assertEqual(second, {})


class MainTests(unittest.TestCase):
    def test_main_rejects_non_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            not_a_dir = Path(tmp) / "nope"
            self.assertEqual(organize.main([str(not_a_dir)]), 1)

    def test_main_succeeds_on_valid_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "a.png").write_text("x")
            self.assertEqual(organize.main([tmp]), 0)
            self.assertTrue((Path(tmp) / "images" / "a.png").exists())


if __name__ == "__main__":
    unittest.main()
