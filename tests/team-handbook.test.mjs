import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const root = new URL("../", import.meta.url);

async function readText(relativePath) {
  return readFile(new URL(relativePath, root), "utf8");
}

test("homepage links first-time users to the team handbook", async () => {
  const shell = await readText("app/_components/WorkbenchShell.tsx");

  assert.match(shell, /href=["']\/guide["']/);
  assert.match(shell, /团队使用手册/);
});

test("handbook explains installation, routing, execution and lawyer review", async () => {
  const handbook = await readText("app/guide/page.tsx");

  for (const required of [
    /虞律团队 AI 工作流使用手册/,
    /安装 WorkBuddy/,
    /加入团队项目/,
    /法律 AI 工作流总入口/,
    /先推荐、律师确认后执行/,
    /待律师复核/,
    /已批准/,
    /已归档/,
    /工具结果仅供工作辅助/,
  ]) {
    assert.match(handbook, required);
  }
});

test("handbook provides copy-ready prompts and troubleshooting guidance", async () => {
  const handbook = await readText("app/guide/page.tsx");

  assert.match(handbook, /只推荐 1–3 个最适合的 Skill/);
  assert.match(handbook, /不得自动批准、归档或对外发送/);
  assert.match(handbook, /专家或 Skill 不可见/);
  assert.match(handbook, /文件无法读取/);
});
