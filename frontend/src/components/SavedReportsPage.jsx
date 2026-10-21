import { useState, useEffect } from "react";
import {
  FileText,
  Trash2,
  Calendar,
  Sprout,
  ArrowRight,
  CloudRain,
  ShieldAlert,
  AlertCircle,
  LogIn,
  CheckCircle2,
  Eye,
  X,
  RefreshCw,
} from "lucide-react";
import { useLanguage } from "../i18n/LanguageContext";
import { getSavedReports, getSavedReport, deleteSavedReport } from "../api";

export default function SavedReportsPage({
  currentUser,
  onOpenAuth,
  onNavigateToAnalyze,
  onLoadReportIntoResults,
}) {
  const { t } = useLanguage();
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedReport, setSelectedReport] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [deletingId, setDeletingId] = useState(null);

  useEffect(() => {
    if (currentUser) {
      loadReports();
    } else {
      setLoading(false);
    }
  }, [currentUser]);

  async function loadReports() {
    setLoading(true);
    setError(null);
    try {
      const data = await getSavedReports();
      setReports(data || []);
    } catch (err) {
      setError(err.message || "Failed to load saved reports.");
    } finally {
      setLoading(false);
    }
  }

  async function handleViewReport(reportId) {
    setLoadingDetail(true);
    try {
      const detail = await getSavedReport(reportId);
      setSelectedReport(detail);
    } catch (err) {
      alert("Error loading report detail: " + err.message);
    } finally {
      setLoadingDetail(false);
    }
  }

  async function handleDelete(reportId, e) {
    e.stopPropagation();
    if (!window.confirm(t("savedReportsDeleteConfirm") || "Are you sure you want to delete this report?")) {
      return;
    }

    setDeletingId(reportId);
    try {
      await deleteSavedReport(reportId);
      setReports((prev) => prev.filter((r) => r.id !== reportId));
      if (selectedReport && selectedReport.id === reportId) {
        setSelectedReport(null);
      }
    } catch (err) {
      alert("Error deleting report: " + err.message);
    } finally {
      setDeletingId(null);
    }
  }

  // State 1: Anonymous / Not Logged In
  if (!currentUser) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6">
        <div className="rounded-2xl border border-soil-200 dark:border-[#235347] bg-white dark:bg-[#163832] p-8 text-center shadow-soft">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-forest-50 dark:bg-[#235347] text-forest-800 dark:text-[#DAF1DE]">
            <LogIn className="h-7 w-7" />
          </div>
          <h2 className="mt-4 font-display text-2xl font-bold text-forest-900 dark:text-white">
            {t("savedReportsAnonymousTitle")}
          </h2>
          <p className="mx-auto mt-2 max-w-lg text-sm text-soil-600 dark:text-white/90">
            {t("savedReportsAnonymousDesc")}
          </p>

          <div className="mt-6 flex justify-center gap-3">
            <button
              type="button"
              onClick={onOpenAuth}
              className="inline-flex items-center gap-2 rounded-lg bg-forest-900 dark:bg-[#235347] px-5 py-2.5 text-xs font-bold text-white shadow hover:bg-forest-800 dark:hover:bg-[#2E6B5C] transition-colors"
            >
              <LogIn className="h-4 w-4" />
              <span>{t("authSignIn")} / {t("authSignUp")}</span>
            </button>
            <button
              type="button"
              onClick={onNavigateToAnalyze}
              className="inline-flex items-center gap-2 rounded-lg border border-soil-200 dark:border-[#235347] bg-white dark:bg-[#0B2B26] px-5 py-2.5 text-xs font-semibold text-forest-900 dark:text-white hover:bg-soil-100 dark:hover:bg-[#235347] transition-colors"
            >
              <span>{t("navAnalyze")}</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    );
  }

  // State 2: Logged In - Main Page
  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-soil-200 dark:border-[#235347] pb-6">
        <div>
          <div className="flex items-center gap-2">
            <FileText className="h-6 w-6 text-forest-800 dark:text-[#DAF1DE]" />
            <h1 className="font-display text-2xl font-bold tracking-tight text-forest-900 dark:text-white">
              {t("savedReportsTitle")}
            </h1>
          </div>
          <p className="mt-1 text-sm text-soil-600 dark:text-white/90">
            {t("savedReportsSubtitle")}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={loadReports}
            disabled={loading}
            className="inline-flex items-center gap-1.5 rounded-lg border border-soil-200 dark:border-[#235347] bg-white dark:bg-[#163832] px-3 py-2 text-xs font-semibold text-forest-900 dark:text-white hover:bg-soil-100 dark:hover:bg-[#235347] disabled:opacity-50 transition-colors"
            title="Refresh saved reports"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </button>
          <button
            type="button"
            onClick={onNavigateToAnalyze}
            className="inline-flex items-center gap-1.5 rounded-lg bg-forest-900 px-4 py-2 text-xs font-bold text-white shadow hover:bg-forest-800 transition-colors"
          >
            <Sprout className="h-4 w-4" />
            <span>New Analysis</span>
          </button>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="mt-6 flex items-start gap-3 rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs text-rose-800">
          <AlertCircle className="h-5 w-5 shrink-0 text-rose-600" />
          <div>
            <p className="font-semibold">Failed to load reports</p>
            <p className="mt-0.5">{error}</p>
          </div>
        </div>
      )}

      {/* Loading Skeleton */}
      {loading && (
        <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((n) => (
            <div key={n} className="animate-pulse rounded-xl border border-soil-200 bg-white p-5">
              <div className="h-4 w-2/3 rounded bg-soil-200" />
              <div className="mt-2 h-3 w-1/3 rounded bg-soil-100" />
              <div className="mt-4 flex gap-2">
                <div className="h-6 w-14 rounded-full bg-soil-200" />
                <div className="h-6 w-14 rounded-full bg-soil-200" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && reports.length === 0 && (
        <div className="mt-12 rounded-2xl border border-dashed border-soil-300 bg-soil-50/50 p-12 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-soil-100 text-soil-500">
            <FileText className="h-6 w-6" />
          </div>
          <h3 className="mt-4 font-display text-lg font-bold text-forest-900">
            {t("savedReportsEmptyTitle")}
          </h3>
          <p className="mx-auto mt-1 max-w-md text-xs text-soil-600">
            {t("savedReportsEmptyDesc")}
          </p>
          <button
            type="button"
            onClick={onNavigateToAnalyze}
            className="mt-6 inline-flex items-center gap-2 rounded-lg bg-forest-900 px-4 py-2 text-xs font-bold text-white shadow hover:bg-forest-800 transition-colors"
          >
            <span>Go to Soil Workspace</span>
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Reports Grid */}
      {!loading && reports.length > 0 && (
        <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {reports.map((report) => {
            const dateStr = new Date(report.created_at).toLocaleDateString(undefined, {
              year: "numeric",
              month: "short",
              day: "numeric",
            });
            const isDeleting = deletingId === report.id;

            return (
              <div
                key={report.id}
                onClick={() => handleViewReport(report.id)}
                className="group relative flex flex-col justify-between rounded-xl border border-soil-200 dark:border-soil-700 bg-white dark:bg-[#12221b] p-5 shadow-soft hover:border-forest-500 dark:hover:border-leaf-500 hover:shadow-md transition-all cursor-pointer"
              >
                <div>
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-display text-base font-bold text-forest-900 dark:text-forest-100 group-hover:text-forest-700 dark:group-hover:text-leaf-300 transition-colors">
                        {report.title || "Soil Analysis"}
                      </h3>
                      <div className="mt-1 flex items-center gap-1.5 text-[11px] text-soil-500 dark:text-soil-400">
                        <Calendar className="h-3.5 w-3.5" />
                        <span>{dateStr}</span>
                      </div>
                    </div>
                    <button
                      type="button"
                      disabled={isDeleting}
                      onClick={(e) => handleDelete(report.id, e)}
                      className="rounded-lg p-1.5 text-soil-400 hover:bg-rose-50 dark:hover:bg-rose-950/60 hover:text-rose-600 transition-colors"
                      title={t("savedReportsDelete")}
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>

                  {/* Crop badge */}
                  <div className="mt-4 flex flex-wrap items-center gap-2">
                    <span className="inline-flex items-center gap-1 rounded-full bg-forest-50 dark:bg-[#183227] border border-forest-200 dark:border-forest-800 px-2.5 py-1 text-[11px] font-semibold text-forest-900 dark:text-leaf-300">
                      <Sprout className="h-3 w-3 text-leaf-600 dark:text-leaf-400" />
                      <span>{report.selected_crop || "General Fit"}</span>
                    </span>

                    {report.apply_today && (
                      <span
                        className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-bold ${
                          report.apply_today === "GO"
                            ? "bg-emerald-50 dark:bg-emerald-950/70 border-emerald-300 dark:border-emerald-700 text-emerald-800 dark:text-emerald-300"
                            : "bg-amber-50 dark:bg-amber-950/70 border-amber-300 dark:border-amber-700 text-amber-800 dark:text-amber-300"
                        }`}
                      >
                        <CloudRain className="h-3 w-3" />
                        <span>{report.apply_today}</span>
                      </span>
                    )}

                    {report.has_deficiency && (
                      <span className="rounded-full bg-rose-50 dark:bg-rose-950/70 border border-rose-200 dark:border-rose-800 px-2 py-0.5 text-[10px] font-semibold text-rose-700 dark:text-rose-300">
                        Deficient
                      </span>
                    )}
                  </div>

                  {/* Summary snippet */}
                  {report.summary_snippet && (
                    <p className="mt-3 line-clamp-2 text-xs text-soil-600 dark:text-soil-300">
                      {report.summary_snippet}
                    </p>
                  )}
                </div>

                <div className="mt-5 flex items-center justify-between border-t border-soil-100 dark:border-soil-800 pt-3 text-xs font-semibold text-forest-800 dark:text-leaf-300">
                  <span className="inline-flex items-center gap-1 group-hover:translate-x-0.5 transition-transform">
                    <Eye className="h-3.5 w-3.5" />
                    <span>{t("savedReportsView")}</span>
                  </span>
                  <span className="text-[11px] text-soil-400 dark:text-soil-500 font-mono">#{report.id}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Detail Modal */}
      {selectedReport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-forest-950/70 p-4 backdrop-blur-sm animate-fade-in">
          <div className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-2xl bg-white dark:bg-[#12221b] p-6 shadow-2xl border border-soil-200 dark:border-soil-700">
            {/* Modal Header */}
            <div className="flex items-start justify-between border-b border-soil-200 dark:border-soil-700 pb-4">
              <div>
                <div className="flex items-center gap-2">
                  <span className="rounded-full bg-forest-100 dark:bg-[#183227] border border-forest-200 dark:border-forest-800 px-2 py-0.5 text-[10px] font-bold text-forest-800 dark:text-leaf-300 uppercase tracking-wide">
                    Saved Soil Report
                  </span>
                  <span className="text-xs text-soil-500 dark:text-soil-400 font-mono">
                    ID #{selectedReport.id}
                  </span>
                </div>
                <h2 className="mt-1 font-display text-xl font-bold text-forest-900 dark:text-forest-100">
                  {selectedReport.title || "Soil Analysis"}
                </h2>
                <p className="text-xs text-soil-500 dark:text-soil-400">
                  Saved on {new Date(selectedReport.created_at).toLocaleString()}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setSelectedReport(null)}
                className="rounded-lg p-1.5 text-soil-400 hover:bg-soil-100 hover:text-soil-700"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Field notes */}
            {selectedReport.notes && (
              <div className="mt-4 rounded-xl border border-soil-200 bg-soil-50 p-3 text-xs text-soil-700">
                <span className="font-semibold text-forest-900">Notes: </span>
                <span>{selectedReport.notes}</span>
              </div>
            )}

            {/* Soil Measurements */}
            <div className="mt-5">
              <h3 className="font-display text-sm font-bold text-forest-900">
                Soil Test Values
              </h3>
              <div className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-4">
                {(selectedReport.soil_data || selectedReport.soil_measurements) &&
                  Object.entries(selectedReport.soil_data || selectedReport.soil_measurements).map(([key, val]) => (
                    <div key={key} className="rounded-lg border border-soil-200 bg-white p-2.5">
                      <div className="text-[10px] font-medium uppercase tracking-wider text-soil-500">
                        {key.replace(/_/g, " ")}
                      </div>
                      <div className="mt-0.5 text-sm font-bold text-forest-900">
                        {val != null ? String(val) : "—"}
                      </div>
                    </div>
                  ))}
              </div>
            </div>

            {/* Nutrient Classifications */}
            {selectedReport.deficiencies && selectedReport.deficiencies.length > 0 && (
              <div className="mt-5">
                <h3 className="font-display text-sm font-bold text-forest-900">
                  Nutrient Status & Critical Limits
                </h3>
                <div className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-4">
                  {selectedReport.deficiencies.map((d, idx) => (
                    <div
                      key={idx}
                      className="rounded-lg border border-soil-200 bg-white p-2.5"
                    >
                      <div className="text-[10px] font-medium uppercase tracking-wider text-soil-500">
                        {d.nutrient?.replace(/_/g, " ")}
                      </div>
                      <div className="mt-0.5 flex items-center justify-between">
                        <span className="text-xs font-bold text-forest-900">
                          {d.value != null ? `${d.value} ${d.unit || ""}` : "—"}
                        </span>
                        <span
                          className={`rounded px-1.5 py-0.2 text-[9px] font-bold ${
                            d.status === "LOW" || d.status === "DEFICIENT"
                              ? "bg-rose-100 text-rose-800"
                              : d.status === "HIGH"
                              ? "bg-blue-100 text-blue-800"
                              : "bg-emerald-100 text-emerald-800"
                          }`}
                        >
                          {d.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Weather application advice */}
            {(selectedReport.application_window || selectedReport.analysis_results?.weather_summary) && (
              <div className="mt-5 rounded-xl border border-soil-200 bg-soil-50 p-4">
                <div className="flex items-center gap-2">
                  <CloudRain className="h-4 w-4 text-forest-800" />
                  <h4 className="font-display text-xs font-bold text-forest-900">
                    Weather Runoff Window Advisory
                  </h4>
                  <span
                    className={`ml-auto rounded-full px-2 py-0.5 text-[10px] font-bold ${
                      (selectedReport.application_window?.apply_today ||
                        selectedReport.analysis_results?.weather_summary?.apply_today) === "GO"
                        ? "bg-emerald-100 text-emerald-800"
                        : "bg-amber-100 text-amber-800"
                    }`}
                  >
                    {selectedReport.application_window?.apply_today ||
                      selectedReport.analysis_results?.weather_summary?.apply_today}
                  </span>
                </div>
                <p className="mt-1 text-xs text-soil-700">
                  {selectedReport.application_window?.reasoning ||
                    selectedReport.analysis_results?.weather_summary?.reasoning}
                </p>
              </div>
            )}

            {/* Explanation / Notes */}
            {selectedReport.explanation && (
              <div className="mt-5 rounded-xl border border-soil-200 bg-forest-50/50 p-4 text-xs text-forest-950">
                <h4 className="font-display font-bold text-forest-900 mb-1">
                  Agronomic Explanation
                </h4>
                <p className="leading-relaxed whitespace-pre-line">{selectedReport.explanation}</p>
              </div>
            )}

            {/* Modal Actions */}
            <div className="mt-6 flex items-center justify-between border-t border-soil-200 pt-4">
              <button
                type="button"
                onClick={() => setSelectedReport(null)}
                className="rounded-lg border border-soil-300 px-4 py-2 text-xs font-semibold text-soil-700 hover:bg-soil-50 transition-colors"
              >
                Close
              </button>
              {onLoadReportIntoResults && (
                <button
                  type="button"
                  onClick={() => {
                    onLoadReportIntoResults(selectedReport);
                    setSelectedReport(null);
                  }}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-forest-900 px-4 py-2 text-xs font-bold text-white shadow hover:bg-forest-800 transition-colors"
                >
                  <Eye className="h-4 w-4" />
                  <span>Open in Full Dashboard</span>
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
