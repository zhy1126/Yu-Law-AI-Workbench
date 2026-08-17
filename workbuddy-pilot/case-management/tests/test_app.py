from __future__ import annotations

from http.cookiejar import CookieJar
import json
import shutil
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener, urlopen

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from case_manager.app import create_server


class AppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        shutil.copytree(PACKAGE_ROOT / "data", self.root / "data")
        shutil.copytree(PACKAGE_ROOT / "dashboard", self.root / "dashboard")
        self.server = create_server(self.root, port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.opener = build_opener(HTTPCookieProcessor(CookieJar()))

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp.cleanup()

    def request(self, method: str, path: str, payload: dict | None = None):
        data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = Request(
            self.base + path,
            data=data,
            headers={"Content-Type": "application/json"} if data is not None else {},
            method=method,
        )
        try:
            response = self.opener.open(request)
            body = response.read()
            content_type = response.headers.get("Content-Type", "")
            value = json.loads(body.decode("utf-8")) if "application/json" in content_type else body.decode("utf-8")
            return response.status, value, response.headers
        except HTTPError as error:
            body = error.read()
            content_type = error.headers.get("Content-Type", "")
            value = json.loads(body.decode("utf-8")) if "application/json" in content_type else body.decode("utf-8")
            return error.code, value, error.headers

    def login(self) -> None:
        status, payload, _ = self.request("POST", "/api/login", {"password": "yulaw-demo"})
        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])

    def test_health_static_home_and_authentication(self) -> None:
        with urlopen(self.base + "/health") as response:
            self.assertEqual(json.loads(response.read().decode("utf-8")), {"ok": True})
        with urlopen(self.base + "/") as response:
            self.assertEqual(response.status, 200)

        status, _, _ = self.request("GET", "/api/dashboard?today=2026-08-17")
        self.assertEqual(status, 401)
        self.assertEqual(self.request("POST", "/api/login", {"password": "错误密码"})[0], 401)

        self.login()
        status, dashboard, _ = self.request("GET", "/api/dashboard?today=2026-08-17")
        self.assertEqual(status, 200)
        self.assertIn("counts", dashboard)
        self.assertEqual(dashboard["caseCount"], 3)

    def test_crud_and_search_share_the_sqlite_store(self) -> None:
        self.login()
        status, case, _ = self.request(
            "POST",
            "/api/cases",
            {
                "title": "申请人丙公司与丁公司服务合同仲裁",
                "caseNumber": "沪仲案字2026第88号",
                "caseType": "仲裁",
                "procedureStage": "仲裁",
                "cause": "服务合同纠纷",
                "ourRole": "申请人",
                "institution": "上海仲裁委员会",
                "riskLevel": "中",
                "riskReason": "",
                "status": "进行中",
                "nextAction": "提交代理词",
                "tags": ["仲裁", "金额大"],
                "notes": "",
                "leadLawyer": "虞律师",
                "handlingLawyer": "周律师",
                "reviewLawyer": "虞律师",
                "actor": "虞律师",
            },
        )
        self.assertEqual(status, 201)
        status, deadline, _ = self.request(
            "POST",
            "/api/deadlines",
            {
                "caseId": case["id"],
                "deadlineType": "文书",
                "title": "提交代理词",
                "dueAt": "2026-08-21T18:00",
                "reminderLevel": "重要",
                "status": "未完成",
                "notes": "",
                "actor": "周律师",
            },
        )
        self.assertEqual(status, 201)
        status, task, _ = self.request(
            "POST",
            "/api/tasks",
            {
                "caseId": case["id"],
                "title": "完成代理词初稿",
                "owner": "周律师",
                "dueAt": "2026-08-20T18:00",
                "priority": "高",
                "status": "进行中",
                "source": "仲裁庭要求",
                "notes": "",
                "actor": "周律师",
            },
        )
        self.assertEqual(status, 201)
        self.assertEqual(
            self.request(
                "POST",
                "/api/documents",
                {
                    "caseId": case["id"],
                    "documentType": "代理词",
                    "title": "仲裁代理词",
                    "status": "起草中",
                    "dueAt": "2026-08-21T18:00",
                    "submissionMethod": "线上",
                    "notes": "",
                    "actor": "周律师",
                },
            )[0],
            201,
        )

        status, cases, _ = self.request("GET", f"/api/cases?{urlencode({'q': '丁公司'})}")
        self.assertEqual(status, 200)
        self.assertEqual([item["id"] for item in cases], [case["id"]])
        self.assertEqual(self.request("PATCH", f"/api/tasks/{task['id']}", {"status": "待律师复核", "actor": "周律师"})[1]["status"], "待律师复核")
        self.assertEqual(deadline["caseId"], case["id"])

    def test_task_update_refreshes_weekly_report_version(self) -> None:
        self.login()
        cases = self.request("GET", "/api/cases?includeClosed=true")[1]
        task = self.request(
            "POST",
            "/api/tasks",
            {
                "caseId": cases[0]["id"],
                "title": "周报联动测试",
                "owner": "陈律师",
                "dueAt": "2026-08-20T18:00",
                "priority": "高",
                "status": "待律师复核",
                "source": "测试",
                "notes": "",
                "actor": "陈律师",
            },
        )[1]
        first = self.request("GET", "/api/weekly-report?week=2026-W34")[1]
        saved = self.request("POST", "/api/weekly-report", first)[1]
        self.assertEqual(saved["sourceVersion"], first["sourceVersion"])

        self.request("PATCH", f"/api/tasks/{task['id']}", {"status": "已完成", "actor": "陈律师"})
        second = self.request("GET", "/api/weekly-report?week=2026-W34")[1]

        self.assertTrue(second["hasUpdates"])
        self.assertGreater(second["sourceVersion"], first["sourceVersion"])

    def test_csv_export_and_payload_validation(self) -> None:
        self.login()
        status, csv_text, headers = self.request("GET", "/api/export/cases.csv")
        self.assertEqual(status, 200)
        self.assertIn("案件名称", csv_text)
        self.assertIn("text/csv", headers.get("Content-Type"))

        status, payload, _ = self.request("POST", "/api/cases", {"unknown": "field"})
        self.assertEqual(status, 400)
        self.assertIn("请求字段", payload["error"])


if __name__ == "__main__":
    unittest.main()
