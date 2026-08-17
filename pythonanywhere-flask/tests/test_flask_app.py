import hashlib
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from flask_app import app, categories, tools  # noqa: E402


class FlaskWorkbenchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config.update(TESTING=True)
        cls.client = app.test_client()

    def test_registry_contains_fifty_tools_and_expected_categories(self):
        self.assertEqual(len(tools), 50)
        self.assertEqual(
            categories,
            ["全部工具", "数据安全", "基础工作", "文书制作", "专业法律分析", "Anthropic Legal"],
        )

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok", "tools": 50})

    def test_homepage_renders_team_guide(self):
        response = self.client.get("/")
        html = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("虞律团队 AI 工作流使用手册", html)
        self.assertIn("安装 WorkBuddy", html)

    def test_skill_library_renders_workbench_and_all_tools(self):
        response = self.client.get("/skills")
        html = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("流程地图", html)
        self.assertIn("工具清单", html)
        self.assertIn("本地律师材料脱敏", html)
        self.assertIn("中国并购交易结构方案规划", html)
        self.assertIn("IPO 上市准备度评估", html)
        self.assertIn("买方尽职调查", html)
        self.assertIn("PE/VC 投资委员会备忘录", html)
        self.assertIn("data-tool-card", html)

    def test_every_tool_has_a_detail_page(self):
        for tool in tools:
            with self.subTest(tool=tool["id"]):
                response = self.client.get(f'/tools/{tool["id"]}')
                html = response.get_data(as_text=True)
                self.assertEqual(response.status_code, 200)
                self.assertIn(tool["name"], html)
                self.assertIn("输入材料", html)
                self.assertIn("输出结果", html)
                self.assertIn("使用步骤", html)
                self.assertIn("使用提示", html)

    def test_unknown_tool_returns_custom_404(self):
        response = self.client.get("/tools/not-a-real-tool")
        self.assertEqual(response.status_code, 404)
        self.assertIn("没有找到这个工具", response.get_data(as_text=True))

    def test_static_assets_are_linked(self):
        guide_html = self.client.get("/").get_data(as_text=True)
        skill_html = self.client.get("/skills").get_data(as_text=True)
        self.assertIn("/static/workbench.css", guide_html)
        self.assertIn("/static/guide.js", guide_html)
        self.assertIn("/static/workbench.js", skill_html)

    def test_homepage_links_the_three_team_destinations(self):
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn('href="/skills"', html)
        self.assertIn('href="/guide"', html)
        self.assertIn('href="/cases/"', html)
        self.assertIn('href="https://www.workbuddy.cn/work/"', html)
        self.assertIn("Skill 库", html)
        self.assertIn("团队使用指南", html)
        self.assertIn("诉讼案例管理", html)

    def test_team_guide_renders_workflow_and_copyable_prompts(self):
        response = self.client.get("/guide")
        html = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("虞律团队 AI 工作流使用手册", html)
        self.assertIn("安装 WorkBuddy", html)
        self.assertIn("先推荐、律师确认后执行", html)
        self.assertIn("待律师复核", html)
        self.assertIn("只推荐 1–3 个最适合的 Skill", html)
        self.assertIn("data-copy-prompt", html)
        self.assertIn("/static/guide.js", html)

    def test_team_guide_omits_retired_material_and_stage_sections(self):
        html = self.client.get("/guide").get_data(as_text=True)

        self.assertNotIn("材料清点", html)
        self.assertNotIn('id="files"', html)
        self.assertNotIn('href="#files"', html)
        self.assertNotIn("材料和文件命名", html)
        self.assertNotIn('id="stages"', html)
        self.assertNotIn('href="#stages"', html)
        self.assertNotIn("六阶段工作流", html)
        self.assertNotIn("人工确认节点", html)
        self.assertIn("Prompt 02｜Skill 推荐", html)
        self.assertIn("<h2>常见问题</h2>", html)
        self.assertIn("<p>待更新</p>", html)
        self.assertNotIn('class="troubleshooting-list"', html)

    def test_team_guide_explains_workbuddy_concepts_before_the_workflow(self):
        html = self.client.get("/guide").get_data(as_text=True)

        self.assertIn('id="concepts"', html)
        self.assertLess(html.index('id="concepts"'), html.index('id="workflow"'))
        for concept in (
            "Agent（智能代理）",
            "WorkBuddy",
            "项目（Project）",
            "任务（Task）",
            "专家（Expert）",
            "Skill（技能）",
        ):
            self.assertIn(concept, html)
        self.assertIn("调用“法律 AI 工作流总入口”专家，推荐 Skill", html)
        self.assertNotIn("周会行动项由周协同整理", html)
        self.assertNotIn("演练通过后，真实客户材料再按照项目权限进入对应工作区", html)

    def test_first_setup_uses_current_invite_link_and_plain_run_wording(self):
        html = self.client.get("/guide").get_data(as_text=True)
        invite_url = (
            "https://www.workbuddy.cn/app/projects?"
            "projectId=p_c8b9b165c7ee47399aedfac40a923d16&amp;"
            "wb_invite_copied_at=1786952018170"
        )

        self.assertIn(f'href="{invite_url}"', html)
        self.assertIn("点击链接加入【WorkBuddy】虞律团队 AI 工作流试验", html)
        self.assertTrue((PROJECT_ROOT / "static" / "workbuddy-first-setup.png").is_file())
        self.assertIn('src="/static/workbuddy-first-setup.png"', html)
        self.assertIn('alt="WorkBuddy 项目任务页中选择法律 AI 工作流总入口专家的示意图"', html)
        self.assertNotIn("先用 Ask 模式", html)
        self.assertNotIn("问一问", html)
        self.assertNotIn("做一做", html)
        self.assertIn("律师确认 Skill、材料、立场和输出后，再进入运行", html)

    def test_install_section_mentions_codex_and_claude_code_deployment(self):
        html = self.client.get("/guide").get_data(as_text=True)
        install_section = html[html.index('id="install"'):html.index('id="setup"')]

        self.assertIn(
            "资源库中的 Skill 不限于 WorkBuddy，也可以部署到 Codex 和 Claude Code",
            install_section,
        )

    def test_team_guide_has_direct_workbuddy_onboarding_checklist(self):
        html = self.client.get("/guide").get_data(as_text=True)
        invite_url = (
            "https://www.workbuddy.cn/app/projects?"
            "projectId=p_c8b9b165c7ee47399aedfac40a923d16&amp;"
            "wb_invite_copied_at=1786952018170"
        )

        self.assertIn("在浏览器或应用商城下载 WorkBuddy 后，使用微信注册并登录", html)
        self.assertIn(
            '<a class="inline-link" href="https://www.workbuddy.cn/work/"'
            ' target="_blank" rel="noreferrer">如果还未安装，可以点击链接安装</a>',
            html,
        )
        self.assertIn(f'href="{invite_url}"', html)
        self.assertIn("点击链接加入【WorkBuddy】虞律团队 AI 工作流试验", html)
        self.assertIn("能在专家栏找到“法律 AI 工作流总入口”", html)
        self.assertNotIn("第一次先用虚拟材料", html)
        self.assertNotIn("能用虚拟材料把任务推进到", html)

    def test_legal_document_skills_are_current_in_catalog_and_guide(self):
        html = self.client.get("/guide").get_data(as_text=True)
        for token in (
            "法律文书制作专家：工作示例",
            "技能 1｜法律服务合同｜DRAFT / REVIEW",
            "技能 2｜法律服务报价函｜DRAFT / REVIEW",
            "技能 3｜法律服务建议书｜Word DRAFT / REVIEW",
            "技能 4｜标书 / 响应文件｜母版生成",
            "$drafting-legal-service-contracts",
            "$handling-legal-fee-quotations",
            "$handling-legal-service-proposals",
            "$generating-law-firm-tenders",
            "GENERAL_LETTER_V1",
            "MA_SPECIAL_V1",
        ):
            self.assertIn(token, html)
        self.assertNotIn("合同 Skill 的当前边界", html)
        self.assertNotIn("它不是所有商业合同的通用审阅器", html)

        by_id = {tool["id"]: tool for tool in tools}
        contract = by_id["drafting-legal-service-contracts"]
        quotation = by_id["quotation-letter"]
        proposal = by_id["legal-service-proposal"]
        tender = by_id["tender-response"]

        for tool in (contract, quotation, proposal, tender):
            self.assertEqual(tool["status"], "local-skill")
        self.assertIn("审阅", contract["summary"])
        self.assertIn("报价函红线版 Word", quotation["outputs"])
        self.assertIn("建议书红线版 Word", proposal["outputs"])
        self.assertIn("固定 Word 母版", tender["summary"])


class AuthenticationTest(unittest.TestCase):
    def setUp(self):
        app.config.update(
            TESTING=True,
            SECRET_KEY="test-secret",
            AUTH_REQUIRED=True,
            AUTH_PASSWORD_HASH=hashlib.sha256(b"test-password").hexdigest(),
        )
        self.client = app.test_client()

    def tearDown(self):
        app.config.update(AUTH_REQUIRED=False, AUTH_PASSWORD_HASH="")

    def test_all_pages_require_one_site_password(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

        invalid = self.client.post("/login", data={"password": "wrong"})
        self.assertEqual(invalid.status_code, 401)
        self.assertIn("密码错误", invalid.get_data(as_text=True))

        valid = self.client.post("/login", data={"password": "test-password"})
        self.assertEqual(valid.status_code, 302)
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/skills").status_code, 200)
        self.assertEqual(self.client.get("/guide").status_code, 200)
        case_response = self.client.get("/cases/")
        self.assertEqual(case_response.status_code, 200)
        case_response.close()

    def test_case_api_returns_json_401_before_login(self):
        response = self.client.get("/api/cases")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json(), {"error": "请先登录虞律团队 AI 工作台"})


class LitigationFlaskTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        app.config.update(TESTING=True, AUTH_REQUIRED=False, CASE_DATA_ROOT=self.temp.name)
        self.client = app.test_client()

    def tearDown(self):
        self.temp.cleanup()

    def test_case_dashboard_and_sqlite_persist_between_clients(self):
        dashboard = self.client.get("/cases/")
        self.assertEqual(dashboard.status_code, 200)
        self.assertIn("诉讼工作台", dashboard.get_data(as_text=True))
        dashboard.close()

        created = self.client.post(
            "/api/cases",
            json={
                "title": "虚拟测试公司诉讼",
                "caseNumber": "（2026）沪01民初100号",
                "caseType": "诉讼",
                "procedureStage": "一审",
                "cause": "合同纠纷",
                "ourRole": "原告",
                "institution": "虚拟法院",
                "riskLevel": "中",
                "riskReason": "仅用于部署验证",
                "status": "进行中",
                "nextAction": "整理虚拟材料",
                "tags": ["虚拟测试"],
                "notes": "不含真实客户信息",
                "leadLawyer": "测试律师",
                "handlingLawyer": "测试律师",
                "reviewLawyer": "测试律师",
                "actor": "部署测试",
            },
        )
        self.assertEqual(created.status_code, 201)
        case_id = created.get_json()["id"]

        second_client = app.test_client()
        records = second_client.get("/api/cases?includeClosed=true").get_json()
        self.assertIn(case_id, [record["id"] for record in records])


if __name__ == "__main__":
    unittest.main()
