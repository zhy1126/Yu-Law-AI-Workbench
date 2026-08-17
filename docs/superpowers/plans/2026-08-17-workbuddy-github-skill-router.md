# WorkBuddy GitHub Skill Router Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update the “法律 AI 工作流总入口” expert so it selects Skills from the public GitHub catalog without requiring the PythonAnywhere password, with a bundled offline fallback.

**Architecture:** Ship the expert as a self-contained WorkBuddy plugin. Its routing Skill fetches one public raw JSON catalog, validates only public metadata, and falls back to a generated local index; execution remains gated by actual local installation and explicit lawyer confirmation.

**Tech Stack:** WorkBuddy expert Markdown/plugin JSON, Node.js index generator, Node.js built-in test runner, GitHub, local WorkBuddy marketplace.

---

### Task 1: Add the expert package with failing routing tests

**Files:**
- Create: `tests/workbuddy-expert-routing.test.mjs`
- Create: `workbuddy-experts/yulaw-team-ai-workbench/.codebuddy-plugin/plugin.json`
- Create: `workbuddy-experts/yulaw-team-ai-workbench/agents/yulaw-team-ai-workbench.md`
- Create: `workbuddy-experts/yulaw-team-ai-workbench/skills/yulaw-workbench-entry/SKILL.md`
- Create: `workbuddy-experts/yulaw-team-ai-workbench/README.md`
- Reuse: `workbuddy-experts/yulaw-team-ai-workbench/avatars/expert.png`

- [ ] **Step 1: Write the failing tests**

Create tests that require the exact public catalog URL, the bundled fallback, a `目录来源` field, explicit confirmation, and an installation-state check:

```js
const publicCatalog = "https://raw.githubusercontent.com/zhy1126/Yu-Law-AI-Workbench/main/pythonanywhere-flask/data/tools.json";
assert.match(skill, new RegExp(publicCatalog.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
assert.match(skill, /references\/skill-router-index\.json/);
assert.match(skill, /目录来源/);
assert.match(skill, /确认按推荐执行/);
assert.match(skill, /实际安装状态/);
assert.match(skill, /不得.*客户.*GitHub/);
```

- [ ] **Step 2: Run the tests and verify RED**

Run:

```bash
node --test tests/workbuddy-expert-routing.test.mjs
```

Expected: FAIL because the expert package is not present on the GitHub main baseline.

- [ ] **Step 3: Add the minimal expert package**

The routing Skill must use this source order:

```markdown
1. Use WebFetch to read the public raw GitHub catalog URL.
2. Accept it only when it parses as a non-empty tool array with id, name, category, status, summary, inputs, outputs, notice and repository fields.
3. On fetch or validation failure, read references/skill-router-index.json and state that the bundled catalog is in use.
4. Do not open PythonAnywhere for automatic routing.
```

Keep the existing state machine and lawyer-confirmation rules. Set the plugin version to `1.2.0`.

- [ ] **Step 4: Run the tests and verify GREEN**

Run:

```bash
node --test tests/workbuddy-expert-routing.test.mjs
```

Expected: all expert routing tests pass.

- [ ] **Step 5: Commit**

```bash
git add tests/workbuddy-expert-routing.test.mjs workbuddy-experts/yulaw-team-ai-workbench
git commit -m "feat: route WorkBuddy skills through GitHub catalog"
```

### Task 2: Generate and verify the bundled fallback

**Files:**
- Create: `scripts/build-workbuddy-router-index.mjs`
- Generate: `workbuddy-experts/yulaw-team-ai-workbench/skills/yulaw-workbench-entry/references/skill-router-index.json`
- Modify: `tests/workbuddy-expert-routing.test.mjs`

- [ ] **Step 1: Add a failing fallback-integrity test**

Require one deterministic routing record for each item in `pythonanywhere-flask/data/tools.json`, with unique IDs and preserved repository/status fields.

- [ ] **Step 2: Run the test and verify RED**

Run:

```bash
node --test tests/workbuddy-expert-routing.test.mjs
```

Expected: FAIL because the generated fallback index is missing.

- [ ] **Step 3: Add the minimal generator and run it**

The generator must read `pythonanywhere-flask/data/tools.json`, validate required public fields, derive file-type hints, and write:

```json
{
  "source": "pythonanywhere-flask/data/tools.json",
  "catalogStatusNote": "目录状态仅用于推荐；执行前必须检查 WorkBuddy 当前实际安装状态。",
  "tools": []
}
```

Run:

```bash
node scripts/build-workbuddy-router-index.mjs
```

- [ ] **Step 4: Run the tests and verify GREEN**

Run:

```bash
node --test tests/workbuddy-expert-routing.test.mjs
```

Expected: all tests pass and the generated index count equals the source catalog count.

- [ ] **Step 5: Commit**

```bash
git add scripts/build-workbuddy-router-index.mjs tests/workbuddy-expert-routing.test.mjs workbuddy-experts/yulaw-team-ai-workbench/skills/yulaw-workbench-entry/references/skill-router-index.json
git commit -m "test: verify WorkBuddy routing fallback"
```

### Task 3: Validate, publish, and install the expert

**Files:**
- Update external installation: `~/.workbuddy/plugins/marketplaces/my-experts/plugins/yulaw-team-ai-workbench`

- [ ] **Step 1: Run repository validation**

Run:

```bash
node scripts/build-workbuddy-router-index.mjs
git diff --exit-code -- workbuddy-experts/yulaw-team-ai-workbench/skills/yulaw-workbench-entry/references/skill-router-index.json
node --test tests/workbuddy-expert-routing.test.mjs
git diff --check
```

Expected: generated fallback is current, tests pass, and no whitespace errors exist.

- [ ] **Step 2: Publish through a draft PR and merge after checks**

Push `agent/workbuddy-github-router`, create a draft PR to `main`, mark it ready after validation, and squash merge it.

- [ ] **Step 3: Back up and replace the installed expert package**

Create a dated backup under `~/.workbuddy/plugins/marketplaces/my-experts/plugins/`, then copy only `workbuddy-experts/yulaw-team-ai-workbench` into the existing installed plugin location. Do not edit WorkBuddy connector credentials or project data.

- [ ] **Step 4: Verify the installed files**

Confirm the installed plugin reports version `1.2.0` and includes the public catalog URL, bundled fallback, `目录来源`, confirmation gate, and installation-state gate.

- [ ] **Step 5: Run one virtual routing scenario**

Use a virtual prompt such as:

```text
我方拟审阅一套虚拟 PE/VC 融资交易文件。只推荐 Skill，不读取真实材料，不执行。
```

Expected: one primary recommendation card, catalog source identified, no PythonAnywhere password request, no execution before explicit lawyer confirmation, and no customer data transmission.
