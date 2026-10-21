import { createContext, useContext, useState, useCallback, useMemo } from "react";
import { translations, statusLabels, nutrientLabels, fertilizerTypeLabels, cropLabels, applyTodayLabels, recommendationLabels, LANGUAGES } from "./translations";

const STORAGE_KEY = "agrimind:lang";
const LanguageContext = createContext(null);

function getInitialLanguage() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored && translations[stored]) return stored;
  } catch (_) {
    // localStorage unavailable (private browsing etc.) - fall back silently
  }
  return "en";
}

export function LanguageProvider({ children }) {
  const [lang, setLangState] = useState(getInitialLanguage);

  const setLang = useCallback((next) => {
    if (!translations[next]) return;
    setLangState(next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch (_) {
      // ignore storage errors
    }
  }, []);

  const value = useMemo(() => {
    const dict = translations[lang] || translations.en;
    const t = (key, ...args) => {
      const entry = dict[key] ?? translations.en[key];
      return typeof entry === "function" ? entry(...args) : entry;
    };
    const statusLabel = (status) => (statusLabels[lang] || statusLabels.en)[status] || status;
    const nutrientLabel = (nutrient) => (nutrientLabels[lang] || nutrientLabels.en)[nutrient] || nutrient;
    const fertilizerTypeLabel = (ftype) => (fertilizerTypeLabels[lang] || fertilizerTypeLabels.en)[ftype] || ftype;
    const cropLabel = (crop) => (cropLabels[lang] || cropLabels.en)[crop] || crop;
    return { lang, setLang, t, statusLabel, nutrientLabel, fertilizerTypeLabel, cropLabel, languages: LANGUAGES };
  }, [lang, setLang]);

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error("useLanguage must be used within a LanguageProvider");
  return ctx;
}
