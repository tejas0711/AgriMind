import { useLanguage } from "../i18n/LanguageContext";
import {
  Sprout,
  Leaf,
  FlaskConical,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  HelpCircle,
  ShieldCheck,
  Info,
} from "lucide-react";
import {
  SECTION_LABELS,
  localizeCropCategory,
  localizeFactor,
  localizeFertilizerName,
  localizeFertilizerPurpose,
  localizeFertilizerNotes,
  localizeFertilizerCautions,
} from "../i18n/agriLocalizer";

export default function RecommendationPanel({ cropScores = [], fertilizerOptions = [] }) {
  const { t, lang, cropLabel, fertilizerTypeLabel } = useLanguage();
  const labels = SECTION_LABELS[lang] || SECTION_LABELS.en;

  return (
    <div className="space-y-6">
      {/* Crop Suitability Section */}
      <div className="rounded-xl border border-soil-200 dark:border-soil-700 bg-white dark:bg-forest-900/60 p-6 shadow-soft space-y-4">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div>
            <h3 className="font-display text-lg font-semibold text-forest-900 dark:text-white flex items-center gap-2">
              <Sprout className="h-5 w-5 text-forest-800 dark:text-[#DAF1DE]" aria-hidden="true" />
              <span>{t("cropSuitabilityHeading")}</span>
            </h3>
            <p className="text-xs text-soil-600 dark:text-white/90 mt-0.5">
              {t("cropSuitabilitySub")}
            </p>
          </div>
          <span className="text-[11px] font-mono text-soil-400 dark:text-soil-500">
            {t("scoreHelper")}
          </span>
        </div>

        {cropScores.length === 0 ? (
          <p className="text-sm text-soil-500 py-3">{t("noCropScores")}</p>
        ) : (
          <div className="space-y-3.5 pt-1">
            {cropScores.map((c) => {
              const scoreColor =
                c.score >= 80
                  ? "bg-forest-700 text-white"
                  : c.score >= 60
                  ? "bg-leaf-600 text-white"
                  : "bg-wheat-500 text-soil-900";
              const barColor =
                c.score >= 80 ? "bg-forest-700" : c.score >= 60 ? "bg-leaf-600" : "bg-wheat-500";

              const categoryBadge =
                c.category === "Highly Suitable"
                  ? "bg-emerald-50 text-emerald-800 border-emerald-300 dark:bg-emerald-950/60 dark:text-emerald-300 dark:border-emerald-700"
                  : c.category === "Moderately Suitable"
                  ? "bg-leaf-50 text-leaf-800 border-leaf-300 dark:bg-leaf-950/60 dark:text-leaf-300 dark:border-leaf-700"
                  : c.category === "Marginally Suitable"
                  ? "bg-amber-50 text-amber-800 border-amber-300 dark:bg-amber-950/60 dark:text-amber-300 dark:border-amber-700"
                  : "bg-red-50 text-red-800 border-red-300 dark:bg-red-950/60 dark:text-red-300 dark:border-red-700";

              const localizedCat = localizeCropCategory(c.category, lang);

              return (
                <div
                  key={c.name}
                  className="rounded-lg border border-soil-200 dark:border-soil-700 bg-soil-50/40 dark:bg-forest-950/40 p-4 hover:bg-soil-50 dark:hover:bg-forest-900/40 transition-colors space-y-3"
                >
                  <div className="flex items-center justify-between gap-4 flex-wrap">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold text-forest-950 dark:text-forest-100">
                        {cropLabel(c.name)}
                      </span>
                      {c.category && (
                        <span
                          className={`rounded-full border px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider font-mono ${categoryBadge}`}
                        >
                          {localizedCat}
                        </span>
                      )}
                    </div>
                    <span className={`rounded px-2.5 py-0.5 text-xs font-mono font-bold ${scoreColor}`}>
                      {c.score} / 100
                    </span>
                  </div>

                  {/* Progress track */}
                  <div
                    className="h-2 w-full rounded-full bg-soil-200 dark:bg-forest-800 overflow-hidden"
                    role="progressbar"
                    aria-label={cropLabel(c.name)}
                    aria-valuenow={c.score}
                    aria-valuemin={0}
                    aria-valuemax={100}
                  >
                    <div
                      className={`h-full rounded-full ${barColor} transition-all duration-500`}
                      style={{ width: `${c.score}%` }}
                    />
                  </div>

                  {/* Positive Contributing Factors */}
                  {c.positive_factors && c.positive_factors.length > 0 && (
                    <div className="space-y-1 pt-1">
                      <span className="text-[10px] font-mono uppercase tracking-wider text-emerald-800 dark:text-emerald-400 font-bold block">
                        {labels.positiveFactors}
                      </span>
                      <ul className="text-xs text-soil-700 dark:text-soil-300 space-y-1">
                        {c.positive_factors.map((pf, i) => (
                          <li key={i} className="flex items-start gap-1.5">
                            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                            <span>{localizeFactor(pf, lang)}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Limiting Factors / Constraints */}
                  {c.limiting_factors && c.limiting_factors.length > 0 && (
                    <div className="space-y-1 pt-1">
                      <span className="text-[10px] font-mono uppercase tracking-wider text-amber-800 dark:text-amber-400 font-bold block">
                        {labels.limitingFactors}
                      </span>
                      <ul className="text-xs text-soil-700 dark:text-soil-300 space-y-1">
                        {c.limiting_factors.map((lf, i) => (
                          <li key={i} className="flex items-start gap-1.5">
                            <AlertCircle className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
                            <span>{localizeFactor(lf, lang)}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Missing parameter notes */}
                  {c.missing_factors && c.missing_factors.length > 0 && (
                    <div className="space-y-1 pt-1">
                      <ul className="text-[11px] text-soil-500 dark:text-soil-400 space-y-0.5 italic">
                        {c.missing_factors.map((mf, i) => (
                          <li key={i} className="flex items-start gap-1.5">
                            <HelpCircle className="h-3 w-3 text-soil-400 shrink-0 mt-0.5" />
                            <span>{mf}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Fertilizer & Amendment Options */}
      <div className="rounded-xl border border-soil-200 dark:border-soil-700 bg-white dark:bg-forest-900/60 p-6 shadow-soft space-y-4">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div>
            <h3 className="font-display text-lg font-semibold text-forest-900 dark:text-white flex items-center gap-2">
              <FlaskConical className="h-5 w-5 text-forest-800 dark:text-[#DAF1DE]" aria-hidden="true" />
              <span>{t("fertilizerHeading")}</span>
            </h3>
            <p className="text-xs text-soil-600 dark:text-white/90 mt-0.5">
              {t("fertilizerSub")}
            </p>
          </div>
          <span className="inline-flex items-center gap-1 rounded bg-leaf-50 dark:bg-leaf-950/60 border border-leaf-200 dark:border-leaf-800 px-2 py-0.5 text-[10px] font-mono text-leaf-800 dark:text-leaf-300">
            <ShieldCheck className="h-3.5 w-3.5 text-leaf-700 dark:text-leaf-400" />
            <span>{labels.zeroPesticides}</span>
          </span>
        </div>

        {fertilizerOptions.length === 0 ? (
          <div className="rounded-lg border border-forest-200 dark:border-forest-700 bg-forest-50/60 dark:bg-forest-950/50 p-4 text-xs text-forest-800 dark:text-forest-200 leading-relaxed">
            {t("noFertilizerNeeded")}
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-3.5">
            {fertilizerOptions.map((f, i) => {
              const isOrganic = f.type === "organic";
              const localizedName = localizeFertilizerName(f.name, lang);
              const localizedPurpose = localizeFertilizerPurpose(f.purpose, lang);
              const localizedNotes = localizeFertilizerNotes(f.application_notes, lang);
              const localizedCautions = localizeFertilizerCautions(f.cautions, lang);

              return (
                <div
                  key={i}
                  className="rounded-lg border border-soil-200 dark:border-soil-700 bg-soil-50/50 dark:bg-forest-950/40 p-4 hover:border-forest-400 dark:hover:border-forest-600 hover:bg-white dark:hover:bg-forest-900/60 transition-all space-y-2.5"
                >
                  <div className="flex items-start justify-between gap-3 flex-wrap">
                    <div>
                      <span className="font-semibold text-sm text-forest-950 dark:text-forest-100 block">
                        {localizedName}
                      </span>
                      {localizedPurpose && (
                        <p className="text-xs text-forest-800 dark:text-forest-300 mt-0.5 font-medium">
                          {localizedPurpose}
                        </p>
                      )}
                    </div>
                    <span
                      className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[10px] font-mono uppercase tracking-wider font-bold shrink-0 ${
                        isOrganic
                          ? "bg-forest-100 text-forest-900 border border-forest-300 dark:bg-forest-800 dark:text-forest-100 dark:border-forest-600"
                          : "bg-wheat-100 text-soil-900 border border-wheat-300 dark:bg-amber-950/60 dark:text-amber-200 dark:border-amber-800"
                      }`}
                    >
                      {isOrganic ? <Leaf className="h-3 w-3" /> : <FlaskConical className="h-3 w-3" />}
                      <span>{fertilizerTypeLabel(f.type)}</span>
                    </span>
                  </div>

                  <div className="text-xs text-soil-700 dark:text-soil-300 leading-relaxed bg-white/80 dark:bg-forest-900/80 rounded p-2.5 border border-soil-100 dark:border-soil-700">
                    <span className="font-semibold text-soil-900 dark:text-forest-200">{labels.applicationGuidance} </span>
                    {localizedNotes}
                  </div>

                  {f.cautions && (
                    <div className="rounded border border-amber-200 dark:border-amber-800 bg-amber-50/70 dark:bg-amber-950/50 p-2.5 text-xs text-amber-950 dark:text-amber-200 flex items-start gap-2">
                      <AlertTriangle className="h-3.5 w-3.5 text-amber-700 dark:text-amber-400 shrink-0 mt-0.5" />
                      <div>
                        <span className="font-semibold text-amber-900 dark:text-amber-300">{labels.caution} </span>
                        {localizedCautions}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
