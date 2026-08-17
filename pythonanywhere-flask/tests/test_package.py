import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class DeploymentPackageTest(unittest.TestCase):
    def test_required_deployment_files_exist(self):
        for relative in [
            "flask_app.py",
            "requirements.txt",
            "README-PythonAnywhere.md",
            "pythonanywhere_wsgi.py.example",
            "build_package.sh",
        ]:
            with self.subTest(relative=relative):
                self.assertTrue((PROJECT_ROOT / relative).is_file(), relative)

    def test_dependency_list_is_minimal_and_pinned(self):
        requirements = (PROJECT_ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
        self.assertEqual(requirements, ["Flask==3.1.2"])

    def test_wsgi_example_exports_application(self):
        content = (PROJECT_ROOT / "pythonanywhere_wsgi.py.example").read_text(encoding="utf-8")
        self.assertIn("from flask_app import app as application", content)
        self.assertIn("project_home", content)

    def test_readme_contains_complete_pythonanywhere_steps(self):
        content = (PROJECT_ROOT / "README-PythonAnywhere.md").read_text(encoding="utf-8")
        for phrase in ["上传并解压", "虚拟环境", "Web 应用", "WSGI", "Reload"]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, content)

    def test_source_tree_has_no_sensitive_or_generated_files(self):
        forbidden_names = {".env", "auth.json", "credentials.json", ".DS_Store"}
        forbidden_parts = {"__pycache__", ".git", "node_modules", ".venv"}
        for path in PROJECT_ROOT.rglob("*"):
            relative = path.relative_to(PROJECT_ROOT)
            self.assertNotIn(path.name, forbidden_names)
            self.assertTrue(forbidden_parts.isdisjoint(relative.parts), str(relative))


if __name__ == "__main__":
    unittest.main()
