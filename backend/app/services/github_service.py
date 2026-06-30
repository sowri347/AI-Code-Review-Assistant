from github import Github, GithubException

from app.config import settings
from app.models.schemas import FileChange, PullRequestSummary


class GitHubService:
    def __init__(self) -> None:
        self._client: Github | None = None

    @property
    def client(self) -> Github:
        if not settings.github_token:
            raise ValueError("GITHUB_TOKEN is not configured")
        if self._client is None:
            self._client = Github(settings.github_token)
        return self._client

    def list_pull_requests(self, owner: str, repo: str, state: str = "open") -> list[PullRequestSummary]:
        repository = self.client.get_repo(f"{owner}/{repo}")
        pulls = repository.get_pulls(state=state, sort="updated", direction="desc")

        summaries = []
        for pr in pulls:
            summaries.append(
                PullRequestSummary(
                    number=pr.number,
                    title=pr.title,
                    author=pr.user.login if pr.user else "unknown",
                    state=pr.state,
                    url=pr.html_url,
                    repo=f"{owner}/{repo}",
                    additions=pr.additions,
                    deletions=pr.deletions,
                    changed_files=pr.changed_files,
                )
            )
            if len(summaries) >= 20:
                break
        return summaries

    def get_pull_request_files(self, owner: str, repo: str, pr_number: int) -> list[FileChange]:
        repository = self.client.get_repo(f"{owner}/{repo}")
        pull = repository.get_pull(pr_number)
        files = pull.get_files()

        return [
            FileChange(
                filename=f.filename,
                status=f.status,
                additions=f.additions,
                deletions=f.deletions,
                patch=f.patch,
            )
            for f in files
        ]

    def get_file_content(self, owner: str, repo: str, path: str, ref: str) -> str:
        repository = self.client.get_repo(f"{owner}/{repo}")
        try:
            content = repository.get_contents(path, ref=ref)
            if isinstance(content, list):
                return ""
            return content.decoded_content.decode("utf-8", errors="replace")
        except GithubException:
            return ""


github_service = GitHubService()
