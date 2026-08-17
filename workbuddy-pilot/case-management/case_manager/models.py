from __future__ import annotations

MATTER_STAGES = ("待收件", "材料已确认", "进行中", "待律师复核", "已批准", "已归档")

REQUIRED_MATTER_FIELDS = {
    "id",
    "title",
    "client",
    "caseType",
    "stage",
    "leadLawyer",
    "handlingLawyer",
    "reviewLawyer",
    "members",
    "priority",
    "openedAt",
    "nextDeadline",
    "tags",
    "confidentiality",
    "revision",
}


def validate_matter(record: dict) -> None:
    missing = sorted(REQUIRED_MATTER_FIELDS - record.keys())
    if missing:
        raise ValueError(f"案件缺少字段：{', '.join(missing)}")
    if record["stage"] not in MATTER_STAGES:
        raise ValueError(f"非法案件阶段：{record['stage']}")
