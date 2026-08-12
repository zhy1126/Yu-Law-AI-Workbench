import sys
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

    def test_registry_contains_twenty_tools_and_expected_categories(self):
        self.assertEqual(len(tools), 20)
        self.assertEqual(
            categories,
            ["全部工具", "数据安全", "基础工作", "文书制作", "专业法律分析", "Anthropic Legal"],
        )

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok", "tools": 20})

    def test_homepage_renders_workbench_and_all_tools(self):
        response = self.client.get("/")
        html = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("虞律团队 AI 工作台", html)
        self.assertIn("流程地图", html)
        self.assertIn("工具清单", html)
        self.assertIn("本地律师材料脱敏", html)
        self.assertIn("中国并购交易结构方案规划", html)
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
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn("/static/workbench.css", html)
        self.assertIn("/static/workbench.js", html)


if __name__ == "__main__":
    unittest.main()
