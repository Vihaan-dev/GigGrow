const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

async function handleResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const message = payload && payload.error ? payload.error : "request_failed";
    const error = new Error(message);
    error.status = response.status;
    error.payload = payload;
    throw error;
  }

  return payload;
}

async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  });

  return handleResponse(response);
}

export const api = {
  // Core state
  getState: (userId) => apiRequest(`/api/state/${userId}`),
  getSummary: (userId, days = 30) => apiRequest(`/api/summary/${userId}?days=${days}`),
  getEarnings: (userId, days = 30) => apiRequest(`/api/earnings/${userId}?days=${days}`),
  getSpending: (userId, days = 30) => apiRequest(`/api/spending/${userId}?days=${days}`),
  getEvents: (userId, days = 30) => apiRequest(`/api/events/${userId}?days=${days}`),

  // Intelligence layer
  getInsights: (userId, days = 30) => apiRequest(`/api/insights/${userId}?days=${days}`),
  getTimeline: (userId, days = 30, forecast = 14, scenario = "baseline") =>
    apiRequest(`/api/timeline/${userId}?days=${days}&forecast=${forecast}&scenario=${scenario}`),
  getForecast: (userId, days = 30, scenario = "baseline") =>
    apiRequest(`/api/forecast/${userId}?days=${days}&scenario=${scenario}`),
  getNudges: (userId, language) =>
    apiRequest(`/api/nudges/${userId}${language ? `?language=${language}` : ""}`),
  getCrisis: (userId) => apiRequest(`/api/crisis/${userId}`),

  // Mutations + flows
  createUser: (payload) => apiRequest("/api/users", {
    method: "POST",
    body: JSON.stringify(payload)
  }),
  logEarning: (payload) => apiRequest("/api/earnings/log", {
    method: "POST",
    body: JSON.stringify(payload)
  }),
  logSpending: (payload) => apiRequest("/api/spending/log", {
    method: "POST",
    body: JSON.stringify(payload)
  }),
  parseSms: (payload) => apiRequest("/api/spending/parse-sms", {
    method: "POST",
    body: JSON.stringify(payload)
  }),
  ingestEvents: (payload) => apiRequest("/api/events/ingest", {
    method: "POST",
    body: JSON.stringify(payload)
  }),
  matchSchemes: (payload) => apiRequest("/api/schemes/match", {
    method: "POST",
    body: JSON.stringify(payload)
  }),
  matchLoans: (payload) => apiRequest("/api/loans/match", {
    method: "POST",
    body: JSON.stringify(payload)
  }),
  chat: (payload) => apiRequest("/api/chat", {
    method: "POST",
    body: JSON.stringify(payload)
  }),
  simulatePurchase: (payload) => apiRequest("/api/purchase/simulate", {
    method: "POST",
    body: JSON.stringify(payload)
  })
};
