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

const DEFAULT_TIMEOUT_MS = 15000;

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
 * Checks backend health at /api/health
 */
export async function checkBackendHealth() {
  try {
    const data = await apiFetch(`${API_BASE}/api/health`, { method: "GET" }, 4000);
    return { ok: true, data };
  } catch (err) {
    return { ok: false, error: err.message };
  }
}

/**
 * Retrieves system info and capabilities at /api/info
 */
export async function getApiInfo() {
  return apiFetch(`${API_BASE}/api/info`, { method: "GET" }, 5000);
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

/**
 * Fetch live weather forecast and geocoding from /api/weather/forecast
 */
export async function getWeatherForecast(params = {}) {
  const query = new URLSearchParams();
  if (params.latitude != null) query.append("latitude", params.latitude);
  if (params.longitude != null) query.append("longitude", params.longitude);
  if (params.location_name) query.append("location_name", params.location_name);
  if (params.days != null) query.append("days", params.days);
  return apiFetch(`${API_BASE}/api/weather/forecast?${query.toString()}`, {
    method: "GET",
  });
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
    30000
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
