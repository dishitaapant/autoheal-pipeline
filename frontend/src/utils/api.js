import axios from "axios";

const BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
  headers: { "Content-Type": "application/json" },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => config,
  (error) => Promise.reject(error)
);

// Response error handler
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const msg =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      "Unknown error";
    return Promise.reject(new Error(msg));
  }
);

export const pipelineAPI = {
  list: (params = {}) => api.get("/api/pipelines/", { params }),
  get: (runId) => api.get(`/api/pipelines/${runId}`),
  getLogs: (runId) => api.get(`/api/pipelines/${runId}/logs`),
  getHealing: (runId) => api.get(`/api/pipelines/${runId}/healing`),
};

export const analyticsAPI = {
  summary: () => api.get("/api/analytics/summary"),
};

export const webhookAPI = {
  triggerTestFailure: () => api.post("/api/webhook/test-failure"),
  triggerFailure: (payload) => api.post("/api/webhook/pipeline-failure", payload),
};

export const healthAPI = {
  check: () => api.get("/api/health/"),
};

export default api;
