import json
import uuid

from openai import OpenAI

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

from app.config import settings
from app.models.schemas import Category, FileChange, ReviewFinding, Severity


SYSTEM_PROMPT = """You are an expert code reviewer. Analyze pull request diffs and identify:
1. Bugs and logic errors
2. Security vulnerabilities
3. Code quality issues
4. Performance concerns
5. Style and best-practice violations

Respond ONLY with valid JSON in this exact format:
{
  "summary": "Brief overall assessment (2-3 sentences)",
  "findings": [
    {
      "category": "bug|security|quality|performance|style",
      "severity": "critical|high|medium|low|info",
      "title": "Short issue title",
      "description": "Detailed explanation",
      "file": "path/to/file.py or null",
      "line": 42 or null,
      "suggestion": "Concrete fix recommendation"
    }
  ]
}

Be specific, actionable, and prioritize real issues over nitpicks. Limit to the 10 most important findings."""


def _build_user_prompt(owner: str, repo: str, pr_number: int, files: list[FileChange]) -> str:
    parts = [f"Review PR #{pr_number} in {owner}/{repo}.\n"]

    for f in files:
        if f.patch:
            parts.append(f"\n--- {f.filename} ({f.status}, +{f.additions}/-{f.deletions}) ---")
            parts.append(f.patch[:8000])

    return "\n".join(parts)


def _parse_findings(raw: list[dict]) -> list[ReviewFinding]:
    findings: list[ReviewFinding] = []
    severity_map = {s.value: s for s in Severity}
    category_map = {c.value: c for c in Category}

    for item in raw:
        try:
            findings.append(
                ReviewFinding(
                    id=str(uuid.uuid4())[:8],
                    category=category_map.get(item.get("category", "quality"), Category.QUALITY),
                    severity=severity_map.get(item.get("severity", "medium"), Severity.MEDIUM),
                    title=item.get("title", "Issue found"),
                    description=item.get("description", ""),
                    file=item.get("file"),
                    line=item.get("line"),
                    suggestion=item.get("suggestion"),
                    source="ai",
                )
            )
        except Exception:
            continue

    return findings


class AIAnalyzer:
    def __init__(self) -> None:
        self._client: OpenAI | None = None
        self._gemini_client = None

    @property
    def client(self) -> OpenAI:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not configured")
        if self._client is None:
            self._client = OpenAI(api_key=settings.openai_api_key)
        return self._client

    @property
    def gemini_client(self):
        if genai is None:
            raise ImportError("google-genai package is not installed")
        if not settings.gemini_api_key or settings.gemini_api_key == "your_gemini_api_key_here":
            raise ValueError("GEMINI_API_KEY is not configured. Please add it to your .env file.")
        if self._gemini_client is None:
            self._gemini_client = genai.Client(api_key=settings.gemini_api_key)
        return self._gemini_client

    def analyze(
        self, owner: str, repo: str, pr_number: int, files: list[FileChange]
    ) -> tuple[str, list[ReviewFinding]]:
        if not files:
            return "No file changes to analyze.", []

        prompt = _build_user_prompt(owner, repo, pr_number, files)

        if settings.ai_provider == "gemini":
            response = self.gemini_client.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    temperature=0.2,
                )
            )
            content = response.text or "{}"
        else:
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            content = response.choices[0].message.content or "{}"

        data = json.loads(content)

        summary = data.get("summary", "Analysis complete.")
        findings = _parse_findings(data.get("findings", []))
        return summary, findings


ai_analyzer = AIAnalyzer()
