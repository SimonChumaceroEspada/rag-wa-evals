"use client";

import { PanelLeftIcon, PlusIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { DEMO, useUi } from "@/lib/ui";

export const SidebarToggle = () => {
  const { toggleSidebar } = useUi();
  return (
    <Button variant="ghost" size="sm" aria-label="sidebar" className="size-8 p-0" onClick={toggleSidebar}>
      <PanelLeftIcon className="size-4" />
    </Button>
  );
};

export const Sidebar = () => {
  const { lang, send, reset, sidebar } = useUi();
  const t =
    lang === "es"
      ? { new: "Nuevo chat", demo: "Preguntas demo", foot: "RAG sobre 26 PDFs × 2 idiomas = 52 documentos · Ragas baseline" }
      : { new: "New chat", demo: "Demo questions", foot: "RAG over 26 PDFs × 2 languages = 52 documents · Ragas baseline" };

  if (!sidebar) return null;

  return (
    <aside className="flex h-full w-64 shrink-0 flex-col gap-3 border-r border-foreground/10 bg-muted/20 p-3">
      <Button variant="outline" size="sm" className="justify-start gap-2" onClick={reset}>
        <PlusIcon className="size-4" />
        {t.new}
      </Button>
      <p className="px-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {t.demo}
      </p>
      <nav className="flex flex-col gap-1 overflow-y-auto">
        {DEMO[lang].map((q) => (
          <button
            key={q}
            type="button"
            onClick={() => send(q)}
            className="rounded-lg px-2 py-1.5 text-left text-sm leading-snug text-muted-foreground transition-colors hover:bg-foreground/5 hover:text-foreground"
          >
            {q}
          </button>
        ))}
      </nav>
      <p className="mt-auto px-1 text-xs text-muted-foreground">{t.foot}</p>
    </aside>
  );
};
