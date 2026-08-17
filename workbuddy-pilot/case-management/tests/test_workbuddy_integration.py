from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
WORKBUDDY_ROOT = PACKAGE_ROOT.parent
REPO_ROOT = WORKBUDDY_ROOT.parent
sys.path.insert(0, str(PACKAGE_ROOT))

from scripts.sync_to_workbuddy import sync_case_management


class WorkBuddyIntegrationTests(unittest.TestCase):
    def test_case_coordinator_expert_preloads_case_skill(self) -> None:
        expert_root = REPO_ROOT / "workbuddy-experts" / "yu-law-case-coordinator"
        plugin = json.loads(
            (expert_root / ".codebuddy-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        agent = (expert_root / "agents" / "yu-law-case-coordinator.md").read_text(encoding="utf-8")

        self.assertEqual(plugin["expertType"], "agent")
        self.assertEqual(plugin["categoryId"], "10-ProjectQuality")
        self.assertEqual(plugin["skills"], ["./skills/yu-law-case-management"])
        self.assertEqual(len(plugin["tags"]), 3)
        self.assertEqual(len(plugin["quickPrompts"]), 3)
        self.assertIn("skills: [yu-law-case-management]", agent)

    def test_global_skill_package_exposes_case_workbench_entry(self) -> None:
        skill_root = REPO_ROOT / "workbuddy-skills" / "yu-law-case-management"
        skill_text = (skill_root / "SKILL.md").read_text(encoding="utf-8")
        metadata = json.loads((skill_root / "_user_meta.json").read_text(encoding="utf-8"))
        agent_yaml = (skill_root / "agents" / "openai.yaml").read_text(encoding="utf-8")

        self.assertIn("name: yu-law-case-management", skill_text)
        self.assertIn("打开案件工作台", skill_text)
        self.assertEqual(metadata["slug"], "yu-law-case-management")
        self.assertIn("$yu-law-case-management", agent_yaml)

    def test_skill_documents_mvp_commands_and_manual_gate(self) -> None:
        text = (PACKAGE_ROOT / "skill" / "SKILL.md").read_text(encoding="utf-8")
        for phrase in ("打开案件工作台", "生成本周议程", "保存周会纪要", "律师确认"):
            self.assertIn(phrase, text)
        for forbidden in ("自动分享", "自动归档", "自动批准"):
            self.assertIn(forbidden, text)

    def test_project_manifest_registers_local_case_workbench(self) -> None:
        manifest = json.loads((WORKBUDDY_ROOT / "pilot-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["caseManagement"]["url"], "http://127.0.0.1:8765")
        self.assertEqual(manifest["caseManagement"]["writebackMode"], "律师确认后写回")

    def test_sync_creates_backup_and_preserves_existing_contract_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            (target / "skill").mkdir()
            (target / "skill" / "SKILL.md").write_text("existing contract skill", encoding="utf-8")
            (target / "WORKBUDDY.md").write_text("existing instructions", encoding="utf-8")
            (target / "pilot-manifest.json").write_text(
                json.dumps({"project": "虞律团队AI工作流试验"}, ensure_ascii=False),
                encoding="utf-8",
            )

            result = sync_case_management(WORKBUDDY_ROOT, target)

            self.assertTrue(result["ok"])
            self.assertTrue(Path(result["backup"]).is_dir())
            self.assertEqual((target / "skill" / "SKILL.md").read_text(encoding="utf-8"), "existing contract skill")
            self.assertTrue((target / "case-management" / "dashboard" / "index.html").is_file())

    def test_sync_rejects_unexpected_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            (target / "pilot-manifest.json").write_text('{"project": "其他项目"}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "目标目录不是 WorkBuddy 法律工作流项目"):
                sync_case_management(WORKBUDDY_ROOT, target)


if __name__ == "__main__":
    unittest.main()
