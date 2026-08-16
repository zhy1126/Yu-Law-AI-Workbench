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

test("handbook gives beginners a concise setup path and a complete team workflow", async () => {
  const handbook = await readText("app/guide/page.tsx");

  for (const required of [
    /虞律团队 AI 工作流使用手册/,
    /https:\/\/www\.workbuddy\.cn\/work\//,
    /微信扫码完成登录/,
    /加入“虞律团队 AI 工作流试验”/,
    /周会或日常工作/,
    /计划栏/,
    /团队资源库/,
    /任务工作区/,
    /法律 AI 工作流总入口/,
    /专业子任务/,
    /成果回到任务/,
    /问一问（Ask）/,
    /想一想（Plan）/,
    /默认权限/,
    /先推荐、律师确认后执行/,
    /待律师复核/,
    /已批准/,
    /已归档/,
    /工具结果仅供工作辅助/,
  ]) {
    assert.match(handbook, required);
  }
});

test("handbook provides copy-ready prompts for every control point", async () => {
  const [handbook, promptBlock] = await Promise.all([
    readText("app/guide/page.tsx"),
    readText("app/guide/PromptBlock.tsx"),
  ]);

  assert.match(handbook, /只推荐 1–3 个最适合的 Skill/);
  assert.match(handbook, /不得自动批准、归档或对外发送/);
  assert.match(handbook, /连接测试/);
  assert.match(handbook, /材料清点/);
  assert.match(handbook, /确认采用 Skill/);
  assert.match(handbook, /律师复核清单/);
  assert.match(handbook, /文件命名/);
  assert.match(handbook, /管理员上线前检查/);
  assert.match(handbook, /专家或 Skill 不可见/);
  assert.match(handbook, /文件无法读取/);
  assert.match(promptBlock, /navigator\.clipboard\.writeText/);
  assert.match(promptBlock, /复制 Prompt/);
  assert.match(promptBlock, /已复制/);
});
