(() => {
  const viewButtons = [...document.querySelectorAll("[data-view-button]")];
  const views = [...document.querySelectorAll("[data-view]")];
  const cards = [...document.querySelectorAll("[data-tool-card]")];
  const categoryButtons = [...document.querySelectorAll("[data-category-filter]")];
  const clearButtons = [...document.querySelectorAll("[data-clear-filters]")];
  const search = document.querySelector("#tool-search");
  const status = document.querySelector("#status-filter");
  const count = document.querySelector("[data-result-count]");
  const empty = document.querySelector("[data-empty-state]");
  let category = "全部工具";

  function showView(name) {
    views.forEach((view) => { view.hidden = view.dataset.view !== name; });
    viewButtons.forEach((button) => {
      const active = button.dataset.viewButton === name;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-pressed", String(active));
    });
  }

  function applyFilters() {
    if (!search || !status || !count || !empty) return;
    const keyword = search.value.trim().toLocaleLowerCase("zh-CN");
    let visible = 0;
    cards.forEach((card) => {
      const matchesCategory = category === "全部工具" || card.dataset.category === category;
      const matchesStatus = status.value === "all" || card.dataset.status === status.value;
      const matchesSearch = !keyword || (card.dataset.search || "").includes(keyword);
      card.hidden = !(matchesCategory && matchesStatus && matchesSearch);
      if (!card.hidden) visible += 1;
    });
    count.textContent = String(visible);
    empty.hidden = visible !== 0;
    const filtered = category !== "全部工具" || status.value !== "all" || keyword !== "";
    clearButtons.forEach((button) => { button.hidden = !filtered; });
  }

  function resetFilters() {
    category = "全部工具";
    if (search) search.value = "";
    if (status) status.value = "all";
    categoryButtons.forEach((button) => {
      const active = button.dataset.categoryFilter === category;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-pressed", String(active));
    });
    applyFilters();
  }

  viewButtons.forEach((button) => button.addEventListener("click", () => showView(button.dataset.viewButton)));
  categoryButtons.forEach((button) => button.addEventListener("click", () => {
    category = button.dataset.categoryFilter;
    categoryButtons.forEach((candidate) => {
      const active = candidate === button;
      candidate.classList.toggle("is-active", active);
      candidate.setAttribute("aria-pressed", String(active));
    });
    applyFilters();
  }));
  search?.addEventListener("input", applyFilters);
  status?.addEventListener("change", applyFilters);
  clearButtons.forEach((button) => button.addEventListener("click", resetFilters));

  const stageButtons = [...document.querySelectorAll("[data-system-stage]")];
  const workflowTools = [...document.querySelectorAll("[data-workflow-tool]")];
  const workflowMessage = document.querySelector("[data-workflow-message]");
  stageButtons.forEach((button) => button.addEventListener("click", () => {
    const wasActive = button.classList.contains("is-active");
    stageButtons.forEach((candidate) => {
      candidate.classList.remove("is-active");
      candidate.setAttribute("aria-pressed", "false");
    });
    if (wasActive) {
      workflowTools.forEach((tool) => tool.classList.remove("is-dimmed"));
      if (workflowMessage) workflowMessage.textContent = "点击任一 Skill，可直接进入该工具的使用说明。";
      return;
    }
    button.classList.add("is-active");
    button.setAttribute("aria-pressed", "true");
    const stage = button.dataset.systemStage;
    workflowTools.forEach((tool) => tool.classList.toggle("is-dimmed", !(tool.dataset.systemStages || "").split("|").includes(stage)));
    if (workflowMessage) workflowMessage.innerHTML = `<strong>${stage}</strong>：已高亮本环节相关的 Skill。`;
  }));
})();
