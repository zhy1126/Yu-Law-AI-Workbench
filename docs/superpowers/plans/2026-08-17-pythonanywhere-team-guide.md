# PythonAnywhere Team Guide Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish the approved WorkBuddy handbook and latest litigation case manager behind one password-protected PythonAnywhere workbench.

**Architecture:** Add Flask session authentication, a Jinja handbook at `/guide`, and a Flask adapter for the existing litigation SQLite repository and dashboard at `/cases/`. Keep the persistent database outside GitHub and leave the deployment updater code-only.

**Tech Stack:** Flask 3.1, Jinja, CSS, browser JavaScript, Python `unittest`

---

### Task 1: Specify the public guide behavior

**Files:**
- Modify: `pythonanywhere-flask/tests/test_flask_app.py`

- [ ] Add a test asserting that `/guide` returns 200 and contains `虞律团队 AI 工作流使用手册`, `安装 WorkBuddy`, `先推荐、律师确认后执行`, `待律师复核`, and `只推荐 1–3 个最适合的 Skill`.
- [ ] Add a test asserting that the homepage links to `/guide` with the label `团队使用手册`.
- [ ] Run the Flask test module and confirm the new assertions fail because the route and navigation do not yet exist.

### Task 1A: Specify authentication and persistent litigation behavior

**Files:**
- Modify: `pythonanywhere-flask/tests/test_flask_app.py`
- Create: `pythonanywhere-flask/tests/test_litigation_flask.py`

- [ ] Add tests showing unauthenticated pages redirect to `/login`, invalid passwords fail, and a valid configured password unlocks the homepage.
- [ ] Add tests showing `/cases/` serves the litigation dashboard and unauthenticated `/api/cases` returns 401.
- [ ] Add a write/read test using a temporary `YULAW_CASE_DATA_ROOT`, then recreate the Flask app and verify the case still exists in the same SQLite database.
- [ ] Run the new tests and confirm they fail because authentication and the Flask litigation adapter are missing.

### Task 2: Add the guide route and approved handbook

**Files:**
- Modify: `pythonanywhere-flask/flask_app.py`
- Create: `pythonanywhere-flask/templates/guide.html`
- Modify: `pythonanywhere-flask/templates/index.html`

- [ ] Add `@app.get("/guide")` returning `render_template("guide.html")`.
- [ ] Add shared navigation to the homepage and the guide.
- [ ] Build the guide with the approved workflow, installation instructions, six stages, review checklist, troubleshooting, and eight copyable Prompt blocks.
- [ ] Run the Flask tests and confirm the route/content tests pass.

### Task 3: Add README styling and copy behavior

**Files:**
- Modify: `pythonanywhere-flask/static/workbench.css`
- Create: `pythonanywhere-flask/static/guide.js`
- Modify: `pythonanywhere-flask/templates/guide.html`

- [ ] Add responsive guide layout, table, checklist, prompt-block, and navigation styles using the existing color variables.
- [ ] Bind each `[data-copy-prompt]` button to the related code block and change its label to `已复制` after success.
- [ ] Extend the guide test to assert the JavaScript asset and copy controls are linked.

### Task 3A: Integrate the litigation dashboard and private data root

**Files:**
- Add from approved implementation: `workbuddy-pilot/case-management/case_manager/database.py`
- Add from approved implementation: `workbuddy-pilot/case-management/case_manager/reporting.py`
- Add from approved implementation: `workbuddy-pilot/case-management/dashboard/*`
- Create: `pythonanywhere-flask/litigation_adapter.py`
- Modify: `pythonanywhere-flask/flask_app.py`
- Modify: `pythonanywhere-flask/templates/index.html`

- [ ] Load the existing litigation package from the repository without copying its runtime database.
- [ ] Instantiate SQLite from `YULAW_CASE_DATA_ROOT`, defaulting to a package-local instance directory only for development and tests.
- [ ] Expose dashboard, session, cases, deadlines, tasks, documents, weekly-report, and CSV routes through Flask.
- [ ] Add three clear homepage destinations: Skill 库, 团队使用指南, 诉讼案例管理.
- [ ] Run the new authentication, persistence, API, and dashboard tests until green.

### Task 4: Verify and publish

**Files:**
- No production files beyond Tasks 1–3.

- [ ] Run `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s pythonanywhere-flask/tests -v` and require zero failures.
- [ ] Run `bash -n pythonanywhere-flask/update_pythonanywhere.sh` and `git diff --check`.
- [ ] Commit, push, open and merge a GitHub pull request after checks pass.
- [ ] Run `/home/YuLaw/Yu-Law-AI-Workbench/pythonanywhere-flask/update_pythonanywhere.sh` on PythonAnywhere.
- [ ] Configure the private password hash, session secret, and `/home/YuLaw/private-data/case-management` data root in the PythonAnywhere WSGI file.
- [ ] Verify login, the three live entrances, the guide Prompt copy controls, and a reversible virtual case write/read on production.
