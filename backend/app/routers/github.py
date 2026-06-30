from fastapi import APIRouter, HTTPException, Query
from github import GithubException

from app.models.schemas import PullRequestSummary, RepoSearchRequest
from app.services.github_service import github_service

router = APIRouter(prefix="/api/github", tags=["github"])


def map_github_exception(exc: GithubException, owner: str, repo: str, pr_number: int | None = None) -> HTTPException:
    error_msg = exc.data.get("message", "") if isinstance(exc.data, dict) else str(exc)

    if exc.status == 404:
        if pr_number is not None:
            detail = f"GitHub pull request '{owner}/{repo} #{pr_number}' not found. Please verify the owner, repository name, and pull request number."
        else:
            detail = f"GitHub repository '{owner}/{repo}' not found. Please check that the repository name is correct and your token has permission to access it."
        return HTTPException(status_code=404, detail=detail)

    if exc.status == 401:
        return HTTPException(status_code=401, detail="GitHub authentication failed. Please check your GITHUB_TOKEN configuration.")

    if exc.status == 403:
        return HTTPException(status_code=403, detail=f"GitHub API access forbidden or rate limit exceeded: {error_msg}")

    return HTTPException(status_code=502, detail=f"GitHub API error ({exc.status}): {error_msg}")


@router.get("/pulls", response_model=list[PullRequestSummary])
def list_pull_requests(
    owner: str = Query(..., description="Repository owner"),
    repo: str = Query(..., description="Repository name"),
    state: str = Query("open", description="PR state: open, closed, or all"),
):
    try:
        return github_service.list_pull_requests(owner, repo, state)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except GithubException as exc:
        raise map_github_exception(exc, owner, repo) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"GitHub API error: {exc}") from exc


@router.post("/validate")
def validate_repo(body: RepoSearchRequest):
    try:
        pulls = github_service.list_pull_requests(body.owner, body.repo)
        return {"valid": True, "open_prs": len(pulls)}
    except GithubException as exc:
        raise map_github_exception(exc, body.owner, body.repo) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
