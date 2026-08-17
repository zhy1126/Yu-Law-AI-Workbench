from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import shutil


def sync_case_management(source: Path, target: Path) -> dict:
    source = source.resolve()
    target = target.resolve()
    manifest_path = target / "pilot-manifest.json"
    if not manifest_path.is_file():
        raise ValueError("目标目录不是 WorkBuddy 法律工作流项目")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("project") != "虞律团队AI工作流试验":
        raise ValueError("目标目录不是 WorkBuddy 法律工作流项目")

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = target / "backups" / f"case-management-pre-sync-{stamp}"
    backup.mkdir(parents=True)
    for name in ("WORKBUDDY.md", "pilot-manifest.json", "case-management"):
        item = target / name
        if item.is_dir():
            shutil.copytree(item, backup / name)
        elif item.is_file():
            shutil.copy2(item, backup / name)

    incoming = source / "case-management"
    destination = target / "case-management"
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(incoming, destination, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "snapshots"))
    shutil.copy2(source / "WORKBUDDY.md", target / "WORKBUDDY.md")
    shutil.copy2(source / "pilot-manifest.json", target / "pilot-manifest.json")
    return {"ok": True, "backup": str(backup), "target": str(destination)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = sync_case_management(args.source, args.target)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False))
        raise SystemExit(1)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
