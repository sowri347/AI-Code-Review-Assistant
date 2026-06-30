# AI Code Review Assistant

An AI-powered platform that reviews GitHub pull requests and suggests fixes. Combines LLM analysis with static security scanning and code quality scoring.

## Features

- **GitHub Integration** — Fetch open PRs and diffs via the GitHub API
- **AI Code Analysis** — OpenAI-powered review with actionable suggestions
- **Bug Detection** — Logic errors, edge cases, and common pitfalls
- **Security Scanning** — Regex patterns + Bandit for Python vulnerabilities
- **Code Quality Scoring** — Maintainability, readability, and complexity metrics

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│  React UI   │────▶│  FastAPI Backend │────▶│  GitHub API │
│  (Vite)     │     │                  │     └─────────────┘
└─────────────┘     │  ┌────────────┐  │     ┌─────────────┐
                    │  │ AI Analyzer│──│────▶│  OpenAI API │
                    │  └────────────┘  │     └─────────────┘
                    │  ┌────────────┐  │
                    │  │  Security  │  │
                    │  │  Scanner   │  │
                    │  └────────────┘  │
                    │  ┌────────────┐  │
                    │  │  Quality   │  │
                    │  │  Scorer    │  │
                    │  └────────────┘  │
                    └──────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- GitHub Personal Access Token (repo scope)
- OpenAI API Key

### Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys

uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173, enter a repo owner and name, then click **Review** on any PR.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check and config status |
| GET | `/api/github/pulls?owner=&repo=` | List open pull requests |
| POST | `/api/review` | Run full AI + static review |

### Review Request

```json
{
  "owner": "facebook",
  "repo": "react",
  "pr_number": 12345
}
```

### Review Response

```json
{
  "pr_number": 12345,
  "repo": "facebook/react",
  "summary": "Overall assessment...",
  "findings": [
    {
      "id": "abc123",
      "category": "security",
      "severity": "high",
      "title": "Hardcoded secret detected",
      "description": "...",
      "file": "src/config.py",
      "line": 12,
      "suggestion": "Move to environment variables",
      "source": "static"
    }
  ],
  "quality": {
    "overall_score": 78.5,
    "maintainability": 82.0,
    "readability": 75.0,
    "complexity_score": 78.0
  },
  "files_analyzed": 5,
  "lines_changed": 142
}
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GITHUB_TOKEN` | GitHub PAT with repo read access |
| `GEMINI_API_KEY` | GeminiAI API key |
| `OPENAI_MODEL` | Model name (default: `gpt-4o-mini`) |
| `CORS_ORIGINS` | Comma-separated allowed origins |

## CI/CD Integration

A GitHub Actions workflow is included at `.github/workflows/pr-review.yml`. Add `GITHUB_TOKEN` and `OPENAI_API_KEY` as repository secrets to enable automated reviews on every PR.

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Settings
│   │   ├── models/schemas.py    # Pydantic models
│   │   ├── routers/             # API routes
│   │   └── services/
│   │       ├── github_service.py
│   │       ├── ai_analyzer.py
│   │       ├── security_scanner.py
│   │       └── quality_scorer.py
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.jsx
│       └── components/
└── .github/workflows/
    └── pr-review.yml
```

## Technologies

- **Backend:** Python, FastAPI, PyGithub, OpenAI SDK, Bandit
- **Frontend:** React, Vite
- **APIs:** GitHub REST API, OpenAI Chat Completions

## License

MIT
