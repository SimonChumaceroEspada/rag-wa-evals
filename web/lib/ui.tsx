"use client";

import { createContext, useContext } from "react";

export type Lang = "es" | "en";

export type UiValue = {
  lang: Lang;
  send: (text: string) => void;
  reset: () => void;
  sidebar: boolean;
  toggleSidebar: () => void;
};

export const UiContext = createContext<UiValue>({
  lang: "en",
  send: () => {},
  reset: () => {},
  sidebar: true,
  toggleSidebar: () => {},
});

export const useUi = () => useContext(UiContext);

export const DEMO: Record<Lang, string[]> = {
  es: [
    "¿Qué uptime garantiza AcmeTech a Enterprise?",
    "¿Cuántos días de vacaciones al año hay?",
    "¿Qué es el acuerdo de confidencialidad?",
    "¿Cuánto tarda la respuesta a una incidencia P1?",
  ],
  en: [
    "What uptime does AcmeTech guarantee Enterprise?",
    "How many vacation days per year?",
    "Tell me about the coding practices.",
    "What is the P1 response time?",
  ],
};
