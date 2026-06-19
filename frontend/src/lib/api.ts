// Leer = same-origin; Next.js leitet /api/* an das Backend weiter (Docker/Prod).
// Optional NEXT_PUBLIC_API_URL nur für lokales Dev ohne Proxy.
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

type FetchOptions = RequestInit & { json?: unknown };

async function apiFetch<T>(path: string, options: FetchOptions = {}): Promise<T> {
  const { json, headers, ...rest } = options;
  const res = await fetch(`${API_URL}${path}`, {
    ...rest,
    credentials: "include",
    headers: {
      ...(json ? { "Content-Type": "application/json" } : {}),
      ...headers,
    },
    body: json ? JSON.stringify(json) : rest.body,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? `API ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export type HealthResponse = { status: string; tenant: string };
export type User = { id: string; is_admin: boolean; totp_enabled: boolean };
export type LoginResponse = { requires_2fa: boolean; user?: User };
export type Project = {
  id: string;
  name: string;
  description: string | null;
  classification: number;
  version: number;
  locked_by_id: string | null;
  locked_until: string | null;
  created_at: string;
  updated_at: string;
};
export type Task = {
  id: string;
  project_id: string;
  title: string;
  body: string | null;
  status: string;
  classification: number;
  version: number;
  locked_by_id: string | null;
  locked_until: string | null;
  created_at: string;
  updated_at: string;
};
export type Member = { id: string; user_id: string; role: string; created_at: string };

export const fetchHealth = () => apiFetch<HealthResponse>("/api/v1/health");
export const fetchMe = () => apiFetch<User>("/api/v1/auth/me");
export const login = (email: string, password: string) =>
  apiFetch<LoginResponse>("/api/v1/auth/login", { method: "POST", json: { email, password } });
export const verify2fa = (totp_code?: string, recovery_code?: string) =>
  apiFetch<LoginResponse>("/api/v1/auth/2fa/verify", {
    method: "POST",
    json: { totp_code, recovery_code },
  });
export const logout = () => apiFetch<void>("/api/v1/auth/logout", { method: "POST" });
export const fetchProjects = () => apiFetch<Project[]>("/api/v1/projects");
export const fetchProject = (id: string) => apiFetch<Project>(`/api/v1/projects/${id}`);
export const createProject = (name: string, description?: string) =>
  apiFetch<Project>("/api/v1/projects", { method: "POST", json: { name, description } });
export const fetchTasks = (projectId: string) =>
  apiFetch<Task[]>(`/api/v1/projects/${projectId}/tasks`);
export const createTask = (projectId: string, title: string, body?: string) =>
  apiFetch<Task>(`/api/v1/projects/${projectId}/tasks`, {
    method: "POST",
    json: { title, body },
  });
export const lockTask = (projectId: string, taskId: string) =>
  apiFetch<Task>(`/api/v1/projects/${projectId}/tasks/${taskId}/lock`, { method: "POST" });
export const updateTask = (
  projectId: string,
  taskId: string,
  data: { title?: string; body?: string; status?: string; version: number }
) =>
  apiFetch<Task>(`/api/v1/projects/${projectId}/tasks/${taskId}`, {
    method: "PATCH",
    json: data,
  });
export const unlockTask = (projectId: string, taskId: string) =>
  apiFetch<Task>(`/api/v1/projects/${projectId}/tasks/${taskId}/lock`, { method: "DELETE" });
