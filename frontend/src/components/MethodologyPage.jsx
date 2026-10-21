import { useLanguage } from "../i18n/LanguageContext";
import { BookOpen, ShieldCheck, Scale, CloudRain, Cpu, AlertTriangle } from "lucide-react";

export default function MethodologyPage() {
  const { t } = useLanguage();

  return (
    <div className="max-w-4xl mx-auto space-y-10 py-6 sm:py-8">
      {/* Header */}
      <div>
        <div className="inline-flex items-center gap-1.5 rounded-full border border-forest-200 bg-forest-50 px-3 py-1 text-xs font-semibold text-forest-800 mb-3">
          <Scale className="h-3.5 w-3.5 text-forest-600" />
          <span>Scientific Transparency</span>
        </div>
        <h1 className="font-display text-2xl sm:text-4xl font-semibold text-forest-900">
          {t("aboutHeading")}
        </h1>
        <p className="mt-2 text-sm sm:text-base text-soil-700 leading-relaxed">
          {t("aboutSub")}
        </p>
      </div>

      {/* 4 Pillars Grid */}
      <div className="grid grid-cols-1 gap-6">
        {/* Section 1: Soil Health Card Standards */}
        <section className="rounded-xl border border-soil-200 bg-white p-6 sm:p-8 shadow-soft space-y-3">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-forest-900 text-wheat-200">
              <Scale className="h-4 w-4" />
            </div>
            <h2 className="font-display text-lg font-semibold text-forest-900">
              {t("shcSectionTitle")}
            </h2>
          </div>
          <p className="text-sm text-soil-700 leading-relaxed">
            {t("shcSectionBody")}
          </p>

          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-xs border border-soil-200 rounded-lg overflow-hidden">
              <thead className="bg-soil-100 text-soil-800 font-mono">
                <tr>
                  <th className="p-2.5 border-b border-soil-200">Nutrient</th>
                  <th className="p-2.5 border-b border-soil-200">Method</th>
                  <th className="p-2.5 border-b border-soil-200 text-amber-900">Low Threshold</th>
                  <th className="p-2.5 border-b border-soil-200 text-forest-800">Medium Band</th>
                  <th className="p-2.5 border-b border-soil-200 text-emerald-900">High Threshold</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-soil-100 font-mono text-soil-700">
                <tr>
                  <td className="p-2.5 font-bold">Nitrogen (N)</td>
                  <td className="p-2.5">Alkaline Permanganate</td>
                  <td className="p-2.5 text-amber-700">&lt; 280 kg/ha</td>
                  <td className="p-2.5">280 – 560 kg/ha</td>
                  <td className="p-2.5 text-emerald-700">&gt; 560 kg/ha</td>
                </tr>
                <tr>
                  <td className="p-2.5 font-bold">Phosphorus (P)</td>
                  <td className="p-2.5">Olsen's Method</td>
                  <td className="p-2.5 text-amber-700">&lt; 10 kg/ha</td>
                  <td className="p-2.5">10 – 25 kg/ha</td>
                  <td className="p-2.5 text-emerald-700">&gt; 25 kg/ha</td>
                </tr>
                <tr>
                  <td className="p-2.5 font-bold">Potassium (K)</td>
                  <td className="p-2.5">Neutral Ammonium Acetate</td>
                  <td className="p-2.5 text-amber-700">&lt; 108 kg/ha</td>
                  <td className="p-2.5">108 – 280 kg/ha</td>
                  <td className="p-2.5 text-emerald-700">&gt; 280 kg/ha</td>
                </tr>
                <tr>
                  <td className="p-2.5 font-bold">Organic Carbon (OC)</td>
                  <td className="p-2.5">Walkley-Black Method</td>
                  <td className="p-2.5 text-amber-700">&lt; 0.50%</td>
                  <td className="p-2.5">0.50 – 0.75%</td>
                  <td className="p-2.5 text-emerald-700">&gt; 0.75%</td>
                </tr>
                <tr>
                  <td className="p-2.5 font-bold">Zinc (Zn)</td>
                  <td className="p-2.5">DTPA Extractable</td>
                  <td className="p-2.5 text-amber-700">&lt; 0.60 ppm (Deficient)</td>
                  <td className="p-2.5" colSpan="2">
                    &ge; 0.60 ppm (Sufficient)
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        {/* Section 2: Weather Runoff Safety Logic */}
        <section className="rounded-xl border border-soil-200 bg-white p-6 sm:p-8 shadow-soft space-y-3">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-forest-900 text-wheat-200">
              <CloudRain className="h-4 w-4" />
            </div>
            <h2 className="font-display text-lg font-semibold text-forest-900">
              {t("weatherSectionTitle")}
            </h2>
          </div>
          <p className="text-sm text-soil-700 leading-relaxed">
            {t("weatherSectionBody")}
          </p>
        </section>

        {/* Section 3: Grounded RAG */}
        <section className="rounded-xl border border-soil-200 bg-white p-6 sm:p-8 shadow-soft space-y-3">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-forest-900 text-wheat-200">
              <BookOpen className="h-4 w-4" />
            </div>
            <h2 className="font-display text-lg font-semibold text-forest-900">
              {t("ragSectionTitle")}
            </h2>
          </div>
          <p className="text-sm text-soil-700 leading-relaxed">
            {t("ragSectionBody")}
          </p>
        </section>

        {/* Section 4: Boundary of AI */}
        <section className="rounded-xl border border-soil-200 bg-white p-6 sm:p-8 shadow-soft space-y-3">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-forest-900 text-wheat-200">
              <Cpu className="h-4 w-4" />
            </div>
            <h2 className="font-display text-lg font-semibold text-forest-900">
              {t("aiRoleTitle")}
            </h2>
          </div>
          <p className="text-sm text-soil-700 leading-relaxed">
            {t("aiRoleBody")}
          </p>
        </section>

        {/* Section 5: Pesticide Safety & Disclaimer */}
        <section className="rounded-xl border border-amber-300 bg-amber-50/70 p-6 sm:p-8 space-y-2">
          <div className="flex items-center gap-2 text-amber-900 font-semibold text-sm">
            <AlertTriangle className="h-4 w-4 text-amber-700" />
            <span>{t("disclaimerTitle")}</span>
          </div>
          <p className="text-xs sm:text-sm text-amber-950 leading-relaxed">
            {t("footerDisclaimer")}
          </p>
        </section>
      </div>
    </div>
  );
}
