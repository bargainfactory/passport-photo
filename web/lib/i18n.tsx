"use client";

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  type ReactNode,
} from "react";

export const LOCALES = [
  "en", "es", "fr", "de", "pt", "ar", "zh", "ja", "ko", "hi", "ru", "tr",
] as const;
export type Locale = (typeof LOCALES)[number];

export const LOCALE_NAMES: Record<Locale, string> = {
  en: "English",
  es: "Espanol",
  fr: "Francais",
  de: "Deutsch",
  pt: "Portugues",
  ar: "العربية",
  zh: "中文",
  ja: "日本語",
  ko: "한국어",
  hi: "हिन्दी",
  ru: "Русский",
  tr: "Turkce",
};

export const RTL_LOCALES: readonly Locale[] = ["ar"];

type Messages = Record<string, string>;

const loaders: Record<Locale, () => Promise<{ default: Messages }>> = {
  en: () => import("@/messages/en"),
  es: () => import("@/messages/es"),
  fr: () => import("@/messages/fr"),
  de: () => import("@/messages/de"),
  pt: () => import("@/messages/pt"),
  ar: () => import("@/messages/ar"),
  zh: () => import("@/messages/zh"),
  ja: () => import("@/messages/ja"),
  ko: () => import("@/messages/ko"),
  hi: () => import("@/messages/hi"),
  ru: () => import("@/messages/ru"),
  tr: () => import("@/messages/tr"),
};

interface I18nContextValue {
  locale: Locale;
  setLocale: (l: Locale) => void;
  t: (key: string, params?: Record<string, string | number>) => string;
  dir: "ltr" | "rtl";
}

const I18nContext = createContext<I18nContextValue | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("en");
  const [messages, setMessages] = useState<Messages>({});
  const [enMessages, setEnMessages] = useState<Messages>({});
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    const stored = typeof window !== "undefined"
      ? (localStorage.getItem("locale") as Locale | null)
      : null;
    if (stored && LOCALES.includes(stored)) {
      setLocaleState(stored);
    } else if (typeof navigator !== "undefined") {
      const browserLang = navigator.language.split("-")[0] as Locale;
      if (LOCALES.includes(browserLang)) setLocaleState(browserLang);
    }
    setHydrated(true);
  }, []);

  useEffect(() => {
    loaders.en().then((m) => setEnMessages(m.default));
  }, []);

  useEffect(() => {
    loaders[locale]().then((m) => setMessages(m.default));
    if (typeof document !== "undefined") {
      document.documentElement.lang = locale;
      document.documentElement.dir = RTL_LOCALES.includes(locale) ? "rtl" : "ltr";
    }
  }, [locale]);

  const setLocale = useCallback((l: Locale) => {
    setLocaleState(l);
    if (typeof window !== "undefined") localStorage.setItem("locale", l);
  }, []);

  const t = useCallback(
    (key: string, params?: Record<string, string | number>): string => {
      let str = messages[key] || enMessages[key] || key;
      if (params) {
        for (const [k, v] of Object.entries(params)) {
          str = str.replaceAll(`{${k}}`, String(v));
        }
      }
      return str;
    },
    [messages, enMessages],
  );

  const dir: "ltr" | "rtl" = RTL_LOCALES.includes(locale) ? "rtl" : "ltr";

  if (!hydrated) return <>{children}</>;

  return (
    <I18nContext.Provider value={{ locale, setLocale, t, dir }}>
      {children}
    </I18nContext.Provider>
  );
}

const fallback: I18nContextValue = {
  locale: "en",
  setLocale: () => {},
  t: (key) => key,
  dir: "ltr",
};

export function useTranslation() {
  const ctx = useContext(I18nContext);
  return ctx ?? fallback;
}
