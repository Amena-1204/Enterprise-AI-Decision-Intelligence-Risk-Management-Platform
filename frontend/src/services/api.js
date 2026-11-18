import axios from "axios";

const api = axios.create({ baseURL: "/api" });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export const auth = {
  login:    (email, password) => api.post("/auth/login", { email, password }),
  register: (data)            => api.post("/auth/register", data),
};

export const customers = {
  list:            (limit = 100, offset = 0) => api.get(`/customers?limit=${limit}&offset=${offset}`),
  get:             (id)                      => api.get(`/customers/${id}`),
  create:          (data)                    => api.post("/customers", data),
  update:          (id, data)                => api.put(`/customers/${id}`, data),
  delete:          (id)                      => api.delete(`/customers/${id}`),
  transactions:    (id, limit = 50)          => api.get(`/customers/${id}/transactions?limit=${limit}`),
};

export const dashboard = {
  summary: () => api.get("/dashboard/summary"),
};

export const predictions = {
  churnList:    ()     => api.get("/predictions/churn"),
  predictChurn: (data) => api.post("/predictions/churn", data),
  fraudList:    ()     => api.get("/predictions/fraud"),
  predictFraud: (data) => api.post("/predictions/fraud", data),
  salesList:    ()     => api.get("/predictions/sales"),
  predictSales: (data) => api.post("/predictions/sales", data),
};

export const fraud = {
  overview: () => api.get("/fraud"),
  regional: () => api.get("/fraud/regional"),
};

export const churn = {
  overview: () => api.get("/churn"),
  atRisk:   () => api.get("/churn/at-risk"),
};

export const sales = {
  list:    (region) => api.get(`/sales${region ? `?region=${region}` : ""}`),
  summary: ()       => api.get("/sales/summary"),
};

export const segments = {
  list:    ()     => api.get("/segments"),
  summary: ()     => api.get("/segments/summary"),
  predict: (data) => api.post("/segments/predict", data),
};

export const ai = {
  ask:            (query, features = {}) => api.post("/ai/ask", { query, features }),
  report:         (report_type)          => api.post("/ai/report", { report_type }),
  indexDocuments: ()                     => api.post("/ai/index-documents"),
};

export default api;
