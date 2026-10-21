import { useRef, useState } from "react";
import {
  UploadCloud,
  FileText,
  X,
  MapPin,
  Sprout,
  AlertCircle,
  Loader2,
  RotateCcw,
  Check,
  Edit3,
  AlertTriangle,
  Info,
  CloudSun,
  Thermometer,
} from "lucide-react";
import { useLanguage } from "../i18n/LanguageContext";
import { API_BASE, getWeatherForecast } from "../api";

const CROPS = [
  "",
  "Tomato",
  "Wheat",
  "Rice (Paddy)",
  "Cotton",
  "Soybean",
  "Onion",
  "Sugarcane",
  "Chickpea (Gram)",
];

const SUGGESTED_LOCATIONS = [
  "Mumbai, Maharashtra",
  "Pune, Maharashtra",
  "Nagpur, Maharashtra",
  "Nashik, Maharashtra",
  "Chhatrapati Sambhajinagar, Maharashtra",
  "Kolhapur, Maharashtra",
  "Solapur, Maharashtra",
  "Amravati, Maharashtra",
  "Baramati, Maharashtra",
];

const MAHARASHTRA_DISTRICTS = [
  "Mumbai, Maharashtra",
  "Mumbai Suburban, Maharashtra",
  "Pune, Maharashtra",
  "Nagpur, Maharashtra",
  "Nashik, Maharashtra",
  "Thane, Maharashtra",
  "Chhatrapati Sambhajinagar, Maharashtra",
  "Kolhapur, Maharashtra",
  "Solapur, Maharashtra",
  "Amravati, Maharashtra",
  "Nanded, Maharashtra",
  "Sangli, Maharashtra",
  "Jalgaon, Maharashtra",
  "Akola, Maharashtra",
  "Latur, Maharashtra",
  "Dhule, Maharashtra",
  "Ahilyanagar (Ahmednagar), Maharashtra",
  "Chandrapur, Maharashtra",
  "Parbhani, Maharashtra",
  "Jalna, Maharashtra",
  "Beed, Maharashtra",
  "Gondia, Maharashtra",
  "Satara, Maharashtra",
  "Yavatmal, Maharashtra",
  "Dharashiv (Osmanabad), Maharashtra",
  "Nandurbar, Maharashtra",
  "Wardha, Maharashtra",
  "Bhandara, Maharashtra",
  "Buldhana, Maharashtra",
  "Washim, Maharashtra",
  "Ratnagiri, Maharashtra",
  "Sindhudurg, Maharashtra",
  "Raigad, Maharashtra",
  "Gadchiroli, Maharashtra",
  "Palghar, Maharashtra",
  "Baramati, Maharashtra",
  "Pandharpur, Maharashtra",
  "Malegaon, Maharashtra",
  "Shirdi, Maharashtra",
];

const PARAMETER_CONFIG = [
  {
    key: "nitrogen",
    label: "Available Nitrogen (N)",
    isCore: true,
    defaultUnit: "kg/ha",
    units: ["kg/ha", "ppm"],
    benchmark: "Low: <280, Med: 280-560, High: >560 kg/ha",
  },
  {
    key: "phosphorus",
    label: "Available Phosphorus (P)",
    isCore: true,
    defaultUnit: "kg/ha",
    units: ["kg/ha", "ppm"],
    benchmark: "Low: <10, Med: 10-25, High: >25 kg/ha",
  },
  {
    key: "potassium",
    label: "Available Potassium (K)",
    isCore: true,
    defaultUnit: "kg/ha",
    units: ["kg/ha", "ppm"],
    benchmark: "Low: <108, Med: 108-280, High: >280 kg/ha",
  },
  {
    key: "ph",
    label: "Soil Reaction (pH)",
    isCore: true,
    defaultUnit: "-",
    units: ["-"],
    benchmark: "Acidic: <6.5, Neutral: 6.5-7.5, Alkaline: >7.5",
  },
  {
    key: "organic_carbon",
    label: "Organic Carbon (OC)",
    isCore: true,
    defaultUnit: "%",
    units: ["%"],
    benchmark: "Low: <0.50%, Med: 0.50-0.75%, High: >0.75%",
  },
  {
    key: "electrical_conductivity",
    label: "Electrical Conductivity (EC)",
    isCore: true,
    defaultUnit: "dS/m",
    units: ["dS/m", "mmhos/cm"],
    benchmark: "Normal: <=1.0 dS/m, Critical: 1.0-2.0 dS/m",
  },
  {
    key: "zinc",
    label: "Available Zinc (Zn)",
    isCore: false,
    defaultUnit: "ppm",
    units: ["ppm", "mg/kg"],
    benchmark: "Critical: 0.60 ppm (DTPA-Zn)",
  },
  {
    key: "iron",
    label: "Available Iron (Fe)",
    isCore: false,
    defaultUnit: "ppm",
    units: ["ppm", "mg/kg"],
    benchmark: "Critical: 4.50 ppm (DTPA-Fe)",
  },
  {
    key: "manganese",
    label: "Available Manganese (Mn)",
    isCore: false,
    defaultUnit: "ppm",
    units: ["ppm", "mg/kg"],
    benchmark: "Critical: 2.00 ppm (DTPA-Mn)",
  },
  {
    key: "copper",
    label: "Available Copper (Cu)",
    isCore: false,
    defaultUnit: "ppm",
    units: ["ppm", "mg/kg"],
    benchmark: "Critical: 0.20 ppm (DTPA-Cu)",
  },
  {
    key: "sulphur",
    label: "Available Sulphur (S)",
    isCore: false,
    defaultUnit: "ppm",
    units: ["ppm", "mg/kg"],
    benchmark: "Critical: 10.0 ppm (Available S)",
  },
  {
    key: "boron",
    label: "Available Boron (B)",
    isCore: false,
    defaultUnit: "ppm",
    units: ["ppm", "mg/kg"],
    benchmark: "Critical: 0.50 ppm (Hot water soluble B)",
  },
];

function calculateRating(key, value) {
  if (value === null || value === undefined || value === "" || isNaN(Number(value))) {
    return "—";
  }
  const val = Number(value);
  switch (key) {
    case "nitrogen":
      return val < 280 ? "LOW" : val <= 560 ? "MEDIUM" : "HIGH";
    case "phosphorus":
      return val < 10 ? "LOW" : val <= 25 ? "MEDIUM" : "HIGH";
    case "potassium":
      return val < 108 ? "LOW" : val <= 280 ? "MEDIUM" : "HIGH";
    case "ph":
      return val < 6.5 ? "ACIDIC" : val <= 7.5 ? "NEUTRAL" : "ALKALINE";
    case "organic_carbon":
      return val < 0.5 ? "LOW" : val <= 0.75 ? "MEDIUM" : "HIGH";
    case "electrical_conductivity":
      return val <= 1.0 ? "NORMAL" : val <= 2.0 ? "CRITICAL" : "HIGH";
    case "zinc":
      return val < 0.6 ? "DEFICIENT" : "SUFFICIENT";
    case "iron":
      return val < 4.5 ? "DEFICIENT" : "SUFFICIENT";
    case "manganese":
      return val < 2.0 ? "DEFICIENT" : "SUFFICIENT";
    case "copper":
      return val < 0.2 ? "DEFICIENT" : "SUFFICIENT";
    case "sulphur":
      return val < 10.0 ? "DEFICIENT" : "SUFFICIENT";
    case "boron":
      return val < 0.5 ? "DEFICIENT" : "SUFFICIENT";
    default:
      return "—";
  }
}

export default function SoilWorkspace({
  file,
  soil,
  onFileSelect,
  onUpdateSoil,
  location,
  onLocationChange,
  crop,
  onCropChange,
  preferOrganic,
  onOrganicChange,
  onAnalyze,
  loading,
  parsing = false,
  error,
  backendStatus = "checking",
  backendError = null,
  onRefreshBackend,
}) {
  const fileInputRef = useRef(null);
  const [dragActive, setDragActive] = useState(false);
  const { t, cropLabel } = useLanguage();

  const [weatherPreview, setWeatherPreview] = useState(null);
  const [checkingWeather, setCheckingWeather] = useState(false);
  const [weatherError, setWeatherError] = useState(null);

  async function handleCheckLiveWeather() {
    if (!location || !location.trim()) return;
    setCheckingWeather(true);
    setWeatherError(null);
    try {
      const res = await getWeatherForecast({ location_name: location.trim() });
      if (res) {
        setWeatherPreview(res);
      }
    } catch (err) {
      setWeatherError(err.message || "Failed to fetch weather for this location.");
    } finally {
      setCheckingWeather(false);
    }
  }

  function handleDrag(e) {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }

  function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const dropped = e.dataTransfer.files[0];
      if (dropped.name.toLowerCase().endsWith(".pdf")) {
        onFileSelect(dropped);
      }
    }
  }

  function formatBytes(bytes) {
    if (!bytes) return "";
    const kb = bytes / 1024;
    return kb > 1024 ? `${(kb / 1024).toFixed(1)} MB` : `${Math.round(kb)} KB`;
  }

  // Handle in-place measurement value edits
  function handleValueEdit(key, rawVal) {
    if (!onUpdateSoil) return;
    const num = rawVal === "" ? null : Number(rawVal);
    const existingMeasurements = soil?.measurements || {};
    const existingM = existingMeasurements[key] || {};
    const cfg = PARAMETER_CONFIG.find((p) => p.key === key);

    const updatedM = {
      ...existingM,
      name: existingM.name || cfg?.label || key,
      field_key: key,
      value: num,
      unit: existingM.unit || cfg?.defaultUnit,
      status: "user_edited",
      is_edited: true,
      rating: calculateRating(key, num),
      typical_range: existingM.typical_range || cfg?.benchmark,
    };

    const newMeasurements = {
      ...existingMeasurements,
      [key]: updatedM,
    };

    const newSoil = {
      ...soil,
      [key]: num !== null ? { value: num, unit: updatedM.unit } : null,
      measurements: newMeasurements,
    };

    onUpdateSoil(newSoil);
  }

  // Handle in-place measurement unit edits
  function handleUnitEdit(key, newUnit) {
    if (!onUpdateSoil) return;
    const existingMeasurements = soil?.measurements || {};
    const existingM = existingMeasurements[key] || {};

    const updatedM = {
      ...existingM,
      unit: newUnit === "-" ? null : newUnit,
      status: "user_edited",
      is_edited: true,
    };

    const newSoil = {
      ...soil,
      [key]:
        existingM.value !== null && existingM.value !== undefined
          ? { value: existingM.value, unit: newUnit === "-" ? null : newUnit }
          : null,
      measurements: {
        ...existingMeasurements,
        [key]: updatedM,
      },
    };

    onUpdateSoil(newSoil);
  }

  // Calculate completeness percentage
  const coreFields = PARAMETER_CONFIG.filter((p) => p.isCore).map((p) => p.key);
  const detectedCoreCount = coreFields.filter((k) => {
    const m = soil?.measurements?.[k];
    const directVal = soil?.[k];
    const val = m ? m.value : directVal?.value;
    return val !== null && val !== undefined && val !== "";
  }).length;
  const coreCompletenessPct = Math.round((detectedCoreCount / coreFields.length) * 100);

  // Count edited fields
  const editedCount = Object.values(soil?.measurements || {}).filter((m) => m.is_edited).length;

  return (
    <div className="max-w-4xl mx-auto space-y-8 py-6 sm:py-8">
      {/* Header */}
      <div>
        <h1 className="font-display text-2xl sm:text-3xl font-semibold text-forest-900 dark:text-white">
          {t("workspaceHeading")}
        </h1>
        <p className="mt-1 text-sm text-soil-600 dark:text-white/90">{t("workspaceSub")}</p>
      </div>

      {/* Backend Offline Notice */}
      {backendStatus === "offline" && !error && (
        <div
          role="status"
          className="rounded-xl border border-amber-300 bg-amber-50/80 p-4 sm:p-5 text-sm text-amber-950 shadow-soft space-y-3"
        >
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-amber-700 shrink-0 mt-0.5" />
            <div className="flex-1 space-y-1">
              <h3 className="font-semibold text-amber-900">
                {t("backendUnavailableTitle") || "FastAPI Backend is Offline"}
              </h3>
              <p className="text-xs sm:text-sm text-amber-800 leading-relaxed">
                {t("backendUnavailableDesc") || "Cannot connect to the AgriMind API server at"}{" "}
                <code className="rounded bg-amber-100 px-1 py-0.5 font-mono text-xs text-amber-900">
                  {API_BASE}
                </code>
                . You can still test all workflow screens, nutrient rating graphs, and crop rankings
                using <strong>Demo Mode</strong>, or launch the backend locally.
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2.5 pt-1 pl-8">
            <button
              type="button"
              onClick={onRefreshBackend}
              className="inline-flex items-center gap-1.5 rounded-lg border border-amber-300 bg-white px-3 py-1.5 text-xs font-semibold text-amber-900 hover:bg-amber-100/70 transition-colors"
            >
              <RotateCcw className="h-3.5 w-3.5 text-amber-700" />
              <span>{t("apiRetry") || "Retry Connection"}</span>
            </button>
            <span className="text-[11px] font-mono text-amber-700 ml-auto hidden sm:inline">
              Command: cd backend && uvicorn app.main:app --reload
            </span>
          </div>
        </div>
      )}

      {/* Error Notice */}
      {error && (
        <div
          role="alert"
          className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800 shadow-soft"
        >
          <AlertCircle className="h-5 w-5 text-red-600 shrink-0 mt-0.5" />
          <div className="flex-1 space-y-1">
            <p className="font-semibold text-red-900">Soil Report Processing Alert</p>
            <p className="leading-relaxed">{error}</p>
          </div>
          <button
            type="button"
            onClick={() => onFileSelect(null)}
            className="text-xs text-red-700 underline hover:text-red-900 shrink-0 font-medium"
          >
            Clear
          </button>
        </div>
      )}

      {/* Main Input Form */}
      <div className="rounded-2xl border border-soil-200 dark:border-[#235347] bg-white dark:bg-[#163832] p-6 sm:p-8 shadow-soft space-y-6">
        {/* Step 1: File Upload */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="block text-xs font-mono font-medium uppercase tracking-wider text-soil-500 dark:text-white">
              {t("step1Title")}
            </label>
            {file && (
              <button
                type="button"
                onClick={() => onFileSelect(null)}
                className="inline-flex items-center gap-1 text-xs text-soil-500 dark:text-[#8EB69B] hover:text-forest-800 dark:hover:text-white transition-colors"
              >
                <X className="h-3.5 w-3.5" />
                <span>{t("removeReport") || "Remove & Upload Another"}</span>
              </button>
            )}
          </div>

          {!file ? (
            <div
              onDragEnter={handleDrag}
              onDragOver={handleDrag}
              onDragLeave={handleDrag}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`group flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 text-center cursor-pointer transition-all ${
                dragActive
                  ? "border-forest-700 bg-forest-50 dark:bg-[#235347]/50"
                  : "border-soil-300 dark:border-[#235347] bg-soil-50/50 dark:bg-[#0B2B26]/80 hover:border-forest-700 dark:hover:border-[#8EB69B] hover:bg-forest-50/60 dark:hover:bg-[#235347]/40"
              }`}
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-white dark:bg-[#163832] text-forest-800 dark:text-[#DAF1DE] shadow-soft group-hover:scale-105 transition-transform">
                <UploadCloud className="h-6 w-6" aria-hidden="true" />
              </div>
              <p className="mt-3 text-sm font-medium text-forest-900 dark:text-[#FFFFFF]">
                {t("step1Placeholder")}
              </p>
              <p className="mt-1 text-xs text-soil-500 dark:text-[#8EB69B]">
                Digital text PDF format (Soil Health Card or accredited lab test report)
              </p>
            </div>
          ) : (
            <div className="flex items-center justify-between rounded-xl border border-soil-300 dark:border-[#235347] bg-soil-50 dark:bg-[#163832] p-4">
              <div className="flex items-center gap-3 min-w-0">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-forest-900 text-white shrink-0">
                  <FileText className="h-5 w-5" aria-hidden="true" />
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="truncate text-sm font-semibold text-forest-900">
                      {file.name}
                    </p>
                    <span className="rounded-full bg-forest-100 px-2 py-0.5 text-[10px] font-semibold text-forest-800">
                      PDF
                    </span>
                  </div>
                  <p className="text-xs text-soil-500">
                    {formatBytes(file.size)} • Digital document parsed via PyMuPDF
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={() => onFileSelect(null)}
                className="rounded-lg p-1.5 text-soil-500 hover:bg-soil-200/60 hover:text-soil-800 transition-colors"
                aria-label="Remove selected file"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          )}

          <input
            ref={fileInputRef}
            type="file"
            accept="application/pdf"
            className="hidden"
            onChange={(e) => e.target.files?.[0] && onFileSelect(e.target.files[0])}
          />
        </div>

        {/* Parsing Progress Banner */}
        {parsing && (
          <div className="rounded-xl border border-forest-300 bg-forest-50/70 p-5 text-center space-y-2 animate-pulse">
            <div className="flex items-center justify-center gap-2 text-forest-900 font-semibold text-sm">
              <Loader2 className="h-4 w-4 animate-spin text-forest-700" />
              <span>{t("parsingPdf") || "Reading PDF with PyMuPDF…"}</span>
            </div>
            <p className="text-xs text-forest-700">
              Extracting digital nutrient tables and matching official Soil Health Card thresholds…
            </p>
          </div>
        )}

        {/* Phase 3: Review & Edit Extracted Soil Measurements Table */}
        {soil && !parsing && (
          <div className="rounded-xl border border-soil-200 dark:border-[#235347] bg-soil-50 dark:bg-[#163832] p-4 sm:p-5 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-soil-200 dark:border-[#235347] pb-3">
              <div>
                <h3 className="font-display text-base font-semibold text-forest-900 dark:text-[#FFFFFF] flex items-center gap-2">
                  <span>{t("reviewHeading") || "Review Extracted Soil Measurements"}</span>
                  {editedCount > 0 && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-sky-100 dark:bg-sky-950/60 px-2 py-0.5 text-[10px] font-semibold text-sky-800 dark:text-sky-300 border border-sky-200 dark:border-sky-800">
                      <Edit3 className="h-3 w-3" />
                      <span>{editedCount} edited</span>
                    </span>
                  )}
                </h3>
                <p className="text-xs text-soil-600 dark:text-[#DAF1DE]/80 mt-0.5">
                  {t("reviewSub") ||
                    "Verify and adjust extracted values from your soil report before running recommendations. Edited values are clearly tracked."}
                </p>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <span className="text-xs font-mono text-forest-900 dark:text-[#FFFFFF] bg-white dark:bg-[#0B2B26] border border-soil-200 dark:border-[#235347] px-2.5 py-1 rounded-lg shadow-sm">
                  Core Completeness:{" "}
                  <strong
                    className={
                      coreCompletenessPct === 100
                        ? "text-emerald-600 dark:text-emerald-400"
                        : "text-amber-600 dark:text-amber-400"
                    }
                  >
                    {coreCompletenessPct}%
                  </strong>
                </span>
              </div>
            </div>

            {/* Warnings alert if any core field was missing or needs review */}
            {(soil.extraction_warnings?.length > 0 ||
              soil.needs_review?.length > 0) && (
              <div className="rounded-lg border border-amber-300 dark:border-amber-700 bg-amber-50 dark:bg-amber-950/40 p-3 text-xs text-amber-900 dark:text-amber-200 space-y-1">
                <div className="flex items-center gap-1.5 font-semibold text-amber-950 dark:text-amber-100">
                  <AlertTriangle className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" />
                  <span>
                    {t("parsingNeedsReviewWarning") ||
                      "Some values need your review or were not detected in the report. You can edit them directly in the table."}
                  </span>
                </div>
                <ul className="list-disc list-inside space-y-0.5 text-amber-800 dark:text-amber-300 pl-1">
                  {soil.extraction_warnings?.slice(0, 3).map((w, idx) => (
                    <li key={idx} className="truncate">{w}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Responsive Table */}
            <div className="overflow-x-auto rounded-lg border border-soil-200 dark:border-[#235347] bg-white dark:bg-[#0B2B26] shadow-sm">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-soil-200 dark:border-[#235347] bg-soil-100 dark:bg-[#163832] font-mono text-forest-900 dark:text-[#FFFFFF]">
                    <th className="py-2.5 px-3 font-semibold">
                      {t("paramHeader") || "Parameter"}
                    </th>
                    <th className="py-2.5 px-3 font-semibold w-28">
                      {t("valueHeader") || "Value"}
                    </th>
                    <th className="py-2.5 px-3 font-semibold w-24">
                      {t("unitHeader") || "Unit"}
                    </th>
                    <th className="py-2.5 px-3 font-semibold text-center">
                      {t("ratingHeader") || "Rating"}
                    </th>
                    <th className="py-2.5 px-3 font-semibold">
                      {t("statusHeader") || "Status"}
                    </th>
                    <th className="py-2.5 px-3 font-semibold hidden md:table-cell">
                      {t("evidenceHeader") || "Report Evidence"}
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-soil-200 dark:divide-[#235347]">
                  {PARAMETER_CONFIG.map((cfg) => {
                    const m = soil.measurements?.[cfg.key];
                    const directVal = soil[cfg.key];
                    const currentVal =
                      m?.value !== undefined && m?.value !== null
                        ? m.value
                        : directVal?.value ?? "";
                    const currentUnit =
                      m?.unit || directVal?.unit || cfg.defaultUnit;
                    const rating =
                      m?.rating || calculateRating(cfg.key, currentVal);
                    const isEdited = Boolean(m?.is_edited);
                    const isMissing = currentVal === "" || currentVal === null;
                    const isNeedsReview =
                      m?.status === "needs_review" ||
                      (cfg.isCore && isMissing);

                    return (
                      <tr
                        key={cfg.key}
                        className={`hover:bg-soil-50 dark:hover:bg-[#163832]/60 transition-colors ${
                          isEdited
                            ? "bg-sky-50/50 dark:bg-sky-950/20"
                            : isNeedsReview
                            ? "bg-amber-50/40 dark:bg-amber-950/20"
                            : ""
                        }`}
                      >
                        {/* Parameter Name & Benchmark */}
                        <td className="py-2 px-3">
                          <div className="font-medium text-forest-900 dark:text-[#FFFFFF]">
                            {cfg.label}
                            {cfg.isCore && (
                              <span className="ml-1.5 rounded-full bg-forest-100 dark:bg-[#235347] px-1.5 py-0.2 text-[9px] font-semibold text-forest-800 dark:text-[#DAF1DE]">
                                Core
                              </span>
                            )}
                          </div>
                          <div className="text-[10px] text-soil-500 dark:text-[#8EB69B] font-mono">
                            {cfg.benchmark}
                          </div>
                        </td>

                        {/* Editable Value */}
                        <td className="py-2 px-3">
                          <input
                            type="number"
                            step="any"
                            value={currentVal}
                            onChange={(e) =>
                              handleValueEdit(cfg.key, e.target.value)
                            }
                            placeholder="—"
                            className={`w-full rounded-md border px-2 py-1 text-xs font-mono font-semibold transition-colors focus:ring-1 focus:ring-forest-700 dark:focus:ring-[#8EB69B] ${
                              isEdited
                                ? "border-sky-400 bg-sky-50/60 dark:bg-sky-950/40 text-sky-900 dark:text-sky-200"
                                : isMissing
                                ? "border-amber-300 dark:border-amber-700 bg-amber-50/50 dark:bg-amber-950/40 text-amber-900 dark:text-amber-200"
                                : "border-soil-300 dark:border-[#235347] bg-white dark:bg-[#122F2A] text-forest-900 dark:text-[#FFFFFF]"
                            }`}
                          />
                        </td>

                        {/* Editable Unit */}
                        <td className="py-2 px-3">
                          {cfg.units.length > 1 ? (
                            <select
                              value={currentUnit || ""}
                              onChange={(e) =>
                                handleUnitEdit(cfg.key, e.target.value)
                              }
                              className="w-full rounded-md border border-soil-300 dark:border-[#235347] bg-white dark:bg-[#122F2A] px-1.5 py-1 text-xs text-forest-900 dark:text-[#FFFFFF] font-mono focus:border-forest-700 dark:focus:border-[#8EB69B] focus:ring-1 focus:ring-forest-700 dark:focus:ring-[#8EB69B]"
                            >
                              {cfg.units.map((u) => (
                                <option key={u} value={u} className="bg-white dark:bg-[#163832] text-forest-900 dark:text-[#FFFFFF]">
                                  {u}
                                </option>
                              ))}
                            </select>
                          ) : (
                            <span className="font-mono text-xs text-soil-600 dark:text-[#DAF1DE] px-1">
                              {cfg.defaultUnit || "—"}
                            </span>
                          )}
                        </td>

                        {/* Rating Band */}
                        <td className="py-2 px-3 text-center">
                          {(() => {
                            if (!rating || rating === "—" || rating === "UNKNOWN") {
                              return (
                                <span className="inline-block rounded px-2 py-0.5 text-[10px] font-mono text-soil-500 dark:text-[#8EB69B] bg-soil-100 dark:bg-[#163832]">
                                  —
                                </span>
                              );
                            }
                            if (["LOW", "DEFICIENT", "ACIDIC"].includes(rating)) {
                              return (
                                <span className="inline-block rounded-full px-2 py-0.5 text-[10px] font-bold tracking-wide bg-amber-100 dark:bg-amber-950/60 text-amber-900 dark:text-amber-200 border border-amber-300 dark:border-amber-700">
                                  {rating}
                                </span>
                              );
                            }
                            if (
                              [
                                "MEDIUM",
                                "NORMAL",
                                "NEUTRAL",
                                "SUFFICIENT",
                              ].includes(rating)
                            ) {
                              return (
                                <span className="inline-block rounded-full px-2 py-0.5 text-[10px] font-bold tracking-wide bg-emerald-100 dark:bg-emerald-950/60 text-emerald-900 dark:text-emerald-200 border border-emerald-300 dark:border-emerald-700">
                                  {rating}
                                </span>
                              );
                            }
                            return (
                              <span className="inline-block rounded-full px-2 py-0.5 text-[10px] font-bold tracking-wide bg-blue-100 dark:bg-blue-950/60 text-blue-900 dark:text-blue-200 border border-blue-300 dark:border-blue-700">
                                {rating}
                              </span>
                            );
                          })()}
                        </td>

                        {/* Status Badge */}
                        <td className="py-2 px-3 whitespace-nowrap">
                          {isEdited ? (
                            <span className="inline-flex items-center gap-1 rounded-full bg-sky-100 dark:bg-sky-950/60 px-2 py-0.5 text-[10px] font-semibold text-sky-800 dark:text-sky-300 border border-sky-200 dark:border-sky-800">
                              <Edit3 className="h-3 w-3" />
                              <span>{t("statusEdited") || "Edited"}</span>
                            </span>
                          ) : m?.status === "extracted" ? (
                            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 dark:bg-emerald-950/40 px-2 py-0.5 text-[10px] font-medium text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                              <Check className="h-3 w-3 text-emerald-600 dark:text-emerald-400" />
                              <span>{t("statusExtracted") || "Extracted"}</span>
                            </span>
                          ) : isNeedsReview ? (
                            <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 dark:bg-amber-950/60 px-2 py-0.5 text-[10px] font-semibold text-amber-900 dark:text-amber-200 border border-amber-300 dark:border-amber-700">
                              <AlertTriangle className="h-3 w-3 text-amber-600 dark:text-amber-400" />
                              <span>{t("statusReview") || "Review"}</span>
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 rounded-full bg-soil-100 dark:bg-[#163832] px-2 py-0.5 text-[10px] font-medium text-soil-500 dark:text-[#8EB69B]">
                              <span>{t("statusMissing") || "Missing"}</span>
                            </span>
                          )}
                        </td>

                        {/* Source Evidence Line */}
                        <td className="py-2 px-3 hidden md:table-cell max-w-xs">
                          {isEdited ? (
                            <span className="text-[11px] text-sky-600 dark:text-sky-400 italic">
                              Manually updated by user
                            </span>
                          ) : m?.source_text ? (
                            <span
                              className="font-mono text-[11px] text-forest-900 dark:text-[#FFFFFF] bg-soil-50 dark:bg-[#163832] px-2 py-0.5 rounded border border-soil-200 dark:border-[#235347] truncate block"
                              title={m.source_text}
                            >
                              {m.source_text}
                            </span>
                          ) : (
                            <span className="text-[11px] text-soil-400 dark:text-[#8EB69B] italic">
                              Not found in PDF
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <div className="flex items-center justify-between text-[11px] text-soil-500 dark:text-[#8EB69B] pt-1">
              <span>{t("editHint") || "Click any value or unit to modify"}</span>
              <span className="font-mono">Standards: Indian Soil Health Card Protocol</span>
            </div>
          </div>
        )}

        {/* Step 2: Location Input */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label
              htmlFor="farm-location"
              className="block text-xs font-mono font-medium uppercase tracking-wider text-soil-500 dark:text-white"
            >
              {t("step2Title")}
            </label>
            <span className="text-[11px] text-soil-500 dark:text-[#8EB69B]">
              Any village, taluka, city, or district in Maharashtra
            </span>
          </div>

          <div className="relative">
            <MapPin className="pointer-events-none absolute left-3.5 top-3.5 h-4 w-4 text-soil-400 dark:text-[#8EB69B]" />
            <input
              id="farm-location"
              list="maharashtra-locations"
              type="text"
              value={location}
              onChange={(e) => {
                onLocationChange(e.target.value);
                setWeatherPreview(null);
                setWeatherError(null);
              }}
              placeholder={t("step2Placeholder") || "e.g. Mumbai, Pune, Baramati, or any location"}
              className="w-full rounded-xl border border-soil-200 dark:border-[#235347] pl-10 pr-28 py-2.5 text-sm bg-white dark:bg-[#0B2B26] text-forest-900 dark:text-[#FFFFFF] placeholder:text-soil-400 dark:placeholder:text-[#8EB69B] focus:border-forest-700 dark:focus:border-[#8EB69B] focus:ring-1 focus:ring-forest-700 dark:focus:ring-[#8EB69B]"
            />
            <button
              type="button"
              onClick={handleCheckLiveWeather}
              disabled={checkingWeather || !location}
              className="absolute right-2 top-2 rounded-lg bg-forest-900 dark:bg-[#235347] px-2.5 py-1 text-xs font-semibold text-white hover:bg-forest-800 disabled:opacity-50 transition-colors"
            >
              {checkingWeather ? "Checking…" : "Live Weather"}
            </button>
          </div>

          <datalist id="maharashtra-locations">
            {MAHARASHTRA_DISTRICTS.map((d) => (
              <option key={d} value={d} />
            ))}
          </datalist>

          {/* Live Weather Preview Banner */}
          {weatherPreview && (
            <div className="rounded-xl border border-soil-200 dark:border-[#235347] bg-soil-50 dark:bg-[#0B2B26] p-3 text-xs text-forest-900 dark:text-white flex items-center justify-between gap-3 shadow-soft">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="flex h-2.5 w-2.5 rounded-full bg-emerald-600 dark:bg-emerald-400 shrink-0"></span>
                <span className="font-bold text-forest-900 dark:text-white">
                  {weatherPreview.location_name || location}:
                </span>
                <span className="font-bold text-base text-forest-900 dark:text-[#DAF1DE] font-mono">
                  {weatherPreview.current_temperature_c != null ? `${weatherPreview.current_temperature_c}°C` : "—"}
                </span>
                <span className="text-soil-400 dark:text-[#235347]">•</span>
                <span className="font-medium text-forest-800 dark:text-[#DAF1DE]">
                  {weatherPreview.current_condition || "Clear"}
                </span>
                {weatherPreview.days?.[0] && (
                  <span className="text-soil-600 dark:text-white/80">
                    (Today: {weatherPreview.days[0].temp_min_c}°C – {weatherPreview.days[0].temp_max_c}°C)
                  </span>
                )}
              </div>
            </div>
          )}

          {weatherError && (
            <div className="rounded-xl border border-rose-200 bg-rose-50 p-2.5 text-xs text-rose-800 flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0 text-rose-600" />
              <span>{weatherError}</span>
            </div>
          )}

          <p className="text-xs text-soil-500 dark:text-[#8EB69B]">{t("locationHelper")}</p>

          {/* Location quick chips */}
          <div className="flex flex-wrap items-center gap-1.5 pt-1 text-xs">
            <span className="text-soil-500 dark:text-[#8EB69B] text-[11px]">Quick presets:</span>
            {SUGGESTED_LOCATIONS.map((loc) => (
              <button
                key={loc}
                type="button"
                onClick={() => {
                  onLocationChange(loc);
                  setWeatherPreview(null);
                  setWeatherError(null);
                }}
                className="rounded-md border border-soil-200 dark:border-[#235347] bg-soil-100 dark:bg-[#235347] px-2 py-0.5 text-[11px] text-soil-700 dark:text-[#FFFFFF] hover:bg-soil-200 dark:hover:bg-[#2E6B5C] transition-colors"
              >
                {loc.split(",")[0]}
              </button>
            ))}
          </div>
        </div>

        {/* Step 3: Crop Selection */}
        <div className="space-y-2">
          <label
            htmlFor="crop-choice"
            className="block text-xs font-mono font-medium uppercase tracking-wider text-soil-500 dark:text-white"
          >
            {t("step3Title")}
          </label>
          <div className="relative">
            <Sprout className="pointer-events-none absolute left-3.5 top-3.5 h-4 w-4 text-soil-400 dark:text-[#8EB69B]" />
            <select
              id="crop-choice"
              value={crop}
              onChange={(e) => onCropChange(e.target.value)}
              className="w-full rounded-xl border border-soil-200 dark:border-[#235347] pl-10 pr-4 py-2.5 text-sm bg-white dark:bg-[#0B2B26] text-forest-900 dark:text-[#FFFFFF] focus:border-forest-700 dark:focus:border-[#8EB69B] focus:ring-1 focus:ring-forest-700 dark:focus:ring-[#8EB69B]"
            >
              <option value="">{t("cropAutoRank")}</option>
              {CROPS.filter(Boolean).map((c) => (
                <option key={c} value={c}>
                  {cropLabel(c)}
                </option>
              ))}
            </select>
          </div>
          <p className="text-xs text-soil-500 dark:text-[#8EB69B]">{t("cropHelper")}</p>
        </div>

        {/* Preferences: Organic */}
        <div className="pt-2 border-t border-soil-200 dark:border-[#235347]">
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={preferOrganic}
              onChange={(e) => onOrganicChange(e.target.checked)}
              className="mt-1 h-4 w-4 rounded border-soil-300 dark:border-[#235347] text-forest-800 dark:text-[#8EB69B] focus:ring-forest-700 dark:focus:ring-[#8EB69B] bg-white dark:bg-[#122F2A]"
            />
            <div>
              <span className="text-sm font-medium text-forest-900 dark:text-[#FFFFFF]">
                {t("organicPrefTitle")}
              </span>
              <p className="text-xs text-soil-500 dark:text-[#8EB69B]">{t("organicPrefHelper")}</p>
            </div>
          </label>
        </div>

        {/* Error Notice near button */}
        {error && (
          <div className="rounded-xl border border-red-300 dark:border-red-800 bg-red-50 dark:bg-red-950/40 p-3.5 text-sm text-red-800 dark:text-red-300 flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-red-600 dark:text-red-400 shrink-0 mt-0.5" />
            <p className="leading-relaxed font-medium">{error}</p>
          </div>
        )}

        {/* Action Buttons */}
        <div className="pt-2 flex flex-col sm:flex-row items-center gap-3">
          <button
            type="button"
            onClick={onAnalyze}
            disabled={loading || parsing}
            className="w-full sm:flex-1 inline-flex items-center justify-center gap-2 rounded-xl bg-forest-900 dark:bg-[#235347] px-6 py-3.5 text-sm font-semibold text-white shadow-soft hover:bg-forest-800 dark:hover:bg-[#2E6B5C] active:scale-[0.99] disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>{t("analyzing")}</span>
              </>
            ) : (
              <span>{t("analyze")}</span>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
