const API_BASE = "/api";

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error("Backend unavailable");
  return res.json();
}

export async function fetchPullRequests(owner, repo, state = "open") {
  const params = new URLSearchParams({ owner, repo, state });
  const res = await fetch(`${API_BASE}/github/pulls?${params}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to fetch pull requests");
  }
  return res.json();
}

export async function reviewPullRequest(owner, repo, prNumber) {
  const res = await fetch(`${API_BASE}/review`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ owner, repo, pr_number: prNumber }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Review failed");
  }
  return res.json();
}
