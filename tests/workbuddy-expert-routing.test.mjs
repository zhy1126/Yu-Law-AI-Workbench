import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const root = new URL("../", import.meta.url);
const expertRoot = "workbuddy-experts/yulaw-team-ai-workbench/";
const publicCatalog =
  "https://raw.githubusercontent.com/zhy1126/Yu-Law-AI-Workbench/main/pythonanywhere-flask/data/tools.json";

async function readTextOrEmpty(relativePath) {
  try {
    return await readFile(new URL(relativePath, root), "utf8");
  } catch (error) {
    if (error?.code === "ENOENT") return "";
    throw error;
  }
}

test("routes through public GitHub first and uses a bundled fallback", async () => {
  const skill = await readTextOrEmpty(
    `${expertRoot}skills/yulaw-workbench-entry/SKILL.md`,
  );

  assert.match(skill, new RegExp(publicCatalog.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  assert.match(skill, /WebFetch/);
  assert.match(skill, /references\/skill-router-index\.json/);
  assert.match(skill, /GitHub.*失败|GitHub.*不可访问/);
  assert.match(skill, /内置目录/);
  assert.match(skill, /不需要.*GitHub.*登录|无需.*GitHub.*登录/);
  assert.match(skill, /不得.*PythonAnywhere.*自动路由|PythonAnywhere.*不参与自动路由/);
});

test("keeps routing separate from installation and execution", async () => {
  const [agent, skill] = await Promise.all([
    readTextOrEmpty(`${expertRoot}agents/yulaw-team-ai-workbench.md`),
    readTextOrEmpty(`${expertRoot}skills/yulaw-workbench-entry/SKILL.md`),
  ]);

  for (const required of [
    "任务分流中",
    "等待律师确认",
    "确认按推荐执行",
    "未经律师明确确认",
    "实际安装状态",
    "待律师复核",
  ]) {
    assert.match(`${agent}\n${skill}`, new RegExp(required));
  }

  for (const required of [
    "推荐 Skill",
    "匹配理由",
    "目录来源",
    "安装状态",
    "风险边界",
    "请律师确认是否使用该 Skill",
  ]) {
    assert.match(skill, new RegExp(required));
  }

  assert.match(`${agent}\n${skill}`, /不得.*客户.*GitHub/);
  assert.match(`${agent}\n${skill}`, /GitHub.*不代表.*已安装|目录.*不代表.*已安装/);
});

test("publishes the router as the legal AI workflow entry expert", async () => {
  const pluginText = await readTextOrEmpty(
    `${expertRoot}.codebuddy-plugin/plugin.json`,
  );

  assert.notEqual(pluginText, "");
  const plugin = JSON.parse(pluginText);
  assert.equal(plugin.version, "1.2.0");
  assert.equal(plugin.displayName.zh, "法律 AI 工作流总入口");
  assert.match(plugin.displayDescription.zh, /GitHub.*推荐.*确认.*执行/);
});
