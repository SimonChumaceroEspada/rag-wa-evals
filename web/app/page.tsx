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
import { Loader2 } from "lucide-react";
import { UiContext, useUi, type Lang, type UiValue } from "@/lib/ui";

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

const WAIT = {
  search: { es: "Buscando en tus documentos", en: "Searching your documents" },
  model: { es: "El modelo está tardando en responder", en: "The model is taking longer than usual" },
  wake: { es: "Despertando el servidor gratuito (~1 min)", en: "Waking the free server (~1 min)" },
} as const;

function RunStatus() {
  const { lang } = useUi();
  const [, tick] = useState(0);
  const [awake, setAwake] = useState<boolean | null>(null);
  const run = typeof window !== "undefined" ? window.__rag : undefined;
  const active = !!run && !run.done;

  useEffect(() => {
    const id = setInterval(() => tick((t) => t + 1), 1000);
    return () => clearInterval(id);
  }, []);

  // Mientras espera, mide el servidor: si no responde el ping, está dormido;
  // si responde y aun así tarda, el cuello de botella es el modelo.
  useEffect(() => {
    if (!active) {
      setAwake(null);
      return;
    }
    let alive = true;
    const ping = async () => {
      try {
        const t0 = Date.now();
        await fetch(`${API}/openapi.json`, { cache: "no-store" });
        if (alive) setAwake(Date.now() - t0 < 4000);
      } catch {
        if (alive) setAwake(false);
      }
    };
    void ping();
    const id = setInterval(() => void ping(), 3000);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, [active]);

  if (!run || run.done) return null;
  const s = Math.floor((Date.now() - run.start) / 1000);
  const key = awake === false ? "wake" : awake === true && s > 10 ? "model" : "search";
  return (
    <div className="flex items-center gap-2 rounded-lg border p-3 text-sm">
      <Loader2 className="size-4 shrink-0 animate-spin text-muted-foreground" />
      <span>
        {WAIT[key][lang]} <span className="text-muted-foreground">({s}s)</span>
      </span>
    </div>
  );
}
export default function Home() {
  const [lang, setLang] = useState<Lang>("en");
  const [sidebar, setSidebar] = useState(true);
  const [wake, setWake] = useState(false);
  const [server, setServer] = useState<"checking" | "awake" | "sleepy">("checking");
  // Despertar al abrir + mantener caliente mientras la pestaña viva:
  // el plan gratis duerme a los 15 min y el cron de Actions llega tarde
  // (medido: 5 corridas en 20 h), así que la web se pega cada 5 min.
  useEffect(() => {
    let alive = true;
    const check = () => {
      const t0 = Date.now();
      fetch(`${API}/openapi.json`, { cache: "no-store" })
        .then((r) => {
          if (alive) setServer(r.ok && Date.now() - t0 < 8000 ? "awake" : "sleepy");
        })
        .catch(() => {
          if (alive) setServer("sleepy");
        });
    };
    check();
    const iv = setInterval(check, 5 * 60_000);
    return () => {
      alive = false;
      clearInterval(iv);
    };
  }, []);
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
      <main className="flex h-dvh w-full overflow-hidden">
        <Sidebar />
        <div className="flex min-h-0 min-w-0 flex-1 flex-col">
          <div className="flex shrink-0 items-center gap-2 px-4 py-2 md:px-10">
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
          <p className="shrink-0 px-4 text-sm text-muted-foreground md:px-10">
            {lang === "es"
              ? "Demo RAG bilingüe (AcmeTech sintético). Gratis: ~1 min la primera vez."
              : "Bilingual RAG demo (synthetic AcmeTech). Free tier: ~1 min the first time."}
            {server !== "awake" && (
              <span className="text-amber-600">
                {" "}
                {server === "sleepy"
                  ? lang === "es"
                    ? "· despertando el servidor, podés preguntar igual"
                    : "· waking the server, feel free to ask anyway"
                  : lang === "es"
                    ? "· comprobando servidor…"
                    : "· checking server…"}
              </span>
            )}
            <button className="ml-2 underline" onClick={() => setWake((w) => !w)}>
              {wake ? (lang === "es" ? "ocultar" : "hide") : lang === "es" ? "¿por qué tarda?" : "why so slow?"}
            </button>
          </p>
          {wake && (
            <p className="shrink-0 px-4 text-sm text-amber-600 md:px-10">
              {lang === "es"
                ? "El servidor gratuito duerme sin tráfico; la primera pregunta lo despierta (~1 min). Las siguientes vuelan."
                : "The free server sleeps without traffic; the first question wakes it (~1 min). The rest fly."}
            </p>
          )}
          <AssistantRuntimeProvider runtime={runtime}>
            <div className="mx-auto w-full max-w-3xl shrink-0 px-4 pt-4">
              <RunStatus />
            </div>
            <Thread />
          </AssistantRuntimeProvider>
        </div>
      </main>
    </UiContext.Provider>
  );
}
