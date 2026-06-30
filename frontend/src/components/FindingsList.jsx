const SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"];

export default function FindingsList({ findings }) {
  if (!findings?.length) {
    return (
      <div className="empty-state">
        <h3>No issues found</h3>
        <p>This pull request looks clean.</p>
      </div>
    );
  }

  return (
    <div>
      <h3 className="section-title">
        Findings ({findings.length})
      </h3>
      <div className="findings-list">
        {findings.map((f) => (
          <div
            key={f.id}
            className={`finding-card severity-${f.severity}`}
          >
            <div className="finding-top">
              <span className="finding-title">{f.title}</span>
              <span className="badge badge-severity">{f.severity}</span>
              <span className="badge badge-category">{f.category}</span>
              <span className="badge badge-source">{f.source}</span>
            </div>
            <p className="finding-desc">{f.description}</p>
            {f.file && (
              <div className="finding-location">
                {f.file}
                {f.line ? `:${f.line}` : ""}
              </div>
            )}
            {f.suggestion && (
              <div className="finding-suggestion">
                <strong>Suggestion:</strong> {f.suggestion}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export { SEVERITY_ORDER };
