import { useLanguage } from "../i18n/LanguageContext";
import { Languages } from "lucide-react";

export default function LanguageSwitcher({ className = "" }) {
  const { lang, setLang, languages } = useLanguage();

  return (
    <div
      className={`inline-flex items-center gap-1.5 rounded-lg border border-soil-200 dark:border-[#235347] bg-white dark:bg-[#163832] p-1 text-xs shadow-soft ${className}`}
      role="group"
      aria-label="Select interface language"
    >
      <Languages className="h-3.5 w-3.5 text-forest-800 dark:text-[#DAF1DE] ml-1.5 shrink-0" aria-hidden="true" />
      <div className="flex items-center gap-0.5">
        {languages.map((l) => {
          const isActive = lang === l.code;
          return (
            <button
              key={l.code}
              type="button"
              onClick={() => setLang(l.code)}
              aria-pressed={isActive}
              className={`rounded-md px-2.5 py-1 text-xs font-semibold transition-all ${
                isActive
                  ? "bg-forest-900 dark:bg-[#235347] text-white shadow-sm ring-1 ring-forest-900/20 dark:ring-[#8EB69B]/40"
                  : "text-forest-900 dark:text-white hover:bg-forest-50 dark:hover:bg-[#235347]/70"
              }`}
            >
              {l.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
