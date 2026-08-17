# PythonAnywhere 团队使用手册接入设计

## 目标

把已经确认的 WorkBuddy README 风格团队手册和最新诉讼案例管理系统接入 PythonAnywhere 版虞律团队 AI 工作台。登录后首页提供 Skill 库、团队使用指南、诉讼案例管理三个入口。

## 范围

- 首页顶部增加“工作台 / 团队使用手册”导航。
- Flask 增加 `/guide` 路由和独立模板。
- Flask 增加 `/cases/` 诉讼案例管理入口，沿用最新深蓝色诉讼工作台。
- 整个网站使用统一密码登录；密码明文不进入 GitHub。
- 手册沿用已确认内容，重点覆盖 WorkBuddy 安装登录、团队项目、六阶段流程、Skill 推荐与确认、律师复核和常见问题。
- Prompt 以代码块展示，并提供浏览器内复制按钮。
- 不改变工具目录、工具数量、PythonAnywhere 更新命令或访问权限。
- 案件、期限、待办、文书、跟进和周报统一写入 PythonAnywhere 持久化 SQLite，数据库不进入 GitHub。

## 实现

Flask 继续使用现有 `base.html`、`workbench.css` 和轻量原生 JavaScript。手册模板只呈现说明文本，不读取或上传客户文件。首页导航和手册共用现有低调绿色视觉体系。

统一登录由 Flask session 实现，应用从 PythonAnywhere 私有环境变量读取密码摘要和 session secret。未登录访问任意业务页面或 API 时，跳转登录页或返回 401。

诉讼工作台复用已有 SQLite 仓储、提醒和周报逻辑，通过 Flask API 暴露 CRUD、周报和 CSV 导出。线上数据库目录由 `YULAW_CASE_DATA_ROOT` 指向 `/home/YuLaw/private-data/case-management`；代码更新、Git 拉取和测试不得删除或覆盖该目录。

## 验证

- `/guide` 返回 200，并包含手册标题、WorkBuddy 安装、六阶段流程和推荐 Prompt。
- 首页包含可访问的 `/guide` 入口。
- Prompt 复制按钮绑定到对应文本块。
- 未登录不能访问 Skill、指南、案例页面或案例 API；登录后三个入口均可使用。
- 案例 API 写入仓库外 SQLite，重新运行一键更新后数据仍存在。
- 原有 12 项部署测试继续通过；新增手册测试通过。
