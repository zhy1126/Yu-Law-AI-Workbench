# 虞律团队 AI 工作台：PythonAnywhere 部署说明

本压缩包是轻量 Flask 版本。入口文件为 `flask_app.py`，不需要 Node.js、数据库或前端构建。

## 一、上传并解压

1. 登录 PythonAnywhere，进入 **Files**。
2. 上传 `yu-law-ai-workbench-pythonanywhere-flask.zip`。
3. 打开 **Consoles → Bash**，执行：

```bash
mkdir -p ~/yu-law-ai-workbench
cd ~/yu-law-ai-workbench
unzip ~/yu-law-ai-workbench-pythonanywhere-flask.zip
```

## 二、建立虚拟环境

在 Bash 控制台执行（Python版本需与后面创建的Web应用一致）：

```bash
mkvirtualenv --python=/usr/bin/python3.13 yu-law-workbench
pip install -r ~/yu-law-ai-workbench/requirements.txt
```

如果你的 PythonAnywhere 页面没有 Python 3.13，请把命令中的版本改为页面提供的版本，并在创建Web应用时选择相同版本。

## 三、创建 Web 应用

1. 进入 **Web** 页面，点击 **Add a new web app**。
2. 选择 **Manual configuration**。
3. 选择与虚拟环境相同的 Python 版本。
4. 在 **Virtualenv** 一栏填写：

```text
/home/YOURUSERNAME/.virtualenvs/yu-law-workbench
```

把 `YOURUSERNAME` 替换为你的 PythonAnywhere 用户名。

## 四、配置 WSGI

在Web页面点击WSGI配置文件链接，删除其中示例内容，再复制 `pythonanywhere_wsgi.py.example` 的内容。务必把：

```python
project_home = "/home/YOURUSERNAME/yu-law-ai-workbench"
```

中的 `YOURUSERNAME` 替换为你的用户名。入口导入应保持：

```python
from flask_app import app as application
```

## 五、静态文件与上线

Flask会直接提供本项目的CSS和JavaScript，首版不需要另设静态文件映射。返回Web页面，点击绿色 **Reload** 按钮，然后访问页面顶部显示的网址。

可先访问以下地址检查运行状态：

```text
https://YOURUSERNAME.pythonanywhere.com/health
```

正常结果为：

```json
{"status":"ok","tools":50}
```

## GitHub 一键更新

首次接入完成后，在 PythonAnywhere Bash 控制台运行：

```bash
bash ~/Yu-Law-AI-Workbench/pythonanywhere-flask/update_pythonanywhere.sh
```

脚本依次从 GitHub 拉取 `main`、运行单元测试并检查 Flask 是否可以导入。全部通过后才重新加载网站；任何一步失败都会停止，不会重新加载当前线上版本。

## 常见问题

- 出现 `No module named flask`：确认Web应用已选择 `yu-law-workbench` 虚拟环境，并重新执行 `pip install -r requirements.txt`。
- 出现 `No module named flask_app`：检查WSGI中的 `project_home` 是否与解压目录一致。
- 修改文件后页面没有变化：回到Web页面点击 **Reload**。
- 当前版本没有访问密码，任何知道网址的人都可以访问；不要在工具说明或代码中放入客户材料、账号或密钥。
