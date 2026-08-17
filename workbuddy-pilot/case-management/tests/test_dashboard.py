from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "dashboard" / "index.html"
CSS = ROOT / "dashboard" / "styles.css"
JS = ROOT / "dashboard" / "app.js"


class LitigationDashboardTests(unittest.TestCase):
    def test_replaces_old_ledger_with_litigation_navigation(self) -> None:
        html = INDEX.read_text(encoding="utf-8")
        self.assertIn("<title>诉讼工作台</title>", html)
        self.assertIn('id="login-screen"', html)
        self.assertIn('id="app-shell"', html)
        for label in ("工作台", "案件", "期限", "待办", "文书", "导出备份"):
            self.assertIn(f">{label}<", html)
        self.assertNotIn("案件台账", html)
        self.assertNotIn("周会中心", html)

    def test_dashboard_matches_reference_information_architecture(self) -> None:
        html = INDEX.read_text(encoding="utf-8")
        self.assertIn("搜索案号、案件名称、当事人、机构、代理人、备注、标签", html)
        for action in ("新建案件", "新增期限", "新增待办", "本周周报"):
            self.assertIn(action, html)
        for metric in ("已逾期", "今日到期", "未来 3 天", "未来 7 天", "保全/续封"):
            self.assertIn(metric, html)
        for section in ("紧急事项", "最近开庭", "保全/续封专项"):
            self.assertIn(section, html)

    def test_has_six_views_and_reusable_forms(self) -> None:
        html = INDEX.read_text(encoding="utf-8")
        for view in ("dashboard", "cases", "deadlines", "tasks", "documents", "backup"):
            self.assertIn(f'data-panel="{view}"', html)
        for form in ("login-form", "case-form", "deadline-form", "task-form", "document-form"):
            self.assertIn(f'id="{form}"', html)
        for field in ("caseNumber", "procedureStage", "institution", "riskLevel", "deadlineType", "reminderLevel", "submissionMethod"):
            self.assertIn(f'name="{field}"', html)

    def test_visual_system_is_dense_and_suitable_for_legal_work(self) -> None:
        css = CSS.read_text(encoding="utf-8").lower()
        for selector in (".sidebar", ".topbar", ".metric-grid", ".data-table", ".modal", ".login-card"):
            self.assertIn(selector, css)
        self.assertIn("width: 220px", css)
        self.assertNotIn("linear-gradient", css)

    def test_script_uses_v2_api_and_safe_dom_rendering(self) -> None:
        js = JS.read_text(encoding="utf-8")
        for endpoint in ("/api/login", "/api/dashboard", "/api/cases", "/api/deadlines", "/api/tasks", "/api/documents", "/api/weekly-report"):
            self.assertIn(endpoint, js)
        for function in ("renderDashboard", "renderCases", "renderDeadlines", "renderTasks", "renderDocuments", "openWeeklyReport", "submitEntityForm"):
            self.assertIn(f"function {function}", js)
        self.assertIn("textContent", js)
        self.assertIn("replaceChildren", js)
        self.assertNotIn("innerHTML", js)
        self.assertNotIn("onclick=", INDEX.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
