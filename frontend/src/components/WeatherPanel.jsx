import React, { useState } from "react";
import { useLanguage } from "../i18n/LanguageContext";
import { applyTodayLabels, recommendationLabels } from "../i18n/translations";
import {
  CloudRain,
  Wind,
  Thermometer,
  Droplets,
  Calendar,
  CheckCircle2,
  AlertTriangle,
  CloudSun,
  MapPin,
  Clock,
  RotateCcw,
  ShieldAlert,
  Info,
  Sun,
  Cloud,
  CloudLightning,
  Sparkles,
  Locate,
} from "lucide-react";

export default function WeatherPanel({
  applicationWindow,
  onRefreshWeather,
  isRefreshing = false,
  locationName = null,
}) {
  const { t, lang } = useLanguage();
  const [inlineLoc, setInlineLoc] = useState("");
  const [detectingGps, setDetectingGps] = useState(false);
  const applyLabel = (code) => (applyTodayLabels[lang] || applyTodayLabels.en)[code] || code;
  const recLabel = (code) => (recommendationLabels[lang] || recommendationLabels.en)[code] || code;

  const handleUseGps = () => {
    if (typeof navigator === "undefined" || !navigator.geolocation) {
      alert("Geolocation is not supported by your browser.");
      return;
    }
    setDetectingGps(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setDetectingGps(false);
        if (onRefreshWeather) {
          onRefreshWeather(null, {
            latitude: pos.coords.latitude,
            longitude: pos.coords.longitude,
          });
        }
      },
      (err) => {
        setDetectingGps(false);
        console.warn("GPS error:", err);
        alert("Could not detect device location. Please enable location permissions or type a city name.");
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  if (!applicationWindow) {
    return (
      <div className="rounded-xl border border-soil-200 dark:border-soil-700 bg-white dark:bg-forest-900/60 p-6 shadow-soft space-y-3">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <h3 className="font-display text-lg font-semibold text-forest-900 dark:text-forest-100 flex items-center gap-2">
            <CloudSun className="h-5 w-5 text-forest-700 dark:text-leaf-400" />
            <span>{t("weatherHeading")}</span>
          </h3>
          {onRefreshWeather && (
            <button
              type="button"
              onClick={() => onRefreshWeather()}
              disabled={isRefreshing}
              className="inline-flex items-center gap-1.5 text-xs text-forest-800 dark:text-leaf-300 hover:text-forest-950 dark:hover:text-leaf-200 font-medium"
            >
              <RotateCcw className={`h-3.5 w-3.5 ${isRefreshing ? "animate-spin" : ""}`} />
              <span>Check Forecast</span>
            </button>
          )}
        </div>
        <p className="text-xs text-soil-500 dark:text-soil-400">{t("weatherEmpty")}</p>
      </div>
    );
  }

  const {
    recommendation,
    apply_today,
    reason,
    next_window,
    forecast_summary,
    forecast_days = [],
    location_name: appLocation,
    latitude,
    longitude,
    fetched_at,
    provider = "Open-Meteo",
    attribution = "Weather data by Open-Meteo.com (CC BY 4.0)",
    current_temperature_c,
    current_condition,
    limitations,
    is_available = true,
    error,
  } = applicationWindow;

  const isGo = apply_today === "GO";
  const displayLocation = appLocation || locationName || (latitude != null && longitude != null ? `${latitude.toFixed(2)}°N, ${longitude.toFixed(2)}°E` : null);
  const formattedFetchedAt = fetched_at ? new Date(fetched_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : null;

  // Real-time temperature & condition resolution
  const resolvedCurrentTemp = current_temperature_c != null ? current_temperature_c : forecast_summary?.current_temperature_c;
  const resolvedCondition = current_condition || forecast_summary?.current_condition || forecast_summary?.condition;

  // Helper for weather icons
  function getWeatherIcon(condition = "") {
    const c = condition.toLowerCase();
    if (c.includes("thunder")) return <CloudLightning className="h-4 w-4 text-amber-500" />;
    if (c.includes("rain") || c.includes("drizzle") || c.includes("shower")) return <CloudRain className="h-4 w-4 text-blue-500" />;
    if (c.includes("cloud") || c.includes("overcast")) return <Cloud className="h-4 w-4 text-soil-400" />;
    return <Sun className="h-4 w-4 text-amber-400" />;
  }

  return (
    <div className="rounded-xl border border-soil-200 dark:border-soil-700 bg-white dark:bg-forest-900/60 p-6 shadow-soft space-y-4">
      {/* Header with Title, Location, Freshness & Refresh */}
      <div className="flex items-start justify-between gap-3 flex-wrap border-b border-soil-100 dark:border-soil-800 pb-3">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="font-display text-lg font-semibold text-forest-900 dark:text-white flex items-center gap-2">
              <CloudSun className="h-5 w-5 text-forest-800 dark:text-[#DAF1DE]" aria-hidden="true" />
              <span>{t("weatherHeading")}</span>
            </h3>

            {displayLocation && (
              <span className="inline-flex items-center gap-1 rounded-full bg-forest-50 dark:bg-forest-800/80 border border-forest-200/80 dark:border-forest-700 px-2.5 py-0.5 text-xs text-forest-900 dark:text-forest-100 font-medium">
                <MapPin className="h-3 w-3 text-forest-700 dark:text-leaf-400" />
                <span className="truncate max-w-[180px] sm:max-w-xs">{displayLocation}</span>
              </span>
            )}

            {/* Current Real-Time Temperature Badge */}
            {is_available && resolvedCurrentTemp != null && (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 dark:bg-amber-950/60 border border-amber-300 dark:border-amber-700 px-2.5 py-0.5 text-xs text-amber-950 dark:text-amber-200 font-bold">
                <Thermometer className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" />
                <span>{resolvedCurrentTemp}°C</span>
                {resolvedCondition && <span className="font-medium text-soil-600 dark:text-soil-300 font-sans">• {resolvedCondition}</span>}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {formattedFetchedAt && (
            <span className="inline-flex items-center gap-1 text-[11px] font-mono text-soil-400 dark:text-soil-500">
              <Clock className="h-3 w-3" />
              <span>{formattedFetchedAt}</span>
            </span>
          )}

          {/* Current GPS Position Button */}
          {typeof navigator !== "undefined" && navigator.geolocation && onRefreshWeather && (
            <button
              type="button"
              onClick={handleUseGps}
              disabled={isRefreshing || detectingGps}
              title="Detect my current farm location using device GPS"
              className="inline-flex items-center gap-1 rounded-md border border-forest-200 dark:border-forest-700 bg-forest-50 dark:bg-forest-800 px-2.5 py-1 text-xs font-semibold text-forest-900 dark:text-forest-100 hover:bg-forest-100 dark:hover:bg-forest-700 transition-colors disabled:opacity-50"
            >
              <Locate className={`h-3.5 w-3.5 text-forest-700 dark:text-leaf-400 ${detectingGps ? "animate-pulse" : ""}`} />
              <span className="hidden md:inline">{detectingGps ? "Locating..." : "Current Position"}</span>
            </button>
          )}

          {onRefreshWeather && (
            <button
              type="button"
              onClick={() => onRefreshWeather()}
              disabled={isRefreshing || detectingGps}
              title="Refresh live weather forecast"
              className="inline-flex items-center gap-1 rounded-md border border-soil-200 dark:border-soil-700 bg-soil-50 dark:bg-forest-800 px-2.5 py-1 text-xs font-medium text-forest-900 dark:text-forest-100 hover:bg-soil-100 dark:hover:bg-forest-700 transition-colors disabled:opacity-50"
            >
              <RotateCcw className={`h-3.5 w-3.5 ${isRefreshing ? "animate-spin text-forest-700 dark:text-leaf-400" : ""}`} />
              <span>{isRefreshing ? "Refreshing..." : "Refresh"}</span>
            </button>
          )}

          {/* Status Badge */}
          <span
            className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold font-mono ${
              !is_available
                ? "bg-soil-100 dark:bg-forest-800 text-soil-800 dark:text-soil-200 border border-soil-300 dark:border-soil-700"
                : isGo
                ? "bg-emerald-100 dark:bg-emerald-950 text-emerald-950 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-700"
                : "bg-amber-100 dark:bg-amber-950 text-amber-950 dark:text-amber-300 border border-amber-300 dark:border-amber-700"
            }`}
          >
            {is_available ? (
              isGo ? <CheckCircle2 className="h-3.5 w-3.5" /> : <AlertTriangle className="h-3.5 w-3.5" />
            ) : (
              <ShieldAlert className="h-3.5 w-3.5 text-soil-600 dark:text-soil-400" />
            )}
            <span>{is_available ? applyLabel(apply_today) : "UNAVAILABLE"}</span>
          </span>
        </div>
      </div>

      {/* Weather Unavailable Notice (Zero fake data) */}
      {!is_available && (
        <div className="rounded-lg border border-amber-300 dark:border-amber-800 bg-amber-50/80 dark:bg-amber-950/50 p-4 space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold text-amber-900 dark:text-amber-300 uppercase tracking-wide">
            <AlertTriangle className="h-4 w-4 text-amber-700 dark:text-amber-400 shrink-0" />
            <span>Weather Forecast Unavailable</span>
          </div>
          <p className="text-xs text-amber-950 dark:text-amber-200 leading-relaxed pl-6">
            {reason}
          </p>
          <p className="text-[11px] text-amber-800/90 dark:text-amber-300/80 pl-6 italic">
            AgriMind adheres strictly to a zero-fabrication policy and does not synthesize fake meteorological readings. Timing decisions should be deferred to visual field inspection.
          </p>
          {onRefreshWeather && (
            <div className="pl-6 pt-2 space-y-2">
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
                <div className="relative flex-1">
                  <MapPin className="pointer-events-none absolute left-2.5 top-2.5 h-3.5 w-3.5 text-soil-400" />
                  <input
                    type="text"
                    value={inlineLoc}
                    onChange={(e) => setInlineLoc(e.target.value)}
                    placeholder="Enter district or town (e.g., Pune, Maharashtra)"
                    className="w-full rounded-md border border-amber-300 dark:border-amber-700 bg-white dark:bg-forest-950 pl-8 pr-3 py-1.5 text-xs text-soil-900 dark:text-soil-100 focus:border-forest-600 focus:ring-1 focus:ring-forest-600"
                  />
                </div>
                <button
                  type="button"
                  onClick={() => onRefreshWeather(inlineLoc.trim() || "Pune, Maharashtra")}
                  disabled={isRefreshing || detectingGps}
                  className="inline-flex items-center justify-center gap-1.5 rounded-md bg-forest-800 dark:bg-forest-700 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-forest-900 dark:hover:bg-forest-600 transition-colors disabled:opacity-50"
                >
                  <RotateCcw className={`h-3 w-3 ${isRefreshing ? "animate-spin" : ""}`} />
                  <span>{isRefreshing ? "Checking..." : "Check Live Weather"}</span>
                </button>
                {typeof navigator !== "undefined" && navigator.geolocation && (
                  <button
                    type="button"
                    onClick={handleUseGps}
                    disabled={isRefreshing || detectingGps}
                    className="inline-flex items-center justify-center gap-1.5 rounded-md border border-forest-300 dark:border-forest-700 bg-forest-50 dark:bg-forest-800 px-3 py-1.5 text-xs font-semibold text-forest-900 dark:text-forest-100 hover:bg-forest-100 dark:hover:bg-forest-700 transition-colors disabled:opacity-50"
                  >
                    <Locate className={`h-3.5 w-3.5 text-forest-700 dark:text-leaf-400 ${detectingGps ? "animate-pulse" : ""}`} />
                    <span>{detectingGps ? "Detecting..." : "Use Current GPS"}</span>
                  </button>
                )}
              </div>

              {/* Quick presets */}
              <div className="flex flex-wrap items-center gap-1.5 text-[11px] text-soil-600 dark:text-soil-400">
                <span className="text-soil-500">Quick select:</span>
                {["Pune, Maharashtra", "Nagpur, Maharashtra", "Nashik, Maharashtra", "Ludhiana, Punjab"].map((city) => (
                  <button
                    key={city}
                    type="button"
                    onClick={() => {
                      setInlineLoc(city);
                      onRefreshWeather(city);
                    }}
                    className="rounded border border-amber-200 dark:border-amber-800 bg-white/80 dark:bg-forest-900 px-2 py-0.5 text-[11px] text-amber-950 dark:text-amber-200 hover:bg-amber-100 dark:hover:bg-amber-900/40 transition-colors"
                  >
                    {city.split(",")[0]}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Agronomic Timing Reason Box */}
      {is_available && (
        <div
          className={`rounded-lg border p-4 text-xs sm:text-sm leading-relaxed space-y-1 ${
            isGo
              ? "border-emerald-200 dark:border-emerald-800 bg-emerald-50/50 dark:bg-emerald-950/40 text-emerald-950 dark:text-emerald-200"
              : "border-amber-200 dark:border-amber-800 bg-amber-50/50 dark:bg-amber-950/40 text-amber-950 dark:text-amber-200"
          }`}
        >
          <div className="font-semibold flex items-center gap-1.5">
            {isGo ? (
              <CheckCircle2 className="h-4 w-4 text-emerald-700 dark:text-emerald-400 shrink-0" />
            ) : (
              <AlertTriangle className="h-4 w-4 text-amber-700 dark:text-amber-400 shrink-0" />
            )}
            <span>{isGo ? "Favorable Application Window Today" : "Application Postponement Advised"}</span>
          </div>
          <p className="pl-5 text-xs text-soil-800 dark:text-soil-300 leading-relaxed">{reason}</p>
        </div>
      )}

      {/* Next Safe Window if Waiting */}
      {is_available && next_window && (
        <div className="flex items-center justify-between gap-3 rounded-lg border border-soil-200 dark:border-soil-700 bg-soil-50 dark:bg-forest-950/60 p-3 text-xs text-soil-800 dark:text-soil-200">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-forest-700 dark:text-leaf-400 shrink-0" />
            <span>
              {t("nextWindowLabel")}: <strong className="font-mono text-forest-900 dark:text-forest-100">{next_window}</strong>
            </span>
          </div>
          <span className="text-[11px] font-mono text-leaf-800 dark:text-leaf-300 bg-leaf-50 dark:bg-leaf-950/60 border border-leaf-200 dark:border-leaf-800 rounded px-2 py-0.5 font-medium">
            Projected Clear Conditions
          </span>
        </div>
      )}

      {/* Today's Forecast Metric Readouts */}
      {is_available && forecast_summary && (
        <div className="space-y-2 pt-1">
          <div className="flex items-center justify-between text-xs">
            <span className="font-mono text-[11px] uppercase tracking-wider text-soil-500 dark:text-soil-400 font-semibold">
              Today's Field Conditions {forecast_summary.condition ? `(${forecast_summary.condition})` : ""}
            </span>
            <span className="text-[11px] text-soil-400 dark:text-soil-500 font-mono">
              Measured 2m above ground
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
            <div className="rounded-lg border border-soil-200 dark:border-soil-700 bg-soil-50/60 dark:bg-forest-950/50 p-2.5 space-y-1">
              <span className="flex items-center gap-1 text-[11px] text-soil-500 dark:text-soil-400 font-medium">
                <CloudRain className="h-3.5 w-3.5 text-forest-600 dark:text-leaf-400" />
                <span>{t("rainLabel")}</span>
              </span>
              <p className="data-readout text-sm font-semibold text-forest-950 dark:text-forest-100">
                {forecast_summary.precipitation_mm ?? 0} mm
              </p>
              <span className="text-[10px] text-soil-500 dark:text-soil-400 font-mono block">
                {forecast_summary.precipitation_probability_pct ?? 0}% probability
              </span>
            </div>

            <div className="rounded-lg border border-soil-200 dark:border-soil-700 bg-soil-50/60 dark:bg-forest-950/50 p-2.5 space-y-1">
              <span className="flex items-center gap-1 text-[11px] text-soil-500 dark:text-soil-400 font-medium">
                <Thermometer className="h-3.5 w-3.5 text-forest-600 dark:text-leaf-400" />
                <span>{t("tempLabel")}</span>
              </span>
              <p className="data-readout text-sm font-bold text-forest-950 dark:text-forest-100">
                {resolvedCurrentTemp != null
                  ? `${resolvedCurrentTemp}°C`
                  : (forecast_summary.temp_min_c != null && forecast_summary.temp_max_c != null
                      ? `${forecast_summary.temp_min_c}–${forecast_summary.temp_max_c}°C`
                      : "—")}
              </p>
              <span className="text-[10px] text-soil-500 dark:text-soil-400 font-mono block">
                {resolvedCurrentTemp != null && forecast_summary.temp_min_c != null && forecast_summary.temp_max_c != null
                  ? `Current (${forecast_summary.temp_min_c}–${forecast_summary.temp_max_c}°C)`
                  : "Diurnal range"}
              </span>
            </div>

            <div className="rounded-lg border border-soil-200 dark:border-soil-700 bg-soil-50/60 dark:bg-forest-950/50 p-2.5 space-y-1">
              <span className="flex items-center gap-1 text-[11px] text-soil-500 dark:text-soil-400 font-medium">
                <Wind className="h-3.5 w-3.5 text-forest-600 dark:text-leaf-400" />
                <span>{t("windLabel")}</span>
              </span>
              <p className="data-readout text-sm font-semibold text-forest-950 dark:text-forest-100">
                {forecast_summary.wind_max_kmh ?? 0} km/h
              </p>
              <span className="text-[10px] text-soil-500 dark:text-soil-400 font-mono block">
                Max gust/velocity
              </span>
            </div>

            <div className="rounded-lg border border-soil-200 dark:border-soil-700 bg-soil-50/60 dark:bg-forest-950/50 p-2.5 space-y-1">
              <span className="flex items-center gap-1 text-[11px] text-soil-500 dark:text-soil-400 font-medium">
                <Droplets className="h-3.5 w-3.5 text-forest-600 dark:text-leaf-400" />
                <span>{t("humidityLabel")}</span>
              </span>
              <p className="data-readout text-sm font-semibold text-forest-950 dark:text-forest-100">
                {forecast_summary.humidity_max_pct ?? 0}%
              </p>
              <span className="text-[10px] text-soil-500 dark:text-soil-400 font-mono block">
                Peak relative humidity
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Multi-Day Forecast Timeline (Up to 5 Days) */}
      {is_available && forecast_days && forecast_days.length > 1 && (
        <div className="space-y-2 pt-2 border-t border-soil-100 dark:border-soil-800">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-mono uppercase tracking-wider text-soil-500 dark:text-soil-400 font-semibold">
              5-Day Agro-Weather Horizon
            </span>
            <span className="text-[11px] text-soil-400 dark:text-soil-500">
              Runoff & drift windows
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
            {forecast_days.slice(0, 5).map((d, idx) => {
              const isToday = idx === 0;
              const isNextSafe = d.date === next_window;
              const hasRunoff = (d.precipitation_mm || 0) >= 8.0 || (d.precipitation_probability_pct || 0) >= 70;
              const hasHighWind = (d.wind_max_kmh || 0) >= 30.0;
              const isSafe = !hasRunoff && !hasHighWind;

              return (
                <div
                  key={d.date}
                  className={`rounded-lg border p-2.5 text-center space-y-1.5 transition-all ${
                    isNextSafe
                      ? "border-emerald-400 dark:border-emerald-600 bg-emerald-50/60 dark:bg-emerald-950/50 ring-1 ring-emerald-300 dark:ring-emerald-700"
                      : isToday
                      ? "border-soil-300 dark:border-soil-600 bg-white dark:bg-forest-900/80 shadow-soft"
                      : "border-soil-100 dark:border-soil-800 bg-soil-50/40 dark:bg-forest-950/40"
                  }`}
                >
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="font-semibold text-forest-950 dark:text-forest-100">
                      {isToday ? "Today" : d.date.slice(5)}
                    </span>
                    {getWeatherIcon(d.condition)}
                  </div>

                  <p className="text-xs font-bold text-forest-900 dark:text-forest-100">
                    {d.temp_min_c != null && d.temp_max_c != null ? `${Math.round(d.temp_min_c)}° / ${Math.round(d.temp_max_c)}°` : "—"}
                  </p>

                  <div className="text-[10px] text-soil-600 dark:text-soil-300 space-y-0.5">
                    <div>{d.precipitation_mm}mm ({d.precipitation_probability_pct}%)</div>
                    <div className="text-soil-500 dark:text-soil-400">{d.wind_max_kmh} km/h</div>
                  </div>

                  <div className="pt-1">
                    <span
                      className={`inline-block rounded px-1.5 py-0.5 text-[9px] font-mono font-bold uppercase tracking-wider ${
                        isSafe
                          ? "bg-emerald-100 dark:bg-emerald-950 text-emerald-900 dark:text-emerald-300"
                          : "bg-amber-100 dark:bg-amber-950 text-amber-900 dark:text-amber-300"
                      }`}
                    >
                      {isSafe ? "CLEAR" : "WAIT"}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Limitations & Legal Notice */}
      <div className="pt-2 border-t border-soil-100 dark:border-soil-800 text-[11px] text-soil-400 dark:text-soil-500">
        <p className="leading-relaxed">
          <span className="font-semibold text-soil-600 dark:text-soil-300">Meteorological Limitation: </span>
          {limitations || "Weather forecasts are probabilistic estimates subject to local micro-climate shifts. Always inspect field conditions and soil moisture before application."}
        </p>
      </div>
    </div>
  );
}
