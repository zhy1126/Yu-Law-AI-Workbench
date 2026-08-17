const state = {
  dashboard: null,
  cases: [],
  deadlines: [],
  tasks: [],
  documents: [],
  query: "",
  currentView: "dashboard",
  weeklyReport: null,
};

const byId = (id) => document.getElementById(id);

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined && text !== null) node.textContent = String(text);
  return node;
}

function showToast(message) {
  const toast = byId("toast");
  toast.textContent = message;
  toast.hidden = false;
  window.setTimeout(() => { toast.hidden = true; }, 2400);
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    credentials: "same-origin",
    ...options,
    headers: options.body ? { "Content-Type": "application/json", ...(options.headers || {}) } : options.headers,
  });
  const contentType = response.headers.get("content-type") || "";
  const result = contentType.includes("application/json") ? await response.json() : null;
  if (!response.ok) {
    if (response.status === 401) showLogin();
    throw new Error(result?.error || "操作失败，请稍后重试");
  }
  return result;
}

function showLogin() {
  byId("login-screen").hidden = false;
  byId("app-shell").hidden = true;
}

function showApp() {
  byId("login-screen").hidden = true;
  byId("app-shell").hidden = false;
}

function switchView(name) {
  state.currentView = name;
  document.querySelectorAll(".view").forEach((panel) => panel.classList.toggle("is-active", panel.dataset.panel === name));
  document.querySelectorAll(".nav-item").forEach((button) => button.classList.toggle("is-active", button.dataset.view === name));
  if (name === "cases") renderCases();
}

function badge(text, tone = "") {
  return element("span", `badge ${tone}`.trim(), text || "—");
}

function mainSubCell(main, sub) {
  const cell = element("div");
  cell.append(element("span", "cell-main", main || "—"));
  if (sub) cell.append(element("span", "cell-sub", sub));
  return cell;
}

function formatTime(value) {
  if (!value) return "—";
  return value.replace("T", " ").slice(0, 16);
}

function caseFor(caseId) {
  return state.cases.find((item) => item.id === caseId) || { title: "未知案件", caseNumber: caseId };
}

function emptyRow(columnCount, message = "暂无记录") {
  const row = element("tr");
  const cell = element("td", "empty-row", message);
  cell.colSpan = columnCount;
  row.append(cell);
  return row;
}

function appendTextCell(row, text, className = "") {
  row.append(element("td", className, text || "—"));
}

function itemTone(item) {
  if (["极重要", "高"].includes(item.reminderLevel || item.priority)) return "danger";
  if (["重要", "中"].includes(item.reminderLevel || item.priority)) return "warning";
  return "";
}

function dashboardRow(item) {
  const row = element("tr");
  const type = element("td");
  type.append(badge(item.itemType, itemTone(item)));
  row.append(type);
  const matter = mainSubCell(item.title, item.caseNumber);
  const itemCell = element("td");
  itemCell.append(matter);
  row.append(itemCell);
  appendTextCell(row, item.caseTitle);
  appendTextCell(row, item.owner || "—");
  appendTextCell(row, formatTime(item.dueAt));
  return row;
}

function renderDashboard() {
  const data = state.dashboard;
  if (!data) return;
  byId("count-overdue").textContent = data.counts.overdue;
  byId("count-today").textContent = data.counts.today;
  byId("count-next3").textContent = data.counts.next3Days;
  byId("count-next7").textContent = data.counts.next7Days;
  byId("count-preservation").textContent = data.counts.preservation;
  byId("nav-dashboard-count").textContent = data.counts.overdue + data.counts.today + data.counts.next3Days;
  byId("nav-cases-count").textContent = data.caseCount;
  byId("nav-deadlines-count").textContent = data.deadlineCount;
  byId("nav-tasks-count").textContent = data.taskCount;
  byId("nav-documents-count").textContent = data.documentCount;
  byId("today-label").textContent = data.generatedFor;

  const emergencyRows = data.emergencyItems.map(dashboardRow);
  byId("emergency-body").replaceChildren(...(emergencyRows.length ? emergencyRows : [emptyRow(5, "暂无紧急事项")]));

  const hearings = data.upcomingHearings.map((item) => {
    const card = element("article", "stack-item");
    card.append(element("strong", "", `${item.title} · ${formatTime(item.dueAt)}`), element("span", "", item.caseTitle), element("span", "", item.caseNumber));
    return card;
  });
  byId("hearing-list").replaceChildren(...(hearings.length ? hearings : [element("p", "empty-row", "未来 30 天暂无开庭")]));

  const preservationRows = data.preservationItems.map((item) => {
    const row = element("tr");
    const type = element("td"); type.append(badge(item.deadlineType, "warning")); row.append(type);
    appendTextCell(row, item.title); appendTextCell(row, item.caseTitle); appendTextCell(row, formatTime(item.dueAt));
    const alert = element("td"); alert.append(badge("保全预警", "warning")); row.append(alert);
    return row;
  });
  byId("preservation-body").replaceChildren(...(preservationRows.length ? preservationRows : [emptyRow(5, "暂无 60 天内保全/续封提醒")]));
}

function matchesCase(item) {
  const query = state.query.trim().toLocaleLowerCase("zh-CN");
  const stage = byId("filter-stage").value;
  const type = byId("filter-type").value;
  const risk = byId("filter-risk").value;
  if (stage && item.procedureStage !== stage) return false;
  if (type && item.caseType !== type) return false;
  if (risk && item.riskLevel !== risk) return false;
  if (!query) return true;
  return [item.title, item.caseNumber, item.institution, item.adjudicator, item.cause, item.notes, item.leadLawyer, item.handlingLawyer, item.reviewLawyer, ...(item.tags || [])]
    .join(" ").toLocaleLowerCase("zh-CN").includes(query);
}

function renderCases() {
  const rows = state.cases.filter(matchesCase).map((item) => {
    const row = element("tr");
    const titleCell = element("td"); titleCell.append(mainSubCell(item.title, item.caseNumber)); row.append(titleCell);
    const stageCell = element("td"); stageCell.append(badge(item.caseType), badge(item.procedureStage)); row.append(stageCell);
    const institutionCell = element("td"); institutionCell.append(mainSubCell(item.institution, item.adjudicator)); row.append(institutionCell);
    const teamCell = element("td"); teamCell.append(mainSubCell(item.handlingLawyer || item.leadLawyer, item.reviewLawyer ? `复核：${item.reviewLawyer}` : "")); row.append(teamCell);
    const nextCell = element("td"); nextCell.append(mainSubCell(item.nextAction || "待补充下一事项", item.status)); row.append(nextCell);
    const tagsCell = element("td"); tagsCell.append(badge(`${item.riskLevel || "中"}风险`, item.riskLevel === "高" ? "danger" : "")); (item.tags || []).forEach((tag) => tagsCell.append(badge(tag))); row.append(tagsCell);
    const actions = element("td", "row-actions");
    const view = element("button", "row-button", "查看"); view.type = "button"; view.addEventListener("click", () => openCaseDetail(item.id));
    const edit = element("button", "row-button", "编辑"); edit.type = "button"; edit.addEventListener("click", () => openEntityForm("case", item));
    actions.append(view, edit); row.append(actions);
    return row;
  });
  byId("cases-body").replaceChildren(...(rows.length ? rows : [emptyRow(7, "没有符合筛选条件的案件")]));
}

function rowActionButton(label, handler) {
  const button = element("button", "row-button", label);
  button.type = "button";
  button.addEventListener("click", handler);
  return button;
}

function renderDeadlines() {
  const rows = state.deadlines.map((item) => {
    const matter = caseFor(item.caseId); const row = element("tr");
    const type = element("td"); type.append(badge(item.deadlineType, itemTone(item))); row.append(type);
    const title = element("td"); title.append(mainSubCell(item.title, item.notes)); row.append(title);
    const caseCell = element("td"); caseCell.append(mainSubCell(matter.title, matter.caseNumber)); row.append(caseCell);
    appendTextCell(row, formatTime(item.dueAt));
    const reminder = element("td"); reminder.append(badge(item.reminderLevel, itemTone(item))); row.append(reminder);
    appendTextCell(row, item.status);
    const actions = element("td", "row-actions");
    if (item.status !== "已完成") actions.append(rowActionButton("完成", () => quickUpdate("deadlines", item.id, { status: "已完成", completedAt: new Date().toISOString() })));
    actions.append(rowActionButton("编辑", () => openEntityForm("deadline", item))); row.append(actions);
    return row;
  });
  byId("deadlines-body").replaceChildren(...(rows.length ? rows : [emptyRow(7)]));
}

function renderTasks() {
  const rows = state.tasks.map((item) => {
    const matter = caseFor(item.caseId); const row = element("tr");
    const priority = element("td"); priority.append(badge(item.priority, itemTone(item))); row.append(priority);
    const title = element("td"); title.append(mainSubCell(item.title, item.notes)); row.append(title);
    const caseCell = element("td"); caseCell.append(mainSubCell(matter.title, matter.caseNumber)); row.append(caseCell);
    appendTextCell(row, item.owner); appendTextCell(row, formatTime(item.dueAt)); appendTextCell(row, item.status);
    const actions = element("td", "row-actions");
    if (item.status !== "已完成") actions.append(rowActionButton("完成", () => quickUpdate("tasks", item.id, { status: "已完成" })));
    actions.append(rowActionButton("编辑", () => openEntityForm("task", item))); row.append(actions);
    return row;
  });
  byId("tasks-body").replaceChildren(...(rows.length ? rows : [emptyRow(7)]));
}

function renderDocuments() {
  const rows = state.documents.map((item) => {
    const matter = caseFor(item.caseId); const row = element("tr");
    const type = element("td"); type.append(badge(item.documentType)); row.append(type);
    const title = element("td"); title.append(mainSubCell(item.title, item.notes)); row.append(title);
    const caseCell = element("td"); caseCell.append(mainSubCell(matter.title, matter.caseNumber)); row.append(caseCell);
    appendTextCell(row, formatTime(item.dueAt)); appendTextCell(row, item.submissionMethod); appendTextCell(row, item.status);
    const actions = element("td", "row-actions"); actions.append(rowActionButton("编辑", () => openEntityForm("document", item))); row.append(actions);
    return row;
  });
  byId("documents-body").replaceChildren(...(rows.length ? rows : [emptyRow(7)]));
}

function populateCaseSelects() {
  document.querySelectorAll("[data-case-select]").forEach((select) => {
    const options = state.cases.map((item) => {
      const option = element("option", "", item.caseNumber ? `${item.title}（${item.caseNumber}）` : item.title);
      option.value = item.id;
      return option;
    });
    select.replaceChildren(...options);
  });
}

function normalizeForInput(value, input) {
  if (input.type === "datetime-local" && value) return String(value).slice(0, 16);
  if (Array.isArray(value)) return value.join("、");
  return value ?? "";
}

function openEntityForm(kind, record = null) {
  const form = byId(`${kind}-form`);
  document.querySelectorAll("#entity-modal form").forEach((item) => { item.hidden = item !== form; });
  form.reset();
  form.dataset.recordId = record?.id || "";
  form.querySelectorAll("[name]").forEach((input) => {
    if (record && Object.hasOwn(record, input.name)) input.value = normalizeForInput(record[input.name], input);
  });
  const titles = { case: "案件", deadline: "期限", task: "待办", document: "文书" };
  byId("entity-modal-title").textContent = `${record ? "编辑" : "新增"}${titles[kind]}`;
  byId("entity-message").textContent = "";
  byId("entity-modal").hidden = false;
  form.querySelector("input, select, textarea")?.focus();
}

function closeModal(id) {
  byId(id).hidden = true;
}

function formPayload(form) {
  const payload = Object.fromEntries(new FormData(form).entries());
  if (form.dataset.kind === "case") {
    payload.tags = String(payload.tags || "").split(/[，,、]/).map((tag) => tag.trim()).filter(Boolean);
    payload.amount = payload.amount ? Number(payload.amount) : null;
  }
  payload.actor = "虞律师";
  return payload;
}

async function submitEntityForm(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const kinds = { case: "cases", deadline: "deadlines", task: "tasks", document: "documents" };
  const collection = kinds[form.dataset.kind];
  const recordId = form.dataset.recordId;
  const path = recordId ? `/api/${collection}/${recordId}` : `/api/${collection}`;
  byId("entity-message").textContent = "正在保存…";
  try {
    await api(path, { method: recordId ? "PATCH" : "POST", body: JSON.stringify(formPayload(form)) });
    closeModal("entity-modal");
    showToast("已保存，本周周报会据此自动更新");
    await loadAll();
  } catch (error) {
    byId("entity-message").textContent = error.message;
  }
}

async function quickUpdate(collection, id, changes) {
  try {
    await api(`/api/${collection}/${id}`, { method: "PATCH", body: JSON.stringify({ ...changes, actor: "虞律师" }) });
    showToast("状态已更新");
    await loadAll();
  } catch (error) {
    showToast(error.message);
  }
}

function detailList(title, items, formatter) {
  const group = element("section", "detail-group"); group.append(element("h3", "", title));
  const list = element("div", "stack-list");
  const rows = items.map((item) => { const row = element("div", "stack-item"); row.append(element("strong", "", formatter(item)), element("span", "", item.status || "")); return row; });
  list.replaceChildren(...(rows.length ? rows : [element("p", "empty-row", "暂无记录")])); group.append(list); return group;
}

async function openCaseDetail(caseId) {
  try {
    const item = await api(`/api/cases/${caseId}`);
    byId("case-detail-title").textContent = item.title;
    const summary = element("div", "detail-summary");
    [["案号", item.caseNumber], ["阶段", item.procedureStage], ["机构", item.institution], ["我方身份", item.ourRole], ["风险", `${item.riskLevel} · ${item.riskReason || "未记录原因"}`], ["下一事项", item.nextAction]].forEach(([label, value]) => {
      const field = element("div", "detail-field"); field.append(element("span", "", label), element("strong", "", value || "—")); summary.append(field);
    });
    byId("case-detail-content").replaceChildren(
      summary,
      detailList("关键期限", item.deadlines, (entry) => `${formatTime(entry.dueAt)} · ${entry.title}`),
      detailList("待办事项", item.tasks, (entry) => `${entry.title} · ${entry.owner || "负责人待定"}`),
      detailList("文书状态", item.documents, (entry) => `${entry.documentType} · ${entry.title}`),
      detailList("跟进记录", item.followups, (entry) => `${entry.occurred_at || ""} · ${entry.content || ""}`),
    );
    byId("case-detail-modal").hidden = false;
  } catch (error) { showToast(error.message); }
}

function isoWeek(date = new Date()) {
  const current = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  const day = current.getUTCDay() || 7;
  current.setUTCDate(current.getUTCDate() + 4 - day);
  const yearStart = new Date(Date.UTC(current.getUTCFullYear(), 0, 1));
  const week = Math.ceil((((current - yearStart) / 86400000) + 1) / 7);
  return `${current.getUTCFullYear()}-W${String(week).padStart(2, "0")}`;
}

function weeklyItemText(item) {
  return `${item.caseTitle || "未知案件"}｜${item.title || item.summary || "事项"}${item.dueAt ? `｜${formatTime(item.dueAt)}` : ""}`;
}

async function openWeeklyReport() {
  try {
    state.weeklyReport = await api(`/api/weekly-report?week=${encodeURIComponent(isoWeek())}`);
    const labels = { progress: "本周进展", deadlineRisks: "期限风险", blocked: "受阻事项", pendingReview: "待律师复核", nextWeek: "下周计划" };
    const sections = Object.entries(labels).map(([key, title]) => {
      const section = element("section", "weekly-section"); section.append(element("h3", "", title));
      const list = element("ul"); const items = state.weeklyReport.sections[key] || [];
      (items.length ? items.map(weeklyItemText) : ["暂无"]).forEach((line) => list.append(element("li", "", line)));
      section.append(list); return section;
    });
    byId("weekly-sections").replaceChildren(...sections);
    byId("weekly-status").textContent = state.weeklyReport.saved
      ? (state.weeklyReport.hasUpdates ? "案件数据已有变化，当前展示已自动刷新；可重新保存快照。" : "已保存快照，案件数据暂无变化。")
      : "根据当前案件数据实时生成，尚未保存快照。";
    byId("weekly-modal").hidden = false;
  } catch (error) { showToast(error.message); }
}

async function saveWeeklyReport() {
  if (!state.weeklyReport) return;
  try {
    await api("/api/weekly-report", { method: "POST", body: JSON.stringify({ week: state.weeklyReport.week, sourceVersion: state.weeklyReport.sourceVersion, sections: state.weeklyReport.sections, status: "草稿" }) });
    showToast("周报快照已保存");
    await openWeeklyReport();
  } catch (error) { showToast(error.message); }
}

async function loadAll() {
  const includeClosed = byId("include-closed").checked;
  const [dashboard, cases, deadlines, tasks, documents] = await Promise.all([
    api("/api/dashboard"),
    api(`/api/cases?includeClosed=${includeClosed}`),
    api("/api/deadlines"),
    api("/api/tasks"),
    api("/api/documents"),
  ]);
  Object.assign(state, { dashboard, cases, deadlines, tasks, documents });
  populateCaseSelects();
  renderDashboard(); renderCases(); renderDeadlines(); renderTasks(); renderDocuments();
}

async function login(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const message = byId("login-message");
  message.textContent = "正在进入…";
  try {
    await api("/api/login", { method: "POST", body: JSON.stringify({ password: new FormData(form).get("password") }) });
    showApp(); form.reset(); message.textContent = ""; await loadAll();
  } catch (error) { message.textContent = error.message; }
}

async function logout() {
  try { await api("/api/logout", { method: "POST", body: JSON.stringify({}) }); } catch (_error) { /* session may already be gone */ }
  showLogin();
}

document.querySelectorAll(".nav-item").forEach((button) => button.addEventListener("click", () => switchView(button.dataset.view)));
document.querySelectorAll("[data-create]").forEach((button) => button.addEventListener("click", () => openEntityForm(button.dataset.create)));
document.querySelectorAll("[data-close]").forEach((button) => button.addEventListener("click", () => closeModal(button.dataset.close)));
document.querySelectorAll("#entity-modal form").forEach((form) => form.addEventListener("submit", submitEntityForm));
["filter-stage", "filter-type", "filter-risk"].forEach((id) => byId(id).addEventListener("change", renderCases));
byId("include-closed").addEventListener("change", loadAll);
byId("global-search").addEventListener("input", (event) => { state.query = event.target.value; if (state.query && state.currentView !== "cases") switchView("cases"); renderCases(); });
byId("weekly-report-button").addEventListener("click", openWeeklyReport);
byId("save-weekly-button").addEventListener("click", saveWeeklyReport);
byId("lock-button").addEventListener("click", logout);
byId("login-form").addEventListener("submit", login);

document.querySelectorAll(".modal-backdrop").forEach((backdrop) => backdrop.addEventListener("click", (event) => { if (event.target === backdrop) backdrop.hidden = true; }));
document.addEventListener("keydown", (event) => { if (event.key === "Escape") document.querySelectorAll(".modal-backdrop:not([hidden])").forEach((modal) => { modal.hidden = true; }); });

(async () => {
  try {
    const session = await api("/api/session");
    if (session.authenticated) { showApp(); await loadAll(); } else showLogin();
  } catch (_error) { showLogin(); }
})();
