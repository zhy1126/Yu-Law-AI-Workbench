from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
import re

from .models import MATTER_STAGES
from .store import JsonStore

ALLOWED_CHANGE_TYPES = {
    "matter.update_stage",
    "matter.update_deadline",
    "task.create",
    "task.update_status",
}


class ProposalConflict(RuntimeError):
    pass


def index_documents(matter_dir: Path, project_root: Path) -> list[dict]:
    root = project_root.resolve()
    matter = matter_dir.resolve()
    if matter != root and root not in matter.parents:
        raise ValueError("案件目录必须位于项目内")
    documents = matter / "documents"
    if not documents.is_dir():
        return []

    records: list[dict] = []
    for path in sorted(documents.iterdir(), key=lambda item: item.name.casefold()):
        if not path.is_file() or path.name.startswith((".", "~$")):
            continue
        resolved = path.resolve()
        if root not in resolved.parents:
            raise ValueError("资料路径超出项目目录")
        suffix = path.suffix.lower()
        if suffix in {".doc", ".docx", ".pdf"}:
            category = "正式文件"
        elif suffix in {".md", ".txt"}:
            category = "工作记录"
        elif suffix in {".xls", ".xlsx", ".csv"}:
            category = "数据表"
        else:
            category = "其他资料"
        match = re.search(r"(?i)(?:^|[-_])v(\d+)(?=\.|[-_]|$)", path.name)
        records.append(
            {
                "name": path.name,
                "category": category,
                "version": f"v{match.group(1)}" if match else "",
                "path": path.relative_to(root).as_posix(),
                "size": path.stat().st_size,
                "updatedAt": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
            }
        )
    return records


def build_weekly_digest(
    matters: list[dict],
    tasks: list[dict],
    *,
    today: date,
    horizon_days: int = 14,
) -> dict:
    matter_by_id = {item["id"]: item for item in matters}
    deadline_risks: list[dict] = []
    material_gaps: list[dict] = []
    for matter in matters:
        if matter["stage"] in {"已批准", "已归档"}:
            continue
        deadline = date.fromisoformat(matter["nextDeadline"])
        days_left = (deadline - today).days
        if days_left <= horizon_days:
            deadline_risks.append(
                {
                    "matterId": matter["id"],
                    "title": matter["title"],
                    "deadline": deadline.isoformat(),
                    "daysLeft": days_left,
                    "priority": matter["priority"],
                }
            )
        if matter.get("materialGaps"):
            material_gaps.append(
                {
                    "matterId": matter["id"],
                    "title": matter["title"],
                    "items": list(matter["materialGaps"]),
                }
            )

    active_tasks = [item for item in tasks if item["status"] != "已完成"]
    overdue = [item for item in active_tasks if date.fromisoformat(item["dueAt"]) < today]
    pending_review = [item for item in active_tasks if item["status"] == "待复核"]
    needs_alignment = [
        {
            "taskId": item["id"],
            "matterId": item["matterId"],
            "matterTitle": matter_by_id.get(item["matterId"], {}).get("title", "未知案件"),
            "reason": "负责人缺失",
        }
        for item in active_tasks
        if not item.get("owner")
    ]

    deadline_risks.sort(key=lambda item: (item["deadline"], item["matterId"]))
    overdue.sort(key=lambda item: (item["dueAt"], item["id"]))
    pending_review.sort(key=lambda item: (item["dueAt"], item["id"]))
    return {
        "generatedFor": today.isoformat(),
        "deadlineRisks": deadline_risks,
        "overdueTasks": overdue,
        "pendingReview": pending_review,
        "materialGaps": material_gaps,
        "needsAlignment": needs_alignment,
    }


def create_proposal(store: JsonStore, *, meeting_id: str, changes: list[dict]) -> dict:
    proposals = store.read("proposals")
    proposal_id = f"P-{meeting_id}"
    existing = next((item for item in proposals if item["id"] == proposal_id), None)
    if existing:
        return existing
    if not changes:
        raise ValueError("拟变更不能为空")
    seen_ids: set[str] = set()
    for change in changes:
        if change.get("type") not in ALLOWED_CHANGE_TYPES:
            raise ValueError(f"不允许的变更类型：{change.get('type', '')}")
        if not change.get("id") or change["id"] in seen_ids:
            raise ValueError("拟变更编号缺失或重复")
        if not change.get("matterId"):
            raise ValueError("拟变更缺少案件编号")
        seen_ids.add(change["id"])

    proposal = {
        "id": proposal_id,
        "meetingId": meeting_id,
        "baseRevision": store.revision + 1,
        "status": "待确认",
        "requiresHumanConfirmation": True,
        "changes": changes,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    proposals.append(proposal)
    store.write("proposals", proposals, event="proposal.created")
    return proposal


def apply_proposal(
    store: JsonStore,
    proposal_id: str,
    accepted_change_ids: list[str],
    *,
    actor: str,
) -> dict:
    proposals = store.read("proposals")
    proposal = next((item for item in proposals if item["id"] == proposal_id), None)
    if proposal is None:
        raise ValueError("拟变更不存在")
    if proposal["status"] == "已写回":
        return {"applied": proposal["acceptedChangeIds"], "revision": proposal["appliedRevision"]}
    if store.revision != proposal["baseRevision"]:
        raise ProposalConflict("数据已更新，请重新生成拟变更")
    if not actor.strip():
        raise ValueError("确认人不能为空")

    accepted = set(accepted_change_ids)
    known = {item["id"] for item in proposal["changes"]}
    accepted &= known
    if not accepted:
        raise ValueError("没有可执行的已确认变更")

    matters = store.read("matters")
    tasks = store.read("tasks")
    matter_by_id = {item["id"]: item for item in matters}
    tasks_changed = False
    matters_changed = False
    for change in proposal["changes"]:
        if change["id"] not in accepted:
            continue
        matter = matter_by_id.get(change["matterId"])
        if matter is None:
            raise ValueError(f"案件不存在：{change['matterId']}")
        if change["type"] == "task.create":
            after = change["after"]
            next_id = max((int(item["id"].split("-")[-1]) for item in tasks), default=0) + 1
            tasks.append(
                {
                    "id": f"TASK-{next_id:03d}",
                    "matterId": change["matterId"],
                    "title": after["title"],
                    "owner": after.get("owner", ""),
                    "reviewer": after.get("reviewer", matter["reviewLawyer"]),
                    "dueAt": after["dueAt"],
                    "status": "待办",
                    "source": "周会",
                    "requiresConfirmation": False,
                    "workbuddyTodoId": "",
                    "syncState": "待同步WorkBuddy",
                }
            )
            tasks_changed = True
        elif change["type"] == "task.update_status":
            task = next((item for item in tasks if item["id"] == change.get("taskId")), None)
            if task is None:
                raise ValueError("任务不存在")
            task["status"] = change["after"]
            task["syncState"] = "待同步WorkBuddy"
            tasks_changed = True
        elif change["type"] == "matter.update_stage":
            if change["after"] not in MATTER_STAGES:
                raise ValueError("非法案件阶段")
            matter["stage"] = change["after"]
            matter["revision"] += 1
            matters_changed = True
        elif change["type"] == "matter.update_deadline":
            date.fromisoformat(change["after"])
            matter["nextDeadline"] = change["after"]
            matter["revision"] += 1
            matters_changed = True

    if tasks_changed:
        store.write("tasks", tasks, event="proposal.tasks_applied", actor=actor)
    if matters_changed:
        store.write("matters", matters, event="proposal.matters_applied", actor=actor)

    proposal["status"] = "已写回"
    proposal["acceptedChangeIds"] = sorted(accepted)
    proposal["rejectedChangeIds"] = sorted(known - accepted)
    proposal["confirmedBy"] = actor
    proposal["confirmedAt"] = datetime.now(timezone.utc).isoformat()
    proposal["appliedRevision"] = store.revision + 1
    revision = store.write("proposals", proposals, event="proposal.applied", actor=actor)
    return {"applied": sorted(accepted), "revision": revision}
