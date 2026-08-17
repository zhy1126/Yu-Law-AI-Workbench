from __future__ import annotations

from datetime import date
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from case_manager.store import JsonStore
from case_manager.workflow import (
    ProposalConflict,
    apply_proposal,
    build_weekly_digest,
    create_proposal,
    index_documents,
)


class WorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        shutil.copytree(PACKAGE_ROOT / "data", self.root / "data")
        self.store = JsonStore(self.root)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_indexes_documents_without_reading_outside_project(self) -> None:
        matter_dir = self.root / "matters" / "MAT-2026-001"
        documents = matter_dir / "documents"
        documents.mkdir(parents=True)
        (documents / "交易文件-v2.docx").write_bytes(b"virtual")
        (documents / "~$交易文件-v2.docx").write_bytes(b"temp")

        index = index_documents(matter_dir, self.root)

        self.assertEqual(len(index), 1)
        self.assertEqual(index[0]["version"], "v2")
        self.assertEqual(index[0]["path"], "matters/MAT-2026-001/documents/交易文件-v2.docx")

    def test_builds_weekly_digest_for_deadlines_gaps_and_alignment(self) -> None:
        digest = build_weekly_digest(
            self.store.read("matters"),
            self.store.read("tasks"),
            today=date(2026, 8, 12),
        )

        self.assertEqual(digest["deadlineRisks"][0]["matterId"], "MAT-2026-003")
        self.assertEqual(digest["overdueTasks"][0]["id"], "TASK-001")
        self.assertIn("MAT-2026-001", {item["matterId"] for item in digest["materialGaps"]})
        self.assertIn("负责人缺失", {item["reason"] for item in digest["needsAlignment"]})

    def test_unconfirmed_proposal_does_not_change_matter_or_tasks(self) -> None:
        matters_before = self.store.read("matters")
        tasks_before = self.store.read("tasks")

        proposal = create_proposal(
            self.store,
            meeting_id="WM-2026-33",
            changes=[
                {
                    "id": "CH-1001",
                    "type": "task.create",
                    "matterId": "MAT-2026-001",
                    "after": {"title": "准备交割清单", "owner": "陈律师", "dueAt": "2026-08-21"},
                    "risk": "低",
                }
            ],
        )

        self.assertEqual(proposal["status"], "待确认")
        self.assertEqual(self.store.read("matters"), matters_before)
        self.assertEqual(self.store.read("tasks"), tasks_before)

    def test_applies_only_accepted_changes_and_is_idempotent(self) -> None:
        proposal = create_proposal(
            self.store,
            meeting_id="WM-2026-33",
            changes=[
                {
                    "id": "CH-1001",
                    "type": "task.create",
                    "matterId": "MAT-2026-001",
                    "after": {"title": "准备交割清单", "owner": "陈律师", "dueAt": "2026-08-21"},
                    "risk": "低",
                },
                {
                    "id": "CH-1002",
                    "type": "matter.update_stage",
                    "matterId": "MAT-2026-002",
                    "after": "待律师复核",
                    "risk": "高",
                },
            ],
        )

        first = apply_proposal(self.store, proposal["id"], ["CH-1001"], actor="虞律师")
        second = apply_proposal(self.store, proposal["id"], ["CH-1001"], actor="虞律师")

        created = [task for task in self.store.read("tasks") if task["title"] == "准备交割清单"]
        self.assertEqual(len(created), 1)
        self.assertEqual(created[0]["syncState"], "待同步WorkBuddy")
        self.assertEqual(first["revision"], second["revision"])
        self.assertEqual(next(item for item in self.store.read("matters") if item["id"] == "MAT-2026-002")["stage"], "进行中")

    def test_rejects_proposal_after_concurrent_change(self) -> None:
        proposal = create_proposal(
            self.store,
            meeting_id="WM-2026-34",
            changes=[
                {
                    "id": "CH-2001",
                    "type": "matter.update_deadline",
                    "matterId": "MAT-2026-003",
                    "after": "2026-08-22",
                    "risk": "高",
                }
            ],
        )
        self.store.write("tasks", self.store.read("tasks"), event="concurrent.update")

        with self.assertRaisesRegex(ProposalConflict, "数据已更新"):
            apply_proposal(self.store, proposal["id"], ["CH-2001"], actor="虞律师")


if __name__ == "__main__":
    unittest.main()
