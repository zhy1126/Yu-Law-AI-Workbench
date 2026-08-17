# PythonAnywhere GitHub One-Command Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `yulaw.pythonanywhere.com` run the Flask package stored in GitHub and update safely with one command.

**Architecture:** GitHub `main` is the release source. PythonAnywhere keeps a clone at `/home/YuLaw/Yu-Law-AI-Workbench`, runs the app directly from `pythonanywhere-flask/`, and uses a guarded shell script that pulls, tests, imports, and only then reloads WSGI. The existing `/home/YuLaw/mysite` remains untouched for rollback.

**Tech Stack:** Git, Flask, Python 3.13, Bash, PythonAnywhere WSGI

---

### Task 1: Restore the Flask deployment package on the release branch

**Files:**
- Create: `pythonanywhere-flask/flask_app.py`
- Create: `pythonanywhere-flask/templates/base.html`
- Create: `pythonanywhere-flask/templates/index.html`
- Create: `pythonanywhere-flask/templates/tool_detail.html`
- Create: `pythonanywhere-flask/templates/404.html`
- Create: `pythonanywhere-flask/static/workbench.css`
- Create: `pythonanywhere-flask/static/workbench.js`
- Create: `pythonanywhere-flask/data/tools.json`
- Create: `pythonanywhere-flask/requirements.txt`
- Create: `pythonanywhere-flask/pythonanywhere_wsgi.py.example`
- Create: `pythonanywhere-flask/tests/test_flask_app.py`
- Create: `pythonanywhere-flask/tests/test_package.py`

- [ ] **Step 1: Restore the previously tested Flask package commit**

Run:

```bash
git cherry-pick b3459e4
```

Expected: `pythonanywhere-flask/` is added without modifying unrelated files.

- [ ] **Step 2: Restore the latest 50-Skill Flask data update**

Run:

```bash
git cherry-pick 4ba8347
```

Expected: root and Flask `tools.json` contain the same 50-entry catalog.

- [ ] **Step 3: Run the existing Flask tests**

Run:

```bash
python3 -m unittest discover -s pythonanywhere-flask/tests -v
```

Expected: all Flask and package tests pass.

### Task 2: Add the guarded one-command updater

**Files:**
- Create: `pythonanywhere-flask/tests/test_update_script.py`
- Create: `pythonanywhere-flask/update_pythonanywhere.sh`
- Modify: `pythonanywhere-flask/README-PythonAnywhere.md`

- [ ] **Step 1: Write a failing test for the update script contract**

Create `pythonanywhere-flask/tests/test_update_script.py` with assertions that the script:

```python
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class UpdateScriptTests(unittest.TestCase):
    def test_update_script_stops_on_error_and_reloads_last(self):
        script = (ROOT / "update_pythonanywhere.sh").read_text(encoding="utf-8")
        self.assertIn("set -euo pipefail", script)
        self.assertIn("git -C \"$REPO_DIR\" pull --ff-only origin main", script)
        self.assertIn("python3.13 -m unittest discover -s tests -v", script)
        self.assertIn("from flask_app import app", script)
        self.assertIn("touch \"$WSGI_FILE\"", script)
        self.assertLess(script.index("python3.13 -m unittest"), script.index("touch \"$WSGI_FILE\""))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test and confirm the script is missing**

Run:

```bash
python3 -m unittest pythonanywhere-flask/tests/test_update_script.py -v
```

Expected: FAIL because `update_pythonanywhere.sh` does not exist.

- [ ] **Step 3: Implement the minimal update script**

Create `pythonanywhere-flask/update_pythonanywhere.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/home/YuLaw/Yu-Law-AI-Workbench"
APP_DIR="$REPO_DIR/pythonanywhere-flask"
WSGI_FILE="/var/www/yulaw_pythonanywhere_com_wsgi.py"

git -C "$REPO_DIR" pull --ff-only origin main
cd "$APP_DIR"
python3.13 -m unittest discover -s tests -v
PYTHONPATH="$APP_DIR" python3.13 -c "from flask_app import app; assert app is not None"
touch "$WSGI_FILE"
git -C "$REPO_DIR" rev-parse --short HEAD
```

- [ ] **Step 4: Document the one-command update**

Add to `README-PythonAnywhere.md`:

````markdown
## GitHub 一键更新

首次接入完成后，在 PythonAnywhere Bash 控制台运行：

```bash
bash ~/Yu-Law-AI-Workbench/pythonanywhere-flask/update_pythonanywhere.sh
```

脚本只有在 Git 拉取、单元测试和 Flask 导入检查全部通过后才重新加载网站。
````

- [ ] **Step 5: Run all Flask tests**

Run:

```bash
python3 -m unittest discover -s pythonanywhere-flask/tests -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit the updater**

Run:

```bash
git add pythonanywhere-flask
git commit -m "feat: add guarded PythonAnywhere updater"
```

### Task 3: Publish and merge the deployment branch

**Files:**
- No additional files.

- [ ] **Step 1: Run complete repository verification**

Run:

```bash
npm run lint
npm test
python3 -m unittest discover -s pythonanywhere-flask/tests -v
git diff --check origin/main...HEAD
```

Expected: all checks pass with no whitespace errors.

- [ ] **Step 2: Push the branch and open a draft PR**

Push `agent/pythonanywhere-github` and open a draft PR targeting `main` that lists the Flask package, guarded updater, tests, and rollback behavior.

- [ ] **Step 3: Merge after checks pass**

Mark the PR ready and merge it. Confirm GitHub `main` contains `pythonanywhere-flask/update_pythonanywhere.sh`.

### Task 4: Switch PythonAnywhere to the GitHub copy

**Files on PythonAnywhere:**
- Modify: `/var/www/yulaw_pythonanywhere_com_wsgi.py`
- Keep unchanged: `/home/YuLaw/mysite`

- [ ] **Step 1: Pull the merged main branch**

Run in the PythonAnywhere Bash console:

```bash
git -C /home/YuLaw/Yu-Law-AI-Workbench pull --ff-only origin main
```

Expected: `pythonanywhere-flask/` appears in the clone.

- [ ] **Step 2: Test the Flask package before switching WSGI**

Run:

```bash
cd /home/YuLaw/Yu-Law-AI-Workbench/pythonanywhere-flask
python3.13 -m unittest discover -s tests -v
PYTHONPATH=/home/YuLaw/Yu-Law-AI-Workbench/pythonanywhere-flask python3.13 -c "from flask_app import app; assert app is not None"
```

Expected: tests and import check pass.

- [ ] **Step 3: Change only the WSGI project directory**

Replace:

```python
project_home = '/home/YuLaw/mysite'
```

with:

```python
project_home = '/home/YuLaw/Yu-Law-AI-Workbench/pythonanywhere-flask'
```

Keep the existing import:

```python
from flask_app import app as application
```

- [ ] **Step 4: Reload and verify production**

Reload `YuLaw.pythonanywhere.com`, then verify:

```text
https://yulaw.pythonanywhere.com/
https://yulaw.pythonanywhere.com/health
```

Expected: the homepage loads and `/health` returns `status: ok`.

- [ ] **Step 5: Run the one-command updater once**

Run:

```bash
bash /home/YuLaw/Yu-Law-AI-Workbench/pythonanywhere-flask/update_pythonanywhere.sh
```

Expected: Git reports no unintended changes, tests pass, WSGI reload is touched, and the deployed commit SHA is printed.
