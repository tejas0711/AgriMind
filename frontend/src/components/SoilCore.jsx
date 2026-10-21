import { useLanguage } from "../i18n/LanguageContext";
import { CheckCircle2, AlertTriangle, AlertCircle, HelpCircle } from "lucide-react";

const STATUS_CONFIG = {
  LOW: {
    bg: "bg-amber-50/80 dark:bg-amber-950/40 border-amber-200 dark:border-amber-800 text-amber-950 dark:text-amber-200",
    badge: "bg-amber-100 dark:bg-amber-900/60 text-amber-900 dark:text-amber-200 border-amber-300 dark:border-amber-700",
    icon: AlertTriangle,
  },
  MEDIUM: {
    bg: "bg-forest-50/60 dark:bg-forest-900/40 border-forest-200 dark:border-forest-800 text-forest-950 dark:text-forest-200",
    badge: "bg-forest-100 dark:bg-forest-800 text-forest-900 dark:text-forest-200 border-forest-300 dark:border-forest-700",
    icon: CheckCircle2,
  },
  HIGH: {
    bg: "bg-emerald-50/60 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-800 text-emerald-950 dark:text-emerald-200",
    badge: "bg-emerald-100 dark:bg-emerald-900/60 text-emerald-900 dark:text-emerald-200 border-emerald-300 dark:border-emerald-700",
    icon: CheckCircle2,
  },
  UNKNOWN: {
    bg: "bg-soil-50/50 dark:bg-forest-950/30 border-soil-200 dark:border-soil-800 text-soil-600 dark:text-soil-400",
    badge: "bg-soil-100 dark:bg-forest-800 text-soil-700 dark:text-soil-300 border-soil-200 dark:border-soil-700",
    icon: HelpCircle,
  },
};

const MICRO_BADGE_KEY = { LOW: "DEFICIENT", HIGH: "SUFFICIENT", UNKNOWN: "UNKNOWN" };

/**
 * Stratified Soil Core Sample Horizon visualization
 * Displays soil test parameters with official benchmarks
 */
export default function SoilCore({ deficiencies = [], soil }) {
  const { t, statusLabel, nutrientLabel } = useLanguage();

  const primaryRows = ["nitrogen", "phosphorus", "potassium", "organic_carbon"].map((key) => {
    const d = deficiencies.find((x) => x.nutrient === key);
    const field = soil?.[key];
    const status = d ? d.status : "UNKNOWN";
    return {
      key,
      label: nutrientLabel(key),
      status,
      badgeText: statusLabel(status),
      value: field?.value != null ? `${field.value} ${field.unit || ""}`.trim() : "—",
    };
  });

  const microRows = ["zinc", "iron", "sulphur"]
    .map((key) => {
      const d = deficiencies.find((x) => x.nutrient === key);
      const field = soil?.[key];
      if (!field && !d) return null;
      const status = d ? d.status : "UNKNOWN";
      return {
        key,
        label: nutrientLabel(key),
        status,
        badgeText: statusLabel(MICRO_BADGE_KEY[status] || status),
        value: field?.value != null ? `${field.value} ${field.unit || ""}`.trim() : "—",
      };
    })
    .filter(Boolean);

  return (
    <div className="rounded-xl border border-soil-200 dark:border-soil-700 bg-white dark:bg-forest-900/60 overflow-hidden shadow-soft">
      {/* Header bar */}
      <div className="border-b border-soil-200 dark:border-[#235347] bg-soil-50 dark:bg-[#163832] px-4 py-3 flex items-center justify-between">
        <h3 className="font-display text-sm font-semibold text-forest-900 dark:text-white">
          {t("soilHealthHeading")}
        </h3>
        <span className="text-[11px] font-mono uppercase tracking-wider text-soil-500 dark:text-white/80">
          Soil Health Card Benchmarks
        </span>
      </div>

      {/* Primary Stratigraphy Layers */}
      <div className="divide-y divide-soil-100 dark:divide-soil-800">
        {primaryRows.map((row) => {
          const config = STATUS_CONFIG[row.status] || STATUS_CONFIG.UNKNOWN;
          const StatusIcon = config.icon;
          return (
            <div
              key={row.key}
              className={`soil-layer flex items-center justify-between px-4 py-3.5 ${config.bg} transition-colors`}
            >
              <div className="flex items-center gap-2.5">
                <StatusIcon className="h-4 w-4 shrink-0 opacity-80" aria-hidden="true" />
                <span className="text-sm font-medium text-forest-950 dark:text-forest-100">
                  {row.label}
                </span>
              </div>

              <div className="flex items-center gap-3">
                <span className="data-readout text-sm font-semibold text-forest-950 dark:text-forest-100">
                  {row.value}
                </span>
                <span
                  className={`border px-2 py-0.5 rounded text-[11px] font-mono uppercase tracking-wider font-semibold ${config.badge}`}
                >
                  {row.badgeText}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Soil pH & EC row */}
      {(soil?.ph || soil?.electrical_conductivity) && (
        <div className="border-t border-soil-200 dark:border-soil-700 bg-soil-100/50 dark:bg-forest-950/70 px-4 py-3 grid grid-cols-2 gap-4 text-xs">
          {soil?.ph && (
            <div className="flex items-center justify-between">
              <span className="font-medium text-soil-700 dark:text-soil-300">{t("soilPh")}:</span>
              <span className="data-readout font-bold text-forest-900 dark:text-forest-100 text-sm">
                {soil.ph.value}
              </span>
            </div>
          )}
          {soil?.electrical_conductivity && (
            <div className="flex items-center justify-between">
              <span className="font-medium text-soil-700 dark:text-soil-300">EC:</span>
              <span className="data-readout font-bold text-forest-900 dark:text-forest-100 text-sm">
                {soil.electrical_conductivity.value} {soil.electrical_conductivity.unit || "dS/m"}
              </span>
            </div>
          )}
        </div>
      )}

      {/* Micronutrients section */}
      {microRows.length > 0 && (
        <div className="border-t border-soil-200 dark:border-[#235347]">
          <div className="bg-soil-100 dark:bg-[#163832] border-b border-soil-200 dark:border-[#235347] px-4 py-2 text-[11px] font-mono uppercase tracking-wider text-forest-900 dark:text-[#DAF1DE]">
            {t("micronutrientsHeading")} (DTPA Critical Limits)
          </div>
          <div className="divide-y divide-soil-100 dark:divide-soil-800">
            {microRows.map((row) => {
              const config = STATUS_CONFIG[row.status] || STATUS_CONFIG.UNKNOWN;
              const StatusIcon = config.icon;
              return (
                <div
                  key={row.key}
                  className={`soil-layer flex items-center justify-between px-4 py-3 ${config.bg} transition-colors`}
                >
                  <div className="flex items-center gap-2">
                    <StatusIcon className="h-3.5 w-3.5 opacity-80" aria-hidden="true" />
                    <span className="text-xs font-medium text-forest-950 dark:text-forest-100">
                      {row.label}
                    </span>
                  </div>

                  <div className="flex items-center gap-3">
                    <span className="data-readout text-xs font-semibold text-forest-950 dark:text-forest-100">
                      {row.value}
                    </span>
                    <span
                      className={`border px-2 py-0.5 rounded text-[10px] font-mono uppercase tracking-wider font-semibold ${config.badge}`}
                    >
                      {row.badgeText}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
