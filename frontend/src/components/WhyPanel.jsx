import { useLanguage } from "../i18n/LanguageContext";
import { BookOpen, ShieldCheck, AlertTriangle, HelpCircle, Scale, Building2, Calendar, FileText, Cpu, CheckCircle2 } from "lucide-react";

export default function WhyPanel({ why, llmProvider, llmModel, isLlmFallback }) {
  const { t } = useLanguage();
  if (!why) return null;

  const confidencePct = Math.round((why.confidence ?? 0) * 100);
  const confidenceColor =
    confidencePct >= 80
      ? "text-emerald-700 bg-emerald-50 border-emerald-300"
      : confidencePct >= 50
      ? "text-amber-700 bg-amber-50 border-amber-300"
      : "text-red-700 bg-red-50 border-red-300";

  return (
    <div className="rounded-xl border border-soil-200 bg-white p-6 shadow-soft space-y-6">
      {/* Header with Confidence Meter & Explanation Provenance */}
      <div className="flex items-start justify-between gap-4 flex-wrap pb-4 border-b border-soil-100">
        <div>
          <h3 className="font-display text-lg font-semibold text-forest-900 flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-forest-700" aria-hidden="true" />
            <span>{t("whyHeading")}</span>
          </h3>
          <p className="text-xs text-soil-500 mt-0.5">
            {t("whySub")}
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {/* Explanation Provenance Badge */}
          {llmProvider && (
            <span
              className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-sans font-medium border ${
                isLlmFallback || llmProvider === "template_fallback"
                  ? "bg-soil-100 text-soil-800 border-soil-300"
                  : "bg-forest-50 text-forest-900 border-forest-300"
              }`}
            >
              <Cpu className="h-3 w-3 text-soil-600" />
              <span>
                {isLlmFallback || llmProvider === "template_fallback"
                  ? "AgriMind Rules Engine"
                  : "AgriMind AI Advisor"}
              </span>
            </span>
          )}

          <div className="flex items-center gap-1.5">
            <span className="text-xs font-mono uppercase text-soil-500">
              {t("confidenceLabel")}:
            </span>
            <span
              className={`inline-flex items-center gap-1 rounded-md border px-2.5 py-1 text-xs font-mono font-bold ${confidenceColor}`}
            >
              <ShieldCheck className="h-3.5 w-3.5" />
              <span>{confidencePct}%</span>
            </span>
          </div>
        </div>
      </div>

      {/* Contradiction Safeguards */}
      {why.contradictions?.length > 0 && (
        <div className="rounded-lg border border-red-300 bg-red-50 p-4 space-y-1.5 shadow-sm">
          <div className="flex items-center gap-2 text-xs font-bold text-red-900 uppercase tracking-wide">
            <AlertTriangle className="h-4 w-4 text-red-600 shrink-0" />
            <span>Nutrient & Agronomic Safeguard Alert</span>
          </div>
          {why.contradictions.map((c, i) => (
            <p key={i} className="text-xs text-red-800 leading-relaxed pl-6">
              {c}
            </p>
          ))}
        </div>
      )}

      {/* Missing Input Warnings & Uncertainty */}
      {why.missing_warnings?.length > 0 && (
        <div className="rounded-lg border border-amber-300 bg-amber-50/80 p-4 space-y-1.5 shadow-sm">
          <div className="flex items-center gap-2 text-xs font-bold text-amber-900 uppercase tracking-wide">
            <HelpCircle className="h-4 w-4 text-amber-700 shrink-0" />
            <span>Unmeasured Soil Properties ({why.missing_warnings.length})</span>
          </div>
          <p className="text-xs text-amber-950 pl-6 leading-relaxed">
            {why.uncertainty_notes || "Some secondary nutrients or micronutrients were not available in the uploaded report:"}
          </p>
          <ul className="text-xs text-amber-900 pl-6 space-y-1 list-disc list-inside pt-1">
            {why.missing_warnings.map((mw, i) => (
              <li key={i}>{mw}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Agronomic Soil Reasoning */}
      {why.reason_soil && (
        <div className="rounded-lg border border-soil-100 bg-soil-50/60 p-4 space-y-1">
          <span className="text-[11px] font-mono uppercase tracking-wider text-soil-500 font-semibold">
            Soil Health Rationale
          </span>
          <p className="text-xs sm:text-sm text-soil-800 leading-relaxed">
            {why.reason_soil}
          </p>
        </div>
      )}

      {/* Weather Factor */}
      {why.weather_factor && (
        <div className="rounded-lg border border-soil-100 bg-soil-50/60 p-4 space-y-1">
          <span className="text-[11px] font-mono uppercase tracking-wider text-soil-500 font-semibold">
            {t("weatherFactorLabel")}
          </span>
          <p className="text-xs sm:text-sm text-soil-800 leading-relaxed">
            {why.weather_factor}
          </p>
        </div>
      )}

      {/* Documented Rule Sources */}
      {why.rule_sources?.length > 0 && (
        <div className="rounded-lg border border-forest-100 bg-forest-50/40 p-4 space-y-2">
          <div className="flex items-center gap-2 text-xs font-semibold text-forest-900 uppercase font-mono">
            <Scale className="h-4 w-4 text-forest-700 shrink-0" />
            <span>Documented Rule Sources & Standards</span>
          </div>
          <ul className="text-xs text-forest-950 space-y-1 pl-6 list-disc list-inside">
            {why.rule_sources.map((src, i) => (
              <li key={i}>{src}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Grounded RAG Evidence & Provenance */}
      <div className="space-y-3 pt-2">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-forest-700" />
            <span className="text-xs font-mono uppercase tracking-wider text-forest-900 font-semibold">
              {t("retrievedEvidenceLabel")}
            </span>
          </div>
          <span className="text-[11px] font-mono text-soil-500">
            Dense semantic search (SentenceTransformers + ChromaDB)
          </span>
        </div>

        {why.evidence && why.evidence.length > 0 ? (
          <div className="grid grid-cols-1 gap-3">
            {why.evidence.map((e, i) => (
              <div
                key={i}
                className="rounded-lg border border-soil-200 bg-soil-50/50 p-3.5 hover:bg-soil-50 transition-colors space-y-2"
              >
                {/* Evidence Metadata Header */}
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-0.5 min-w-0">
                    <p className="font-semibold text-xs text-forest-950 truncate">
                      {e.title || e.heading || e.source}
                    </p>
                    <div className="flex items-center gap-3 text-[11px] text-soil-500 flex-wrap">
                      {e.issuing_organization && (
                        <span className="flex items-center gap-1 text-forest-800">
                          <Building2 className="h-3 w-3 shrink-0" />
                          <span>{e.issuing_organization}</span>
                        </span>
                      )}
                      {e.doc_date && (
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3 w-3 shrink-0" />
                          <span>{e.doc_date}</span>
                        </span>
                      )}
                      <span className="font-mono text-soil-400">
                        {e.source}
                      </span>
                    </div>
                  </div>

                  <span className="rounded bg-emerald-100 text-emerald-900 border border-emerald-300 px-2 py-0.5 text-[10px] font-mono font-bold shrink-0">
                    {Math.round((e.score ?? 0) * 100)}% match
                  </span>
                </div>

                {/* Evidence Text Snippet */}
                <p className="text-xs text-soil-700 leading-relaxed bg-white/70 p-2.5 rounded border border-soil-100 italic">
                  "{e.text}"
                </p>
              </div>
            ))}
          </div>
        ) : (
          <div className="rounded-lg border border-soil-200 bg-soil-50/30 p-3.5 text-xs text-soil-500 space-y-1">
            <p className="font-medium text-soil-700">No specific literature chunks retrieved.</p>
            <p>
              Recommendations are evaluated purely against documented Soil Health Card rules without invented citations.
            </p>
          </div>
        )}
      </div>

      {/* Provisional Advisory Notice */}
      <div className="rounded-lg border border-soil-200 bg-soil-50/30 p-3 text-[11px] text-soil-500 leading-relaxed">
        <span className="font-semibold text-soil-700">Provisional Advisory: </span>
        {why.provisional_notice ||
          "All recommendations and suitability calculations are rule-based guidelines. Consult your local agricultural university or Krishi Vigyan Kendra (KVK) officer for field-level verification."}
      </div>
    </div>
  );
}
