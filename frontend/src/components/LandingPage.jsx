import { ArrowRight, FileCheck, ShieldCheck, CloudRain } from "lucide-react";
import { useLanguage } from "../i18n/LanguageContext";

export default function LandingPage({ onGoToAnalyze }) {
  const { t } = useLanguage();

  return (
    <div className="space-y-16 py-6 sm:py-10">
      {/* Hero Section */}
      <section className="relative overflow-hidden rounded-2xl border border-soil-200 dark:border-[#235347] bg-white dark:bg-[#163832] p-6 sm:p-12 shadow-soft">
        <div className="max-w-3xl space-y-6">
          <h1 className="font-display text-3xl font-semibold tracking-tight text-forest-900 dark:text-white sm:text-5xl leading-[1.12]">
            {t("heroHeading")}
          </h1>

          <p className="text-base sm:text-lg leading-relaxed text-soil-600 dark:text-white/90">
            {t("heroDescription")}
          </p>

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <button
              type="button"
              onClick={onGoToAnalyze}
              className="inline-flex items-center gap-2 rounded-xl bg-forest-900 dark:bg-[#235347] px-6 py-3.5 text-sm font-semibold text-white shadow-soft hover:bg-forest-800 dark:hover:bg-[#2E6B5C] active:scale-[0.99] transition-all"
            >
              <span>{t("heroCta")}</span>
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
        </div>
      </section>

      {/* 3-Step Process */}
      <section className="space-y-6">
        <div>
          <h2 className="font-display text-2xl sm:text-3xl font-semibold text-forest-900 dark:text-white">
            {t("howItWorksHeading")}
          </h2>
          <p className="mt-1 text-sm text-soil-600 dark:text-white/90">
            {t("howItWorksSub")}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="group rounded-xl border border-soil-200 dark:border-[#235347] bg-white dark:bg-[#163832] p-6 shadow-soft hover:shadow-card hover:-translate-y-1.5 hover:border-forest-400 dark:hover:border-[#8EB69B] transition-all duration-300 ease-out space-y-3 cursor-default">
            <div className="flex items-center justify-between">
              <span className="font-mono text-sm font-bold text-forest-800 dark:text-[#DAF1DE] transition-colors duration-200 group-hover:text-forest-600 dark:group-hover:text-white">
                {t("step1Num")}
              </span>
              <FileCheck className="h-5 w-5 text-forest-800 dark:text-[#DAF1DE] transition-transform duration-300 group-hover:scale-110 group-hover:-translate-y-0.5" aria-hidden="true" />
            </div>
            <h3 className="font-display text-lg font-semibold text-forest-900 dark:text-white transition-colors duration-200 group-hover:text-forest-700 dark:group-hover:text-[#DAF1DE]">
              {t("step1Name")}
            </h3>
            <p className="text-sm text-soil-600 dark:text-white/90 leading-relaxed">
              {t("step1Detail")}
            </p>
          </div>

          <div className="group rounded-xl border border-soil-200 dark:border-[#235347] bg-white dark:bg-[#163832] p-6 shadow-soft hover:shadow-card hover:-translate-y-1.5 hover:border-forest-400 dark:hover:border-[#8EB69B] transition-all duration-300 ease-out space-y-3 cursor-default">
            <div className="flex items-center justify-between">
              <span className="font-mono text-sm font-bold text-forest-800 dark:text-[#DAF1DE] transition-colors duration-200 group-hover:text-forest-600 dark:group-hover:text-white">
                {t("step2Num")}
              </span>
              <CloudRain className="h-5 w-5 text-forest-800 dark:text-[#DAF1DE] transition-transform duration-300 group-hover:scale-110 group-hover:-translate-y-0.5" aria-hidden="true" />
            </div>
            <h3 className="font-display text-lg font-semibold text-forest-900 dark:text-white transition-colors duration-200 group-hover:text-forest-700 dark:group-hover:text-[#DAF1DE]">
              {t("step2Name")}
            </h3>
            <p className="text-sm text-soil-600 dark:text-white/90 leading-relaxed">
              {t("step2Detail")}
            </p>
          </div>

          <div className="group rounded-xl border border-soil-200 dark:border-[#235347] bg-white dark:bg-[#163832] p-6 shadow-soft hover:shadow-card hover:-translate-y-1.5 hover:border-forest-400 dark:hover:border-[#8EB69B] transition-all duration-300 ease-out space-y-3 cursor-default">
            <div className="flex items-center justify-between">
              <span className="font-mono text-sm font-bold text-forest-800 dark:text-[#DAF1DE] transition-colors duration-200 group-hover:text-forest-600 dark:group-hover:text-white">
                {t("step3Num")}
              </span>
              <ShieldCheck className="h-5 w-5 text-forest-800 dark:text-[#DAF1DE] transition-transform duration-300 group-hover:scale-110 group-hover:-translate-y-0.5" aria-hidden="true" />
            </div>
            <h3 className="font-display text-lg font-semibold text-forest-900 dark:text-white transition-colors duration-200 group-hover:text-forest-700 dark:group-hover:text-[#DAF1DE]">
              {t("step3Name")}
            </h3>
            <p className="text-sm text-soil-600 dark:text-white/90 leading-relaxed">
              {t("step3Detail")}
            </p>
          </div>
        </div>
      </section>

      {/* Core Design Principles / Guardrails */}
      <section className="rounded-2xl border border-soil-200 dark:border-[#235347] bg-white dark:bg-[#163832] text-forest-900 dark:text-white p-6 sm:p-10 shadow-soft hover:shadow-card hover:border-forest-300 dark:hover:border-[#8EB69B]/70 transition-all duration-300 space-y-6">
        <div>
          <span className="font-mono text-xs uppercase tracking-wider text-forest-800 dark:text-[#DAF1DE]">
            Architectural Integrity
          </span>
          <h2 className="font-display text-2xl sm:text-3xl font-semibold mt-1 text-forest-900 dark:text-white">
            {t("principlesHeading")}
          </h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 pt-2">
          <div className="space-y-2 border-l-2 border-forest-600 dark:border-[#235347] pl-4 transition-all duration-200 hover:border-forest-900 dark:hover:border-[#8EB69B] hover:translate-x-1">
            <h3 className="font-medium text-base text-forest-900 dark:text-[#DAF1DE]">
              {t("p1Title")}
            </h3>
            <p className="text-xs sm:text-sm text-soil-600 dark:text-white/90 leading-relaxed">
              {t("p1Desc")}
            </p>
          </div>

          <div className="space-y-2 border-l-2 border-forest-600 dark:border-[#235347] pl-4 transition-all duration-200 hover:border-forest-900 dark:hover:border-[#8EB69B] hover:translate-x-1">
            <h3 className="font-medium text-base text-forest-900 dark:text-[#DAF1DE]">
              {t("p2Title")}
            </h3>
            <p className="text-xs sm:text-sm text-soil-600 dark:text-white/90 leading-relaxed">
              {t("p2Desc")}
            </p>
          </div>

          <div className="space-y-2 border-l-2 border-forest-600 dark:border-[#235347] pl-4 transition-all duration-200 hover:border-forest-900 dark:hover:border-[#8EB69B] hover:translate-x-1">
            <h3 className="font-medium text-base text-forest-900 dark:text-[#DAF1DE]">
              {t("p3Title")}
            </h3>
            <p className="text-xs sm:text-sm text-soil-600 dark:text-white/90 leading-relaxed">
              {t("p3Desc")}
            </p>
          </div>

          <div className="space-y-2 border-l-2 border-forest-600 dark:border-[#235347] pl-4 transition-all duration-200 hover:border-forest-900 dark:hover:border-[#8EB69B] hover:translate-x-1">
            <h3 className="font-medium text-base text-forest-900 dark:text-[#DAF1DE]">
              {t("p4Title")}
            </h3>
            <p className="text-xs sm:text-sm text-soil-600 dark:text-white/90 leading-relaxed">
              {t("p4Desc")}
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
