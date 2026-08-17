"""Flask adapter for the existing Yu Law litigation workbench."""

from __future__ import annotations

import csv
from datetime import date
import hashlib
import io
from pathlib import Path
import secrets
import sys

from flask import Blueprint, Response, current_app, g, jsonify, request, send_from_directory, session


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
CASE_PACKAGE_ROOT = REPOSITORY_ROOT / "workbuddy-pilot" / "case-management"
DASHBOARD_ROOT = CASE_PACKAGE_ROOT / "dashboard"
if str(CASE_PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(CASE_PACKAGE_ROOT))

from case_manager.database import LitigationDatabase  # noqa: E402
from case_manager.reporting import build_dashboard, build_weekly_report, save_weekly_report  # noqa: E402


litigation = Blueprint("litigation", __name__)

CASE_FIELDS = {
    "title", "caseNumber", "caseType", "procedureStage", "cause", "ourRole",
    "institution", "adjudicator", "amount", "riskLevel", "riskReason", "status",
    "nextAction", "tags", "notes", "leadLawyer", "handlingLawyer", "reviewLawyer",
}
DEADLINE_FIELDS = {"caseId", "deadlineType", "title", "dueAt", "reminderLevel", "status", "completedAt", "notes"}
TASK_FIELDS = {"caseId", "title", "owner", "dueAt", "priority", "status", "source", "workbuddyTodoId", "syncState", "notes"}
DOCUMENT_FIELDS = {"caseId", "documentType", "title", "status", "dueAt", "submissionMethod", "notes"}


def _database() -> LitigationDatabase:
    if "litigation_database" not in g:
        root = Path(current_app.config["CASE_DATA_ROOT"])
        g.litigation_database = LitigationDatabase(root)
    return g.litigation_database


@litigation.teardown_request
def close_database(_error=None) -> None:
    database = g.pop("litigation_database", None)
    if database is not None:
        database.close()


def _payload() -> dict:
    value = request.get_json(silent=True)
    if not isinstance(value, dict):
        raise ValueError("请求必须是 JSON 对象")
    return value


def _validated(payload: dict, allowed: set[str]) -> tuple[dict, str]:
    unknown = set(payload) - allowed - {"actor"}
    if unknown or not (set(payload) & allowed):
        raise ValueError("请求字段不完整或包含未知字段")
    actor = payload.get("actor", "虞律团队用户")
    if not isinstance(actor, str) or not actor.strip():
        raise ValueError("操作人不能为空")
    return {key: value for key, value in payload.items() if key in allowed}, actor.strip()


def _password_matches(value: str) -> bool:
    expected = current_app.config.get("AUTH_PASSWORD_HASH", "")
    actual = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return bool(expected and secrets.compare_digest(actual, expected))


@litigation.get("/cases/")
def cases_dashboard():
    return send_from_directory(DASHBOARD_ROOT, "index.html")


@litigation.get("/styles.css")
def cases_styles():
    return send_from_directory(DASHBOARD_ROOT, "styles.css")


@litigation.get("/app.js")
def cases_script():
    return send_from_directory(DASHBOARD_ROOT, "app.js")


@litigation.get("/api/session")
def case_session():
    return jsonify(authenticated=bool(session.get("authenticated")))


@litigation.post("/api/login")
def case_login():
    try:
        payload = _payload()
    except ValueError as error:
        return jsonify(error=str(error)), 400
    password = payload.get("password")
    if not isinstance(password, str) or not _password_matches(password):
        return jsonify(error="密码错误"), 401
    session.clear()
    session["authenticated"] = True
    return jsonify(ok=True)


@litigation.post("/api/logout")
def case_logout():
    session.clear()
    return jsonify(ok=True)


@litigation.get("/api/dashboard")
def case_dashboard_data():
    try:
        current = date.fromisoformat(request.args.get("today", date.today().isoformat()))
        return jsonify(build_dashboard(_database(), today=current))
    except ValueError as error:
        return jsonify(error=str(error)), 400


@litigation.get("/api/cases")
def list_cases():
    records = _database().list_cases(include_closed=request.args.get("includeClosed", "false").lower() == "true")
    query = request.args.get("q", "").strip().casefold()
    if query:
        def matches(item: dict) -> bool:
            values = [
                item.get("title", ""), item.get("caseNumber", ""), item.get("institution", ""),
                item.get("adjudicator", ""), item.get("cause", ""), item.get("ourRole", ""),
                item.get("notes", ""), item.get("leadLawyer", ""), item.get("handlingLawyer", ""),
                item.get("reviewLawyer", ""), *item.get("tags", []),
            ]
            return any(query in str(value).casefold() for value in values)
        records = [record for record in records if matches(record)]
    return jsonify(records)


@litigation.get("/api/cases/<case_id>")
def get_case(case_id: str):
    try:
        return jsonify(_database().get_case(case_id))
    except ValueError as error:
        return jsonify(error=str(error)), 404


@litigation.get("/api/deadlines")
def list_deadlines():
    return jsonify(_database().list_deadlines(request.args.get("caseId")))


@litigation.get("/api/tasks")
def list_tasks():
    return jsonify(_database().list_tasks(request.args.get("caseId")))


@litigation.get("/api/documents")
def list_documents():
    return jsonify(_database().list_documents(request.args.get("caseId")))


@litigation.get("/api/followups")
def list_followups():
    return jsonify(_database().list_followups(request.args.get("caseId")))


@litigation.get("/api/weekly-report")
def weekly_report():
    week = request.args.get("week", date.today().strftime("%G-W%V"))
    try:
        return jsonify(build_weekly_report(_database(), week=week))
    except ValueError as error:
        return jsonify(error=str(error)), 400


def _create_record(kind: str):
    database = _database()
    definitions = {
        "cases": (CASE_FIELDS, database.create_case),
        "deadlines": (DEADLINE_FIELDS, database.create_deadline),
        "tasks": (TASK_FIELDS, database.create_task),
        "documents": (DOCUMENT_FIELDS, database.create_document),
    }
    try:
        allowed, creator = definitions[kind]
        data, actor = _validated(_payload(), allowed)
        return jsonify(creator(data, actor=actor)), 201
    except (ValueError, KeyError) as error:
        return jsonify(error=str(error)), 400


@litigation.post("/api/cases")
def create_case():
    return _create_record("cases")


@litigation.post("/api/deadlines")
def create_deadline():
    return _create_record("deadlines")


@litigation.post("/api/tasks")
def create_task():
    return _create_record("tasks")


@litigation.post("/api/documents")
def create_document():
    return _create_record("documents")


@litigation.post("/api/weekly-report")
def create_weekly_report():
    try:
        return jsonify(save_weekly_report(_database(), _payload())), 201
    except (ValueError, KeyError) as error:
        return jsonify(error=str(error)), 400


def _update_record(kind: str, record_id: str):
    database = _database()
    definitions = {
        "cases": (CASE_FIELDS, database.update_case),
        "deadlines": (DEADLINE_FIELDS, database.update_deadline),
        "tasks": (TASK_FIELDS, database.update_task),
        "documents": (DOCUMENT_FIELDS, database.update_document),
    }
    try:
        allowed, updater = definitions[kind]
        data, actor = _validated(_payload(), allowed)
        return jsonify(updater(record_id, data, actor=actor))
    except (ValueError, KeyError) as error:
        return jsonify(error=str(error)), 400


@litigation.patch("/api/cases/<record_id>")
def update_case(record_id: str):
    return _update_record("cases", record_id)


@litigation.patch("/api/deadlines/<record_id>")
def update_deadline(record_id: str):
    return _update_record("deadlines", record_id)


@litigation.patch("/api/tasks/<record_id>")
def update_task(record_id: str):
    return _update_record("tasks", record_id)


@litigation.patch("/api/documents/<record_id>")
def update_document(record_id: str):
    return _update_record("documents", record_id)


@litigation.get("/api/export/<dataset>.csv")
def export_csv(dataset: str):
    database = _database()
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
        return jsonify(error="导出类型不存在"), 404
    records, columns = sources[dataset]
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(columns), extrasaction="ignore")
    writer.writerow(columns)
    writer.writerows(records)
    content = "\ufeff" + buffer.getvalue()
    return Response(
        content,
        content_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{dataset}.csv"'},
    )


def register_litigation(app) -> None:
    app.register_blueprint(litigation)
