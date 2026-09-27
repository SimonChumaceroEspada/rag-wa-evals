"use client";

import { useState } from "react";
import {
  AssistantRuntimeProvider,
  useLocalRuntime,
  type ChatModelAdapter,
} from "@assistant-ui/react";
import { Thread } from "@/components/thread.aui";
import { Button } from "@/components/ui/button";

const API = process.env.NEXT_PUBLIC_API_URL ?? "https://rag-wa-evals.onrender.com";
let currentLang = "es";

const RagAdapter: ChatModelAdapter = {
  async run({ messages, abortSignal }) {
    const last = [...messages].reverse().find((m) => m.role === "user");
    const q = last?.content?.[0]?.type === "text" ? last.content[0].text : "";
    const ctrl = new AbortController();
    const kill = setTimeout(() => ctrl.abort(), 5 * 60 * 1000);
    const onAbort = () => ctrl.abort();
    abortSignal?.addEventListener("abort", onAbort);
    try {
      const r = await fetch(`${API}/ask?q=${encodeURIComponent(q)}&lang=${currentLang}`, {
        signal: ctrl.signal,
      });
      const d = await r.json();
      const srcs = (d.sources ?? [])
        .map((s: { source: string; score: number }, i: number) => `- [${i + 1}] ${s.source} (${Number(s.score).toFixed(3)})`)
        .join("\n");
      const text = `${d.answer ?? "?"}\n\n**Fuentes:**\n${srcs}`;
      return { content: [{ type: "text", text }] };
    } finally {
      clearTimeout(kill);
      abortSignal?.removeEventListener("abort", onAbort);
    }
  },
};

export default function Home() {
  const [lang, setLang] = useState("es");
  const [wake, setWake] = useState(false);
  const runtime = useLocalRuntime(RagAdapter);
  return (
    <main className="mx-auto flex h-dvh max-w-2xl flex-col gap-2 p-4">
      <div className="flex items-center gap-2">
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
        <Thread />
      </AssistantRuntimeProvider>
    </main>
  );
}
