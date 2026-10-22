/**
 * AgriMind Backend API Client
 * Configured via VITE_API_BASE_URL (with fallback to VITE_API_BASE and http://localhost:8000)
 */

const API_BASE = (
  import.meta.env.VITE_API_URL ||
  import.meta.env.VITE_API_BASE_URL ||
  import.meta.env.VITE_API_BASE ||
  "http://localhost:8000"
).replace(/\/$/, "");

const DEFAULT_TIMEOUT_MS = 60000;

class ApiError extends Error {
  constructor(message, status = 0, detail = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

const TOKEN_KEY = "agrimind_auth_token";

export function getAuthToken() {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch (_) {
    return null;
  }
}

export function setAuthToken(token) {
  try {
    if (token) {
      localStorage.setItem(TOKEN_KEY, token);
    } else {
      localStorage.removeItem(TOKEN_KEY);
    }
  } catch (_) {}
}

export function clearAuthToken() {
  setAuthToken(null);
}

/**
 * Internal fetch wrapper with timeout and connection error handling
 */
async function apiFetch(url, options = {}, timeoutMs = DEFAULT_TIMEOUT_MS) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const token = getAuthToken();
  const headers = {
    ...(options.headers || {}),
  };
  if (token && !headers["Authorization"] && !headers["authorization"]) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  try {
    const res = await fetch(url, {
      ...options,
      headers,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (!res.ok) {
      let detail = `Server responded with ${res.status}: ${res.statusText}`;
      try {
        const body = await res.json();
        detail = body.detail || detail;
      } catch (_) {
        // non-JSON error
      }
      throw new ApiError(detail, res.status);
    }

    // Handle 204 No Content
    if (res.status === 204) {
      return null;
    }

    return await res.json();
  } catch (err) {
    clearTimeout(timeoutId);

    if (err.name === "AbortError") {
      throw new ApiError(
        `Request to ${API_BASE} timed out after ${timeoutMs / 1000}s. Please check if the server is responsive.`,
        408
      );
    }

    if (err instanceof ApiError) {
      throw err;
    }

    // Network error / connection refused
    throw new ApiError(
      `Cannot connect to AgriMind API at ${API_BASE}. Please ensure the FastAPI backend is running (e.g. uvicorn app.main:app --port 8000) or explore using Demo Mode.`,
      0
    );
  }
}

/**
 * Checks backend health at /api/health (with 35s timeout for cloud cold starts)
 */
export async function checkBackendHealth() {
  try {
    const data = await apiFetch(`${API_BASE}/api/health`, { method: "GET" }, 35000);
    return { ok: true, data };
  } catch (err) {
    // Retry once in case of cold-start wake-up
    try {
      const retryData = await apiFetch(`${API_BASE}/api/health`, { method: "GET" }, 25000);
      return { ok: true, data: retryData };
    } catch (_) {
      return { ok: false, error: err.message };
    }
  }
}

/**
 * Retrieves system info and capabilities at /api/info
 */
export async function getApiInfo() {
  return apiFetch(`${API_BASE}/api/info`, { method: "GET" }, 15000);
}

/**
 * Parse a soil report PDF into structured measurements (/api/soil/parse)
 */
export async function parseSoilReport(file) {
  const formData = new FormData();
  formData.append("file", file);
  return apiFetch(`${API_BASE}/api/soil/parse`, {
    method: "POST",
    body: formData,
  });
}

/**
 * Upload a soil report PDF for text extraction and parsing (alias)
 */
export async function uploadSoilReport(file) {
  return parseSoilReport(file);
}

/**
 * Request recommendation from multi-agent orchestrator
 */
export async function getRecommendation(payload) {
  try {
    return await apiFetch(`${API_BASE}/api/recommendations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch (err) {
    if (err.status === 404) {
      // Fallback to singular alias if server uses older route
      return await apiFetch(`${API_BASE}/api/recommendation`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    }
    throw err;
  }
}

const INDIAN_COORDS = {
  pune: [18.5204, 73.8567, "Pune, Maharashtra, India"],
  mumbai: [19.0760, 72.8777, "Mumbai, Maharashtra, India"],
  nagpur: [21.1458, 79.0882, "Nagpur, Maharashtra, India"],
  nashik: [19.9975, 73.7898, "Nashik, Maharashtra, India"],
  kolhapur: [16.7050, 74.2433, "Kolhapur, Maharashtra, India"],
  solapur: [17.6599, 75.9064, "Solapur, Maharashtra, India"],
  amravati: [20.9374, 77.7796, "Amravati, Maharashtra, India"],
  aurangabad: [19.8762, 75.3433, "Chhatrapati Sambhajinagar, Maharashtra, India"],
  "chhatrapati sambhajinagar": [19.8762, 75.3433, "Chhatrapati Sambhajinagar, Maharashtra, India"],
  baramati: [18.1517, 74.5770, "Baramati, Maharashtra, India"],
  satara: [17.6805, 73.9922, "Satara, Maharashtra, India"],
  sangli: [16.8524, 74.5815, "Sangli, Maharashtra, India"],
  jalgaon: [21.0077, 75.5626, "Jalgaon, Maharashtra, India"],
  nanded: [19.1383, 77.3210, "Nanded, Maharashtra, India"],
  ahilyanagar: [19.0948, 74.7480, "Ahilyanagar, Maharashtra, India"],
  ahmednagar: [19.0948, 74.7480, "Ahilyanagar, Maharashtra, India"],
  ludhiana: [30.9010, 75.8573, "Ludhiana, Punjab, India"],
  delhi: [28.6139, 77.2090, "Delhi, India"],
  bengaluru: [12.9716, 77.5946, "Bengaluru, Karnataka, India"],
  hyderabad: [17.3850, 78.4867, "Hyderabad, Telangana, India"],
};

const WMO_MAP = {
  0: "Clear sky",
  1: "Mainly clear",
  2: "Partly cloudy",
  3: "Overcast",
  45: "Foggy",
  48: "Depositing rime fog",
  51: "Light drizzle",
  53: "Moderate drizzle",
  55: "Dense drizzle",
  61: "Slight rain",
  63: "Moderate rain",
  65: "Heavy rain",
  71: "Slight snow",
  73: "Moderate snow",
  75: "Heavy snow",
  80: "Slight rain showers",
  81: "Moderate rain showers",
  82: "Violent rain showers",
  95: "Thunderstorm",
  96: "Thunderstorm with slight hail",
  99: "Thunderstorm with heavy hail",
};

async function fetchClientDirectWeather(params = {}) {
  let lat = params.latitude;
  let lon = params.longitude;
  let locName = params.location_name || "Pune, Maharashtra, India";

  if (lat == null || lon == null) {
    const clean = (locName || "").toLowerCase().replace(/,\s*india/i, "").replace(/,\s*maharashtra/i, "").trim();
    if (INDIAN_COORDS[clean]) {
      [lat, lon, locName] = INDIAN_COORDS[clean];
    } else {
      try {
        const geoUrl = `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(locName)}&count=1&language=en&format=json`;
        const geoRes = await fetch(geoUrl);
        if (geoRes.ok) {
          const geoData = await geoRes.json();
          if (geoData.results && geoData.results.length > 0) {
            const top = geoData.results[0];
            lat = top.latitude;
            lon = top.longitude;
            locName = [top.name, top.admin1, top.country].filter(Boolean).join(", ");
          }
        }
      } catch (_) {}
    }
  }

  if (lat == null || lon == null) {
    lat = 18.5204;
    lon = 73.8567;
  }

  const daysCount = params.days || 5;
  const forecastUrl = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m&daily=precipitation_sum,precipitation_probability_max,temperature_2m_max,temperature_2m_min,windspeed_10m_max,relative_humidity_2m_max,weathercode&forecast_days=${daysCount}&timezone=auto`;

  const resp = await fetch(forecastUrl);
  if (!resp.ok) {
    throw new Error(`Weather provider responded with status ${resp.status}`);
  }

  const data = await resp.json();
  const current = data.current || {};
  const daily = data.daily || {};
  const currentTemp = current.temperature_2m != null ? Math.round(current.temperature_2m * 10) / 10 : null;
  const currentCond = WMO_MAP[current.weather_code] || "Clear sky";
  const currentWind = current.wind_speed_10m != null ? Math.round(current.wind_speed_10m * 10) / 10 : 0;
  const currentHum = current.relative_humidity_2m != null ? Math.round(current.relative_humidity_2m) : 50;

  const dates = daily.time || [];
  const pSum = daily.precipitation_sum || [];
  const pProb = daily.precipitation_probability_max || [];
  const tMax = daily.temperature_2m_max || [];
  const tMin = daily.temperature_2m_min || [];
  const wMax = daily.windspeed_10m_max || [];
  const wCode = daily.weathercode || [];

  const days = dates.map((d, i) => ({
    date: d,
    temp_max_c: tMax[i] != null ? Math.round(tMax[i] * 10) / 10 : 30,
    temp_min_c: tMin[i] != null ? Math.round(tMin[i] * 10) / 10 : 20,
    precipitation_mm: pSum[i] != null ? Math.round(pSum[i] * 10) / 10 : 0,
    precipitation_probability_pct: pProb[i] != null ? Math.round(pProb[i]) : 0,
    wind_max_kmh: wMax[i] != null ? Math.round(wMax[i] * 10) / 10 : 10,
    weather_code: wCode[i] || 0,
    condition: WMO_MAP[wCode[i]] || "Mainly clear",
    is_safe: (pSum[i] || 0) < 8 && (pProb[i] || 0) < 50 && (wMax[i] || 0) < 30 && (tMax[i] || 0) < 40,
  }));

  const today = days[0] || {};
  let applyToday = "GO";
  let recReason = `Optimal window today: calm winds (${today.wind_max_kmh || 10} km/h), minimal rainfall (${today.precipitation_mm || 0}mm, ${today.precipitation_probability_pct || 0}%), moderate temperature (${today.temp_max_c || 30}°C). Safe for foliar spray and fertilizer topdressing.`;

  if ((today.precipitation_mm || 0) >= 20 || (today.precipitation_probability_pct || 0) >= 70 || ((today.precipitation_mm || 0) >= 8 && (today.precipitation_probability_pct || 0) >= 50)) {
    applyToday = "WAIT";
    recReason = `Rain expected today (${today.precipitation_mm || 0}mm, ${today.precipitation_probability_pct || 0}% chance). Risk of nutrient runoff and leaching. Postpone application until field dries.`;
  } else if ((today.wind_max_kmh || 0) >= 30) {
    applyToday = "WAIT";
    recReason = `High winds predicted today (${today.wind_max_kmh} km/h). Postpone spray to prevent drift.`;
  } else if ((today.temp_max_c || 0) >= 40) {
    applyToday = "WAIT";
    recReason = `Extreme heat today (${today.temp_max_c}°C). Postpone to cooler hours to avoid leaf scorch.`;
  }

  const appWindow = {
    recommendation: "YES",
    apply_today: applyToday,
    reason: recReason,
    location_name: locName,
    latitude: lat,
    longitude: lon,
    fetched_at: new Date().toISOString(),
    current_temperature_c: currentTemp,
    current_condition: currentCond,
    forecast_days: days,
    forecast_summary: today,
    is_available: true,
  };

  return {
    location_name: locName,
    latitude: lat,
    longitude: lon,
    current_temperature_c: currentTemp,
    current_condition: currentCond,
    current_humidity: currentHum,
    current_wind_kmh: currentWind,
    days: days,
    generated_at: new Date().toISOString(),
    application_window: appWindow,
  };
}

/**
 * Fetch live weather forecast with automatic client-side fallback if backend encounters cloud IP rate limiting
 */
export async function getWeatherForecast(params = {}) {
  const query = new URLSearchParams();
  if (params.latitude != null) query.append("latitude", params.latitude);
  if (params.longitude != null) query.append("longitude", params.longitude);
  if (params.location_name) query.append("location_name", params.location_name);
  if (params.days != null) query.append("days", params.days);

  try {
    return await apiFetch(`${API_BASE}/api/weather/forecast?${query.toString()}`, {
      method: "GET",
    });
  } catch (backendErr) {
    // Fall back to direct browser fetch (bypasses Render shared cloud IP rate limiting)
    return await fetchClientDirectWeather(params);
  }
}

/**
 * Send interactive follow-up question to AgriMind chat
 */
export async function sendChatMessage(
  message,
  soil,
  selectedCrop,
  language = "en",
  location = null,
  applicationWindow = null
) {
  return apiFetch(
    `${API_BASE}/api/chat`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        soil,
        selected_crop: selectedCrop,
        location,
        application_window: applicationWindow,
        language,
      }),
    },
    60000
  );
}

/**
 * Authentication Endpoints
 */
export async function registerUser(userData) {
  return apiFetch(`${API_BASE}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(userData),
  });
}

export async function loginUser(credentials) {
  return apiFetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(credentials),
  });
}

export async function getCurrentUser() {
  return apiFetch(`${API_BASE}/api/auth/me`, {
    method: "GET",
  });
}

/**
 * Saved Reports Endpoints
 */
export async function saveReport(reportPayload) {
  return apiFetch(`${API_BASE}/api/reports`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(reportPayload),
  });
}

export async function getSavedReports() {
  return apiFetch(`${API_BASE}/api/reports`, {
    method: "GET",
  });
}

export async function getSavedReport(reportId) {
  return apiFetch(`${API_BASE}/api/reports/${reportId}`, {
    method: "GET",
  });
}

export async function deleteSavedReport(reportId) {
  return apiFetch(`${API_BASE}/api/reports/${reportId}`, {
    method: "DELETE",
  });
}

export { API_BASE, ApiError };
