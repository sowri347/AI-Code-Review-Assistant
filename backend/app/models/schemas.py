from enum import Enum

from pydantic import BaseModel, Field


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Category(str, Enum):
    BUG = "bug"
    SECURITY = "security"
    QUALITY = "quality"
    PERFORMANCE = "performance"
    STYLE = "style"


class PullRequestSummary(BaseModel):
    number: int
    title: str
    author: str
    state: str
    url: str
    repo: str
    additions: int
    deletions: int
    changed_files: int


class FileChange(BaseModel):
    filename: str
    status: str
    additions: int
    deletions: int
    patch: str | None = None


class ReviewFinding(BaseModel):
    id: str
    category: Category
    severity: Severity
    title: str
    description: str
    file: str | None = None
    line: int | None = None
    suggestion: str | None = None
    source: str = "ai"


class QualityMetrics(BaseModel):
    overall_score: float = Field(ge=0, le=100)
    maintainability: float = Field(ge=0, le=100)
    readability: float = Field(ge=0, le=100)
    complexity_score: float = Field(ge=0, le=100)
    test_coverage_hint: str | None = None


class ReviewReport(BaseModel):
    pr_number: int
    repo: str
    summary: str
    findings: list[ReviewFinding]
    quality: QualityMetrics
    files_analyzed: int
    lines_changed: int


class ReviewRequest(BaseModel):
    owner: str
    repo: str
    pr_number: int


class RepoSearchRequest(BaseModel):
    owner: str
    repo: str
