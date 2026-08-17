from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PACKAGE_ROOT / "scripts" / "manage_workbench.py"


class WorkbenchCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        shutil.copytree(PACKAGE_ROOT / "data", self.root / "data")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_cli(self, *arguments: str) -> tuple[int, dict]:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(self.root), *arguments],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode, json.loads(result.stdout)

    def test_dashboard_and_weekly_report_use_sqlite(self) -> None:
        code, dashboard = self.run_cli("dashboard", "--today", "2026-08-17")
        self.assertEqual(code, 0)
        self.assertEqual(dashboard["caseCount"], 3)

        code, report = self.run_cli("weekly-report", "--week", "2026-W34")
        self.assertEqual(code, 0)
        self.assertEqual(report["week"], "2026-W34")

    def test_create_and_update_task_are_idempotent_by_task_id(self) -> None:
        self.run_cli("dashboard", "--today", "2026-08-17")
        case_id = json.loads(
            subprocess.run(
                [sys.executable, str(SCRIPT), "--root", str(self.root), "list-cases"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout
        )[0]["id"]
        code, task = self.run_cli(
            "create-task",
            "--case-id", case_id,
            "--title", "整理庭审提纲",
            "--owner", "陈律师",
            "--due-at", "2026-08-20T18:00",
        )
        self.assertEqual(code, 0)

        code, updated = self.run_cli(
            "update-task", "--task-id", task["id"], "--status", "待律师复核", "--actor", "陈律师"
        )
        self.assertEqual(code, 0)
        self.assertEqual(updated["status"], "待律师复核")


if __name__ == "__main__":
    unittest.main()
