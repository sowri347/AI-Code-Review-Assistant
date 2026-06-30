import re
import subprocess
import tempfile
from pathlib import Path

from app.models.schemas import Category, ReviewFinding, Severity


SECURITY_PATTERNS: list[tuple[str, str, Severity, str]] = [
    (
        r"(?i)(password|secret|api_key|apikey|token)\s*=\s*['\"][^'\"]+['\"]",
        "Hardcoded secret detected",
        Severity.CRITICAL,
        "Move secrets to environment variables or a secrets manager.",
    ),
    (
        r"(?i)eval\s*\(",
        "Use of eval()",
        Severity.HIGH,
        "Avoid eval(); use safer alternatives like ast.literal_eval or structured parsing.",
    ),
    (
        r"(?i)exec\s*\(",
        "Use of exec()",
        Severity.HIGH,
        "Avoid exec(); refactor to explicit, auditable logic.",
    ),
    (
        r"(?i)pickle\.loads?\(",
        "Unsafe deserialization with pickle",
        Severity.HIGH,
        "Pickle can execute arbitrary code; use JSON or other safe formats.",
    ),
    (
        r"(?i)subprocess\.(call|run|Popen)\([^)]*shell\s*=\s*True",
        "Shell injection risk",
        Severity.HIGH,
        "Avoid shell=True; pass arguments as a list instead.",
    ),
    (
        r"(?i)sql\s*=.*\+.*|f['\"].*SELECT.*\{",
        "Possible SQL injection",
        Severity.HIGH,
        "Use parameterized queries or an ORM instead of string concatenation.",
    ),
    (
        r"(?i)innerHTML\s*=",
        "DOM XSS risk",
        Severity.MEDIUM,
        "Sanitize user input or use textContent / safe DOM APIs.",
    ),
    (
        r"(?i)dangerouslySetInnerHTML",
        "React XSS risk",
        Severity.MEDIUM,
        "Ensure content is sanitized before using dangerouslySetInnerHTML.",
    ),
]


def scan_content(filename: str, content: str) -> list[ReviewFinding]:
    findings: list[ReviewFinding] = []
    lines = content.splitlines()

    for pattern, title, severity, suggestion in SECURITY_PATTERNS:
        for line_no, line in enumerate(lines, start=1):
            if re.search(pattern, line):
                findings.append(
                    ReviewFinding(
                        id=f"sec-{filename}-{line_no}-{len(findings)}",
                        category=Category.SECURITY,
                        severity=severity,
                        title=title,
                        description=f"Pattern matched in `{filename}` at line {line_no}.",
                        file=filename,
                        line=line_no,
                        suggestion=suggestion,
                        source="static",
                    )
                )

    return findings


def scan_with_bandit(content: str, filename: str) -> list[ReviewFinding]:
    findings: list[ReviewFinding] = []
    if not filename.endswith(".py"):
        return findings

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            ["bandit", "-f", "json", "-q", tmp_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.stdout.strip():
            import json

            data = json.loads(result.stdout)
            for item in data.get("results", []):
                severity_map = {
                    "HIGH": Severity.HIGH,
                    "MEDIUM": Severity.MEDIUM,
                    "LOW": Severity.LOW,
                }
                findings.append(
                    ReviewFinding(
                        id=f"bandit-{filename}-{item.get('line_number', 0)}",
                        category=Category.SECURITY,
                        severity=severity_map.get(item.get("issue_severity", "LOW"), Severity.LOW),
                        title=item.get("issue_text", "Bandit security issue"),
                        description=item.get("issue_text", ""),
                        file=filename,
                        line=item.get("line_number"),
                        suggestion="Review Bandit recommendation and remediate.",
                        source="bandit",
                    )
                )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return findings


def scan_file(filename: str, content: str) -> list[ReviewFinding]:
    findings = scan_content(filename, content)
    findings.extend(scan_with_bandit(content, filename))
    return findings
