from __future__ import annotations

from datetime import date
import sys
import tempfile
import unittest
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from case_manager.database import LitigationDatabase
from case_manager.reporting import build_dashboard, build_weekly_report, save_weekly_report


class ReportingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.db = LitigationDatabase(self.root)
        self.case = self.db.create_case(
            {
                "title": "原告甲公司与乙公司买卖合同纠纷",
                "caseNumber": "（2026）沪0101民初123号",
                "caseType": "诉讼",
                "procedureStage": "一审",
                "institution": "上海市黄浦区人民法院",
                "riskLevel": "高",
                "riskReason": "已申请财产保全",
                "status": "进行中",
                "nextAction": "准备第一次开庭",
                "tags": ["保全中"],
                "leadLawyer": "虞律师",
                "handlingLawyer": "陈律师",
                "reviewLawyer": "虞律师",
            }
        )

    def tearDown(self) -> None:
        self.db.close()
        self.temp.cleanup()

    def add_deadline(self, title: str, due_at: str, deadline_type: str = "其他") -> dict:
        return self.db.create_deadline(
            {
                "caseId": self.case["id"],
                "deadlineType": deadline_type,
                "title": title,
                "dueAt": due_at,
                "reminderLevel": "重要",
                "status": "未完成",
                "notes": "",
            }
        )

    def test_dashboard_buckets_deadlines_and_tasks(self) -> None:
        self.add_deadline("已逾期举证", "2026-08-16T18:00", "举证")
        self.add_deadline("今日提交", "2026-08-17T18:00", "文书")
        self.add_deadline("三日内开庭", "2026-08-19T09:30", "开庭")
        self.add_deadline("七日内缴费", "2026-08-23T18:00", "缴费")
        self.add_deadline("续封申请", "2026-09-20T18:00", "续封")
        self.db.create_task(
            {
                "caseId": self.case["id"],
                "title": "今日联系法官",
                "owner": "陈律师",
                "dueAt": "2026-08-17T17:00",
                "priority": "高",
                "status": "进行中",
                "source": "跟进",
                "notes": "",
            }
        )

        result = build_dashboard(self.db, today=date(2026, 8, 17))

        self.assertEqual(result["counts"]["overdue"], 1)
        self.assertEqual(result["counts"]["today"], 2)
        self.assertEqual(result["counts"]["next3Days"], 1)
        self.assertEqual(result["counts"]["next7Days"], 2)
        self.assertEqual(result["counts"]["preservation"], 1)
        self.assertEqual(result["upcomingHearings"][0]["title"], "三日内开庭")

    def test_weekly_report_marks_updates_after_database_change(self) -> None:
        task = self.db.create_task(
            {
                "caseId": self.case["id"],
                "title": "完成证据目录",
                "owner": "陈律师",
                "dueAt": "2026-08-20T18:00",
                "priority": "高",
                "status": "待律师复核",
                "source": "周会",
                "notes": "等待复核",
            }
        )
        first = build_weekly_report(self.db, week="2026-W34")
        saved = save_weekly_report(self.db, first)

        self.assertEqual(saved["sourceVersion"], first["sourceVersion"])
        self.assertFalse(build_weekly_report(self.db, week="2026-W34")["hasUpdates"])

        self.db.update_task(task["id"], {"status": "已完成"}, actor="陈律师")
        second = build_weekly_report(self.db, week="2026-W34")

        self.assertTrue(second["hasUpdates"])
        self.assertNotEqual(first["sourceVersion"], second["sourceVersion"])
        self.assertNotEqual(first["sections"], second["sections"])
        self.assertNotIn(task["id"], [item["id"] for item in second["sections"]["pendingReview"]])

    def test_weekly_report_has_fixed_lawyer_sections(self) -> None:
        report = build_weekly_report(self.db, week="2026-W34")

        self.assertEqual(
            list(report["sections"]),
            ["progress", "deadlineRisks", "blocked", "pendingReview", "nextWeek"],
        )
        self.assertEqual(report["week"], "2026-W34")
        self.assertEqual(report["sourceVersion"], self.db.data_version)


if __name__ == "__main__":
    unittest.main()
