import type { Metadata } from "next";
import Link from "next/link";
import { PromptBlock } from "./PromptBlock";

export const metadata: Metadata = {
  title: "团队使用手册｜虞律团队 AI 工作台",
  description: "从安装 WorkBuddy 到完成首个律师复核任务的虞律团队零基础操作手册",
};

const workflowStages = ["待收件", "材料已确认", "生成中", "待律师复核", "已批准", "已归档"];

const connectionPrompt = `这是连接测试。请不要读取文件、不要调用 Skill、不要连接外部服务，也不要生成正式成果。

请只回复以下三项：
1. 你当前使用的专家名称；
2. 你是否理解“先推荐、律师确认后执行”；
3. 你能否在未获确认前停止执行。

如果当前不是“法律 AI 工作流总入口”，请直接提醒我切换专家。`;

const inventoryPrompt = `这是【项目/任务名称】的材料清点，不是正式审阅或起草。

委托方立场：【填写，例如投资人/公司/收购方/出售方】
任务目标：【填写】
截止时间：【填写】
已提供材料：【逐项填写文件名】

请只输出：
1. 已收到的文件及版本；
2. 可能重复、过期或无法识别的文件；
3. 开始工作前仍缺少的材料；
4. 必须由律师确认的事实。

不要调用 Skill，不要改文件，不要开始起草或审阅。`;

const recommendPrompt = `这是【项目/任务名称】。先不要执行。

任务类型：【报价函/标书/法律服务建议书/合同起草/合同审阅/尽调/并购结构/IPO 等】
委托方立场：【填写】
适用法域：【填写】
目标成果：【填写】
材料范围：【填写文件名或文件夹】
特别关注：【填写】

请只推荐 1–3 个最适合的 Skill，并逐一说明：
1. 匹配理由；
2. 它需要哪些输入；
3. 它会交付什么；
4. 当前还缺什么；
5. 主要风险和律师确认点。

请给出首选方案，但等我确认后再执行。`;

const executePrompt = `确认采用【Skill 名称】执行本任务。

委托方立场：【填写】
确认材料范围：【填写】
任务范围：【填写】
不在范围内的事项：【填写；没有则写“无”】
输出格式：【填写，例如 Word 审阅清单 + Excel 问题表】
截止时间：【填写】

执行要求：
1. 只使用已经确认的材料和版本；
2. 不确定的事实必须标记，不得自行补造；
3. 发现材料冲突、规则冲突或版本不明时先停止并列出待确认项；
4. 所有成果标记“待经办律师复核”；
5. 推进到“待律师复核”为止；
6. 不得自动批准、归档或对外发送；不得自动分享或上传。`;

const clarificationPrompt = `请暂停当前生成，不要继续修改文件。

请把尚未解决的问题整理为一张确认清单，每项包括：
- 编号；
- 需要确认的事实或选择；
- 为什么会影响成果；
- 可选方案；
- 建议由谁确认。

等我逐项回复后，再总结我的确认内容并询问是否恢复执行。`;

const reviewPrompt = `请对当前成果做一次“交付前自检”，但不要替律师批准。

请按以下维度逐项检查并引用对应位置：
1. 委托方立场是否一致；
2. 人名、主体、金额、比例、日期和版本是否一致；
3. 是否存在未处理的批注、占位符或待确认项；
4. 法律依据和外部数据库引用是否可核验；
5. 是否遗漏用户明确要求的输出；
6. 文件名、格式和交付目录是否正确；
7. 是否存在不应对外披露的信息。

最后只输出“复核清单 + 发现的问题 + 建议处理方式”，并保持状态为“待律师复核”。`;

const statusPrompt = `请只汇报当前任务状态，不要继续执行。

按以下格式输出：
- 当前阶段：
- 已完成：
- 正在处理：
- 缺少材料：
- 待律师确认：
- 已生成成果及保存位置：
- 下一步建议：

如果当前成果尚未经律师复核，不得写“已完成”或“可直接发送”。`;

const stopPrompt = `立即停止当前任务，不再调用任何 Skill、脚本、连接器或外部服务，也不要修改、上传、分享、批准或归档任何文件。

请只说明：
1. 停止前最后完成的步骤；
2. 已经发生的文件变更；
3. 当前成果所在位置；
4. 是否存在需要人工检查或恢复的事项。`;

export default function GuidePage() {
  return (
    <div className="site-shell">
      <header className="site-header">
        <Link className="brand-home" href="/" aria-label="返回虞律团队 AI 工作台首页">
          <span className="brand-mark" aria-hidden="true">虞律</span>
          <span className="brand-copy">
            <span className="eyebrow">YU LAW TEAM</span>
            <span className="brand-name">虞律团队 AI 工作台</span>
          </span>
        </Link>
        <nav className="site-nav" aria-label="主要导航">
          <Link href="/">工作台</Link>
          <Link href="/guide" aria-current="page">团队使用手册</Link>
        </nav>
      </header>

      <main id="main-content" className="guide-page" tabIndex={-1}>
        <header className="guide-intro guide-intro-readme">
          <p className="hero-kicker">README · 新成员从零上手</p>
          <h1>虞律团队 AI 工作流使用手册</h1>
          <p>从下载安装到完成第一个“待律师复核”任务。第一次使用时，请从上到下逐项操作，不要跳步，也不要使用真实客户材料演练。</p>
          <div className="guide-meta" aria-label="手册信息">
            <span>适用对象：第一次使用的团队成员</span>
            <span>预计时间：20–30 分钟</span>
            <span>更新：2026 年 8 月</span>
          </div>
          <div className="guide-principle">
            <strong>唯一默认流程</strong>
            <span>先推荐、律师确认后执行；AI 最多执行到“待律师复核”。</span>
          </div>
        </header>

        <div className="guide-layout guide-layout-readme">
          <aside className="guide-toc">
            <p className="panel-label">目录</p>
            <nav aria-label="手册目录">
              <a href="#finish-line">完成标准</a>
              <a href="#roles">先理解四个部分</a>
              <a href="#before-install">安装前准备</a>
              <a href="#install">下载安装 WorkBuddy</a>
              <a href="#first-setup">首次设置</a>
              <a href="#demo">第一次完整演练</a>
              <a href="#prompts">Prompt 复制区</a>
              <a href="#materials">材料与文件命名</a>
              <a href="#skills">模式、专家与 Skill</a>
              <a href="#workflow">六阶段工作流</a>
              <a href="#review">律师复核清单</a>
              <a href="#troubleshooting">常见问题</a>
              <a href="#admin">管理员上线前检查</a>
            </nav>
            <Link className="back-link" href="/">← 返回 AI 工作台</Link>
          </aside>

          <article className="guide-article guide-readme">
            <section id="finish-line" className="guide-section">
              <p className="section-index">00</p>
              <h2>你做到什么才算“安装完成”</h2>
              <p>不是看到 WorkBuddy 图标就算完成。以下六项全部满足，才算可以进入团队试用。</p>
              <ul className="readme-checklist">
                <li>□ WorkBuddy 可以正常打开并登录。</li>
                <li>□ 能进入“虞律团队 AI 工作流试验”项目，而不是自己新建一个同名项目。</li>
                <li>□ 能看到团队计划栏、资源库以及项目材料。</li>
                <li>□ 能找到并召唤“法律 AI 工作流总入口”。</li>
                <li>□ 能用本页连接测试 Prompt 得到正确回复。</li>
                <li>□ 能用虚拟材料把一个任务推进到“待律师复核”，且没有自动批准、归档或对外发送。</li>
              </ul>
              <div className="guide-callout guide-callout-warning">
                <strong>第一次演练禁止使用真实客户材料</strong>
                <p>先用团队管理员提供的虚拟材料验证安装、权限和流程。虚拟演练通过后，再由经办律师决定是否在获授权的项目中使用真实材料。</p>
              </div>
            </section>

            <section id="roles" className="guide-section">
              <p className="section-index">01</p>
              <h2>先理解四个部分</h2>
              <p className="readme-lead">一句话记忆：在 WorkBuddy 里工作，用总入口选能力，用 Skill 做标准动作，最后由律师负责。</p>
              <div className="role-grid">
                <div><h3>WorkBuddy</h3><p>实际工作的地方。项目、计划、材料、任务、专家、Skill 和成果都在这里组织。</p></div>
                <div><h3>虞律 AI 工作台网页</h3><p>类似工具目录和 README。用来查“有什么能力、适合什么任务、需要什么材料”，网页本身不读取客户文件。</p></div>
                <div><h3>法律 AI 工作流总入口</h3><p>团队的任务路由专家。它先理解任务、推荐 Skill、列出缺口，得到律师确认后才执行。</p></div>
                <div><h3>经办律师</h3><p>决定立场、范围和风险边界，确认事实，复核成果，并手动批准、归档及对外发送。</p></div>
              </div>
              <div className="readme-route" aria-label="四部分关系">
                <span>你在 WorkBuddy 发起任务</span><b>→</b><span>总入口推荐 Skill</span><b>→</b><span>律师确认</span><b>→</b><span>Skill 执行</span><b>→</b><span>律师复核</span>
              </div>
            </section>

            <section id="before-install" className="guide-section">
              <p className="section-index">02</p>
              <h2>安装前准备</h2>
              <h3>请先向团队管理员取得</h3>
              <ul className="guide-checklist">
                <li>团队项目邀请；项目名称应为“虞律团队 AI 工作流试验”。</li>
                <li>团队管理员姓名及出现问题时的联系方法。</li>
                <li>首次演练用的虚拟任务说明或虚拟材料包。</li>
                <li>确认你应当能看到的专家名称：“法律 AI 工作流总入口”。</li>
              </ul>
              <h3>电脑和账号准备</h3>
              <div className="guide-table system-table" role="table" aria-label="系统要求">
                <div role="row"><strong role="columnheader">设备</strong><strong role="columnheader">最低要求</strong><strong role="columnheader">下载选择</strong></div>
                <div role="row"><span role="cell">Mac Apple 芯片（M1/M2/M3/M4 等）</span><span role="cell">macOS 12.0+</span><span role="cell">Mac ARM64 / Apple 芯片</span></div>
                <div role="row"><span role="cell">Mac Intel 芯片</span><span role="cell">macOS 12.0+</span><span role="cell">Mac X64 / Intel</span></div>
                <div role="row"><span role="cell">Windows 电脑</span><span role="cell">Windows 10 及以上</span><span role="cell">Windows x64（兼容 ARM64）</span></div>
              </div>
              <ul className="guide-checklist">
                <li>准备可以扫码登录的微信。</li>
                <li>确认电脑可以正常联网，并设置 Chrome、Safari 或 Edge 为默认浏览器。</li>
                <li>预留一个虚拟演练文件夹，不要直接选择“桌面”“下载”或整个“文稿”作为工作空间。</li>
              </ul>
            </section>

            <section id="install" className="guide-section">
              <p className="section-index">03</p>
              <h2>下载安装 WorkBuddy</h2>
              <p>只从官方入口下载：<a className="inline-link" href="https://www.workbuddy.cn/work/" target="_blank" rel="noreferrer">WorkBuddy 官方下载页</a>。</p>

              <h3>Mac：先判断芯片，再安装</h3>
              <ol className="readme-steps">
                <li><strong>查看芯片。</strong><span>点击屏幕左上角苹果图标 →“关于本机”。看到 Apple M 系列就选 Apple 芯片；看到 Intel 就选 Intel。</span></li>
                <li><strong>下载正确版本。</strong><span>M 系列选择“.dmg（Apple 芯片）”；Intel 选择“.dmg（Intel）”。</span></li>
                <li><strong>打开安装包。</strong><span>下载完成后双击 <code>.dmg</code> 文件。</span></li>
                <li><strong>安装应用。</strong><span>把 WorkBuddy 图标拖到 Applications（应用程序）文件夹，等待复制完成。</span></li>
                <li><strong>推出安装盘。</strong><span>在 Finder 左侧找到已挂载的 WorkBuddy，点击推出；安装包可在确认可用后删除。</span></li>
                <li><strong>第一次打开。</strong><span>按 <code>Command + 空格</code>，输入 WorkBuddy 并打开。如系统询问是否打开从互联网下载的应用，核对名称后选择打开。</span></li>
              </ol>

              <h3>Windows：按安装向导完成</h3>
              <ol className="readme-steps">
                <li><strong>下载 Windows 版本。</strong><span>在官方下载页选择 Windows x64（兼容 ARM64）。</span></li>
                <li><strong>双击安装包。</strong><span>打开下载完成的安装程序；如出现系统确认，先核对发布来源和应用名称。</span></li>
                <li><strong>按向导安装。</strong><span>同意协议 → 保持默认安装路径 → 确认开始菜单文件夹 → 建议创建桌面快捷方式 → 点击安装。</span></li>
                <li><strong>完成并启动。</strong><span>安装结束后点击完成，从桌面或开始菜单打开 WorkBuddy。</span></li>
              </ol>

              <h3>登录</h3>
              <ol className="readme-steps">
                <li><strong>点击登录。</strong><span>WorkBuddy 会调用默认浏览器打开登录页面。</span></li>
                <li><strong>阅读并勾选协议。</strong><span>确认《服务条款》和《隐私协议》后继续。</span></li>
                <li><strong>微信扫码完成登录。</strong><span>扫码后在手机端确认，浏览器完成后会自动返回客户端。</span></li>
                <li><strong>检查更新。</strong><span>在左下角个人中心或头像菜单中点击“检查更新”，确保使用团队要求的版本。</span></li>
              </ol>
              <div className="guide-callout">
                <strong>你应该看到什么</strong>
                <p>WorkBuddy 主界面可以正常显示左侧导航、新建任务入口和个人头像；关闭并重新打开后仍保持登录。</p>
              </div>
              <p className="source-note">官方参考：<a href="https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Installation-Mac-Guide" target="_blank" rel="noreferrer">Mac 安装指南</a> · <a href="https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Installation-Win-Guide" target="_blank" rel="noreferrer">Windows 安装指南</a></p>
            </section>

            <section id="first-setup" className="guide-section">
              <p className="section-index">04</p>
              <h2>首次设置：不要直接开始真实工作</h2>
              <h3>步骤 1：加入正确的团队项目</h3>
              <ol className="readme-steps">
                <li><strong>打开管理员发来的项目邀请。</strong><span>使用与 WorkBuddy 登录相同的账号接受。</span></li>
                <li><strong>进入项目。</strong><span>确认标题是“虞律团队 AI 工作流试验”。不要为解决“看不到项目”而自行新建同名项目。</span></li>
                <li><strong>检查四个入口。</strong><span>至少应看到项目对话或任务、计划栏、资源库，以及项目可用的专家/Skill。</span></li>
              </ol>

              <h3>步骤 2：找到“法律 AI 工作流总入口”</h3>
              <ol className="readme-steps">
                <li><strong>点击左侧“专家”。</strong><span>进入“我的专家”或项目配置的专家区域。</span></li>
                <li><strong>搜索完整名称。</strong><span>输入“法律 AI 工作流总入口”。如果有相似名称，选择说明中包含“先推荐、律师确认后执行”的版本。</span></li>
                <li><strong>召唤专家。</strong><span>进入该专家的对话界面，再发送下面的连接测试 Prompt。</span></li>
              </ol>
              <PromptBlock label="Prompt 01｜连接测试" description="确认你选对专家；不读文件、不调用 Skill。" prompt={connectionPrompt} />

              <h3>步骤 3：设置本地工作空间</h3>
              <ol className="readme-steps">
                <li><strong>新建虚拟演练文件夹。</strong><span>例如 <code>YULAW-DEMO-首次演练</code>，不要放在真实案件文件夹里。</span></li>
                <li><strong>在新任务中选择该文件夹。</strong><span>点击工作空间或文件夹选择入口，在系统文件选择器中选中它，无需手工输入路径。</span></li>
                <li><strong>选择“默认权限”。</strong><span>不要开启完全访问。看到文件修改、工作空间外访问或外部连接请求时，先看清路径和动作再决定。</span></li>
                <li><strong>第一次优先用“问一问（Ask）”。</strong><span>只做连接和需求确认；复杂任务需要先看执行计划时用“想一想（Plan）”，律师确认后才进入“做一做（Craft）”。</span></li>
                <li><strong>模型保持团队默认。</strong><span>不要为了测试随意切换多个模型；模型选择不改变律师复核责任。</span></li>
              </ol>
              <p className="source-note">官方参考：<a href="https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Task-Bar" target="_blank" rel="noreferrer">新建任务栏、模式和工作空间</a> · <a href="https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Permission-Modes" target="_blank" rel="noreferrer">默认权限与安全沙箱</a></p>
            </section>

            <section id="demo" className="guide-section">
              <p className="section-index">05</p>
              <h2>第一次完整跑通：虚拟任务演练</h2>
              <p>建议管理员先准备一个不含真实客户信息的虚拟材料包。没有文件也可以完成“材料清点 + Skill 推荐”，但不要假装已经完成正式审阅。</p>
              <div className="demo-brief">
                <strong>建议演练任务</strong>
                <p>完全虚拟的 PE/VC 融资文件审阅：虚拟公司 A 拟接受虚拟基金 B 投资，团队代表公司方，只验证材料清点、Skill 推荐和律师确认停点。</p>
              </div>
              <ol className="demo-runbook">
                <li><span>1</span><div><h3>建立任务</h3><p>名称写“YULAW-DEMO｜PEVC 文件审阅｜你的姓名｜日期”，状态放在“待收件”。</p></div></li>
                <li><span>2</span><div><h3>添加虚拟材料</h3><p>把虚拟文件放进当前演练工作空间；在对话中逐一写出文件名，不要只说“都在文件夹里”。</p></div></li>
                <li><span>3</span><div><h3>材料清点</h3><p>复制 Prompt 02。核对 WorkBuddy 列出的文件名和版本，正确后再把状态改为“材料已确认”。</p></div></li>
                <li><span>4</span><div><h3>只做 Skill 推荐</h3><p>复制 Prompt 03。此时不得直接审阅文件或生成成果。</p></div></li>
                <li><span>5</span><div><h3>律师确认</h3><p>经办律师确认首选 Skill、公司方立场、文件范围、输出格式和截止时间。</p></div></li>
                <li><span>6</span><div><h3>启动执行</h3><p>复制 Prompt 04，把【】内字段填完整。执行开始后状态改为“生成中”。</p></div></li>
                <li><span>7</span><div><h3>处理停点</h3><p>出现事实缺口或冲突时，使用 Prompt 05。未确认前不让 AI 继续猜测。</p></div></li>
                <li><span>8</span><div><h3>接收成果</h3><p>在右侧“产物”和“变更”中核对生成文件、保存位置和修改记录，将状态设为“待律师复核”。</p></div></li>
                <li><span>9</span><div><h3>律师复核</h3><p>先使用 Prompt 06 做机器自检，再由律师逐项核验。演练阶段不需要进入“已批准”。</p></div></li>
              </ol>
              <div className="guide-callout">
                <strong>演练通过标准</strong>
                <p>总入口先推荐、律师确认后才执行；成果可以找到；任务停在“待律师复核”；没有读取工作空间外文件，没有自动分享、批准或归档。</p>
              </div>
            </section>

            <section id="prompts" className="guide-section prompt-library">
              <p className="section-index">06</p>
              <h2>Prompt 复制区</h2>
              <p>点击右上角“复制 Prompt”，粘贴到“法律 AI 工作流总入口”的对话框。所有【】都需要替换；不能确认的地方请明确写“待确认”。</p>
              <PromptBlock label="Prompt 01｜连接测试" description="确认专家和控制原则，不读取材料。" prompt={connectionPrompt} />
              <PromptBlock label="Prompt 02｜材料清点" description="只确认文件、版本和缺口，不开始正文工作。" prompt={inventoryPrompt} />
              <PromptBlock label="Prompt 03｜Skill 推荐" description="只推荐 1–3 个能力，等待律师确认。" prompt={recommendPrompt} />
              <PromptBlock label="Prompt 04｜确认采用 Skill 并执行" description="律师确认范围后才发送，自动执行最多到待律师复核。" prompt={executePrompt} />
              <PromptBlock label="Prompt 05｜暂停并列确认问题" description="遇到缺口、冲突或选择题时先停下。" prompt={clarificationPrompt} />
              <PromptBlock label="Prompt 06｜律师复核清单" description="让 AI 做交付前自检，但不替律师批准。" prompt={reviewPrompt} />
              <PromptBlock label="Prompt 07｜只汇报进度" description="不希望它继续执行时，用结构化方式询问状态。" prompt={statusPrompt} />
              <PromptBlock label="Prompt 08｜立即停止" description="发现范围、权限或材料错误时立即刹车。" prompt={stopPrompt} />
            </section>

            <section id="materials" className="guide-section">
              <p className="section-index">07</p>
              <h2>材料放在哪里、文件怎么命名</h2>
              <h3>三个位置不要混用</h3>
              <div className="guide-table material-table" role="table" aria-label="材料位置">
                <div role="row"><strong role="columnheader">位置</strong><strong role="columnheader">放什么</strong><strong role="columnheader">不要放什么</strong></div>
                <div role="row"><span role="cell">获授权的项目工作空间</span><span role="cell">本项目合同、附件、任务说明、项目成果</span><span role="cell">其他客户材料、整个个人文稿目录</span></div>
                <div role="row"><span role="cell">团队资源库</span><span role="cell">团队批准的通用模板、公开法规资料、使用规范</span><span role="cell">未经批准的客户文件、个人临时版本</span></div>
                <div role="row"><span role="cell">虞律 AI 工作台网页</span><span role="cell">只查看工具说明和本手册</span><span role="cell">任何客户材料、案号、姓名或任务正文</span></div>
              </div>

              <h3>推荐文件夹结构</h3>
              <pre className="folder-tree"><code>{`YYYYMMDD-客户简称-事项简称/
├── 01-输入材料/
├── 02-批准模板与参考/
├── 03-AI工作成果/
└── 04-律师复核与最终稿/`}</code></pre>

              <h3>文件命名</h3>
              <p><code>文件主题_日期_v版本_来源.扩展名</code></p>
              <ul className="guide-checklist">
                <li>示例：<code>投资协议_20260816_v03_客户反馈.docx</code></li>
                <li>示例：<code>股东协议_20260816_v02_我方修订.docx</code></li>
                <li>不要使用“最新版”“最终版2”“新建文档”等无法判断先后的名称。</li>
                <li>发送任务时把实际文件名写入 Prompt，并说明哪个是当前版本、哪个只是参考。</li>
              </ul>

              <h3>材料确认前逐项勾选</h3>
              <ul className="readme-checklist">
                <li>□ 文件可以打开，不是空文件、损坏文件或临时锁定文件。</li>
                <li>□ 已删除或隔离明显重复、过期和无关文件。</li>
                <li>□ 当前版本和上一版本标识清楚。</li>
                <li>□ 委托方立场、适用法域和目标成果已经写明。</li>
                <li>□ 真实材料已获授权进入当前项目。</li>
              </ul>
            </section>

            <section id="skills" className="guide-section">
              <p className="section-index">08</p>
              <h2>问一问、想一想、做一做；专家和 Skill 怎么选</h2>
              <div className="guide-table mode-table" role="table" aria-label="工作模式选择">
                <div role="row"><strong role="columnheader">模式</strong><strong role="columnheader">什么时候用</strong><strong role="columnheader">虞律团队默认做法</strong></div>
                <div role="row"><span role="cell">问一问（Ask）</span><span role="cell">了解情况、清点材料、推荐 Skill</span><span role="cell">第一次接触任务先用它</span></div>
                <div role="row"><span role="cell">想一想（Plan）</span><span role="cell">复杂、多步骤、需要先确认执行计划</span><span role="cell">并购、尽调、批量审阅优先考虑</span></div>
                <div role="row"><span role="cell">做一做（Craft）</span><span role="cell">已经确认范围，需要生成或修改文件</span><span role="cell">律师确认 Skill、材料和输出后再用</span></div>
              </div>
              <h3>专家和 Skill 的区别</h3>
              <ul className="guide-rules">
                <li><strong>专家：</strong>决定从什么角度理解任务以及如何组织工作。这里优先使用“法律 AI 工作流总入口”。</li>
                <li><strong>Skill：</strong>完成某一类标准动作，例如 PE/VC 文件审阅、并购结构规划、标书制作或合同受控起草。</li>
                <li><strong>连接器 / MCP：</strong>按授权访问外部数据库或服务。只有任务确实需要、项目已经授权时才启用。</li>
              </ul>
              <h3>工作台中的状态怎么理解</h3>
              <div className="status-legend">
                <p><strong>已接入：</strong>团队环境已经可以使用。</p>
                <p><strong>本地 Skill：</strong>需要确认当前电脑或 WorkBuddy 是否已安装、启用。</p>
                <p><strong>可安装：</strong>可以按详情页来源下载，但应先核验来源、权限和许可。</p>
                <p><strong>建设中 / 规划中：</strong>仅表示路线图，不应声称已经执行。</p>
              </div>
              <p className="source-note">官方参考：<a href="https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Expert-Center" target="_blank" rel="noreferrer">专家</a> · <a href="https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market" target="_blank" rel="noreferrer">Skill 安装与启用</a></p>
            </section>

            <section id="workflow" className="guide-section">
              <p className="section-index">09</p>
              <h2>六阶段工作流：每一步谁负责</h2>
              <ol className="guide-flow" aria-label="任务状态流程">
                {workflowStages.map((stage, index) => <li key={stage}><span>{index + 1}</span><strong>{stage}</strong></li>)}
              </ol>
              <div className="workflow-detail-table" role="table" aria-label="六阶段职责">
                <div role="row"><strong>阶段</strong><strong>进入条件</strong><strong>此阶段要做什么</strong><strong>谁确认</strong></div>
                <div role="row"><span>待收件</span><span>任务刚建立</span><span>写清目标、期限、负责人和材料清单</span><span>发起人</span></div>
                <div role="row"><span>材料已确认</span><span>文件和版本已经清点</span><span>确认立场、法域、范围、缺口及可使用权限</span><span>经办律师</span></div>
                <div role="row"><span>生成中</span><span>Skill 和输出已获确认</span><span>执行、校验；遇到冲突立即暂停</span><span>AI 执行，律师处理停点</span></div>
                <div role="row"><span>待律师复核</span><span>成果已生成并可定位</span><span>复核事实、法律、遗漏、格式、引用和保密</span><span>经办律师</span></div>
                <div role="row"><span>已批准</span><span>律师完成复核和必要修改</span><span>记录批准人、时间和批准版本</span><span>具名律师手动确认</span></div>
                <div role="row"><span>已归档</span><span>批准版本与过程文件齐备</span><span>按团队目录归档并保留版本记录</span><span>具名律师手动确认</span></div>
              </div>
              <div className="guide-callout guide-callout-warning"><strong>红线</strong><p>AI 不得自行把任务从“待律师复核”推进到“已批准”或“已归档”，也不得自行把成果发送给客户、对方或第三方。</p></div>
            </section>

            <section id="review" className="guide-section">
              <p className="section-index">10</p>
              <h2>律师复核清单</h2>
              <p>Prompt 06 只能辅助发现问题，不能替代下列人工复核。</p>
              <div className="review-grid">
                <section><h3>事实</h3><ul><li>主体、姓名、金额、比例、日期</li><li>文件版本和交易阶段</li><li>委托方立场</li></ul></section>
                <section><h3>法律</h3><ul><li>适用法域和法律依据</li><li>引用是否真实、现行、可核验</li><li>事实与法律结论是否区分</li></ul></section>
                <section><h3>完整性</h3><ul><li>用户要求的输出是否齐全</li><li>是否有遗漏条款或附件</li><li>待确认事项是否全部保留</li></ul></section>
                <section><h3>文件</h3><ul><li>批注、占位符和修订痕迹</li><li>格式、页码、目录和文件名</li><li>交付版本与复核版本一致</li></ul></section>
                <section><h3>保密</h3><ul><li>是否含其他客户信息</li><li>是否误用了公开位置</li><li>对外发送范围是否获批准</li></ul></section>
                <section><h3>记录</h3><ul><li>批准人和批准时间</li><li>最终版本号</li><li>归档位置及后续待办</li></ul></section>
              </div>
            </section>

            <section id="troubleshooting" className="guide-section">
              <p className="section-index">11</p>
              <h2>常见问题：按现象排查</h2>
              <dl className="troubleshooting-list troubleshooting-detailed">
                <div><dt>下载后打不开或版本选错</dt><dd>Mac 先到“关于本机”核对 Apple 芯片或 Intel；确认 macOS 12+。Windows 确认 Windows 10+。删除错误安装包后从官方下载页重新下载。</dd></div>
                <div><dt>点击登录没有反应</dt><dd>先设置 Chrome、Safari 或 Edge 为默认浏览器，完全退出 WorkBuddy 后重开；也可以复制登录链接到默认浏览器完成验证。</dd></div>
                <div><dt>看不到“虞律团队 AI 工作流试验”</dt><dd>不要自行新建同名项目。确认接受邀请的账号与 WorkBuddy 登录账号一致，把账号标识和项目邀请截图发给管理员。</dd></div>
                <div><dt>专家或 Skill 不可见</dt><dd>刷新项目，进入“专家 / 我的专家”核对名称；Skill 则到“已安装”确认是否启用。仍不存在时联系管理员，不得假装已经调用。</dd></div>
                <div><dt>文件无法读取</dt><dd>检查文件能否在本机打开、是否加密、是否为临时文件；确认文件在当前工作空间。不要把客户文件移到公开位置来绕过读取问题。</dd></div>
                <div><dt>弹出权限确认</dt><dd>看清动作、完整路径和影响范围。工作空间外访问、批量修改、上传、删除或陌生脚本一律先取消，让 WorkBuddy 解释为什么需要。</dd></div>
                <div><dt>它跳过推荐直接开始执行</dt><dd>立即发送 Prompt 08，停止后重新选择“法律 AI 工作流总入口”，再用 Prompt 03 明确“先不要执行”。</dd></div>
                <div><dt>结果找不到</dt><dd>查看右侧“产物”“工作空间文件”和“变更”；再发送 Prompt 07，要求列出准确文件名和保存位置。</dd></div>
                <div><dt>结果看起来不对</dt><dd>不要批准。停在“待律师复核”，列出具体偏差，补充立场、模板、版本和输出要求，再决定是否重新执行。</dd></div>
                <div><dt>仍无法解决</dt><dd>保存不含客户内容的错误截图、时间、系统版本和 WorkBuddy 版本，先交团队管理员；产品问题可参考官方 FAQ 或联系官方支持。</dd></div>
              </dl>
              <p className="source-note">官方参考：<a href="https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/FAQ" target="_blank" rel="noreferrer">WorkBuddy 常见问题</a>（官方支持邮箱：workbuddy@tencent.com）</p>
            </section>

            <section id="admin" className="guide-section">
              <p className="section-index">12</p>
              <h2>管理员上线前检查</h2>
              <p>下周让团队安装前，管理员应先完成以下准备，否则新人会卡在“装好了但看不到项目/专家”。</p>
              <ul className="readme-checklist admin-checklist">
                <li>□ 已确定统一的 WorkBuddy 版本与官方下载入口。</li>
                <li>□ 已邀请全部试用成员加入“虞律团队 AI 工作流试验”。</li>
                <li>□ 已确认成员能看到计划栏和团队资源库。</li>
                <li>□ “法律 AI 工作流总入口”已向试用成员可见。</li>
                <li>□ 首轮使用的 Skill 已安装、启用并完成虚拟测试。</li>
                <li>□ 已准备不含真实客户数据的虚拟演练材料。</li>
                <li>□ 默认权限和“待律师复核”停点已经写入项目规则。</li>
                <li>□ 已指定一名安装答疑人和一名法律成果复核人。</li>
                <li>□ 已把本手册的访问权限开放给参加试用的团队成员。</li>
              </ul>
              <h3>每位成员的验收回执</h3>
              <pre className="acceptance-template"><code>{`姓名：【填写】
电脑系统：【Mac Apple 芯片 / Mac Intel / Windows】
WorkBuddy 版本：【填写】
已进入团队项目：【是 / 否】
已看到法律 AI 工作流总入口：【是 / 否】
连接测试通过：【是 / 否】
虚拟任务已到待律师复核：【是 / 否】
遇到的问题：【填写；没有写“无”】`}</code></pre>
            </section>
          </article>
        </div>
      </main>

      <footer className="site-footer">
        <p>虞律团队 · 内部工作入口</p>
        <p>工具结果仅供工作辅助，关键结论须由经办律师复核。</p>
      </footer>
    </div>
  );
}
