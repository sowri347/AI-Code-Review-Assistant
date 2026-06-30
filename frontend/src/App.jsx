import { useCallback, useEffect, useState } from "react";
import { fetchHealth, fetchPullRequests, reviewPullRequest } from "./api";
import PullRequestList from "./components/PullRequestList";
import QualityScore from "./components/QualityScore";
import FindingsList, { SEVERITY_ORDER } from "./components/FindingsList";

export default function App() {
  const [owner, setOwner] = useState("");
  const [repo, setRepo] = useState("");
  const [health, setHealth] = useState(null);
  const [pullRequests, setPullRequests] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [reviewing, setReviewing] = useState(null);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch(() => setHealth({ status: "error" }));
  }, []);

  const handleSearch = useCallback(async () => {
    if (!owner.trim() || !repo.trim()) return;
    setLoading(true);
    setError(null);
    setReport(null);
    try {
      const prs = await fetchPullRequests(owner.trim(), repo.trim());
      setPullRequests(prs);
    } catch (err) {
      setError(err.message);
      setPullRequests(null);
    } finally {
      setLoading(false);
    }
  }, [owner, repo]);

  const handleReview = useCallback(
    async (prNumber) => {
      setReviewing(prNumber);
      setError(null);
      try {
        const result = await reviewPullRequest(owner.trim(), repo.trim(), prNumber);
        setReport(result);
      } catch (err) {
        setError(err.message);
      } finally {
        setReviewing(null);
      }
    },
    [owner, repo]
  );

  const filteredFindings =
    report?.findings?.filter(
      (f) => filter === "all" || f.category === filter || f.severity === filter
    ) ?? [];

  const categories = report
    ? [...new Set(report.findings.map((f) => f.category))]
    : [];

  return (
    <div className="app">
      <header className="header">
        <div className="header-left">
          <h1>AI Code Review Assistant</h1>
          <p>Automated PR analysis with bug detection, security scanning, and quality scoring</p>
        </div>
        {health && (
          <div className="status-badge">
            <span
              className={`status-dot ${
                health.github_configured && health.openai_configured ? "ok" : "warn"
              }`}
            />
            {health.github_configured && health.openai_configured
              ? "APIs configured"
              : "Configure API keys in .env"}
          </div>
        )}
      </header>

      <form
        className="repo-form"
        onSubmit={(e) => {
          e.preventDefault();
          handleSearch();
        }}
      >
        <input
          placeholder="Owner (e.g. facebook)"
          value={owner}
          onChange={(e) => setOwner(e.target.value)}
        />
        <input
          placeholder="Repository (e.g. react)"
          value={repo}
          onChange={(e) => setRepo(e.target.value)}
        />
        <button className="btn btn-primary" type="submit" disabled={loading}>
          {loading ? "Loading..." : "Load PRs"}
        </button>
      </form>

      {error && <div className="error-banner">{error}</div>}

      {loading && (
        <div className="loading">
          <div className="spinner" />
          Fetching pull requests...
        </div>
      )}

      {!loading && pullRequests !== null && (
        <PullRequestList
          pullRequests={pullRequests}
          onReview={handleReview}
          reviewing={reviewing}
        />
      )}

      {reviewing && (
        <div className="loading">
          <div className="spinner" />
          Running AI analysis and security scan on PR #{reviewing}...
        </div>
      )}

      {report && !reviewing && (
        <div className="review-panel">
          <div className="review-header">
            <h2>
              Review: {report.repo} #{report.pr_number}
            </h2>
            <span style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
              {report.files_analyzed} files &middot; {report.lines_changed} lines changed
            </span>
          </div>

          <div className="summary-box">{report.summary}</div>

          <QualityScore quality={report.quality} />

          <div className="filter-bar">
            <button
              className={`filter-btn ${filter === "all" ? "active" : ""}`}
              onClick={() => setFilter("all")}
            >
              All ({report.findings.length})
            </button>
            {categories.map((cat) => (
              <button
                key={cat}
                className={`filter-btn ${filter === cat ? "active" : ""}`}
                onClick={() => setFilter(cat)}
              >
                {cat} ({report.findings.filter((f) => f.category === cat).length})
              </button>
            ))}
            {SEVERITY_ORDER.filter((s) =>
              report.findings.some((f) => f.severity === s)
            ).map((sev) => (
              <button
                key={sev}
                className={`filter-btn ${filter === sev ? "active" : ""}`}
                onClick={() => setFilter(sev)}
              >
                {sev}
              </button>
            ))}
          </div>

          <FindingsList findings={filteredFindings} />
        </div>
      )}
    </div>
  );
}
