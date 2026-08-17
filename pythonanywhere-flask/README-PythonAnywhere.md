# 虞律团队 AI 工作台：PythonAnywhere 部署说明

线上版本从 GitHub 仓库运行，包含 Skill 库、团队使用指南和诉讼案例管理。程序代码由 GitHub 更新；案例数据保存在 PythonAnywhere 私有目录，不进入 GitHub。

## 一、从 GitHub 获取代码

在 PythonAnywhere 的 **Consoles → Bash** 中执行：

```bash
git clone https://github.com/zhy1126/Yu-Law-AI-Workbench.git ~/Yu-Law-AI-Workbench
```

## 二、建立虚拟环境

Python 版本需与 Web 应用一致：

```bash
mkvirtualenv --python=/usr/bin/python3.13 yu-law-workbench
pip install -r ~/Yu-Law-AI-Workbench/pythonanywhere-flask/requirements.txt
```

## 三、创建 Web 应用

1. 进入 **Web** 页面，点击 **Add a new web app**。
2. 选择 **Manual configuration**。
3. 选择与虚拟环境相同的 Python 版本。
4. 在 **Virtualenv** 一栏填写 `/home/YOURUSERNAME/.virtualenvs/yu-law-workbench`。

## 四、配置 WSGI、统一密码和数据目录

在 Web 页面打开 WSGI 文件，参考 `pythonanywhere_wsgi.py.example` 配置：

- `project_home` 指向 `/home/YOURUSERNAME/Yu-Law-AI-Workbench/pythonanywhere-flask`；
- `YULAW_PASSWORD_HASH` 保存统一密码的 SHA-256 摘要，不保存明文；
- `YULAW_SESSION_SECRET` 使用随机字符串；
- `YULAW_CASE_DATA_ROOT` 指向 `/home/YOURUSERNAME/private-data/case-management`；
- `YULAW_SECURE_COOKIE` 在线上 HTTPS 环境设为 `1`。

先建立私有数据目录：

```bash
mkdir -p ~/private-data/case-management
chmod 700 ~/private-data ~/private-data/case-management
```

案例 SQLite 最终位于：

```text
/home/YOURUSERNAME/private-data/case-management/data/litigation.db
```

该目录在 GitHub 仓库之外，一键更新不会覆盖案件、期限、待办、文书和周报。

## 五、Reload 与检查

返回 Web 页面点击绿色 **Reload**。访问首页时应先显示统一密码登录页；登录后能看到三个入口。

健康检查地址：

```text
https://YOURUSERNAME.pythonanywhere.com/health
```

正常结果：

```json
{"status":"ok","tools":50}
```

## GitHub 一键更新

以后 GitHub `main` 更新后，在 PythonAnywhere Bash 控制台运行：

```bash
bash ~/Yu-Law-AI-Workbench/pythonanywhere-flask/update_pythonanywhere.sh
```

脚本先拉取代码、运行 Flask 测试和导入检查，全部通过后才 Reload。脚本不读取、不删除、不覆盖 `~/private-data`。

## 常见问题

- `No module named flask`：确认 Web 应用选择了正确虚拟环境，并重新安装 requirements。
- `No module named flask_app`：检查 WSGI 的 `project_home`。
- 登录后仍回到登录页：检查 `YULAW_SESSION_SECRET` 和浏览器 Cookie，并重新 Reload。
- 案例页面无法写入：检查 private-data 目录是否存在，以及 YuLaw 账号是否有写权限。
- GitHub 更新后页面无变化：重新运行一键更新，并确认命令最后显示新的 commit 号。
