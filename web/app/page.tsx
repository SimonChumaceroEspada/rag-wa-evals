"use client";

import { useEffect, useState } from "react";
import {
  AssistantRuntimeProvider,
  useLocalRuntime,
  type ChatModelAdapter,
} from "@assistant-ui/react";
import { Thread } from "@/components/thread.aui";
import { Button } from "@/components/ui/button";
import { Sidebar, SidebarToggle } from "@/components/sidebar";
import { UiContext, type Lang, type UiValue } from "@/lib/ui";

const API = process.env.NEXT_PUBLIC_API_URL ?? "https://rag-wa-evals.onrender.com";
let currentLang = "en";

const RagAdapter: ChatModelAdapter = {
  async run({ messages, abortSignal }) {
    const last = [...messages].reverse().find((m) => m.role === "user");
    const q = last?.content?.[0]?.type === "text" ? last.content[0].text : "";
    if (typeof window !== "undefined") window.__rag = { start: Date.now(), done: false };
    const ctrl = new AbortController();
    const kill = setTimeout(() => ctrl.abort(), 5 * 60 * 1000);
    const onAbort = () => ctrl.abort();
    abortSignal?.addEventListener("abort", onAbort);
    try {
      const r = await fetch(`${API}/ask?q=${encodeURIComponent(q)}&lang=${currentLang}`, {
        signal: ctrl.signal,
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const d = await r.json();
      if (!d || !d.answer) throw new Error("respuesta vacía");
      const srcs = (d.sources ?? [])
        .map((s: { source: string; score: number }, i: number) => `- [${i + 1}] ${s.source} (${Number(s.score).toFixed(3)})`)
        .join("\n");
      const text = `${d.answer ?? "?"}\n\n**Fuentes:**\n${srcs}`;
      if (typeof window !== "undefined") window.__rag = { start: 0, done: true };
      return { content: [{ type: "text", text }] };
    } catch (e) {
      if (typeof window !== "undefined") window.__rag = { start: 0, done: true };
      const msg = e instanceof Error && e.name === "AbortError"
        ? "⏱️ +5 min sin respuesta: el servidor gratuito sigue dormido o saturado. Reintenta en 1 min."
        : `⚠️ Falló la petición (${e instanceof Error ? e.message : e}). Revisa tu conexión y reintenta.`;
      return { content: [{ type: "text", text: msg }] };
    } finally {
      clearTimeout(kill);
      abortSignal?.removeEventListener("abort", onAbort);
    }
  },
};

declare global { var __rag: { start: number; done: boolean } | undefined }

const STAGES = ["buscando en 52 PDFs…", "fusionando denso + BM25…", "reordenando top-20…", "redactando con citas…"];

function RunStatus() {
  const [, tick] = useState(0);
  const [num, setNum] = useState(7);
  const [msg, setMsg] = useState("Adivina 1-10 mientras esperas:");
  const [tries, setTries] = useState(0);
  useEffect(() => {
    const id = setInterval(() => tick((t) => t + 1), 1000);
    return () => clearInterval(id);
  }, []);
  const run = typeof window !== "undefined" ? window.__rag : undefined;
  if (!run || run.done) return null;
  const s = Math.floor((Date.now() - run.start) / 1000);
  return (
    <div className="rounded-lg border p-3 text-sm">
      <p>⏳ {STAGES[Math.min(Math.floor(s / 15), STAGES.length - 1)]} ({s}s)</p>
      <p className="mt-2">
        {msg}{" "}
        {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => (
          <button key={n} className="mx-0.5 rounded border px-1" onClick={() => {
            setTries((t) => t + 1);
            setMsg(n === num ? `¡Sí! era el ${num} en ${tries + 1} intentos 🎉` : n < num ? "más alto…" : "más bajo…");
            if (n === num) { setNum(1 + Math.floor(Math.random() * 10)); setTries(0); }
          }}>{n}</button>
        ))}
      </p>
    </div>
  );
}
export default function Home() {
  const [lang, setLang] = useState<Lang>("en");
  const [sidebar, setSidebar] = useState(true);
  const [wake, setWake] = useState(false);
  const runtime = useLocalRuntime(RagAdapter);
  const ui: UiValue = {
    lang,
    sidebar,
    toggleSidebar: () => setSidebar((s) => !s),
    send: (text) => runtime.thread.append(text),
    reset: () => runtime.thread.reset(),
  };
  return (
    <UiContext.Provider value={ui}>
      <main className="flex h-dvh w-full">
        <Sidebar />
        <div className="flex min-h-0 min-w-0 flex-1 flex-col px-4 md:px-10">
          <div className="flex items-center gap-2 py-2">
            <SidebarToggle />
            <h1 className="text-xl font-bold">rag-wa-evals</h1>
            <div className="ml-auto flex gap-1">
              {(["es", "en"] as const).map((l) => (
                <Button
                  key={l}
                  size="sm"
                  variant={lang === l ? "default" : "outline"}
                  onClick={() => { setLang(l); currentLang = l; }}
                >
                  {l.toUpperCase()}
                </Button>
              ))}
            </div>
          </div>
          <p className="text-sm text-muted-foreground">
            Demo RAG bilingüe (AcmeTech sintético). Gratis: ~1 min la primera vez.
            <button className="ml-2 underline" onClick={() => setWake((w) => !w)}>
              {wake ? "ocultar" : "¿por qué tarda?"}
            </button>
          </p>
          {wake && (
            <p className="text-sm text-amber-600">
              El servidor gratuito duerme sin tráfico; la primera pregunta lo despierta (~1 min). Las siguientes vuelan.
            </p>
          )}
          <AssistantRuntimeProvider runtime={runtime}>
            <div className="mx-auto w-full max-w-3xl pt-4">
              <RunStatus />
            </div>
            <Thread />
          </AssistantRuntimeProvider>
        </div>
      </main>
    </UiContext.Provider>
  );
}
