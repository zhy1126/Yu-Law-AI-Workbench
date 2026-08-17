from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import uuid


CASE_FIELDS = {
    "title": "title",
    "caseNumber": "case_number",
    "caseType": "case_type",
    "procedureStage": "procedure_stage",
    "cause": "cause",
    "ourRole": "our_role",
    "institution": "institution",
    "adjudicator": "adjudicator",
    "amount": "amount",
    "riskLevel": "risk_level",
    "riskReason": "risk_reason",
    "status": "status",
    "nextAction": "next_action",
    "notes": "notes",
    "leadLawyer": "lead_lawyer",
    "handlingLawyer": "handling_lawyer",
    "reviewLawyer": "review_lawyer",
}

DEADLINE_FIELDS = {
    "caseId": "case_id",
    "deadlineType": "deadline_type",
    "title": "title",
    "dueAt": "due_at",
    "reminderLevel": "reminder_level",
    "status": "status",
    "completedAt": "completed_at",
    "notes": "notes",
}

TASK_FIELDS = {
    "caseId": "case_id",
    "title": "title",
    "owner": "owner",
    "dueAt": "due_at",
    "priority": "priority",
    "status": "status",
    "source": "source",
    "workbuddyTodoId": "workbuddy_todo_id",
    "syncState": "sync_state",
    "notes": "notes",
}

DOCUMENT_FIELDS = {
    "caseId": "case_id",
    "documentType": "document_type",
    "title": "title",
    "status": "status",
    "dueAt": "due_at",
    "submissionMethod": "submission_method",
    "notes": "notes",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


class LitigationDatabase:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.data_dir = self.root / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.data_dir / "litigation.db"
        self.connection = sqlite3.connect(self.path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self._create_schema()

    def close(self) -> None:
        self.connection.close()

    def _create_schema(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS cases (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                case_number TEXT NOT NULL DEFAULT '',
                case_type TEXT NOT NULL DEFAULT '诉讼',
                procedure_stage TEXT NOT NULL DEFAULT '立案前',
                cause TEXT NOT NULL DEFAULT '',
                our_role TEXT NOT NULL DEFAULT '',
                institution TEXT NOT NULL DEFAULT '',
                adjudicator TEXT NOT NULL DEFAULT '',
                amount REAL,
                risk_level TEXT NOT NULL DEFAULT '中',
                risk_reason TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT '进行中',
                next_action TEXT NOT NULL DEFAULT '',
                tags_json TEXT NOT NULL DEFAULT '[]',
                notes TEXT NOT NULL DEFAULT '',
                lead_lawyer TEXT NOT NULL DEFAULT '',
                handling_lawyer TEXT NOT NULL DEFAULT '',
                review_lawyer TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS parties (
                id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
                role TEXT NOT NULL,
                name TEXT NOT NULL,
                contact_name TEXT NOT NULL DEFAULT '',
                phone TEXT NOT NULL DEFAULT '',
                wechat TEXT NOT NULL DEFAULT '',
                lawyer TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS deadlines (
                id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
                deadline_type TEXT NOT NULL,
                title TEXT NOT NULL,
                due_at TEXT NOT NULL,
                reminder_level TEXT NOT NULL DEFAULT '重要',
                status TEXT NOT NULL DEFAULT '未完成',
                completed_at TEXT,
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                owner TEXT NOT NULL DEFAULT '',
                due_at TEXT,
                priority TEXT NOT NULL DEFAULT '中',
                status TEXT NOT NULL DEFAULT '未开始',
                source TEXT NOT NULL DEFAULT '',
                workbuddy_todo_id TEXT NOT NULL DEFAULT '',
                sync_state TEXT NOT NULL DEFAULT '仅本地',
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
                document_type TEXT NOT NULL,
                title TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT '未起草',
                due_at TEXT,
                submission_method TEXT NOT NULL DEFAULT '线上',
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS followups (
                id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
                occurred_at TEXT NOT NULL,
                target TEXT NOT NULL,
                method TEXT NOT NULL,
                content TEXT NOT NULL,
                author TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS weekly_reports (
                week TEXT PRIMARY KEY,
                source_version INTEGER NOT NULL,
                content_json TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT '草稿',
                generated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event TEXT NOT NULL,
                actor TEXT NOT NULL,
                object_id TEXT NOT NULL,
                summary TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_deadlines_due_at ON deadlines(due_at);
            CREATE INDEX IF NOT EXISTS idx_tasks_due_at ON tasks(due_at);
            CREATE INDEX IF NOT EXISTS idx_cases_status ON cases(status);
            """
        )
        self.connection.execute(
            "INSERT OR IGNORE INTO settings(key, value) VALUES('data_version', '0')"
        )
        default_hash = hashlib.sha256("yulaw-demo".encode("utf-8")).hexdigest()
        self.connection.execute(
            "INSERT OR IGNORE INTO settings(key, value) VALUES('password_hash', ?)",
            (default_hash,),
        )
        self.connection.commit()

    @property
    def data_version(self) -> int:
        row = self.connection.execute(
            "SELECT value FROM settings WHERE key = 'data_version'"
        ).fetchone()
        return int(row["value"])

    def verify_password(self, value: str) -> bool:
        digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
        row = self.connection.execute(
            "SELECT value FROM settings WHERE key = 'password_hash'"
        ).fetchone()
        return bool(row and row["value"] == digest)

    def _bump(self, *, event: str, actor: str, object_id: str, summary: str) -> None:
        version = self.data_version + 1
        self.connection.execute(
            "UPDATE settings SET value = ? WHERE key = 'data_version'", (str(version),)
        )
        self.connection.execute(
            "INSERT INTO activity_log(event, actor, object_id, summary, created_at) VALUES(?,?,?,?,?)",
            (event, actor, object_id, summary, _now()),
        )

    def _require_case(self, case_id: str) -> None:
        if not self.connection.execute(
            "SELECT 1 FROM cases WHERE id = ?", (case_id,)
        ).fetchone():
            raise ValueError(f"案件不存在：{case_id}")

    @staticmethod
    def _case_from_row(row: sqlite3.Row) -> dict:
        return {
            "id": row["id"],
            "title": row["title"],
            "caseNumber": row["case_number"],
            "caseType": row["case_type"],
            "procedureStage": row["procedure_stage"],
            "cause": row["cause"],
            "ourRole": row["our_role"],
            "institution": row["institution"],
            "adjudicator": row["adjudicator"],
            "amount": row["amount"],
            "riskLevel": row["risk_level"],
            "riskReason": row["risk_reason"],
            "status": row["status"],
            "nextAction": row["next_action"],
            "tags": json.loads(row["tags_json"]),
            "notes": row["notes"],
            "leadLawyer": row["lead_lawyer"],
            "handlingLawyer": row["handling_lawyer"],
            "reviewLawyer": row["review_lawyer"],
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"],
        }

    @staticmethod
    def _record_from_row(row: sqlite3.Row, fields: dict[str, str]) -> dict:
        result = {"id": row["id"]}
        for public, column in fields.items():
            result[public] = row[column]
        if "created_at" in row.keys():
            result["createdAt"] = row["created_at"]
            result["updatedAt"] = row["updated_at"]
        return result

    def list_cases(self, *, include_closed: bool = False) -> list[dict]:
        sql = "SELECT * FROM cases"
        params: tuple = ()
        if not include_closed:
            sql += " WHERE status != ?"
            params = ("已结案",)
        sql += " ORDER BY updated_at DESC, id"
        return [self._case_from_row(row) for row in self.connection.execute(sql, params)]

    def get_case(self, case_id: str) -> dict:
        row = self.connection.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
        if row is None:
            raise ValueError(f"案件不存在：{case_id}")
        result = self._case_from_row(row)
        result["deadlines"] = self.list_deadlines(case_id)
        result["tasks"] = self.list_tasks(case_id)
        result["documents"] = self.list_documents(case_id)
        result["followups"] = self.list_followups(case_id)
        result["parties"] = [dict(item) for item in self.connection.execute("SELECT * FROM parties WHERE case_id = ? ORDER BY id", (case_id,))]
        return result

    def create_case(self, payload: dict, *, actor: str = "system") -> dict:
        if not str(payload.get("title", "")).strip():
            raise ValueError("案件名称不能为空")
        case_id = str(payload.get("id") or _new_id("CASE"))
        now = _now()
        values = {key: payload.get(key, "") for key in CASE_FIELDS}
        values.update(
            {
                "caseType": payload.get("caseType", "诉讼"),
                "procedureStage": payload.get("procedureStage", "立案前"),
                "riskLevel": payload.get("riskLevel", "中"),
                "status": payload.get("status", "进行中"),
                "amount": payload.get("amount"),
            }
        )
        columns = [CASE_FIELDS[key] for key in CASE_FIELDS]
        prepared = [values[key] for key in CASE_FIELDS]
        tags = payload.get("tags", [])
        with self.connection:
            self.connection.execute(
                f"INSERT INTO cases(id,{','.join(columns)},tags_json,created_at,updated_at) VALUES({','.join('?' for _ in range(len(columns)+4))})",
                [case_id, *prepared, json.dumps(tags, ensure_ascii=False), now, now],
            )
            self._bump(event="case.created", actor=actor, object_id=case_id, summary=values["title"])
        return self.get_case(case_id)

    def update_case(self, case_id: str, payload: dict, *, actor: str) -> dict:
        self._require_case(case_id)
        updates: list[str] = []
        values: list = []
        for key, column in CASE_FIELDS.items():
            if key in payload:
                updates.append(f"{column} = ?")
                values.append(payload[key])
        if "tags" in payload:
            updates.append("tags_json = ?")
            values.append(json.dumps(payload["tags"], ensure_ascii=False))
        if not updates:
            return self.get_case(case_id)
        updates.append("updated_at = ?")
        values.extend([_now(), case_id])
        with self.connection:
            self.connection.execute(f"UPDATE cases SET {', '.join(updates)} WHERE id = ?", values)
            self._bump(event="case.updated", actor=actor, object_id=case_id, summary="更新案件")
        return self.get_case(case_id)

    def _list_records(self, table: str, fields: dict[str, str], case_id: str | None) -> list[dict]:
        sql = f"SELECT * FROM {table}"
        params: tuple = ()
        if case_id:
            sql += " WHERE case_id = ?"
            params = (case_id,)
        order = "due_at, id" if table in {"deadlines", "tasks", "documents"} else "occurred_at DESC, id"
        sql += f" ORDER BY {order}"
        return [self._record_from_row(row, fields) for row in self.connection.execute(sql, params)]

    def list_deadlines(self, case_id: str | None = None) -> list[dict]:
        return self._list_records("deadlines", DEADLINE_FIELDS, case_id)

    def list_tasks(self, case_id: str | None = None) -> list[dict]:
        return self._list_records("tasks", TASK_FIELDS, case_id)

    def list_documents(self, case_id: str | None = None) -> list[dict]:
        return self._list_records("documents", DOCUMENT_FIELDS, case_id)

    def list_followups(self, case_id: str | None = None) -> list[dict]:
        sql = "SELECT * FROM followups"
        params: tuple = ()
        if case_id:
            sql += " WHERE case_id = ?"
            params = (case_id,)
        sql += " ORDER BY occurred_at DESC, id"
        return [dict(row) for row in self.connection.execute(sql, params)]

    def _create_related(
        self,
        *,
        table: str,
        prefix: str,
        fields: dict[str, str],
        payload: dict,
        required_title: str,
        event: str,
        actor: str,
    ) -> dict:
        case_id = str(payload.get("caseId", ""))
        self._require_case(case_id)
        if not str(payload.get(required_title, "")).strip():
            raise ValueError("事项名称不能为空")
        record_id = str(payload.get("id") or _new_id(prefix))
        now = _now()
        columns = [fields[key] for key in fields]
        prepared = [payload.get(key) for key in fields]
        defaults = {
            "reminderLevel": "重要",
            "status": "未完成" if table == "deadlines" else ("未开始" if table == "tasks" else "未起草"),
            "priority": "中",
            "source": "本地录入",
            "syncState": "仅本地",
            "notes": "",
            "owner": "",
            "workbuddyTodoId": "",
            "submissionMethod": "线上",
            "completedAt": None,
            "dueAt": None,
        }
        prepared = [defaults.get(key) if value is None else value for key, value in zip(fields, prepared)]
        with self.connection:
            self.connection.execute(
                f"INSERT INTO {table}(id,{','.join(columns)},created_at,updated_at) VALUES({','.join('?' for _ in range(len(columns)+3))})",
                [record_id, *prepared, now, now],
            )
            self._bump(event=event, actor=actor, object_id=record_id, summary=str(payload.get(required_title, "")))
        row = self.connection.execute(f"SELECT * FROM {table} WHERE id = ?", (record_id,)).fetchone()
        return self._record_from_row(row, fields)

    def create_deadline(self, payload: dict, *, actor: str = "system") -> dict:
        if not payload.get("dueAt"):
            raise ValueError("期限时间不能为空")
        return self._create_related(table="deadlines", prefix="DL", fields=DEADLINE_FIELDS, payload=payload, required_title="title", event="deadline.created", actor=actor)

    def create_task(self, payload: dict, *, actor: str = "system") -> dict:
        return self._create_related(table="tasks", prefix="TASK", fields=TASK_FIELDS, payload=payload, required_title="title", event="task.created", actor=actor)

    def create_document(self, payload: dict, *, actor: str = "system") -> dict:
        return self._create_related(table="documents", prefix="DOC", fields=DOCUMENT_FIELDS, payload=payload, required_title="title", event="document.created", actor=actor)

    def _update_related(self, table: str, fields: dict[str, str], record_id: str, payload: dict, *, actor: str) -> dict:
        if not self.connection.execute(f"SELECT 1 FROM {table} WHERE id = ?", (record_id,)).fetchone():
            raise ValueError(f"记录不存在：{record_id}")
        updates: list[str] = []
        values: list = []
        for key, column in fields.items():
            if key in payload:
                updates.append(f"{column} = ?")
                values.append(payload[key])
        if not updates:
            row = self.connection.execute(f"SELECT * FROM {table} WHERE id = ?", (record_id,)).fetchone()
            return self._record_from_row(row, fields)
        updates.append("updated_at = ?")
        values.extend([_now(), record_id])
        with self.connection:
            self.connection.execute(f"UPDATE {table} SET {', '.join(updates)} WHERE id = ?", values)
            self._bump(event=f"{table[:-1]}.updated", actor=actor, object_id=record_id, summary=f"更新 {record_id}")
        row = self.connection.execute(f"SELECT * FROM {table} WHERE id = ?", (record_id,)).fetchone()
        return self._record_from_row(row, fields)

    def update_deadline(self, deadline_id: str, payload: dict, *, actor: str) -> dict:
        return self._update_related("deadlines", DEADLINE_FIELDS, deadline_id, payload, actor=actor)

    def update_task(self, task_id: str, payload: dict, *, actor: str) -> dict:
        return self._update_related("tasks", TASK_FIELDS, task_id, payload, actor=actor)

    def update_document(self, document_id: str, payload: dict, *, actor: str) -> dict:
        return self._update_related("documents", DOCUMENT_FIELDS, document_id, payload, actor=actor)

    def get_weekly_report_snapshot(self, week: str) -> dict | None:
        row = self.connection.execute(
            "SELECT * FROM weekly_reports WHERE week = ?", (week,)
        ).fetchone()
        if row is None:
            return None
        return {
            "week": row["week"],
            "sourceVersion": row["source_version"],
            "sections": json.loads(row["content_json"]),
            "status": row["status"],
            "generatedAt": row["generated_at"],
        }

    def save_weekly_report_snapshot(self, report: dict) -> dict:
        generated_at = _now()
        with self.connection:
            self.connection.execute(
                """INSERT INTO weekly_reports(week,source_version,content_json,status,generated_at)
                VALUES(?,?,?,?,?)
                ON CONFLICT(week) DO UPDATE SET
                    source_version = excluded.source_version,
                    content_json = excluded.content_json,
                    status = excluded.status,
                    generated_at = excluded.generated_at""",
                (
                    report["week"],
                    report["sourceVersion"],
                    json.dumps(report["sections"], ensure_ascii=False),
                    report.get("status", "草稿"),
                    generated_at,
                ),
            )
            self.connection.execute(
                "INSERT INTO activity_log(event, actor, object_id, summary, created_at) VALUES(?,?,?,?,?)",
                ("weekly_report.saved", "system", report["week"], "保存周报快照", generated_at),
            )
        return self.get_weekly_report_snapshot(report["week"])

    def list_activity(self, *, since: str | None = None) -> list[dict]:
        sql = "SELECT * FROM activity_log"
        params: tuple = ()
        if since:
            sql += " WHERE created_at >= ?"
            params = (since,)
        sql += " ORDER BY created_at DESC, id DESC"
        return [dict(row) for row in self.connection.execute(sql, params)]

    def migrate_legacy_json(self) -> dict[str, int]:
        marker = self.connection.execute(
            "SELECT value FROM settings WHERE key = 'legacy_migration_complete'"
        ).fetchone()
        if marker:
            return {"cases": 0, "tasks": 0, "deadlines": 0}

        def read(name: str) -> list[dict]:
            path = self.data_dir / f"{name}.json"
            if not path.is_file():
                return []
            value = json.loads(path.read_text(encoding="utf-8"))
            return value if isinstance(value, list) else []

        matters = read("matters")
        tasks = read("tasks")
        counts = {"cases": 0, "tasks": 0, "deadlines": 0}
        now = _now()
        with self.connection:
            for matter in matters:
                exists = self.connection.execute("SELECT 1 FROM cases WHERE id = ?", (matter.get("id"),)).fetchone()
                if exists:
                    continue
                self.connection.execute(
                    """INSERT INTO cases(
                        id,title,case_number,case_type,procedure_stage,cause,our_role,institution,
                        adjudicator,amount,risk_level,risk_reason,status,next_action,tags_json,notes,
                        lead_lawyer,handling_lawyer,review_lawyer,created_at,updated_at
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        matter["id"], matter["title"], "", "诉讼" if matter.get("caseType") != "PE/VC" else "仲裁",
                        "一审", matter.get("caseType", ""), "", "", "", None,
                        {"高": "高", "中": "中", "低": "低"}.get(matter.get("priority"), "中"),
                        "；".join(matter.get("materialGaps", [])),
                        "进行中" if matter.get("stage") != "已归档" else "已结案",
                        "", json.dumps(matter.get("tags", []), ensure_ascii=False), matter.get("client", ""),
                        matter.get("leadLawyer", ""), matter.get("handlingLawyer", ""), matter.get("reviewLawyer", ""),
                        matter.get("openedAt", now), now,
                    ),
                )
                counts["cases"] += 1
                if matter.get("nextDeadline"):
                    self.connection.execute(
                        "INSERT OR IGNORE INTO deadlines(id,case_id,deadline_type,title,due_at,reminder_level,status,completed_at,notes,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                        (f"DL-{matter['id']}", matter["id"], "其他", "下一关键期限", f"{matter['nextDeadline']}T18:00", "重要", "未完成", None, "从旧案件数据迁移", now, now),
                    )
                    counts["deadlines"] += 1
            for task in tasks:
                if not self.connection.execute("SELECT 1 FROM cases WHERE id = ?", (task.get("matterId"),)).fetchone():
                    continue
                if self.connection.execute("SELECT 1 FROM tasks WHERE id = ?", (task.get("id"),)).fetchone():
                    continue
                status_map = {"待办": "未开始", "待复核": "待律师复核", "已完成": "已完成"}
                self.connection.execute(
                    "INSERT INTO tasks(id,case_id,title,owner,due_at,priority,status,source,workbuddy_todo_id,sync_state,notes,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (task["id"], task["matterId"], task["title"], task.get("owner", ""), f"{task['dueAt']}T18:00" if task.get("dueAt") and "T" not in task["dueAt"] else task.get("dueAt"), "中", status_map.get(task.get("status"), task.get("status", "未开始")), task.get("source", "旧系统"), task.get("workbuddyTodoId", ""), task.get("syncState", "仅本地"), "", now, now),
                )
                counts["tasks"] += 1
            self.connection.execute(
                "INSERT INTO settings(key, value) VALUES('legacy_migration_complete', ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (now,),
            )
            if any(counts.values()):
                self._bump(event="legacy.migrated", actor="system", object_id="legacy-json", summary=json.dumps(counts, ensure_ascii=False))
        return counts
