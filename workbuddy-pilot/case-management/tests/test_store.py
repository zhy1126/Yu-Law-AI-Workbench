from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from case_manager.models import validate_matter
from case_manager.store import JsonStore


class StoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        shutil.copytree(PACKAGE_ROOT / "data", self.root / "data")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_seeded_store_returns_three_virtual_matters(self) -> None:
        store = JsonStore(self.root)

        matters = store.read("matters")

        self.assertEqual(len(matters), 3)
        self.assertTrue(all(item["client"].startswith("示例") for item in matters))

    def test_write_increments_revision_and_appends_log(self) -> None:
        store = JsonStore(self.root)
        before = store.revision
        tasks = store.read("tasks")
        tasks[0]["status"] = "进行中"

        revision = store.write("tasks", tasks, event="task.updated", actor="虞律师")

        self.assertEqual(revision, before + 1)
        self.assertEqual(store.revision, before + 1)
        self.assertEqual(store.read("activity-log")[-1]["event"], "task.updated")
        self.assertEqual(store.read("activity-log")[-1]["actor"], "虞律师")

    def test_write_is_atomic_and_creates_snapshot(self) -> None:
        store = JsonStore(self.root)
        revision_before_write = store.revision
        matters = store.read("matters")
        matters[0]["priority"] = "中"

        store.write("matters", matters, event="matter.updated")

        snapshots = list((self.root / "snapshots").glob("*.json"))
        self.assertEqual(len(snapshots), 1)
        snapshot = json.loads(snapshots[0].read_text(encoding="utf-8"))
        self.assertEqual(snapshot["revision"], revision_before_write)
        self.assertFalse(any((self.root / "data").glob("*.tmp")))

    def test_rejects_unknown_dataset(self) -> None:
        store = JsonStore(self.root)

        with self.assertRaisesRegex(ValueError, "未知数据集"):
            store.read("secrets")

    def test_validates_required_matter_fields_and_stage(self) -> None:
        matter = JsonStore(self.root).read("matters")[0]
        validate_matter(matter)

        with self.assertRaisesRegex(ValueError, "案件缺少字段"):
            validate_matter({"id": "MAT-BAD"})

        invalid = dict(matter, stage="已删除")
        with self.assertRaisesRegex(ValueError, "非法案件阶段"):
            validate_matter(invalid)


if __name__ == "__main__":
    unittest.main()
