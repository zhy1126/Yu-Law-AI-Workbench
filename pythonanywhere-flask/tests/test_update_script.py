from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class UpdateScriptTests(unittest.TestCase):
    def test_update_script_stops_on_error_and_reloads_last(self):
        script = (ROOT / "update_pythonanywhere.sh").read_text(encoding="utf-8")

        self.assertIn("set -euo pipefail", script)
        self.assertIn('git -C "$REPO_DIR" pull --ff-only origin main', script)
        self.assertIn(
            "PYTHONDONTWRITEBYTECODE=1 python3.13 -m unittest discover -s tests -v",
            script,
        )
        self.assertIn("python3.13 -m unittest discover -s tests -v", script)
        self.assertIn("from flask_app import app", script)
        self.assertIn('touch "$WSGI_FILE"', script)
        self.assertLess(
            script.index("python3.13 -m unittest"),
            script.index('touch "$WSGI_FILE"'),
        )


if __name__ == "__main__":
    unittest.main()
