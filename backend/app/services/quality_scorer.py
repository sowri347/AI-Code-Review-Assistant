import re
from pathlib import Path

from app.models.schemas import QualityMetrics


def _count_functions(content: str) -> int:
    return len(re.findall(r"^\s*(def |function |const \w+ = .*=>|async def )", content, re.MULTILINE))


def _estimate_complexity(content: str) -> float:
    keywords = len(re.findall(r"\b(if|elif|else|for|while|case|catch|&&|\|\|)\b", content))
    lines = max(len(content.splitlines()), 1)
    return min(100.0, (keywords / lines) * 500)


def _score_readability(content: str) -> float:
    lines = [line for line in content.splitlines() if line.strip()]
    if not lines:
        return 100.0

    long_lines = sum(1 for line in lines if len(line) > 120)
    comment_lines = sum(
        1
        for line in lines
        if line.strip().startswith(("#", "//", "/*", "*", '"""', "'''"))
    )
    avg_length = sum(len(line) for line in lines) / len(lines)

    score = 100.0
    score -= (long_lines / len(lines)) * 30
    score -= max(0, avg_length - 80) * 0.3
    score += min(20, (comment_lines / len(lines)) * 40)
    return max(0.0, min(100.0, score))


def _score_maintainability(content: str, filename: str) -> float:
    lines = len(content.splitlines())
    functions = _count_functions(content)
    complexity = _estimate_complexity(content)

    score = 100.0
    if lines > 500:
        score -= min(30, (lines - 500) / 50)
    if functions == 0 and lines > 50:
        score -= 15
    score -= complexity * 0.4

    if filename.endswith((".test.", "_test.", ".spec.")):
        score += 5

    return max(0.0, min(100.0, score))


def analyze_files(changes: list[tuple[str, str]]) -> QualityMetrics:
    if not changes:
        return QualityMetrics(
            overall_score=100.0,
            maintainability=100.0,
            readability=100.0,
            complexity_score=100.0,
            test_coverage_hint="No files to analyze.",
        )

    maintainability_scores: list[float] = []
    readability_scores: list[float] = []
    complexity_scores: list[float] = []
    has_tests = False

    for filename, content in changes:
        if not content.strip():
            continue
        maintainability_scores.append(_score_maintainability(content, filename))
        readability_scores.append(_score_readability(content))
        complexity_scores.append(max(0.0, 100.0 - _estimate_complexity(content)))
        if any(
            marker in filename.lower()
            for marker in (".test.", "_test.", ".spec.", "/tests/", "\\tests\\")
        ):
            has_tests = True

    maintainability = sum(maintainability_scores) / len(maintainability_scores)
    readability = sum(readability_scores) / len(readability_scores)
    complexity_score = sum(complexity_scores) / len(complexity_scores)
    overall = maintainability * 0.4 + readability * 0.3 + complexity_score * 0.3

    hint = "Test files detected in this PR." if has_tests else "Consider adding unit tests for changed code."

    return QualityMetrics(
        overall_score=round(overall, 1),
        maintainability=round(maintainability, 1),
        readability=round(readability, 1),
        complexity_score=round(complexity_score, 1),
        test_coverage_hint=hint,
    )


def extract_added_lines(patch: str | None) -> str:
    if not patch:
        return ""
    added: list[str] = []
    for line in patch.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            added.append(line[1:])
    return "\n".join(added)
