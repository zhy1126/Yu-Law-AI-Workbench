import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "团队使用手册｜虞律团队 AI 工作台",
  description: "虞律团队安装 WorkBuddy、选择 Skill、执行任务及律师复核的简明手册",
};

const onboardingSteps = [
  {
    title: "安装 WorkBuddy",
    text: "使用团队管理员统一提供的官方安装入口完成安装，不要使用来源不明的安装包。",
  },
  {
    title: "登录并加入团队项目",
    text: "使用工作账号登录，加入“虞律团队 AI 工作流试验”，确认可以看到团队资源库与计划栏。",
  },
  {
    title: "找到工作流总入口",
    text: "在项目专家中打开“法律 AI 工作流总入口”。它负责理解任务并推荐 Skill，不直接替代律师作专业判断。",
  },
  {
    title: "准备任务和材料",
    text: "写清事项名称、委托方立场、任务目标、期限、材料清单与保密要求；客户文件只放在获授权的项目或本地工作区。",
  },
  {
    title: "先推荐、律师确认后执行",
    text: "先让总入口推荐 1–3 个 Skill。经办律师确认工具、范围和输出后，再启动正式执行。",
  },
  {
    title: "复核、批准与归档",
    text: "AI 自动执行最多到“待律师复核”。“已批准”“已归档”及任何对外发送均由经办律师手动完成。",
  },
];

const workflowStages = [
  "待收件",
  "材料已确认",
  "生成中",
  "待律师复核",
  "已批准",
  "已归档",
];

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
        <header className="guide-intro">
          <p className="hero-kicker">TEAM HANDBOOK · QUICK START</p>
          <h1>虞律团队 AI 工作流使用手册</h1>
          <p>
            给第一次使用 WorkBuddy 和虞律 AI 工作台的团队成员。按本页顺序操作，通常十分钟即可完成基础设置并发起第一个受控任务。
          </p>
          <div className="guide-principle">
            <strong>默认工作原则</strong>
            <span>先推荐、律师确认后执行；AI 生成到待律师复核为止。</span>
          </div>
        </header>

        <div className="guide-layout">
          <aside className="guide-toc">
            <p className="panel-label">本页目录</p>
            <nav aria-label="手册目录">
              <a href="#roles">先认识四个部分</a>
              <a href="#install">安装与首次设置</a>
              <a href="#workflow">标准工作流程</a>
              <a href="#prompts">可直接复制的指令</a>
              <a href="#skills">如何选择 Skill</a>
              <a href="#safety">材料与复核边界</a>
              <a href="#troubleshooting">常见问题</a>
            </nav>
            <Link className="back-link" href="/">← 返回 AI 工作台</Link>
          </aside>

          <article className="guide-article">
            <section id="roles" className="guide-section">
              <p className="section-index">01</p>
              <h2>先认识四个部分</h2>
              <div className="role-grid">
                <div>
                  <h3>WorkBuddy</h3>
                  <p>实际协作入口：承接项目、计划、材料、团队资源库、专家和任务进度。</p>
                </div>
                <div>
                  <h3>虞律 AI 工作台网页</h3>
                  <p>Skill 目录与说明书：查看流程地图、工具状态、输入输出和安装来源；网页本身不读取客户材料。</p>
                </div>
                <div>
                  <h3>法律 AI 工作流总入口</h3>
                  <p>任务路由专家：先理解任务，再推荐最合适的 Skill，待律师确认后才进入执行。</p>
                </div>
                <div>
                  <h3>经办律师</h3>
                  <p>决定工作范围、适用立场和风险边界，复核成果，并手动完成批准、归档及对外发送。</p>
                </div>
              </div>
            </section>

            <section id="install" className="guide-section">
              <p className="section-index">02</p>
              <h2>安装与首次设置</h2>
              <ol className="onboarding-list">
                {onboardingSteps.map((step, index) => (
                  <li key={step.title}>
                    <span>{String(index + 1).padStart(2, "0")}</span>
                    <div>
                      <h3>{step.title}</h3>
                      <p>{step.text}</p>
                    </div>
                  </li>
                ))}
              </ol>
              <div className="guide-callout">
                <strong>首次检查</strong>
                <p>能看到团队项目、资源库、计划栏和“法律 AI 工作流总入口”后，再开始处理任务；缺少任一项时联系项目管理员。</p>
              </div>
            </section>

            <section id="workflow" className="guide-section">
              <p className="section-index">03</p>
              <h2>标准工作流程</h2>
              <p>每项任务统一沿以下状态推进，状态是团队协作和责任边界，不是单纯的进度标签。</p>
              <ol className="guide-flow" aria-label="任务状态流程">
                {workflowStages.map((stage, index) => (
                  <li key={stage}>
                    <span>{index + 1}</span>
                    <strong>{stage}</strong>
                  </li>
                ))}
              </ol>
              <ul className="guide-rules">
                <li><strong>待收件：</strong>建立任务，写明目标、期限、负责人和材料清单。</li>
                <li><strong>材料已确认：</strong>经办律师确认版本、完整性、委托方立场及可使用范围。</li>
                <li><strong>生成中：</strong>按已确认的 Skill 和范围执行；校验失败时停在此处并报告。</li>
                <li><strong>待律师复核：</strong>AI 自动执行的终点。律师核对事实、法律依据、引用、数字、格式和遗漏。</li>
                <li><strong>已批准 / 已归档：</strong>只允许经办律师手动操作，不得由 AI 自动完成。</li>
              </ul>
            </section>

            <section id="prompts" className="guide-section">
              <p className="section-index">04</p>
              <h2>可直接复制的指令</h2>
              <h3>第一步：只做 Skill 推荐</h3>
              <pre><code>{`这是【项目/任务名称】。先不要执行。请根据我的任务说明和文件清单，只推荐 1–3 个最适合的 Skill；逐一说明匹配理由、所需输入、预期输出和主要风险。等我确认后再执行。`}</code></pre>
              <h3>第二步：确认后执行</h3>
              <pre><code>{`确认采用【Skill 名称】。委托方立场为【填写】，任务范围为【填写】，输出为【填写】。请只使用已确认材料执行，推进到“待律师复核”为止；不得自动批准、归档或对外发送。遇到事实缺口、规则冲突或材料版本不明时先停止并列出待确认项。`}</code></pre>
              <h3>材料不完整时</h3>
              <pre><code>{`先不要起草或审阅正文。请只检查现有材料是否足够，按“已有材料 / 缺失材料 / 需要律师确认的事实”输出清单。`}</code></pre>
            </section>

            <section id="skills" className="guide-section">
              <p className="section-index">05</p>
              <h2>如何选择 Skill</h2>
              <p>团队成员不需要一次安装全部 Skill。先由总入口按任务推荐，再查看工作台详情页确认输入、输出、适用范围和接入状态。</p>
              <div className="guide-table" role="table" aria-label="Skill 场景举例">
                <div role="row"><strong role="columnheader">工作场景</strong><strong role="columnheader">优先查找方向</strong></div>
                <div role="row"><span role="cell">报价函、标书、法律服务建议书、法律服务合同</span><span role="cell">文书制作类 Skill</span></div>
                <div role="row"><span role="cell">PE/VC 文件审阅、并购交易结构、尽职调查、IPO 准备</span><span role="cell">专业法律分析类 Skill</span></div>
                <div role="row"><span role="cell">脱敏、材料整理、项目空间和任务跟踪</span><span role="cell">数据安全与基础工作类 Skill</span></div>
              </div>
              <p className="guide-small">“可安装”表示可按详情页来源下载；“本地 Skill”或“已接入”的实际可用范围，以项目管理员当周配置为准。</p>
            </section>

            <section id="safety" className="guide-section">
              <p className="section-index">06</p>
              <h2>材料与复核边界</h2>
              <ul className="guide-checklist">
                <li>真实客户材料仅放入已获授权的 WorkBuddy 项目或本地工作区，不上传到公开网页、公开 GitHub 或无关项目。</li>
                <li>执行前确认文件版本、材料完整性、委托方立场、适用法域、截止时间和输出用途。</li>
                <li>调用威科先行等外部数据库时，以项目已授权的连接为准，并保留可核验的出处和检索日期。</li>
                <li>工具结果仅供工作辅助，关键结论须由经办律师复核；不把模型判断直接作为对外法律意见。</li>
                <li>任何对客户、对方或第三方的发送、分享、批准和归档均由律师手动确认。</li>
              </ul>
            </section>

            <section id="troubleshooting" className="guide-section">
              <p className="section-index">07</p>
              <h2>常见问题</h2>
              <dl className="troubleshooting-list">
                <div>
                  <dt>专家或 Skill 不可见</dt>
                  <dd>先确认已加入正确团队项目并刷新资源库；仍不可见时，将项目名称和截图发给管理员。</dd>
                </div>
                <div>
                  <dt>文件无法读取</dt>
                  <dd>检查文件是否仍在获授权的工作区、是否加密、是否为支持格式；不要为解决读取问题把客户文件移到公开位置。</dd>
                </div>
                <div>
                  <dt>不知道选哪个 Skill</dt>
                  <dd>不要猜。使用本页“第一步”指令，只让总入口做推荐，待律师确认后再执行。</dd>
                </div>
                <div>
                  <dt>结果与预期不一致</dt>
                  <dd>停在“待律师复核”，补充立场、范围、模板版本和具体偏差；不要直接批准或对外发送。</dd>
                </div>
              </dl>
            </section>
          </article>
        </div>
      </main>

      <footer className="site-footer">
        <p>虞律团队 · 内部工作入口</p>
        <p>AI 提效，专业判断始终由律师完成。</p>
      </footer>
    </div>
  );
}
