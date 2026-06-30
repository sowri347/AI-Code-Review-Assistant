from fastapi import APIRouter, HTTPException
from github import GithubException
import openai

from app.models.schemas import ReviewReport, ReviewRequest
from app.routers.github import map_github_exception
from app.services.ai_analyzer import ai_analyzer
from app.services.github_service import github_service
from app.services.quality_scorer import analyze_files, extract_added_lines
from app.services.security_scanner import scan_file

router = APIRouter(prefix="/api/review", tags=["review"])


def map_openai_exception(exc: openai.OpenAIError) -> HTTPException:
    if isinstance(exc, openai.AuthenticationError):
        return HTTPException(
            status_code=401,
            detail="OpenAI authentication failed. Please verify that your OPENAI_API_KEY in the .env file is correct."
        )

    if isinstance(exc, openai.RateLimitError):
        msg = str(exc)
        if "quota" in msg.lower() or "billing" in msg.lower() or "insufficient_quota" in msg.lower():
            detail = "OpenAI quota exceeded. Please check your OpenAI billing plan and credits. Make sure your account has active funds."
        else:
            detail = "OpenAI API rate limit reached. Please wait a moment before trying again."
        return HTTPException(status_code=429, detail=detail)

    if isinstance(exc, openai.APIConnectionError):
        return HTTPException(
            status_code=503,
            detail="Failed to connect to OpenAI API servers. Please check your network connection."
        )

    return HTTPException(
        status_code=502,
        detail=f"OpenAI API error: {exc}"
    )


@router.post("", response_model=ReviewReport)
def review_pull_request(body: ReviewRequest):
    try:
        files = github_service.get_pull_request_files(body.owner, body.repo, body.pr_number)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except GithubException as exc:
        raise map_github_exception(exc, body.owner, body.repo, body.pr_number) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch PR: {exc}") from exc

    if not files:
        raise HTTPException(status_code=404, detail="No files found in this pull request")

    static_findings = []
    file_contents: list[tuple[str, str]] = []

    for f in files:
        added = extract_added_lines(f.patch)
        if added:
            file_contents.append((f.filename, added))
            static_findings.extend(scan_file(f.filename, added))

    try:
        ai_summary, ai_findings = ai_analyzer.analyze(
            body.owner, body.repo, body.pr_number, files
        )
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except openai.OpenAIError as exc:
        raise map_openai_exception(exc) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI analysis failed: {exc}") from exc

    all_findings = ai_findings + static_findings
    all_findings.sort(
        key=lambda f: {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}.get(
            f.severity.value, 5
        )
    )

    quality = analyze_files(file_contents)
    total_additions = sum(f.additions for f in files)
    total_deletions = sum(f.deletions for f in files)

    return ReviewReport(
        pr_number=body.pr_number,
        repo=f"{body.owner}/{body.repo}",
        summary=ai_summary,
        findings=all_findings,
        quality=quality,
        files_analyzed=len(files),
        lines_changed=total_additions + total_deletions,
    )
