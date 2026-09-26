import api from "./client";

const get = (url, params) => api.get(url, { params }).then((r) => r.data);
const post = (url, body) => api.post(url, body).then((r) => r.data);
const put = (url, body) => api.put(url, body).then((r) => r.data);

export const authApi = {
  signup: (body) => post("/auth/signup", body),
  login: (body) => post("/auth/login", body),
  forgotPassword: (email) => post("/auth/forgot-password", { email }),
  resetPassword: (body) => post("/auth/reset-password", body),
  me: () => get("/auth/me"),
};

export const masterApi = {
  categories: () => get("/categories"),
  uoms: () => get("/uoms"),
  warehouses: () => get("/warehouses"),
  createWarehouse: (body) => post("/warehouses", body),
  locations: (params) => get("/locations", params),
  createLocation: (body) => post("/locations", body),
  partners: (type) => get("/partners", type ? { type } : undefined),
  reorderRules: () => get("/reorder-rules"),
  saveReorderRule: (body) => put("/reorder-rules", body),
};

export const productApi = {
  list: (params) => get("/products", params),
  create: (body) => post("/products", body),
  update: (id, body) => put(`/products/${id}`, body),
  stock: (id) => get(`/products/${id}/stock`),
};

export const operationApi = {
  list: (params) => get("/operations", params),
  get: (id) => get(`/operations/${id}`),
  create: (body) => post("/operations", body),
  confirm: (id) => post(`/operations/${id}/confirm`),
  validate: (id) => post(`/operations/${id}/validate`),
  cancel: (id) => post(`/operations/${id}/cancel`),
  moves: (params) => get("/moves", params),
};

export const dashboardApi = {
  kpis: (params) => get("/dashboard/kpis", params),
  lowStock: (params) => get("/dashboard/low-stock", params),
};

// Drop empty filter values so they aren't sent as ?x=
export const clean = (obj) =>
  Object.fromEntries(Object.entries(obj).filter(([, v]) => v !== "" && v !== null && v !== undefined));
