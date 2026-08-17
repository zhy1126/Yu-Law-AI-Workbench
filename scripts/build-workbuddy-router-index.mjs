import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const projectRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const sourceLabel = "pythonanywhere-flask/data/tools.json";
const sourcePath = resolve(projectRoot, sourceLabel);
const outputPath = resolve(
  projectRoot,
  "workbuddy-experts/yulaw-team-ai-workbench/skills/yulaw-workbench-entry/references/skill-router-index.json",
);

const fileTypePatterns = [
  ["DOCX/Word", /docx|word|红线稿|批注|法律意见书|招股说明书|合同|协议|章程|函|报告|文书/i],
  ["PDF", /pdf/i],
  ["PPTX/演示文稿", /pptx|ppt|演示|建议书|述标/i],
  ["XLSX/表格", /xlsx|xls|excel|表格|台账|清单|矩阵|模型/i],
  ["TXT/Markdown", /txt|markdown|文本|摘要|备忘录/i],
];

function requiredString(value, label) {
  if (typeof value !== "string" || !value.trim()) {
    throw new TypeError(`${label} must be a non-empty string`);
  }
  return value.trim();
}

function stringArray(value, label) {
  if (!Array.isArray(value) || value.some((item) => typeof item !== "string")) {
    throw new TypeError(`${label} must be a string array`);
  }
  return value.map((item) => item.trim()).filter(Boolean);
}

function nullableString(value, label) {
  if (value === null) return null;
  return requiredString(value, label);
}

function normalizeTool(tool, index) {
  const label = `tools[${index}]`;
  const id = requiredString(tool.id, `${label}.id`);
  const name = requiredString(tool.name, `${label}.name`);
  const category = requiredString(tool.category, `${label}.category`);
  const catalogStatus = requiredString(tool.status, `${label}.status`);
  const summary = requiredString(tool.summary, `${label}.summary`);
  const inputs = stringArray(tool.inputs, `${label}.inputs`);
  const outputs = stringArray(tool.outputs, `${label}.outputs`);
  const notice = requiredString(tool.notice, `${label}.notice`);
  const repository = nullableString(tool.repository, `${label}.repository`);
  const localUrl = nullableString(tool.localUrl, `${label}.localUrl`);
  const searchText = [name, category, summary, ...inputs, ...outputs, notice].join(" | ");

  return {
    id,
    name,
    category,
    catalogStatus,
    summary,
    inputs,
    outputs,
    notice,
    repository,
    localUrl,
    fileTypeHints: fileTypePatterns
      .filter(([, pattern]) => pattern.test(searchText))
      .map(([fileType]) => fileType),
    searchText,
  };
}

const source = JSON.parse(await readFile(sourcePath, "utf8"));
if (!Array.isArray(source) || source.length === 0) {
  throw new TypeError(`${sourceLabel} must contain a non-empty array`);
}

const tools = source.map(normalizeTool);
if (new Set(tools.map(({ id }) => id)).size !== tools.length) {
  throw new TypeError(`${sourceLabel} contains duplicate tool IDs`);
}

const index = {
  source: sourceLabel,
  count: tools.length,
  catalogStatusNote:
    "目录状态仅用于推荐；执行前必须检查 WorkBuddy 当前实际安装状态。installable、planned 或 building 不等于已安装。",
  tools,
};

await mkdir(dirname(outputPath), { recursive: true });
await writeFile(outputPath, `${JSON.stringify(index, null, 2)}\n`, "utf8");
process.stdout.write(`Wrote ${tools.length} routing records to ${outputPath}\n`);
