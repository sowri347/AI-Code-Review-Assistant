function scoreClass(score) {
  if (score >= 75) return "score-good";
  if (score >= 50) return "score-mid";
  return "score-low";
}

export default function QualityScore({ quality }) {
  if (!quality) return null;

  const metrics = [
    { label: "Overall", value: quality.overall_score },
    { label: "Maintainability", value: quality.maintainability },
    { label: "Readability", value: quality.readability },
    { label: "Complexity", value: quality.complexity_score },
  ];

  return (
    <div>
      <h3 className="section-title">Code Quality Score</h3>
      <div className="quality-grid">
        {metrics.map((m) => (
          <div key={m.label} className="quality-card">
            <div className={`quality-score ${scoreClass(m.value)}`}>{m.value}</div>
            <div className="quality-label">{m.label}</div>
          </div>
        ))}
      </div>
      {quality.test_coverage_hint && (
        <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: "1rem" }}>
          {quality.test_coverage_hint}
        </p>
      )}
    </div>
  );
}
