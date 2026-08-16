"use client";

import { useState } from "react";

type PromptBlockProps = {
  label: string;
  description: string;
  prompt: string;
};

export function PromptBlock({ label, description, prompt }: PromptBlockProps) {
  const [copyState, setCopyState] = useState<"idle" | "copied" | "failed">("idle");

  async function copyPrompt() {
    try {
      await navigator.clipboard.writeText(prompt);
      setCopyState("copied");
      window.setTimeout(() => setCopyState("idle"), 1800);
    } catch {
      setCopyState("failed");
    }
  }

  const buttonLabel = copyState === "copied" ? "已复制" : copyState === "failed" ? "请手动复制" : "复制 Prompt";

  return (
    <section className="prompt-block" aria-label={label}>
      <header>
        <div>
          <strong>{label}</strong>
          <p>{description}</p>
        </div>
        <button type="button" onClick={copyPrompt} aria-live="polite">
          {buttonLabel}
        </button>
      </header>
      <pre><code>{prompt}</code></pre>
    </section>
  );
}
