import { useState } from "react";
import { X, User, Lock, Mail, LogIn, UserPlus, AlertCircle, ShieldCheck } from "lucide-react";
import { useLanguage } from "../i18n/LanguageContext";
import { loginUser, registerUser, setAuthToken } from "../api";

export default function AuthModal({ isOpen, onClose, onAuthSuccess }) {
  const { t } = useLanguage();
  const [mode, setMode] = useState("login"); // "login" | "register"
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (mode === "login") {
        const res = await loginUser({ email: email.trim(), password });
        if (res.access_token) {
          setAuthToken(res.access_token);
          if (onAuthSuccess) {
            onAuthSuccess(res.user);
          }
          onClose();
        }
      } else {
        const payload = {
          email: email.trim(),
          password,
        };
        if (fullName.trim()) {
          payload.full_name = fullName.trim();
        }
        const res = await registerUser(payload);
        if (res.access_token) {
          setAuthToken(res.access_token);
          if (onAuthSuccess) {
            onAuthSuccess(res.user);
          }
          onClose();
        }
      }
    } catch (err) {
      setError(err.message || "Authentication failed. Please check your details.");
    } finally {
      setLoading(false);
    }
  }

  function switchMode(newMode) {
    setMode(newMode);
    setError(null);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-forest-950/70 p-4 backdrop-blur-sm animate-fade-in">
      <div
        className="w-full max-w-md rounded-2xl bg-white dark:bg-[#12221b] p-6 shadow-2xl border border-soil-200 dark:border-soil-700 transition-all"
        role="dialog"
        aria-modal="true"
        aria-labelledby="auth-modal-title"
      >
        {/* Header */}
        <div className="flex items-start justify-between border-b border-soil-200 dark:border-soil-700 pb-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-forest-900 dark:bg-forest-800 text-wheat-300">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <h2 id="auth-modal-title" className="font-display text-lg font-bold text-forest-900 dark:text-forest-100">
                {mode === "login" ? t("authLoginTitle") : t("authRegisterTitle")}
              </h2>
              <p className="text-xs text-soil-600 dark:text-soil-300">
                {mode === "login" ? t("authLoginSubtitle") : t("authRegisterSubtitle")}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-soil-400 hover:bg-soil-100 dark:hover:bg-forest-800 hover:text-soil-700 dark:hover:text-soil-200 transition-colors"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Mode Tabs */}
        <div className="mt-4 flex rounded-lg bg-soil-100 dark:bg-[#1a352a] p-1">
          <button
            type="button"
            onClick={() => switchMode("login")}
            className={`flex-1 rounded-md py-1.5 text-xs font-semibold transition-all ${
              mode === "login"
                ? "bg-white dark:bg-forest-800 text-forest-900 dark:text-white shadow-sm"
                : "text-soil-600 dark:text-soil-300 hover:text-forest-900 dark:hover:text-white"
            }`}
          >
            {t("authSignIn")}
          </button>
          <button
            type="button"
            onClick={() => switchMode("register")}
            className={`flex-1 rounded-md py-1.5 text-xs font-semibold transition-all ${
              mode === "register"
                ? "bg-white dark:bg-forest-800 text-forest-900 dark:text-white shadow-sm"
                : "text-soil-600 dark:text-soil-300 hover:text-forest-900 dark:hover:text-white"
            }`}
          >
            {t("authSignUp")}
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mt-3 flex items-start gap-2 rounded-lg border border-rose-200 dark:border-rose-900 bg-rose-50 dark:bg-rose-950/60 p-3 text-xs text-rose-800 dark:text-rose-200">
            <AlertCircle className="h-4 w-4 shrink-0 text-rose-600 dark:text-rose-400 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="mt-4 space-y-3">
          <div>
            <label className="block text-xs font-semibold text-soil-700 dark:text-soil-200">
              Email Address
            </label>
            <div className="relative mt-1">
              <Mail className="absolute left-3 top-2.5 h-4 w-4 text-soil-400 dark:text-soil-500" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="e.g. ram.patil@example.com"
                className="w-full rounded-lg border border-soil-300 dark:border-soil-700 py-2 pl-9 pr-3 text-xs bg-white dark:bg-[#183227] text-soil-900 dark:text-white placeholder-soil-400 dark:placeholder-soil-500 focus:border-forest-600 dark:focus:border-leaf-500 focus:outline-none focus:ring-1 focus:ring-forest-600 dark:focus:ring-leaf-500"
              />
            </div>
          </div>

          {mode === "register" && (
            <div>
              <label className="block text-xs font-semibold text-soil-700 dark:text-soil-200">
                Full Name / Farm Title (Optional)
              </label>
              <div className="relative mt-1">
                <User className="absolute left-3 top-2.5 h-4 w-4 text-soil-400 dark:text-soil-500" />
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g. Ram Patil"
                  className="w-full rounded-lg border border-soil-300 dark:border-soil-700 py-2 pl-9 pr-3 text-xs bg-white dark:bg-[#183227] text-soil-900 dark:text-white placeholder-soil-400 dark:placeholder-soil-500 focus:border-forest-600 dark:focus:border-leaf-500 focus:outline-none focus:ring-1 focus:ring-forest-600 dark:focus:ring-leaf-500"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-soil-700 dark:text-soil-200">
              {t("authPassword")}
            </label>
            <div className="relative mt-1">
              <Lock className="absolute left-3 top-2.5 h-4 w-4 text-soil-400 dark:text-soil-500" />
              <input
                type="password"
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="At least 6 characters"
                className="w-full rounded-lg border border-soil-300 dark:border-soil-700 py-2 pl-9 pr-3 text-xs bg-white dark:bg-[#183227] text-soil-900 dark:text-white placeholder-soil-400 dark:placeholder-soil-500 focus:border-forest-600 dark:focus:border-leaf-500 focus:outline-none focus:ring-1 focus:ring-forest-600 dark:focus:ring-leaf-500"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg bg-forest-900 dark:bg-leaf-600 py-2.5 text-xs font-bold text-white shadow hover:bg-forest-800 dark:hover:bg-leaf-500 disabled:opacity-50 transition-colors"
          >
            {loading ? (
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
            ) : mode === "login" ? (
              <>
                <LogIn className="h-4 w-4" />
                <span>{t("authSubmitLogin")}</span>
              </>
            ) : (
              <>
                <UserPlus className="h-4 w-4" />
                <span>{t("authSubmitRegister")}</span>
              </>
            )}
          </button>
        </form>

        {/* Footer switch */}
        <div className="mt-4 text-center">
          <button
            type="button"
            onClick={() => switchMode(mode === "login" ? "register" : "login")}
            className="text-xs font-medium text-forest-800 dark:text-leaf-300 hover:underline"
          >
            {mode === "login" ? t("authSwitchToRegister") : t("authSwitchToLogin")}
          </button>
        </div>
      </div>
    </div>
  );
}
