from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12)
    display_name: str = Field(default="", max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TwoFactorVerifyRequest(BaseModel):
    totp_code: str | None = None
    recovery_code: str | None = None


class TwoFactorConfirmRequest(BaseModel):
    code: str = Field(min_length=6, max_length=8)
    email: EmailStr


class TwoFactorSetupResponse(BaseModel):
    provisioning_uri: str
    secret: str


class UserResponse(BaseModel):
    id: str
    is_admin: bool
    totp_enabled: bool


class LoginResponse(BaseModel):
    requires_2fa: bool = False
    user: UserResponse | None = None


class ProjectCreateRequest(BaseModel):
    key: str = Field(min_length=2, max_length=8, pattern=r"^[A-Za-z][A-Za-z0-9]{1,7}$")
    name: str = Field(min_length=1, max_length=256)
    project_type: str = Field(default="other")
    description: str | None = Field(default=None, max_length=4096)
    classification: int = Field(default=1, ge=0, le=3)


class ProjectUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=256)
    description: str | None = Field(default=None, max_length=4096)
    version: int = Field(ge=1)


class ProjectResponse(BaseModel):
    id: str
    key: str
    project_type: str
    name: str
    description: str | None
    classification: int
    version: int
    locked_by_id: str | None
    locked_until: str | None
    created_at: str
    updated_at: str


class TaskCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=256)
    body: str | None = Field(default=None, max_length=8192)
    status: str = Field(default="open")
    classification: int = Field(default=1, ge=0, le=3)


class TaskUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=256)
    body: str | None = Field(default=None, max_length=8192)
    status: str | None = None
    version: int = Field(ge=1)


class TaskResponse(BaseModel):
    id: str
    project_id: str
    title: str
    body: str | None
    status: str
    classification: int
    version: int
    locked_by_id: str | None
    locked_until: str | None
    created_at: str
    updated_at: str


class MemberAddRequest(BaseModel):
    user_id: str
    role: Literal["viewer", "member", "manager"] = "member"


class MemberResponse(BaseModel):
    id: str
    user_id: str
    role: str
    created_at: str


class PlanningArtifactResponse(BaseModel):
    slug: str
    status: str
    content: str
    version: int
    generated_at: str | None
    has_content: bool


class PlanningCompletionStepResponse(BaseModel):
    key: str
    label: str
    filled: bool
    status: str


class PlanningCompletionResponse(BaseModel):
    has_project_idea: bool
    filled_count: int
    total_count: int
    artifact_filled: int
    artifact_total: int
    approved_count: int
    is_complete: bool
    is_fully_approved: bool
    missing_labels: list[str]
    steps: list[PlanningCompletionStepResponse]


class PlanningStateResponse(BaseModel):
    project_key: str
    revision: int
    project_idea: str
    budget_basis: dict
    artifacts: list[PlanningArtifactResponse]
    completion: PlanningCompletionResponse


class SaveProjectIdeaRequest(BaseModel):
    idea: str = Field(default="", max_length=65536)
    expected_revision: int = Field(ge=1)


class SaveArtifactRequest(BaseModel):
    content: str = Field(default="", max_length=131072)
    expected_version: int = Field(ge=0)


class SetArtifactStatusRequest(BaseModel):
    status: Literal["pending", "draft", "approved"]


class GenerateIdeaRequest(BaseModel):
    seed: str | None = Field(default=None, max_length=8192)
    expected_revision: int = Field(ge=1)


class GenerateArtifactRequest(BaseModel):
    expected_revision: int = Field(ge=1)


class BudgetBasisUpdateRequest(BaseModel):
    budget_ceiling_chf: float | None = None
    notes: str = ""
    expected_revision: int = Field(ge=1)


class BudgetBasisConfirmRequest(BaseModel):
    expected_revision: int = Field(ge=1)
