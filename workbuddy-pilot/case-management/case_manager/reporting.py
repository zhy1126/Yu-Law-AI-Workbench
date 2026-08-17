from __future__ import annotations

from datetime import date, datetime, timedelta

from .database import LitigationDatabase


OPEN_DEADLINE_STATUSES = {"未完成", "延期"}
OPEN_TASK_STATUSES = {"未开始", "进行中", "受阻", "待律师复核", "延期"}


def _day(value: str | None) -> date | None:
    if not value:
        return None
    return datetime.fromisoformat(value).date()


def _case_index(db: LitigationDatabase) -> dict[str, dict]:
    return {item["id"]: item for item in db.list_cases(include_closed=True)}


def _with_case(item: dict, cases: dict[str, dict], *, item_type: str) -> dict:
    case = cases.get(item["caseId"], {})
    return {
        **item,
        "itemType": item_type,
        "caseTitle": case.get("title", "未知案件"),
        "caseNumber": case.get("caseNumber", ""),
    }


def build_dashboard(db: LitigationDatabase, *, today: date | None = None) -> dict:
    current = today or date.today()
    cases = _case_index(db)
    deadlines = [
        _with_case(item, cases, item_type="期限")
        for item in db.list_deadlines()
        if item["status"] in OPEN_DEADLINE_STATUSES
    ]
    tasks = [
        _with_case(item, cases, item_type="待办")
        for item in db.list_tasks()
        if item["status"] in OPEN_TASK_STATUSES and item.get("dueAt")
    ]
    active_items = deadlines + tasks

    def days_left(item: dict) -> int:
        due = _day(item.get("dueAt"))
        return (due - current).days if due else 999999

    counts = {
        "overdue": sum(days_left(item) < 0 for item in active_items),
        "today": sum(days_left(item) == 0 for item in active_items),
        "next3Days": sum(1 <= days_left(item) <= 3 for item in active_items),
        "next7Days": sum(1 <= days_left(item) <= 7 for item in active_items),
        "preservation": sum(
            item["itemType"] == "期限"
            and item.get("deadlineType") in {"保全", "续封"}
            and 0 <= days_left(item) <= 60
            for item in active_items
        ),
    }
    emergency = sorted(
        [item for item in active_items if days_left(item) <= 3],
        key=lambda item: (item.get("dueAt") or "", item["id"]),
    )
    hearings = sorted(
        [
            item
            for item in deadlines
            if item.get("deadlineType") == "开庭" and 0 <= days_left(item) <= 30
        ],
        key=lambda item: item["dueAt"],
    )
    preservation = sorted(
        [
            item
            for item in deadlines
            if item.get("deadlineType") in {"保全", "续封"}
            and 0 <= days_left(item) <= 60
        ],
        key=lambda item: item["dueAt"],
    )
    return {
        "dataVersion": db.data_version,
        "generatedFor": current.isoformat(),
        "counts": counts,
        "emergencyItems": emergency,
        "upcomingHearings": hearings,
        "preservationItems": preservation,
        "caseCount": len([item for item in cases.values() if item["status"] != "已结案"]),
        "deadlineCount": len(deadlines),
        "taskCount": len([item for item in db.list_tasks() if item["status"] in OPEN_TASK_STATUSES]),
        "documentCount": len(db.list_documents()),
    }


def _iso_week_range(week: str) -> tuple[date, date]:
    try:
        year_text, week_text = week.split("-W", 1)
        monday = date.fromisocalendar(int(year_text), int(week_text), 1)
    except (ValueError, TypeError) as error:
        raise ValueError("周次格式必须为 YYYY-Www") from error
    return monday, monday + timedelta(days=6)


def build_weekly_report(db: LitigationDatabase, *, week: str) -> dict:
    monday, sunday = _iso_week_range(week)
    cases = _case_index(db)
    tasks = [_with_case(item, cases, item_type="待办") for item in db.list_tasks()]
    deadlines = [_with_case(item, cases, item_type="期限") for item in db.list_deadlines()]

    def due_between(item: dict, start: date, end: date) -> bool:
        due = _day(item.get("dueAt"))
        return bool(due and start <= due <= end)

    sections = {
        "progress": [item for item in tasks if item["status"] == "已完成" and due_between(item, monday, sunday)],
        "deadlineRisks": [
            item
            for item in deadlines
            if item["status"] in OPEN_DEADLINE_STATUSES
            and _day(item.get("dueAt"))
            and _day(item.get("dueAt")) <= sunday + timedelta(days=7)
        ],
        "blocked": [item for item in tasks if item["status"] in {"受阻", "延期"}],
        "pendingReview": [item for item in tasks if item["status"] == "待律师复核"],
        "nextWeek": [
            item
            for item in tasks
            if item["status"] in OPEN_TASK_STATUSES
            and due_between(item, sunday + timedelta(days=1), sunday + timedelta(days=7))
        ],
    }
    for items in sections.values():
        items.sort(key=lambda item: (item.get("dueAt") or "", item["id"]))
    snapshot = db.get_weekly_report_snapshot(week)
    return {
        "week": week,
        "sourceVersion": db.data_version,
        "sections": sections,
        "hasUpdates": bool(snapshot and snapshot["sourceVersion"] != db.data_version),
        "saved": snapshot,
    }


def save_weekly_report(db: LitigationDatabase, report: dict) -> dict:
    required = {"week", "sourceVersion", "sections"}
    if not required.issubset(report):
        raise ValueError("周报字段不完整")
    if report["sourceVersion"] != db.data_version:
        raise ValueError("案件数据已更新，请重新生成周报")
    return db.save_weekly_report_snapshot(report)
