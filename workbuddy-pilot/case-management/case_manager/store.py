from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path

from .models import validate_matter

DATASETS = ("matters", "tasks", "meetings", "proposals", "activity-log")


class JsonStore:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.data_dir = self.root / "data"
        self.snapshot_dir = self.root / "snapshots"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        for name in DATASETS:
            path = self.data_dir / f"{name}.json"
            if not path.exists():
                self._atomic_write(path, [])
        meta = self.data_dir / "meta.json"
        if not meta.exists():
            self._atomic_write(meta, {"revision": 0})

    @property
    def revision(self) -> int:
        return int(self._read_json(self.data_dir / "meta.json")["revision"])

    def read(self, name: str) -> list[dict]:
        if name not in DATASETS:
            raise ValueError(f"未知数据集：{name}")
        value = self._read_json(self.data_dir / f"{name}.json")
        if not isinstance(value, list):
            raise ValueError(f"数据集格式无效：{name}")
        return value

    def write(self, name: str, records: list[dict], *, event: str, actor: str = "system") -> int:
        if name not in DATASETS or name == "activity-log":
            raise ValueError(f"不可直接写入数据集：{name}")
        if name == "matters":
            for record in records:
                validate_matter(record)
        self.snapshot(event)
        revision = self.revision + 1
        self._atomic_write(self.data_dir / f"{name}.json", records)
        self._atomic_write(self.data_dir / "meta.json", {"revision": revision})
        self.append_activity(event, actor=actor, summary=f"更新 {name}", object_id=name)
        return revision

    def snapshot(self, label: str) -> Path:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        path = self.snapshot_dir / f"{stamp}-{label.replace('/', '-')}.json"
        payload = {
            "revision": self.revision,
            "data": {name: self.read(name) for name in DATASETS},
        }
        self._atomic_write(path, payload)
        return path

    def append_activity(self, event: str, *, actor: str, summary: str, object_id: str = "") -> None:
        records = self.read("activity-log")
        records.append(
            {
                "event": event,
                "actor": actor,
                "summary": summary,
                "objectId": object_id,
                "createdAt": datetime.now(timezone.utc).isoformat(),
            }
        )
        self._atomic_write(self.data_dir / "activity-log.json", records)

    @staticmethod
    def _read_json(path: Path):
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _atomic_write(path: Path, value) -> None:
        temp = path.with_suffix(path.suffix + ".tmp")
        with temp.open("w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
