# WorkBuddy GitHub Skill 路由设计

## 目标

让“法律 AI 工作流总入口”在 WorkBuddy 内完成 Skill 选择，不要求律师登录 PythonAnywhere。专家只读取公开 GitHub 中的工作台目录；客户材料、案例数据和正式成果仍留在 WorkBuddy 或受保护的后台。

## 目录来源

专家按以下顺序读取 Skill 目录：

1. 首选公开 GitHub 原始文件：`https://raw.githubusercontent.com/zhy1126/Yu-Law-AI-Workbench/main/pythonanywhere-flask/data/tools.json`。
2. GitHub 不可访问、返回异常或数据格式不完整时，使用专家包内的 `references/skill-router-index.json`。
3. PythonAnywhere 网页不参与自动路由；只有用户明确要求查看网页时才返回网页链接，并提示其需要团队密码。

读取公开目录不需要 GitHub 登录或 WorkBuddy GitHub 连接器。GitHub 连接器仅作为以后读取私有仓库的可选扩展，不属于本次范围。

## 推荐与执行

专家从任务目的、文件类型、用户立场、预期成果、法域和交易阶段中提取非敏感特征，推荐 1 个主 Skill，必要时最多列出 2 个备选，并注明目录来源和实际安装状态。

GitHub 中存在某项 Skill 不代表它已经安装。律师明确确认推荐后，专家必须检查 WorkBuddy 当前是否已安装并启用该 Skill；未安装时只提供来源和安装提示，不得自动安装，也不得用相近能力冒充执行。

## 安全边界

- 不向 GitHub、PythonAnywhere 或公开网页发送客户名称、案号、金额、文件正文或其他敏感信息。
- GitHub 目录只用于读取公开的 Skill 元数据，不用于读取案例管理数据。
- PythonAnywhere 的统一密码、案例管理和写入接口保持不变，不允许专家绕过。
- 专业成果继续执行“先推荐、律师确认后执行”，自动流程只到“待律师复核”。

## 失败处理

- GitHub 读取失败：标明“使用内置目录”，继续完成推荐。
- GitHub 数据无法解析或条目缺字段：不采用该版本，回退内置目录。
- GitHub 与内置目录不一致：推荐时标明来源；执行时以 WorkBuddy 的实际安装状态为准。
- 没有合适 Skill：明确说明“当前目录未覆盖”，不得猜测或强行匹配。

## 验证

- 自动测试确认专家把 GitHub 原始目录作为首选、内置目录作为回退。
- 自动测试确认路由不要求 PythonAnywhere 密码，也不将网页作为自动执行入口。
- 自动测试确认 GitHub 条目不能替代安装状态检查和律师确认。
- 使用虚拟任务验证推荐卡包含：推荐 Skill、匹配理由、目录来源、安装状态、风险边界和确认提示。
