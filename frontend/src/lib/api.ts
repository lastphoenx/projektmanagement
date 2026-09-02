// Leer = same-origin; Next.js leitet /api/* an das Backend weiter (Docker/Prod).
// Optional NEXT_PUBLIC_API_URL nur für lokales Dev ohne Proxy.
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

type FetchOptions = RequestInit & { json?: unknown };

function formatApiError(detail: unknown, fallback: string): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object" && "msg" in item) {
          return String((item as { msg: unknown }).msg);
        }
        return JSON.stringify(item);
      })
      .join(", ");
  }
  if (detail && typeof detail === "object" && "message" in detail) {
    return String((detail as { message: unknown }).message);
  }
  return fallback;
}

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
    throw new Error(formatApiError(err.detail, `API ${res.status}`));
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export type HealthResponse = { status: string; tenant: string };
export type User = { id: string; is_admin: boolean; totp_enabled: boolean };
export type LoginResponse = { requires_2fa: boolean; user?: User };
export type Project = {
  id: string;
  key: string;
  project_type: string;
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

export type PlanningArtifact = {
  slug: string;
  status: string;
  content: string;
  version: number;
  generated_at: string | null;
  has_content: boolean;
};

export type PlanningCompletionStep = {
  key: string;
  label: string;
  filled: boolean;
  status: string;
};

export type PlanningCompletion = {
  has_project_idea: boolean;
  filled_count: number;
  total_count: number;
  artifact_filled: number;
  artifact_total: number;
  approved_count: number;
  is_complete: boolean;
  is_fully_approved: boolean;
  missing_labels: string[];
  steps: PlanningCompletionStep[];
};

export type PlanningState = {
  project_key: string;
  revision: number;
  project_idea: string;
  budget_basis: Record<string, unknown>;
  artifacts: PlanningArtifact[];
  completion: PlanningCompletion;
};

export type PspAnalysis = {
  total_pt: number;
  personal_chf: number;
  sachkosten_chf: number;
  reserve_chf: number;
  estimated_total_chf: number;
  role_lines: { role: string; pt: number; rate_chf: number; total_chf: number }[];
  work_package_count: number;
  status: string;
  budget_ceiling_chf?: number | null;
  deviation_chf?: number;
  deviation_pct?: number;
  fits_ceiling?: boolean;
};

export type AdminLlmProvider = {
  id: string;
  label: string;
  is_local: boolean;
  configured: boolean;
  base_url: string | null;
  models: string[];
};

export type AdminLlmState = {
  providers: AdminLlmProvider[];
  active: {
    provider: string;
    model: string;
    base_url: string | null;
    source: string;
  };
};

export type SecurityCatalogEntry = {
  level: number;
  name: string;
  label: string;
  retention_days: number | null;
  gdpr_relevant: boolean;
  exportable: boolean;
  erasure_strategy: string;
  requires_master_key: boolean;
  requires_user_key: boolean;
  requires_anonymization_before_external_llm: boolean;
  never_leaves_infrastructure: boolean;
};

export type SecurityCatalogState = {
  classification_catalog: SecurityCatalogEntry[];
  table_defaults: {
    model: string;
    table: string;
    default_classification: string;
    policy_source: string;
  }[];
  field_registry_overrides: {
    model: string;
    field: string;
    classification: string;
    table_default: string;
    is_override: boolean;
    gdpr_personal: boolean;
  }[];
  planning_step_fields: {
    step_number: number | null;
    label: string;
    slug: string | null;
    model: string;
    field: string;
    table: string;
    table_default: string;
    effective_classification: string;
    has_field_override: boolean;
    note?: string;
  }[];
  catalog_version: string;
  concept: {
    level_1: string;
    level_2: string;
    level_3: string;
  };
};

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
export const fetchProjectByKey = (key: string) =>
  apiFetch<Project>(`/api/v1/projects/by-key/${encodeURIComponent(key)}`);
export const createProject = (data: {
  key: string;
  name: string;
  project_type: string;
  description?: string;
}) =>
  apiFetch<Project>("/api/v1/projects", {
    method: "POST",
    json: data,
  });
export const deleteProject = (id: string) =>
  apiFetch<void>(`/api/v1/projects/${id}`, { method: "DELETE" });
export const updateProject = (
  id: string,
  data: { name?: string; description?: string | null; version: number }
) =>
  apiFetch<Project>(`/api/v1/projects/${id}`, {
    method: "PATCH",
    json: data,
  });
export const fetchPlanning = (projectKey: string) =>
  apiFetch<PlanningState>(
    `/api/v1/projects/by-key/${encodeURIComponent(projectKey)}/planning`
  );
export const saveProjectIdea = (projectKey: string, idea: string, expectedRevision: number) =>
  apiFetch<PlanningState>(
    `/api/v1/projects/by-key/${encodeURIComponent(projectKey)}/planning/idea`,
    { method: "PUT", json: { idea, expected_revision: expectedRevision } }
  );
export const savePlanningArtifact = (
  projectKey: string,
  slug: string,
  content: string,
  expectedVersion: number
) =>
  apiFetch<PlanningState>(
    `/api/v1/projects/by-key/${encodeURIComponent(projectKey)}/planning/artifacts/${slug}`,
    { method: "PUT", json: { content, expected_version: expectedVersion } }
  );
export const setPlanningArtifactStatus = (
  projectKey: string,
  slug: string,
  status: "pending" | "draft" | "approved"
) =>
  apiFetch<PlanningState>(
    `/api/v1/projects/by-key/${encodeURIComponent(projectKey)}/planning/artifacts/${slug}/status`,
    { method: "PATCH", json: { status } }
  );
export const generateProjectIdea = (
  projectKey: string,
  expectedRevision: number,
  seed?: string
) =>
  apiFetch<PlanningState>(
    `/api/v1/projects/by-key/${encodeURIComponent(projectKey)}/planning/generate/idea`,
    { method: "POST", json: { expected_revision: expectedRevision, seed } }
  );
export const generatePlanningArtifact = (
  projectKey: string,
  slug: string,
  expectedRevision: number
) =>
  apiFetch<PlanningState>(
    `/api/v1/projects/by-key/${encodeURIComponent(projectKey)}/planning/generate/artifacts/${slug}`,
    { method: "POST", json: { expected_revision: expectedRevision } }
  );
export const generateJiraCsvFromPsp = (projectKey: string, expectedRevision: number) =>
  apiFetch<PlanningState>(
    `/api/v1/projects/by-key/${encodeURIComponent(projectKey)}/planning/generate/jira-csv`,
    { method: "POST", json: { expected_revision: expectedRevision } }
  );
export const generateBudgetPlanFromPsp = (projectKey: string, expectedRevision: number) =>
  apiFetch<PlanningState>(
    `/api/v1/projects/by-key/${encodeURIComponent(projectKey)}/planning/generate/budget-plan`,
    { method: "POST", json: { expected_revision: expectedRevision } }
  );
export const fetchPspAnalysis = (projectKey: string) =>
  apiFetch<PspAnalysis>(
    `/api/v1/projects/by-key/${encodeURIComponent(projectKey)}/planning/psp-analysis`
  );
export const updateBudgetBasis = (
  projectKey: string,
  data: { budget_ceiling_chf: number | null; notes: string; expected_revision: number }
) =>
  apiFetch<{ analysis: PspAnalysis; planning: PlanningState }>(
    `/api/v1/projects/by-key/${encodeURIComponent(projectKey)}/planning/budget-basis`,
    { method: "PUT", json: data }
  );
export const confirmBudgetBasis = (projectKey: string, expectedRevision: number) =>
  apiFetch<PlanningState>(
    `/api/v1/projects/by-key/${encodeURIComponent(projectKey)}/planning/budget-basis/confirm`,
    { method: "POST", json: { expected_revision: expectedRevision } }
  );
export const fetchAdminLlm = () => apiFetch<AdminLlmState>("/api/v1/admin/llm");
export const saveAdminLlm = (data: {
  provider: string;
  model: string;
  base_url?: string;
  api_key?: string;
}) => apiFetch<AdminLlmState>("/api/v1/admin/llm", { method: "PUT", json: data });
export const testAdminLlm = (data: { provider: string; model: string; base_url?: string }) =>
  apiFetch<{ ok: boolean; message: string }>("/api/v1/admin/llm/test", {
    method: "POST",
    json: data,
  });
export const fetchAdminSecurityCatalog = () =>
  apiFetch<SecurityCatalogState>("/api/v1/admin/security/catalog");
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

export type {
  PortfolioEligibleProject,
  PortfolioFormData,
  PortfolioMatrixPoint,
  PortfolioProject,
  PortfolioWsjfItem,
} from "@/lib/portfolio-types";

export const fetchPortfolioProjects = () =>
  apiFetch<import("@/lib/portfolio-types").PortfolioProject[]>("/api/v1/portfolio/projects");

export const fetchPortfolioEligibleProjects = () =>
  apiFetch<import("@/lib/portfolio-types").PortfolioEligibleProject[]>(
    "/api/v1/portfolio/eligible-projects"
  );

export const fetchPortfolioMatrix = () =>
  apiFetch<import("@/lib/portfolio-types").PortfolioMatrixPoint[]>(
    "/api/v1/portfolio/matrix-data"
  );

export const fetchPortfolioWsjf = () =>
  apiFetch<import("@/lib/portfolio-types").PortfolioWsjfItem[]>(
    "/api/v1/portfolio/wsjf-ranking"
  );

export const fetchPortfolioProject = (id: string) =>
  apiFetch<import("@/lib/portfolio-types").PortfolioProject>(
    `/api/v1/portfolio/projects/${id}`
  );

export const createPortfolioProject = (data: import("@/lib/portfolio-types").PortfolioFormData & { project_key: string }) =>
  apiFetch<import("@/lib/portfolio-types").PortfolioProject>("/api/v1/portfolio/projects", {
    method: "POST",
    json: data,
  });

export const updatePortfolioProject = (
  id: string,
  data: Partial<import("@/lib/portfolio-types").PortfolioFormData>
) =>
  apiFetch<import("@/lib/portfolio-types").PortfolioProject>(
    `/api/v1/portfolio/projects/${id}`,
    { method: "PUT", json: data }
  );

export const deletePortfolioProject = (id: string) =>
  apiFetch<void>(`/api/v1/portfolio/projects/${id}`, { method: "DELETE" });

export function planningExportDocxUrl(projectKey: string): string {
  return `/api/v1/projects/by-key/${encodeURIComponent(projectKey)}/planning/export-docx`;
}

export function planningArtifactExportDocxUrl(projectKey: string, slug: string): string {
  return `/api/v1/projects/by-key/${encodeURIComponent(projectKey)}/planning/artifacts/${encodeURIComponent(slug)}/export-docx`;
}

export type PiiFinding = { entity_type: string; text: string; score: number };

export const analyzePlanningPii = (projectKey: string, text: string) =>
  apiFetch<{ findings_count: number; findings: PiiFinding[] }>(
    `/api/v1/projects/by-key/${encodeURIComponent(projectKey)}/planning/pii-analyze`,
    { method: "POST", json: { text } }
  );

export type PrivacyUserSummary = {
  id: string;
  is_active: boolean;
  is_admin: boolean;
  totp_enabled: boolean;
  created_at: string;
};

export const fetchAdminPrivacyUsers = () =>
  apiFetch<PrivacyUserSummary[]>("/api/v1/admin/privacy/users");

export function adminPrivacyExportUrl(userId: string): string {
  return `/api/v1/admin/privacy/users/${userId}/export`;
}

export const adminPrivacyErase = (userId: string) =>
  apiFetch<{ erased_user_id: string; strategy: string; audit_events_pseudonymized: number }>(
    `/api/v1/admin/privacy/users/${userId}/erase`,
    { method: "POST" }
  );

export const adminPrivacyPurgeRetention = () =>
  apiFetch<{ purged: { sessions: number; audit_log: number } }>(
    "/api/v1/admin/privacy/retention/purge",
    { method: "POST" }
  );
