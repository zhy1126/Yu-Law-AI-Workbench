from __future__ import annotations

import shutil
import sqlite3
import sys
import tempfile
import unittest
import os
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from case_manager.database import LitigationDatabase


def sample_case() -> dict:
    return {
        "title": "测试买卖合同纠纷",
        "caseNumber": "（2026）沪0101民初999号",
        "caseType": "诉讼",
        "procedureStage": "一审",
        "cause": "买卖合同纠纷",
        "ourRole": "原告",
        "institution": "上海市黄浦区人民法院",
        "adjudicator": "王法官",
        "amount": 500000,
        "riskLevel": "中",
        "riskReason": "对方履约能力待核实",
        "status": "进行中",
        "nextAction": "准备证据目录",
        "tags": ["重点客户", "保全中"],
        "notes": "仅用于测试",
        "leadLawyer": "虞律师",
        "handlingLawyer": "陈律师",
        "reviewLawyer": "虞律师",
    }


class LitigationDatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        shutil.copytree(PACKAGE_ROOT / "data", self.root / "data")
        self.db = LitigationDatabase(self.root)

    def tearDown(self) -> None:
        self.db.close()
        self.temp.cleanup()

    @unittest.skipIf(os.name == "nt", "Windows does not enforce POSIX file modes")
    def test_database_and_parent_directory_use_private_permissions(self):
        self.assertEqual(self.db.data_dir.stat().st_mode & 0o777, 0o700)
        self.assertEqual(self.db.path.stat().st_mode & 0o777, 0o600)

    def test_creates_all_core_tables(self) -> None:
        names = {
            row[0]
            for row in self.db.connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }

        self.assertTrue(
            {
                "cases",
                "parties",
                "deadlines",
                "tasks",
                "documents",
                "followups",
                "weekly_reports",
                "activity_log",
                "settings",
            }.issubset(names)
        )

    def test_migrates_legacy_json_once(self) -> None:
        first = self.db.migrate_legacy_json()
        second = self.db.migrate_legacy_json()

        self.assertEqual(first["cases"], 3)
        self.assertEqual(first["tasks"], 6)
        self.assertEqual(first["deadlines"], 3)
        self.assertEqual(second, {"cases": 0, "tasks": 0, "deadlines": 0})
        self.assertEqual(len(self.db.list_cases(include_closed=True)), 3)
        self.assertEqual(len(self.db.list_tasks()), 6)

    def test_write_increments_data_version_and_logs_activity(self) -> None:
        before = self.db.data_version

        created = self.db.create_case(sample_case(), actor="虞律师")

        self.assertEqual(self.db.data_version, before + 1)
        self.assertEqual(created["title"], "测试买卖合同纠纷")
        activity = self.db.connection.execute(
            "SELECT event, actor, object_id FROM activity_log ORDER BY id DESC LIMIT 1"
        ).fetchone()
        self.assertEqual(tuple(activity), ("case.created", "虞律师", created["id"]))

    def test_crud_uses_stable_ids_and_case_relationships(self) -> None:
        case = self.db.create_case(sample_case())
        deadline = self.db.create_deadline(
            {
                "caseId": case["id"],
                "deadlineType": "开庭",
                "title": "第一次开庭",
                "dueAt": "2026-08-25T09:30",
                "reminderLevel": "极重要",
                "status": "未完成",
                "notes": "第五法庭",
            }
        )
        task = self.db.create_task(
            {
                "caseId": case["id"],
                "title": "准备庭审提纲",
                "owner": "陈律师",
                "dueAt": "2026-08-23T18:00",
                "priority": "高",
                "status": "未开始",
                "source": "庭前准备",
                "notes": "",
            }
        )

        updated = self.db.update_task(task["id"], {"status": "进行中"}, actor="陈律师")

        self.assertTrue(case["id"].startswith("CASE-"))
        self.assertTrue(deadline["id"].startswith("DL-"))
        self.assertTrue(task["id"].startswith("TASK-"))
        self.assertEqual(updated["status"], "进行中")
        self.assertEqual(self.db.list_deadlines(case["id"])[0]["title"], "第一次开庭")

    def test_rejects_unknown_case_relationship(self) -> None:
        with self.assertRaisesRegex(ValueError, "案件不存在"):
            self.db.create_task(
                {
                    "caseId": "CASE-MISSING",
                    "title": "无效任务",
                    "owner": "",
                    "dueAt": "2026-08-20T18:00",
                    "priority": "中",
                    "status": "未开始",
                    "source": "测试",
                    "notes": "",
                }
            )


if __name__ == "__main__":
    unittest.main()
