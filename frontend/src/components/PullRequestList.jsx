export default function PullRequestList({ pullRequests, onReview, reviewing }) {
  if (!pullRequests?.length) {
    return (
      <div className="empty-state">
        <h3>No open pull requests</h3>
        <p>Try a different repository or check that your token has access.</p>
      </div>
    );
  }

  return (
    <div>
      <h3 className="section-title">Open Pull Requests</h3>
      <div className="pr-list">
        {pullRequests.map((pr) => (
          <div key={pr.number} className="pr-card">
            <div className="pr-info">
              <h3>
                #{pr.number} {pr.title}
              </h3>
              <div className="pr-meta">
                <span>by {pr.author}</span>
                <span>{pr.changed_files} files changed</span>
              </div>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
              <div className="pr-stats">
                <span className="additions">+{pr.additions}</span>
                <span className="deletions">-{pr.deletions}</span>
              </div>
              <button
                className="btn btn-primary btn-sm"
                onClick={() => onReview(pr.number)}
                disabled={reviewing === pr.number}
              >
                {reviewing === pr.number ? "Reviewing..." : "Review"}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
