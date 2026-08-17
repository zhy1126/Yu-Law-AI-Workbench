document.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-copy-prompt]");
  if (!button) return;
  const prompt = document.getElementById(button.dataset.copyPrompt);
  if (!prompt) return;
  try {
    await navigator.clipboard.writeText(prompt.textContent.trim());
    const original = button.textContent;
    button.textContent = "已复制";
    window.setTimeout(() => { button.textContent = original; }, 1600);
  } catch (_error) {
    button.textContent = "请手动复制";
  }
});
