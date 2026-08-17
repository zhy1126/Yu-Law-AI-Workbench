from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import sys

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from case_manager.database import LitigationDatabase
from case_manager.reporting import build_dashboard, build_weekly_report


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description="诉讼工作台本地命令入口")
    command.add_argument("--root", type=Path, default=PACKAGE_ROOT)
    sub = command.add_subparsers(dest="command", required=True)

    dashboard = sub.add_parser("dashboard")
    dashboard.add_argument("--today", default=date.today().isoformat())
    report = sub.add_parser("weekly-report")
    report.add_argument("--week", required=True)
    sub.add_parser("list-cases")

    create_task = sub.add_parser("create-task")
    create_task.add_argument("--case-id", required=True)
    create_task.add_argument("--title", required=True)
    create_task.add_argument("--owner", default="")
    create_task.add_argument("--due-at", default="")
    create_task.add_argument("--priority", default="中")
    create_task.add_argument("--actor", default="WorkBuddy")

    update_task = sub.add_parser("update-task")
    update_task.add_argument("--task-id", required=True)
    update_task.add_argument("--status", required=True)
    update_task.add_argument("--actor", required=True)
    return command


def main() -> None:
    args = parser().parse_args()
    db = LitigationDatabase(args.root)
    try:
        db.migrate_legacy_json()
        if args.command == "dashboard":
            result = build_dashboard(db, today=date.fromisoformat(args.today))
        elif args.command == "weekly-report":
            result = build_weekly_report(db, week=args.week)
        elif args.command == "list-cases":
            result = db.list_cases(include_closed=True)
        elif args.command == "create-task":
            result = db.create_task(
                {
                    "caseId": args.case_id,
                    "title": args.title,
                    "owner": args.owner,
                    "dueAt": args.due_at or None,
                    "priority": args.priority,
                    "status": "未开始",
                    "source": "WorkBuddy",
                    "syncState": "已同步",
                    "notes": "",
                },
                actor=args.actor,
            )
        elif args.command == "update-task":
            result = db.update_task(args.task_id, {"status": args.status}, actor=args.actor)
        else:
            raise ValueError("未知命令")
        print(json.dumps(result, ensure_ascii=False))
    except (ValueError, OSError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False))
        raise SystemExit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
