from __future__ import annotations

import csv
from datetime import date
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import io
import json
from pathlib import Path
import secrets
from urllib.parse import parse_qs, urlparse

from .database import LitigationDatabase
from .reporting import build_dashboard, build_weekly_report, save_weekly_report

MAX_BODY = 256 * 1024

CASE_FIELDS = {
    "title", "caseNumber", "caseType", "procedureStage", "cause", "ourRole",
    "institution", "adjudicator", "amount", "riskLevel", "riskReason", "status",
    "nextAction", "tags", "notes", "leadLawyer", "handlingLawyer", "reviewLawyer",
}
DEADLINE_FIELDS = {"caseId", "deadlineType", "title", "dueAt", "reminderLevel", "status", "completedAt", "notes"}
TASK_FIELDS = {"caseId", "title", "owner", "dueAt", "priority", "status", "source", "workbuddyTodoId", "syncState", "notes"}
DOCUMENT_FIELDS = {"caseId", "documentType", "title", "status", "dueAt", "submissionMethod", "notes"}


class LitigationHTTPServer(ThreadingHTTPServer):
    database: LitigationDatabase

    def server_close(self) -> None:
        super().server_close()
        if hasattr(self, "database"):
            self.database.close()


def create_server(root: Path, *, port: int = 8765) -> ThreadingHTTPServer:
    project_root = root.resolve()
    database = LitigationDatabase(project_root)
    database.migrate_legacy_json()
    dashboard = project_root / "dashboard"
    sessions: set[str] = set()

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(dashboard), **kwargs)

        def log_message(self, format: str, *args) -> None:
            return

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/health":
                self._json(HTTPStatus.OK, {"ok": True})
                return
            if parsed.path == "/api/session":
                self._json(HTTPStatus.OK, {"authenticated": self._authorized()})
                return
            if not parsed.path.startswith("/api/"):
                super().do_GET()
                return
            if not self._require_auth():
                return

            query = parse_qs(parsed.query)
            try:
                if parsed.path == "/api/dashboard":
                    current = date.fromisoformat(query.get("today", [date.today().isoformat()])[0])
                    self._json(HTTPStatus.OK, build_dashboard(database, today=current))
                elif parsed.path == "/api/cases":
                    include_closed = query.get("includeClosed", ["false"])[0].lower() == "true"
                    records = database.list_cases(include_closed=include_closed)
                    q = query.get("q", [""])[0].strip().casefold()
                    if q:
                        records = [item for item in records if self._case_matches(item, q)]
                    self._json(HTTPStatus.OK, records)
                elif parsed.path.startswith("/api/cases/"):
                    self._json(HTTPStatus.OK, database.get_case(parsed.path.rsplit("/", 1)[-1]))
                elif parsed.path == "/api/deadlines":
                    self._json(HTTPStatus.OK, database.list_deadlines(query.get("caseId", [None])[0]))
                elif parsed.path == "/api/tasks":
                    self._json(HTTPStatus.OK, database.list_tasks(query.get("caseId", [None])[0]))
                elif parsed.path == "/api/documents":
                    self._json(HTTPStatus.OK, database.list_documents(query.get("caseId", [None])[0]))
                elif parsed.path == "/api/followups":
                    self._json(HTTPStatus.OK, database.list_followups(query.get("caseId", [None])[0]))
                elif parsed.path == "/api/weekly-report":
                    week = query.get("week", [date.today().strftime("%G-W%V")])[0]
                    self._json(HTTPStatus.OK, build_weekly_report(database, week=week))
                elif parsed.path.startswith("/api/export/") and parsed.path.endswith(".csv"):
                    dataset = parsed.path.removeprefix("/api/export/").removesuffix(".csv")
                    self._export_csv(dataset)
                else:
                    self._json(HTTPStatus.NOT_FOUND, {"error": "接口不存在"})
            except (ValueError, KeyError) as error:
                self._json(HTTPStatus.BAD_REQUEST, {"error": str(error)})

        def do_POST(self) -> None:
            path = urlparse(self.path).path
            payload = self._read_payload()
            if payload is None:
                return
            if path == "/api/login":
                if set(payload) != {"password"}:
                    self._json(HTTPStatus.BAD_REQUEST, {"error": "请求字段不完整或包含未知字段"})
                    return
                if not isinstance(payload["password"], str) or not database.verify_password(payload["password"]):
                    self._json(HTTPStatus.UNAUTHORIZED, {"error": "密码错误"})
                    return
                token = secrets.token_urlsafe(24)
                sessions.add(token)
                self._json(
                    HTTPStatus.OK,
                    {"ok": True},
                    headers={"Set-Cookie": f"litigation_session={token}; Path=/; HttpOnly; SameSite=Strict"},
                )
                return
            if not self._require_auth():
                return
            try:
                if path == "/api/logout":
                    token = self._session_token()
                    if token:
                        sessions.discard(token)
                    self._json(HTTPStatus.OK, {"ok": True}, headers={"Set-Cookie": "litigation_session=; Path=/; Max-Age=0; HttpOnly; SameSite=Strict"})
                elif path == "/api/cases":
                    data, actor = self._validated(payload, CASE_FIELDS)
                    self._json(HTTPStatus.CREATED, database.create_case(data, actor=actor))
                elif path == "/api/deadlines":
                    data, actor = self._validated(payload, DEADLINE_FIELDS)
                    self._json(HTTPStatus.CREATED, database.create_deadline(data, actor=actor))
                elif path == "/api/tasks":
                    data, actor = self._validated(payload, TASK_FIELDS)
                    self._json(HTTPStatus.CREATED, database.create_task(data, actor=actor))
                elif path == "/api/documents":
                    data, actor = self._validated(payload, DOCUMENT_FIELDS)
                    self._json(HTTPStatus.CREATED, database.create_document(data, actor=actor))
                elif path == "/api/weekly-report":
                    self._json(HTTPStatus.CREATED, save_weekly_report(database, payload))
                else:
                    self._json(HTTPStatus.NOT_FOUND, {"error": "接口不存在"})
            except (ValueError, KeyError) as error:
                self._json(HTTPStatus.BAD_REQUEST, {"error": str(error)})

        def do_PATCH(self) -> None:
            path = urlparse(self.path).path
            if not self._require_auth():
                return
            payload = self._read_payload()
            if payload is None:
                return
            try:
                if path.startswith("/api/cases/"):
                    data, actor = self._validated(payload, CASE_FIELDS)
                    result = database.update_case(path.rsplit("/", 1)[-1], data, actor=actor)
                elif path.startswith("/api/deadlines/"):
                    data, actor = self._validated(payload, DEADLINE_FIELDS)
                    result = database.update_deadline(path.rsplit("/", 1)[-1], data, actor=actor)
                elif path.startswith("/api/tasks/"):
                    data, actor = self._validated(payload, TASK_FIELDS)
                    result = database.update_task(path.rsplit("/", 1)[-1], data, actor=actor)
                elif path.startswith("/api/documents/"):
                    data, actor = self._validated(payload, DOCUMENT_FIELDS)
                    result = database.update_document(path.rsplit("/", 1)[-1], data, actor=actor)
                else:
                    self._json(HTTPStatus.NOT_FOUND, {"error": "接口不存在"})
                    return
                self._json(HTTPStatus.OK, result)
            except (ValueError, KeyError) as error:
                self._json(HTTPStatus.BAD_REQUEST, {"error": str(error)})

        @staticmethod
        def _case_matches(item: dict, query: str) -> bool:
            values = [
                item.get("title", ""), item.get("caseNumber", ""), item.get("institution", ""),
                item.get("adjudicator", ""), item.get("cause", ""), item.get("ourRole", ""),
                item.get("notes", ""), item.get("leadLawyer", ""), item.get("handlingLawyer", ""),
                item.get("reviewLawyer", ""), *item.get("tags", []),
            ]
            return any(query in str(value).casefold() for value in values)

        def _session_token(self) -> str:
            cookie = SimpleCookie(self.headers.get("Cookie", ""))
            morsel = cookie.get("litigation_session")
            return morsel.value if morsel else ""

        def _authorized(self) -> bool:
            return self._session_token() in sessions

        def _require_auth(self) -> bool:
            if self._authorized():
                return True
            self._json(HTTPStatus.UNAUTHORIZED, {"error": "请先解锁诉讼工作台"})
            return False

        def _validated(self, payload: dict, allowed: set[str]) -> tuple[dict, str]:
            unknown = set(payload) - allowed - {"actor"}
            if unknown or not (set(payload) & allowed):
                raise ValueError("请求字段不完整或包含未知字段")
            actor = payload.get("actor", "本地用户")
            if not isinstance(actor, str) or not actor.strip():
                raise ValueError("操作人不能为空")
            return {key: value for key, value in payload.items() if key in allowed}, actor.strip()

        def _read_payload(self) -> dict | None:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self._json(HTTPStatus.BAD_REQUEST, {"error": "请求长度无效"})
                return None
            if length > MAX_BODY:
                self._json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "请求内容过大"})
                return None
            try:
                value = json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                self._json(HTTPStatus.BAD_REQUEST, {"error": "JSON 格式无效"})
                return None
            if not isinstance(value, dict):
                self._json(HTTPStatus.BAD_REQUEST, {"error": "请求必须是对象"})
                return None
            return value

        def _export_csv(self, dataset: str) -> None:
            sources = {
                "cases": (database.list_cases(include_closed=True), {
                    "id": "编号", "title": "案件名称", "caseNumber": "案号", "caseType": "类型",
                    "procedureStage": "阶段", "institution": "机构", "riskLevel": "风险", "status": "状态",
                    "nextAction": "下一事项", "handlingLawyer": "经办律师",
                }),
                "deadlines": (database.list_deadlines(), {"id": "编号", "caseId": "案件编号", "deadlineType": "期限类型", "title": "事项", "dueAt": "截止时间", "status": "状态"}),
                "tasks": (database.list_tasks(), {"id": "编号", "caseId": "案件编号", "title": "待办", "owner": "负责人", "dueAt": "截止时间", "priority": "优先级", "status": "状态"}),
                "documents": (database.list_documents(), {"id": "编号", "caseId": "案件编号", "documentType": "文书类型", "title": "文书", "status": "状态", "dueAt": "提交期限"}),
                "followups": (database.list_followups(), {"id": "编号", "case_id": "案件编号", "occurred_at": "时间", "target": "对象", "method": "方式", "content": "内容", "author": "记录人"}),
            }
            if dataset not in sources:
                self._json(HTTPStatus.NOT_FOUND, {"error": "导出类型不存在"})
                return
            records, columns = sources[dataset]
            buffer = io.StringIO()
            writer = csv.DictWriter(buffer, fieldnames=list(columns), extrasaction="ignore")
            writer.writerow(columns)
            writer.writerows(records)
            content = ("\ufeff" + buffer.getvalue()).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", f'attachment; filename="{dataset}.csv"')
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def _json(self, status: HTTPStatus, payload, *, headers: dict[str, str] | None = None) -> None:
            content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            for name, value in (headers or {}).items():
                self.send_header(name, value)
            self.end_headers()
            self.wfile.write(content)

    server = LitigationHTTPServer(("127.0.0.1", port), Handler)
    server.database = database
    return server
