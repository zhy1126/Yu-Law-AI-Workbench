# PythonAnywhere 通过 GitHub 一键更新设计

## 目标

将 `yulaw.pythonanywhere.com` 从手工上传文件改为 GitHub 驱动的部署。日常更新由团队成员在 PythonAnywhere 运行一个命令触发，不在 GitHub 推送后自动上线。

## 现状

- 线上网站当前从 `/home/YuLaw/mysite` 运行，Python 版本为 3.13。
- WSGI 文件为 `/var/www/yulaw_pythonanywhere_com_wsgi.py`。
- GitHub 仓库已经克隆到 `/home/YuLaw/Yu-Law-AI-Workbench`。
- GitHub 当前 `main` 分支尚未包含 `pythonanywhere-flask/`，需要先补充安全可公开的 Flask 部署目录。

## 发布结构

- GitHub `main` 是唯一发布来源。
- PythonAnywhere 运行 `/home/YuLaw/Yu-Law-AI-Workbench/pythonanywhere-flask`。
- 现有 `/home/YuLaw/mysite` 保留为回退副本，不删除、不覆盖。
- 一键更新脚本位于 `/home/YuLaw/update-yulaw-workbench.sh`。

## 更新流程

更新脚本依次执行：

1. 从 GitHub 获取 `main` 的最新提交；
2. 仅允许快进更新，避免覆盖 PythonAnywhere 上的临时修改；
3. 运行 Flask 单元测试和基础导入检查；
4. 测试通过后触发 WSGI 重新加载；
5. 输出本次部署的 Git 提交号。

任一步失败，脚本立即停止，不重新加载网站，线上继续使用上一次可运行版本。

## 首次切换

先在 GitHub 独立分支补入 Flask 部署目录并完成测试，通过 PR 合并到 `main`。随后在 PythonAnywhere 验证 Flask 应用可以从新目录导入，再把 WSGI 的 `project_home` 改为新目录并重新加载。切换后访问首页、工具详情页和 `/health` 检查运行状态。

## 安全边界

- 仓库和网站中不存放客户材料、账号、令牌或其他密钥。
- 不在 GitHub 推送后自动发布，保留人工触发节点。
- 更新脚本不执行强制覆盖、删除目录或自动回滚数据。
- WSGI 切换前保留现有配置和 `/home/YuLaw/mysite`。

## 验收标准

- PythonAnywhere 能从 GitHub `main` 拉取更新；
- 一条命令可以完成拉取、测试和重新加载；
- 测试失败时网站不重新加载；
- `https://yulaw.pythonanywhere.com/health` 返回正常状态；
- 首页和工具详情页可正常访问；
- 原 `/home/YuLaw/mysite` 仍可用于人工回退。
