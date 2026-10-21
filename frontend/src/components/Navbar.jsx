import { useState } from "react";
import {
  Sprout,
  Compass,
  UploadCloud,
  FileText,
  MessageSquare,
  Menu,
  X,
  User,
  LogIn,
  LogOut,
  Bookmark,
  Sun,
  Moon,
} from "lucide-react";
import { useLanguage } from "../i18n/LanguageContext";
import LanguageSwitcher from "./LanguageSwitcher";

export default function Navbar({
  activeTab,
  onTabChange,
  hasResults,
  currentUser = null,
  onOpenAuthModal,
  onLogout,
  theme = "light",
  onToggleTheme,
}) {
  const { t } = useLanguage();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { id: "overview", label: t("navHome"), icon: Compass },
    { id: "analyze", label: t("navAnalyze"), icon: UploadCloud },
    {
      id: "results",
      label: t("navResults"),
      icon: FileText,
      badge: hasResults ? "Active" : null,
      disabled: !hasResults,
    },
    { id: "assistant", label: t("navAssistant"), icon: MessageSquare },
    { id: "saved-reports", label: t("navSavedReports"), icon: Bookmark },
  ];

  function handleSelect(id) {
    onTabChange(id);
    setMobileMenuOpen(false);
  }

  return (
    <header className="sticky top-0 z-40 border-b border-soil-200 dark:border-[#235347] bg-white dark:bg-[#163832] backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
        {/* Brand */}
        <button
          type="button"
          onClick={() => handleSelect("overview")}
          className="group flex items-center gap-2.5 text-left focus-visible:ring-2 focus-visible:ring-forest-600 dark:focus-visible:ring-[#8EB69B] rounded-lg p-1"
        >
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-forest-900 dark:bg-[#235347] text-white shadow-soft transition-transform group-hover:scale-105">
            <Sprout className="h-6 w-6" aria-hidden="true" />
          </div>
          <div>
            <span className="font-display text-2xl sm:text-3xl font-bold tracking-tight text-forest-900 dark:text-white">
              AgriMind
            </span>
          </div>
        </button>

        {/* Desktop Navigation Links */}
        <nav className="hidden items-center gap-1 md:flex" aria-label="Main navigation">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => !item.disabled && handleSelect(item.id)}
                disabled={item.disabled}
                className={`flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-semibold transition-all ${
                  isActive
                    ? "bg-forest-900 dark:bg-[#235347] text-white shadow-sm ring-1 ring-forest-900/20 dark:ring-[#8EB69B]/40"
                    : item.disabled
                    ? "cursor-not-allowed text-soil-300 dark:text-[#6C9B7E] opacity-50"
                    : "text-forest-900 dark:text-white hover:bg-forest-50 dark:hover:bg-[#235347]/70 hover:text-forest-800 dark:hover:text-[#DAF1DE]"
                }`}
              >
                <Icon className="h-4 w-4" aria-hidden="true" />
                <span>{item.label}</span>
                {item.badge && (
                  <span className="ml-1 rounded-full bg-forest-800 dark:bg-[#8EB69B] px-1.5 py-0.2 text-[9px] font-semibold text-white dark:text-[#0B2B26]">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Desktop Actions */}
        <div className="hidden items-center gap-2.5 md:flex">
          {/* Dark Mode Toggle Button */}
          <button
            type="button"
            onClick={onToggleTheme}
            title={theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode"}
            aria-label="Toggle Dark Mode"
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-soil-200 dark:border-[#235347] bg-white dark:bg-[#163832] text-forest-800 dark:text-[#DAF1DE] hover:bg-forest-50 dark:hover:bg-[#235347] transition-colors shadow-sm"
          >
            {theme === "dark" ? (
              <Sun className="h-4 w-4 text-[#DAF1DE]" />
            ) : (
              <Moon className="h-4 w-4 text-forest-800" />
            )}
          </button>

          {/* User Authentication Pill / Sign In Button */}
          {currentUser ? (
            <div className="flex items-center gap-1.5 rounded-lg border border-soil-200 dark:border-[#235347] bg-soil-50 dark:bg-[#235347] px-2.5 py-1 text-xs">
              <User className="h-3.5 w-3.5 text-forest-800 dark:text-[#DAF1DE]" />
              <span
                className="font-semibold text-forest-900 dark:text-white max-w-[120px] truncate"
                title={currentUser.full_name || currentUser.email}
              >
                {currentUser.full_name || currentUser.email.split("@")[0]}
              </span>
              <button
                type="button"
                onClick={onLogout}
                title={t("authSignOut")}
                className="ml-1 text-soil-500 dark:text-[#8EB69B] hover:text-rose-600 transition-colors"
                aria-label={t("authSignOut")}
              >
                <LogOut className="h-3.5 w-3.5" />
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={onOpenAuthModal}
              className="inline-flex items-center gap-1.5 rounded-lg border border-forest-900 dark:border-[#235347] bg-forest-900 dark:bg-[#235347] px-3 py-1.5 text-xs font-semibold text-white hover:bg-forest-800 dark:hover:bg-[#2E6B5C] shadow-sm transition-colors"
            >
              <LogIn className="h-3.5 w-3.5" />
              <span>{t("authSignIn")}</span>
            </button>
          )}

          <LanguageSwitcher />
        </div>

        {/* Mobile Menu Button & Mobile Dark Mode */}
        <div className="flex items-center gap-2 md:hidden">
          <button
            type="button"
            onClick={onToggleTheme}
            title={theme === "dark" ? "Light Mode" : "Dark Mode"}
            aria-label="Toggle Dark Mode"
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-soil-200 dark:border-[#235347] bg-white dark:bg-[#163832] text-forest-800 dark:text-[#DAF1DE]"
          >
            {theme === "dark" ? (
              <Sun className="h-4 w-4 text-[#DAF1DE]" />
            ) : (
              <Moon className="h-4 w-4 text-forest-800" />
            )}
          </button>
          <LanguageSwitcher />
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="rounded-lg border border-soil-200 dark:border-[#235347] p-2 text-forest-900 dark:text-white hover:bg-forest-50 dark:hover:bg-[#235347]"
            aria-expanded={mobileMenuOpen}
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu Drawer */}
      {mobileMenuOpen && (
        <div className="border-t border-soil-200 dark:border-[#235347] bg-white dark:bg-[#163832] px-4 py-3 md:hidden">
          <div className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => !item.disabled && handleSelect(item.id)}
                  disabled={item.disabled}
                  className={`flex w-full items-center justify-between rounded-lg px-3 py-2.5 text-sm font-semibold ${
                    isActive
                      ? "bg-forest-900 dark:bg-[#235347] text-white"
                      : item.disabled
                      ? "cursor-not-allowed text-soil-300 dark:text-[#6C9B7E] opacity-50"
                      : "text-forest-900 dark:text-white hover:bg-forest-50 dark:hover:bg-[#235347]/60"
                  }`}
                >
                  <span className="flex items-center gap-2.5">
                    <Icon className="h-4 w-4" />
                    <span>{item.label}</span>
                  </span>
                  {item.badge && (
                    <span className="rounded-full bg-forest-800 dark:bg-[#8EB69B] px-2 py-0.5 text-[10px] text-white dark:text-[#0B2B26]">
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          <div className="mt-3 pt-3 border-t border-soil-200 dark:border-[#235347] space-y-2">
            {currentUser ? (
              <div className="flex items-center justify-between rounded-lg border border-soil-200 dark:border-[#235347] bg-soil-50 dark:bg-[#235347] p-2.5">
                <div className="flex items-center gap-2">
                  <User className="h-4 w-4 text-forest-800 dark:text-[#DAF1DE]" />
                  <span className="text-xs font-semibold text-forest-900 dark:text-white">
                    {currentUser.full_name || currentUser.email.split("@")[0]}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    onLogout();
                    setMobileMenuOpen(false);
                  }}
                  className="inline-flex items-center gap-1 text-xs font-medium text-rose-600 hover:text-rose-800"
                >
                  <LogOut className="h-3.5 w-3.5" />
                  <span>{t("authSignOut")}</span>
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => {
                  onOpenAuthModal();
                  setMobileMenuOpen(false);
                }}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-forest-900 dark:bg-[#235347] py-2.5 text-xs font-bold text-white shadow hover:bg-forest-800 dark:hover:bg-[#2E6B5C]"
              >
                <LogIn className="h-4 w-4" />
                <span>{t("authSignIn")} / {t("authSignUp")}</span>
              </button>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
