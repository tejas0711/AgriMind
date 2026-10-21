import { useRef } from "react";
import { useLanguage } from "../i18n/LanguageContext";

const CROPS = ["", "Tomato", "Wheat", "Rice (Paddy)", "Cotton", "Soybean", "Onion", "Sugarcane", "Chickpea (Gram)"];

export default function InputPanel({
  fileName,
  onFileSelect,
  location,
  onLocationChange,
  crop,
  onCropChange,
  onAnalyze,
  loading,
  error,
}) {
  const fileInputRef = useRef(null);
  const { t, cropLabel } = useLanguage();

  return (
    <div className="surface-card rounded-3xl border border-soil-300/70 p-5 md:p-6 space-y-5">
      <div className="flex items-center gap-3 pb-1">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-leaf-500 text-white shadow-sm">
          <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5" aria-hidden="true">
            <path d="M12 16V4m0 0L7.5 8.5M12 4l4.5 4.5M5 14v4.5A1.5 1.5 0 0 0 6.5 20h11a1.5 1.5 0 0 0 1.5-1.5V14" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        <div>
          <p className="font-display text-lg font-semibold text-soil-900">{t("step1Title")}</p>
        </div>
      </div>

      <div>
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="group w-full text-left px-4 py-4 rounded-xl border-2 border-dashed border-soil-300/80 hover:border-leaf-500 hover:bg-leaf-500/5 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-leaf-500 bg-soil-50/80 text-sm"
        >
          <span className="flex items-center gap-3">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white text-leaf-700 shadow-sm group-hover:text-leaf-600">
              <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5" aria-hidden="true">
                <path d="M7 3.75h6l4.25 4.5v12H7a2 2 0 0 1-2-2v-12a2.5 2.5 0 0 1 2-2.5Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
                <path d="M13 4v5h4M8 13h6m-6 3h6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
            </span>
            <span className="min-w-0">
              <span className="block truncate font-medium text-soil-900">
                {fileName || t("step1Placeholder")}
              </span>
            </span>
          </span>
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={(e) => e.target.files?.[0] && onFileSelect(e.target.files[0])}
        />
      </div>

      <div>
        <label htmlFor="farm-location" className="block text-xs font-mono uppercase tracking-wider text-soil-600 mb-2">
          {t("step2Title")}
        </label>
        <input
          id="farm-location"
          type="text"
          value={location}
          onChange={(e) => onLocationChange(e.target.value)}
          placeholder={t("step2Placeholder")}
          className="w-full px-4 py-3 rounded-xl border border-soil-300/80 bg-white/90 text-sm shadow-sm transition focus:outline-none focus:ring-2 focus:ring-leaf-500 focus:border-leaf-500"
        />
        <p className="mt-1.5 text-xs leading-relaxed text-soil-500">{t("locationHelper")}</p>
      </div>

      <div>
        <label htmlFor="crop-choice" className="block text-xs font-mono uppercase tracking-wider text-soil-600 mb-2">
          {t("step3Title")}
        </label>
        <select
          id="crop-choice"
          value={crop}
          onChange={(e) => onCropChange(e.target.value)}
          className="w-full px-4 py-3 rounded-xl border border-soil-300/80 bg-white/90 text-sm shadow-sm transition focus:outline-none focus:ring-2 focus:ring-leaf-500 focus:border-leaf-500"
        >
          <option value="">{t("cropAutoRank")}</option>
          {CROPS.filter(Boolean).map((c) => (
            <option key={c} value={c}>
              {cropLabel(c)}
            </option>
          ))}
        </select>
        <p className="mt-1.5 text-xs leading-relaxed text-soil-500">{t("cropHelper")}</p>
      </div>

      {error && (
        <p role="alert" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-xl px-3 py-2">{error}</p>
      )}

      <button
        onClick={onAnalyze}
        disabled={loading}
        className="group w-full py-3.5 rounded-xl bg-leaf-600 hover:bg-leaf-700 active:scale-[0.99] disabled:opacity-50 disabled:cursor-not-allowed text-white font-display font-semibold tracking-wide shadow-[0_8px_20px_rgba(69,107,40,0.2)] transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-leaf-500 focus-visible:ring-offset-2"
      >
        {loading ? (
          <span className="inline-flex items-center justify-center gap-2">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" aria-hidden="true" />
            {t("analyzing")}
          </span>
        ) : t("analyze")}
      </button>
    </div>
  );
}
