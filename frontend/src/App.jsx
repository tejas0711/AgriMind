import { useState, useEffect, useCallback } from "react";
import Navbar from "./components/Navbar";
import LandingPage from "./components/LandingPage";
import SoilWorkspace from "./components/SoilWorkspace";
import ResultsDashboard from "./components/ResultsDashboard";
import AssistantPage from "./components/AssistantPage";
import SavedReportsPage from "./components/SavedReportsPage";
import AuthModal from "./components/AuthModal";
import {
  uploadSoilReport,
  getRecommendation,
  checkBackendHealth,
  getCurrentUser,
  getAuthToken,
  clearAuthToken,
} from "./api";
import { useLanguage } from "./i18n/LanguageContext";

export default function App() {
  const { lang, t } = useLanguage();

  // Dark Mode State (default: light mode)
  const [theme, setTheme] = useState(() => {
    try {
      const saved = localStorage.getItem("agrimind:theme");
      if (saved === "dark") return "dark";
      if (saved === "light") return "light";
    } catch (_) {}
    return "light";
  });

  useEffect(() => {
    try {
      localStorage.setItem("agrimind:theme", theme);
    } catch (_) {}
    if (theme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [theme]);

  const handleToggleTheme = () => {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  };

  // Navigation State
  const [activeTab, setActiveTab] = useState("overview");

  // User Authentication State
  const [currentUser, setCurrentUser] = useState(null);
  const [authModalOpen, setAuthModalOpen] = useState(false);

  // Backend Health State (internal)
  const [backendStatus, setBackendStatus] = useState("checking");
  const [backendError, setBackendError] = useState(null);

  // Input & Analysis State
  const [file, setFile] = useState(null);
  const [soil, setSoil] = useState(null);
  const [location, setLocation] = useState("Pune, Maharashtra");
  const [crop, setCrop] = useState("");
  const [preferOrganic, setPreferOrganic] = useState(false);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [error, setError] = useState(null);

  // Refresh backend health
  const refreshBackendStatus = useCallback(async () => {
    setBackendStatus("checking");
    try {
      const res = await checkBackendHealth();
      if (res.ok) {
        setBackendStatus("connected");
        setBackendError(null);
      } else {
        setBackendStatus("offline");
        setBackendError(res.error || "Cannot connect to server");
      }
    } catch (err) {
      setBackendStatus("offline");
      setBackendError(err.message);
    }
  }, []);

  // Check health and current user session on mount
  useEffect(() => {
    refreshBackendStatus();
    if (getAuthToken()) {
      getCurrentUser()
        .then((user) => setCurrentUser(user))
        .catch(() => {
          clearAuthToken();
          setCurrentUser(null);
        });
    }
  }, [refreshBackendStatus]);

  function handleLogout() {
    clearAuthToken();
    setCurrentUser(null);
  }

  function handleLoadSavedReportIntoResults(savedReport) {
    if (!savedReport) return;
    const soilData = savedReport.soil_data || savedReport.soil_measurements || {};
    setResult({
      soil: soilData,
      selected_crop: savedReport.selected_crop,
      application_window: savedReport.application_window || savedReport.analysis_results?.weather_summary || null,
      deficiencies: savedReport.deficiencies || Object.values(savedReport.analysis_results?.soil_classification || {}),
      crop_scores: savedReport.crop_scores || savedReport.analysis_results?.crop_scores || [],
      fertilizer_options: savedReport.fertilizer_options || savedReport.analysis_results?.fertilizer_options || [],
      why: { plain_language_summary: savedReport.explanation },
      llm_explanation: savedReport.explanation || savedReport.analysis_results?.llm_explanation || null,
    });
    setSoil(soilData);
    setCrop(savedReport.selected_crop || "");
    setActiveTab("results");
  }

  // File selection and parsing handler
  async function handleFileSelect(selected) {
    setFile(selected);
    setError(null);
    if (!selected) {
      setSoil(null);
      return;
    }

    setParsing(true);
    try {
      const parsed = await uploadSoilReport(selected);
      setSoil(parsed);
    } catch (err) {
      setError(`Could not read soil report: ${err.message}`);
      setSoil(null);
    } finally {
      setParsing(false);
    }
  }

  // Handle updates made by farmer in the review table
  function handleUpdateSoil(updatedSoil) {
    setSoil(updatedSoil);
  }

  // Live Analysis handler
  async function handleAnalyze() {
    if (!soil) {
      setError(t("uploadFirstError"));
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const rec = await getRecommendation({
        soil: soil,
        selected_crop: crop || null,
        location_name: location || null,
        prefer_organic: preferOrganic,
        language: lang,
      });
      setResult(rec);
      setActiveTab("results");
    } catch (err) {
      setError(`Analysis failed: ${err.message}. Please check that the server is online and try again.`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-canvas dark:bg-[#0B2B26] text-forest-900 dark:text-white font-body transition-colors duration-200">
      {/* Top Navbar */}
      <Navbar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        hasResults={Boolean(result)}
        currentUser={currentUser}
        onOpenAuthModal={() => setAuthModalOpen(true)}
        onLogout={handleLogout}
        theme={theme}
        onToggleTheme={handleToggleTheme}
      />

      {/* Main Page Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6">
        {activeTab === "overview" && (
          <LandingPage
            onGoToAnalyze={() => setActiveTab("analyze")}
          />
        )}

        {activeTab === "analyze" && (
          <SoilWorkspace
            file={file}
            soil={soil}
            onFileSelect={handleFileSelect}
            onUpdateSoil={handleUpdateSoil}
            location={location}
            onLocationChange={setLocation}
            crop={crop}
            onCropChange={setCrop}
            preferOrganic={preferOrganic}
            onOrganicChange={setPreferOrganic}
            onAnalyze={handleAnalyze}
            loading={loading}
            parsing={parsing}
            error={error}
            backendStatus={backendStatus}
            backendError={backendError}
            onRefreshBackend={refreshBackendStatus}
          />
        )}

        {activeTab === "results" && (
          <ResultsDashboard
            result={result}
            currentUser={currentUser}
            onOpenAuth={() => setAuthModalOpen(true)}
            onAskAssistant={() => setActiveTab("assistant")}
            onNewUpload={() => setActiveTab("analyze")}
          />
        )}

        {activeTab === "assistant" && (
          <AssistantPage
            soil={soil}
            selectedCrop={crop || null}
            location={location || result?.location_name || "Pune, Maharashtra"}
            applicationWindow={result?.application_window || null}
          />
        )}

        {activeTab === "saved-reports" && (
          <SavedReportsPage
            currentUser={currentUser}
            onOpenAuth={() => setAuthModalOpen(true)}
            onNavigateToAnalyze={() => setActiveTab("analyze")}
            onLoadReportIntoResults={handleLoadSavedReportIntoResults}
          />
        )}
      </main>

      {/* Authentication Modal */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        onAuthSuccess={(user) => {
          setCurrentUser(user);
        }}
      />

      {/* Footer */}
      <footer className="border-t border-soil-200 dark:border-[#235347] bg-white dark:bg-[#163832] py-8 px-4 sm:px-6 mt-16 text-xs text-soil-600 dark:text-white">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-center sm:text-left leading-relaxed max-w-3xl">
            {t("footerDisclaimer")}
          </p>
          <div className="flex items-center gap-4 text-forest-800 dark:text-[#DAF1DE] font-semibold shrink-0">
            <button
              type="button"
              onClick={() => setActiveTab("assistant")}
              className="hover:underline"
            >
              Assistant
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
}
