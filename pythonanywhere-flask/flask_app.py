"""Lightweight PythonAnywhere entry point for the Yu Law AI Workbench."""

from __future__ import annotations

import json
from pathlib import Path

from flask import Flask, abort, jsonify, render_template


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "tools.json"

categories = ["全部工具", "数据安全", "基础工作", "文书制作", "专业法律分析", "Anthropic Legal"]
status_labels = {
    "connected": "已接入",
    "local-skill": "本地 Skill",
    "installable": "可安装",
    "building": "建设中",
    "planned": "规划中",
}
business_stages = ["前期准备", "具体工作", "文书起草"]
workflow_levels = ["通用能力层", "专业法律工作层", "文书交付层"]
system_stages = ["发起任务", "权限确认", "资料读取 / 脱敏", "Skill 执行", "结果整理", "律师复核 / 归档"]


def _profile(level, business, system):
    return {"level": level, "businessStages": business, "systemStages": system}


source_to_review = ["资料读取 / 脱敏", "Skill 执行", "结果整理", "律师复核 / 归档"]
execution_to_review = ["Skill 执行", "结果整理", "律师复核 / 归档"]
workflow_profiles = {
    "local-legal-redaction": _profile("入口与保障层", business_stages, ["资料读取 / 脱敏", "律师复核 / 归档"]),
    "matter-workspace": _profile("入口与保障层", business_stages, ["权限确认", *source_to_review]),
    "cold-start-interview": _profile("通用能力层", ["前期准备"], ["发起任务", "权限确认"]),
    "basic-work-skills": _profile("通用能力层", ["前期准备", "具体工作"], source_to_review),
    "ai-tool-handoff": _profile("通用能力层", ["具体工作"], ["资料读取 / 脱敏", "Skill 执行", "律师复核 / 归档"]),
    "transaction-structure-planning": _profile("专业法律工作层", ["前期准备", "具体工作"], source_to_review),
    "pe-vc-financing-doc-review": _profile("专业法律工作层", ["具体工作"], source_to_review),
    "diligence-issue-extraction": _profile("专业法律工作层", ["具体工作"], source_to_review),
    "tabular-review": _profile("专业法律工作层", ["具体工作"], source_to_review),
    "material-contract-schedule": _profile("专业法律工作层", ["具体工作"], source_to_review),
    "closing-checklist": _profile("专业法律工作层", ["具体工作"], execution_to_review),
    "integration-management": _profile("专业法律工作层", ["具体工作"], execution_to_review),
    "entity-compliance": _profile("专业法律工作层", ["具体工作"], execution_to_review),
    "deal-team-summary": _profile("文书交付层", ["具体工作"], ["结果整理", "律师复核 / 归档"]),
    "legal-service-proposal": _profile("文书交付层", ["文书起草"], execution_to_review),
    "quotation-letter": _profile("文书交付层", ["文书起草"], execution_to_review),
    "tender-response": _profile("文书交付层", ["文书起草"], execution_to_review),
    "drafting-legal-service-contracts": _profile("文书交付层", ["文书起草"], execution_to_review),
    "board-minutes": _profile("文书交付层", ["文书起草"], execution_to_review),
    "written-consent": _profile("文书交付层", ["文书起草"], execution_to_review),
}


def load_tools(path: Path = DATA_FILE):
    """Load and minimally validate the standalone tool registry."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise RuntimeError("data/tools.json 必须是数组")

    required = {
        "id", "name", "category", "status", "summary", "version", "repository",
        "localUrl", "inputs", "outputs", "steps", "notice",
    }
    ids = set()
    for index, tool in enumerate(raw):
        if not isinstance(tool, dict) or set(tool) != required:
            raise RuntimeError(f"tools[{index}] 字段不完整")
        if not tool["id"] or tool["id"] in ids:
            raise RuntimeError(f"tools[{index}] id 无效或重复")
        if tool["category"] not in categories[1:]:
            raise RuntimeError(f"tools[{index}] category 不受支持")
        if tool["status"] not in status_labels:
            raise RuntimeError(f"tools[{index}] status 不受支持")
        ids.add(tool["id"])
    return raw


tools = load_tools()
tools_by_id = {tool["id"]: tool for tool in tools}

app = Flask(__name__)


@app.context_processor
def inject_shared_data():
    return {
        "status_labels": status_labels,
        "categories": categories,
        "business_stages": business_stages,
        "workflow_levels": workflow_levels,
        "system_stages": system_stages,
        "workflow_profiles": workflow_profiles,
    }


@app.get("/")
def index():
    counts = {category: sum(tool["category"] == category for tool in tools) for category in categories[1:]}
    counts["全部工具"] = len(tools)
    return render_template("index.html", tools=tools, counts=counts)


@app.get("/tools/<tool_id>")
def tool_detail(tool_id):
    tool = tools_by_id.get(tool_id)
    if tool is None:
        abort(404)
    return render_template("tool_detail.html", tool=tool)


@app.get("/health")
def health():
    return jsonify(status="ok", tools=len(tools))


@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
