import { useState, useEffect } from "react";
import { useLanguage } from "../i18n/LanguageContext";
import SoilCore from "./SoilCore";
import RecommendationPanel from "./RecommendationPanel";
import WeatherPanel from "./WeatherPanel";
import { getLocalizedSummary } from "../i18n/agriLocalizer";
import { getWeatherForecast, saveReport } from "../api";
import {
  Sparkles,
  MessageSquare,
  ArrowRight,
  ShieldCheck,
  AlertTriangle,
  RotateCcw,
  Info,
  Bookmark,
  Check,
  X,
  Lock,
} from "lucide-react";

export default function ResultsDashboard({
  result,
  isDemo,
  onAskAssistant,
  onNewUpload,
  currentUser = null,
  onOpenAuth = null,
}) {
  const { t, lang } = useLanguage();
  const localizedSummary = getLocalizedSummary(result, lang);

  const [appWindow, setAppWindow] = useState(result?.application_window || null);
  const [isRefreshingWeather, setIsRefreshingWeather] = useState(false);
  const [weatherError, setWeatherError] = useState(null);

  // Report Save State
  const [saveModalOpen, setSaveModalOpen] = useState(false);
  const [saveTitle, setSaveTitle] = useState("");
  const [saveNotes, setSaveNotes] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState(null);

  // Sync state if result updates from parent
  useEffect(() => {
    if (result?.application_window) {
      setAppWindow(result.application_window);
    }
  }, [result?.application_window]);

  if (!result) return null;

  const {
    soil,
    deficiencies = [],
    crop_scores = [],
    fertilizer_options = [],
    partial_failures = [],
    why,
    llm_explanation,
  } = result;

  const handleRefreshWeather = async (customLoc = null, coords = null) => {
    setIsRefreshingWeather(true);
    setWeatherError(null);
    try {
      const params = {};
      if (coords && coords.latitude != null && coords.longitude != null) {
        params.latitude = coords.latitude;
        params.longitude = coords.longitude;
      } else {
        const validLocName = typeof customLoc === "string" && customLoc.trim() ? customLoc.trim() : null;
        const location = validLocName || appWindow?.location_name || result.location_name || "Pune, Maharashtra";
        if (!validLocName && appWindow?.latitude != null && appWindow?.longitude != null) {
          params.latitude = appWindow.latitude;
          params.longitude = appWindow.longitude;
          params.location_name = location;
        } else {
          params.location_name = location;
        }
      }
      params.days = 5;

      const res = await getWeatherForecast(params);
      if (res) {
        if (res.application_window) {
          setAppWindow(res.application_window);
        } else if (res.days && res.days.length > 0) {
          setAppWindow({
            recommendation: "YES",
            apply_today: "GO",
            reason: "Forecast refreshed successfully.",
            forecast_summary: res.days[0],
            forecast_days: res.days,
            location_name: res.location_name || params.location_name,
            latitude: res.latitude,
            longitude: res.longitude,
            fetched_at: res.generated_at || new Date().toISOString(),
            current_temperature_c: res.current_temperature_c,
            current_condition: res.current_condition,
            is_available: true,
          });
        }
      }
    } catch (err) {
      setWeatherError(err.message || "Failed to refresh weather forecast from Open-Meteo.");
    } finally {
      setIsRefreshingWeather(false);
    }
  };

  // Compute key summary metrics
  const lowCount = deficiencies.filter((d) => d.status === "LOW").length;
  const isGo = appWindow?.apply_today === "GO";
  const primaryLow = deficiencies.find((d) => d.status === "LOW");

  function handleOpenSave() {
    if (!currentUser) {
      if (onOpenAuth) onOpenAuth();
      return;
    }
    setSaveTitle(`Soil Report - ${result?.selected_crop || "Farm Plot"}`);
    setSaveError(null);
    setSaveModalOpen(true);
  }

  async function handleSaveSubmit(e) {
    e.preventDefault();
    setIsSaving(true);
    setSaveError(null);

    try {
      const payload = {
        title: saveTitle.trim() || "Soil Analysis",
        farm_name: null,
        selected_crop: result?.selected_crop || null,
        soil_data: result?.soil || {},
        deficiencies: deficiencies || [],
        crop_scores: crop_scores || [],
        fertilizer_options: fertilizer_options || [],
        application_window: appWindow || null,
        evidence: [],
        explanation: localizedSummary || llm_explanation || why?.plain_language_summary || null,
        notes: saveNotes.trim() || null,
      };

      await saveReport(payload);
      setSaveSuccess(true);
      setTimeout(() => {
        setSaveModalOpen(false);
      }, 1200);
    } catch (err) {
      setSaveError(err.message || "Failed to save report.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="space-y-8 py-6 sm:py-8">
      {/* Partial Failures Warning Banner (Multi-Agent Fault Tolerance) */}
      {partial_failures && partial_failures.length > 0 && (
        <div
          role="alert"
          className="rounded-xl border border-amber-300 dark:border-amber-800 bg-amber-50/90 dark:bg-amber-950/50 p-4 text-xs sm:text-sm text-amber-950 dark:text-amber-200 flex items-start gap-3 shadow-soft"
        >
          <AlertTriangle className="h-5 w-5 text-amber-700 dark:text-amber-400 shrink-0 mt-0.5" />
          <div className="space-y-1 flex-1">
            <span className="font-bold uppercase tracking-wider text-[11px] text-amber-900 dark:text-amber-300">
              Partial Analysis Notice
            </span>
            <p className="leading-relaxed text-amber-900 dark:text-amber-300">
              Soil and crop analysis completed successfully, but some secondary services encountered issues:
            </p>
            <ul className="list-disc list-inside space-y-0.5 text-amber-800 dark:text-amber-400 text-xs">
              {partial_failures.map((msg, idx) => (
                <li key={idx}>{msg}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Dashboard Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl sm:text-3xl font-semibold text-forest-900 dark:text-white">
            {t("resultsHeading")}
          </h1>
          <p className="mt-1 text-sm text-soil-600 dark:text-white/90">
            {t("resultsSub")}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Save Report Button */}
          <button
            type="button"
            onClick={handleOpenSave}
            disabled={saveSuccess}
            className={`inline-flex items-center gap-1.5 rounded-xl px-3.5 py-2.5 text-xs font-semibold shadow-soft transition-colors ${
              saveSuccess
                ? "bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-700 cursor-default"
                : "border border-forest-900 dark:border-[#235347] bg-forest-900 dark:bg-[#235347] text-white hover:bg-forest-800 dark:hover:bg-[#2E6B5C]"
            }`}
            title={currentUser ? t("saveReportButton") : t("saveReportSignInPrompt")}
          >
            {saveSuccess ? (
              <>
                <Check className="h-4 w-4 text-emerald-700 dark:text-emerald-400" />
                <span>{t("saveReportSaved")}</span>
              </>
            ) : (
              <>
                <Bookmark className="h-4 w-4" />
                <span>{currentUser ? t("saveReportButton") : t("saveReportButton")}</span>
              </>
            )}
          </button>

          <button
            type="button"
            onClick={onAskAssistant}
            className="inline-flex items-center gap-1.5 rounded-xl bg-forest-900 dark:bg-[#235347] px-4 py-2.5 text-xs font-semibold text-white shadow-soft hover:bg-forest-800 dark:hover:bg-[#2E6B5C] transition-colors"
          >
            <MessageSquare className="h-4 w-4" />
            <span>{t("chatHeading")}</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </button>

          <button
            type="button"
            onClick={onNewUpload}
            className="inline-flex items-center gap-1.5 rounded-xl border border-soil-200 dark:border-[#235347] bg-white dark:bg-[#163832] px-3.5 py-2.5 text-xs font-medium text-forest-900 dark:text-[#FFFFFF] hover:bg-soil-100 dark:hover:bg-[#235347] transition-colors"
          >
            <RotateCcw className="h-4 w-4 text-soil-500 dark:text-[#8EB69B]" />
            <span>{t("step1Change")}</span>
          </button>
        </div>
      </div>

      {/* Top 3 Executive Summary Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="rounded-xl border border-soil-200 dark:border-[#235347] bg-white dark:bg-[#163832] p-4 shadow-soft space-y-1">
          <span className="text-[11px] font-mono uppercase tracking-wider text-soil-500 dark:text-[#8EB69B]">
            {t("completenessLabel")}
          </span>
          <p className="data-readout text-2xl font-bold text-forest-900 dark:text-[#FFFFFF]">
            {soil?.completeness ? `${Math.round(soil.completeness() * 100)}%` : "100%"}
          </p>
          <p className="text-xs text-soil-500 dark:text-[#8EB69B]">
            Key NPK & physical parameters parsed
          </p>
        </div>

        <div className="rounded-xl border border-soil-200 dark:border-[#235347] bg-white dark:bg-[#163832] p-4 shadow-soft space-y-1">
          <span className="text-[11px] font-mono uppercase tracking-wider text-soil-500 dark:text-[#8EB69B]">
            {t("primaryLimitingLabel")}
          </span>
          <p className="text-xl font-bold text-amber-900 dark:text-amber-300 truncate">
            {primaryLow ? primaryLow.nutrient.replace("_", " ").toUpperCase() : "None Detected"}
          </p>
          <p className="text-xs text-soil-500 dark:text-[#8EB69B]">
            {lowCount > 0 ? `${lowCount} nutrient(s) require amendment` : "Balanced fertility profile"}
          </p>
        </div>

        <div className="rounded-xl border border-soil-200 dark:border-[#235347] bg-white dark:bg-[#163832] p-4 shadow-soft space-y-1">
          <span className="text-[11px] font-mono uppercase tracking-wider text-soil-500 dark:text-[#8EB69B]">
            {t("timingStatusLabel")}
          </span>
          <div className="flex items-center gap-2">
            <span
              className={`rounded-full px-2.5 py-0.5 text-xs font-bold font-mono ${
                !appWindow || appWindow.is_available === false
                  ? "bg-soil-200 dark:bg-forest-800 text-soil-800 dark:text-soil-200"
                  : isGo
                  ? "bg-emerald-100 dark:bg-emerald-950 text-emerald-950 dark:text-emerald-300"
                  : "bg-amber-100 dark:bg-amber-950 text-amber-950 dark:text-amber-300"
              }`}
            >
              {!appWindow || appWindow.is_available === false
                ? "UNAVAILABLE"
                : isGo
                ? "SUITABLE TODAY"
                : "WAIT (WEATHER RISK)"}
            </span>
          </div>
          <p className="text-xs text-soil-500 dark:text-soil-400 truncate">
            {appWindow?.reason || "Based on live weather forecast"}
          </p>
        </div>
      </div>

      {/* Main Grid: Soil Core & Plain Terms & Weather on Left (no scrolling down!), Recommendations on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-7">
        {/* Left Column (6 cols): Soil Core -> Summary in Plain Terms -> Live Weather Panel */}
        <div className="lg:col-span-6 space-y-6">
          <SoilCore deficiencies={deficiencies} soil={soil} />

          {/* Plain terms explanation */}
          {(localizedSummary || llm_explanation) && (
            <div className="rounded-xl border border-soil-200 dark:border-[#235347] bg-forest-50 dark:bg-[#163832] p-5 shadow-soft space-y-2">
              <div className="flex items-center justify-between gap-2 flex-wrap">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-forest-800 dark:text-[#DAF1DE]" />
                  <h3 className="font-display text-sm font-semibold text-forest-900 dark:text-[#FFFFFF]">
                    {t("plainTermsHeading")}
                  </h3>
                </div>
                {result.llm_provider && (
                  <span className="text-[10px] font-sans font-medium px-2.5 py-0.5 rounded-full bg-forest-100 dark:bg-[#235347] text-forest-800 dark:text-[#DAF1DE] border border-forest-200 dark:border-[#235347]">
                    {result.is_llm_fallback || result.llm_provider === "template_fallback"
                      ? "AgriMind Rules Engine"
                      : "AgriMind AI Advisor"}
                  </span>
                )}
              </div>
              <p className="text-xs sm:text-sm text-forest-900 dark:text-[#FFFFFF] leading-relaxed whitespace-pre-line">
                {localizedSummary || llm_explanation}
              </p>
            </div>
          )}

          {/* Live Weather Panel directly under Summary in Plain Terms */}
          <WeatherPanel
            applicationWindow={appWindow}
            onRefreshWeather={handleRefreshWeather}
            isRefreshing={isRefreshingWeather}
            refreshError={weatherError}
          />
        </div>

        {/* Right Column (6 cols): Crop Suitability & Fertilizer Options */}
        <div className="lg:col-span-6 space-y-6">
          <RecommendationPanel
            cropScores={crop_scores}
            fertilizerOptions={fertilizer_options}
          />
        </div>
      </div>

      {/* Official Agronomic Disclaimer Banner */}
      {result.provisional_disclaimer && (
        <div className="rounded-xl border border-soil-200 dark:border-soil-700 bg-soil-50/60 dark:bg-forest-900/50 p-4 text-xs text-soil-600 dark:text-soil-300 flex items-start gap-3 shadow-soft">
          <ShieldCheck className="h-5 w-5 text-forest-700 dark:text-leaf-400 shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            <span className="font-semibold text-forest-950 dark:text-forest-100">Agricultural Notice: </span>
            {result.provisional_disclaimer}
          </p>
        </div>
      )}

      {/* Save Report Modal */}
      {saveModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-forest-950/70 p-4 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-md rounded-2xl bg-white dark:bg-forest-900 p-6 shadow-2xl border border-soil-200 dark:border-soil-700">
            <div className="flex items-start justify-between border-b border-soil-200 dark:border-soil-700 pb-3">
              <div className="flex items-center gap-2">
                <Bookmark className="h-5 w-5 text-forest-800 dark:text-leaf-400" />
                <h3 className="font-display text-base font-bold text-forest-900 dark:text-forest-100">
                  {t("saveReportModalTitle")}
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setSaveModalOpen(false)}
                className="rounded-lg p-1 text-soil-400 hover:bg-soil-100 dark:hover:bg-forest-800 hover:text-soil-700 dark:hover:text-soil-200"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {saveError && (
              <div className="mt-3 rounded-lg border border-rose-200 dark:border-rose-800 bg-rose-50 dark:bg-rose-950/60 p-2.5 text-xs text-rose-800 dark:text-rose-200">
                {saveError}
              </div>
            )}

            {saveSuccess ? (
              <div className="py-8 text-center">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300">
                  <Check className="h-6 w-6" />
                </div>
                <h4 className="mt-3 font-display text-base font-bold text-forest-900 dark:text-forest-100">
                  {t("saveReportSaved")}
                </h4>
                <p className="mt-1 text-xs text-soil-600 dark:text-soil-400">
                  Report is permanently saved to your PostgreSQL history.
                </p>
              </div>
            ) : (
              <form onSubmit={handleSaveSubmit} className="mt-4 space-y-3">
                <div>
                  <label className="block text-xs font-semibold text-soil-700 dark:text-soil-300">
                    {t("saveReportTitleLabel")}
                  </label>
                  <input
                    type="text"
                    required
                    value={saveTitle}
                    onChange={(e) => setSaveTitle(e.target.value)}
                    className="mt-1 w-full rounded-lg border border-soil-300 dark:border-soil-600 dark:bg-forest-950 p-2 text-xs text-soil-900 dark:text-soil-100 focus:border-forest-600 focus:outline-none focus:ring-1 focus:ring-forest-600"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-soil-700 dark:text-soil-300">
                    {t("saveReportNotesLabel")}
                  </label>
                  <textarea
                    rows={3}
                    value={saveNotes}
                    onChange={(e) => setSaveNotes(e.target.value)}
                    placeholder="e.g. Field A after kharif harvest, planning rabi wheat"
                    className="mt-1 w-full rounded-lg border border-soil-300 dark:border-soil-600 dark:bg-forest-950 p-2 text-xs text-soil-900 dark:text-soil-100 focus:border-forest-600 focus:outline-none focus:ring-1 focus:ring-forest-600"
                  />
                </div>

                <div className="mt-5 flex justify-end gap-2 border-t border-soil-100 dark:border-soil-700 pt-3">
                  <button
                    type="button"
                    onClick={() => setSaveModalOpen(false)}
                    className="rounded-lg border border-soil-300 dark:border-soil-600 px-3 py-1.5 text-xs font-medium text-soil-700 dark:text-soil-300 hover:bg-soil-50 dark:hover:bg-forest-800"
                  >
                    {t("saveReportCancel")}
                  </button>
                  <button
                    type="submit"
                    disabled={isSaving}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-forest-900 dark:bg-forest-700 px-4 py-1.5 text-xs font-bold text-white shadow hover:bg-forest-800 dark:hover:bg-forest-600 disabled:opacity-50"
                  >
                    {isSaving && (
                      <span className="h-3 w-3 animate-spin rounded-full border border-white border-t-transparent" />
                    )}
                    <span>{isSaving ? t("saveReportSaving") : t("saveReportConfirm")}</span>
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
