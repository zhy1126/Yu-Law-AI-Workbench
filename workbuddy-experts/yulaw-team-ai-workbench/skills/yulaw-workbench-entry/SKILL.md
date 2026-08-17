---
name: yulaw-workbench-entry
description: Use when a Yu Law legal task, authorized file, or WorkBuddy plan item needs to be matched to a suitable legal Skill before execution.
---

# 虞律法律 Skill 路由入口

## 目录来源

PythonAnywhere 不参与自动路由。选择 Skill 时按以下顺序读取目录：

1. 使用 `WebFetch` 只读访问公开 GitHub 原始目录：`https://raw.githubusercontent.com/zhy1126/Yu-Law-AI-Workbench/main/pythonanywhere-flask/data/tools.json`。
2. 仅在返回内容是非空 JSON 数组，且每项包含 `id`、`name`、`category`、`status`、`summary`、`inputs`、`outputs`、`notice` 和 `repository` 字段时采用。
3. GitHub 不可访问、读取失败或数据格式不完整时，读取 `references/skill-router-index.json`，并在推荐卡中注明“目录来源：内置目录”。

公开 GitHub 目录无需 GitHub 登录，也不要求输入 PythonAnywhere 密码。只有用户明确要求查看工作台网页时，才返回 `https://yulaw.pythonanywhere.com/`；不得把网页作为自动路由或执行接口。

## 推荐流程

1. 读取当前项目规则、任务和已授权材料范围。
2. 提取最少的非敏感路由特征：任务目的、文件类型、用户立场、预期成果、法域和交易阶段。不得将客户名称、案号、金额、文件正文或敏感任务说明发送到 GitHub。
3. 根据有效目录推荐 1 个主 Skill；只有适用边界确有差异时列出最多 2 个备选。匹配不足时只问一个最关键的问题。
4. 只读检查主 Skill 的实际安装状态。GitHub 目录存在不代表已安装；目录中的状态也不能证明 WorkBuddy 已安装或启用该 Skill。
5. 按固定推荐卡输出并停止：

   - **推荐 Skill：** 名称和标识
   - **匹配理由：** 为什么适合本任务
   - **适合处理：** 本次允许它处理的范围
   - **需要补充：** 无则写“暂无”
   - **目录来源：** 公开 GitHub / 内置目录
   - **安装状态：** 已安装 / 未安装 / 尚未确认
   - **风险边界：** 最重要的人工判断与复核事项
   - **备选 Skill：** 最多 2 个；无必要备选则写“无”
   - **确认提示：** 请律师确认是否使用该 Skill；如同意，请回复“确认按推荐执行”或“确认使用 <Skill 名称>”。

6. 输出推荐卡后进入“等待律师确认”。未经律师明确确认，不得进入“生成中”，不得调用目标 Skill，不得生成正式成果。
7. 确认后再次核对主 Skill 和实际安装状态；未安装或无法确认时明确停止，不得用名称相近的能力替代。
8. 已安装时才进入“生成中”并执行。完成后把成果停在“待律师复核”；不得自动批准、归档或对外发送。

## 选择原则

- 文件审阅、方案规划、文书起草和项目管理属于不同任务，不因材料相同而混用 Skill。
- 一个任务确需多个 Skill 时，先推荐负责主交付物的 Skill；其他能力作为后续步骤。
- 工作台没有匹配项时，明确说明“当前目录未覆盖”，不得猜测或强行匹配。
- 公开 GitHub 目录只提供路由元数据，不用于读取客户文件、案例数据或成果。
