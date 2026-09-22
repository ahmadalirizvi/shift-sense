# Shift Sense

Shift Sense learns patterns from completed staff schedules and proposes assignments for a new blank week. It uses location, shift type, day, time, recency, rotation patterns, and conflict detection to help produce a rota that is faster to review and safer to publish.

The project is split into a FastAPI backend and a React/Vite frontend. Historical schedules are uploaded to the backend's in-memory learning engine; a blank schedule is then analysed and returned as JSON plus a downloadable Excel workbook.

## Contents

- [Features](#features)
- [Architecture](#architecture)
- [Requirements](#requirements)
- [Local setup](#local-setup)
- [Run the application](#run-the-application)
- [Use the application](#use-the-application)
- [Excel workbook format](#excel-workbook-format)
- [Prediction behavior](#prediction-behavior)
- [API reference](#api-reference)
- [Testing](#testing)
- [Configuration](#configuration)
- [Project structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Data and security](#data-and-security)
- [Contributing](#contributing)
- [Development guidelines](#development-guidelines)
- [Known limitations](#known-limitations)
- [License](#license)

## Features

- Upload multiple completed `.xlsx` schedules as historical training data.
- Upload a blank `.xlsx` schedule for the next week.
- Match assignments by location, shift type, day, and start/end time.
- Fall back from exact matches to shift-type and location-level matches.
- Weight recent schedules more heavily than older schedules.
- Detect simple employee rotation patterns.
- Detect overlapping assignments across locations and remove the lower-confidence assignment.
- Return confidence values from `0` to `100` and flag uncertain shifts for review.
- Generate reasoning from the rule-based engine, with optional Google Gemini explanations.
- Display predictions in the web interface and download the generated workbook.
- Show historical coverage and week-offset counts in the Learning history view.

## Architecture

```text
React + Vite frontend
        |
        | /api proxy in development
        v
FastAPI backend
  |-- ShiftParser       Excel parsing and output generation
  |-- PatternEngine     Historical matching and confidence scoring
  |-- ConflictDetector  Overlap detection and resolution
  |-- AIReasoningEngine Optional Gemini explanations with fallback
```

The backend currently keeps the pattern engine in process memory. Restarting the server clears the learned history. Uploaded files and generated workbooks are stored locally in ignored `uploads/` and `outputs/` directories.

## Requirements

- macOS, Linux, or Windows
- Python 3.10+ recommended
- Node.js 18+ and npm
- Excel workbooks in `.xlsx` format
- Optional: a Google Gemini API key for AI-generated explanations

## Local setup

From the repository root:

```bash
cd shift-sense
```

### Backend environment

Create or reuse a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
```

On Windows PowerShell, activate with:

```powershell
.venv\Scripts\Activate.ps1
```

### Frontend dependencies

```bash
cd frontend
npm install
cd ..
```

## Run the application

Use two terminals from the repository root.

### Terminal 1: backend

```bash
.venv/bin/uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Windows PowerShell:

```powershell
.venv\Scripts\python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend URLs:

- API: <http://127.0.0.1:8000>
- Swagger UI: <http://127.0.0.1:8000/docs>
- Health check: <http://127.0.0.1:8000/health>

### Terminal 2: frontend

```bash
cd frontend
npm run dev -- --host 127.0.0.1
```

Open the URL printed by Vite, normally <http://127.0.0.1:3000>. If port 3000 is already in use, Vite chooses another port, such as 3001. Use the URL it prints.

The Vite development server proxies `/api/*` to the backend and removes the `/api` prefix. For example, frontend `/api/history` reaches backend `/history`.

### Production frontend preview

```bash
cd frontend
npm run build
npm run preview
```

The production build is written to `frontend/dist/`, which is ignored by Git.

## Use the application

1. Open the frontend URL.
2. Open **Learning history** in the sidebar.
3. Select one or more completed `.xlsx` workbooks.
4. Click **Add to learning set**.
5. Return to the main page.
6. Select a blank upcoming-week workbook.
7. Click **Generate predictions**.
8. Review assignments, confidence, conflicts, and reasoning.
9. Download the generated Excel workbook.

Upload historical workbooks in the order you want them weighted. The current implementation assigns `week_offset` based on upload order within one request: the first file is offset `0`, the next is offset `1`, and so on.

## Excel workbook format

Every non-empty worksheet must contain these columns. Column names are trimmed for surrounding whitespace but are otherwise case-sensitive.

| Column | Required | Description |
| --- | --- | --- |
| `Date` | Yes | Shift date. ISO dates and common `DD/MM/YYYY`, `MM/DD/YYYY`, and hyphenated formats are supported. |
| `Day` | Yes | Day of week, such as `Monday` or `Saturday`. |
| `Shift Type` | Yes | Shift category, such as `Day` or `Night`. |
| `Start Time` | Yes | Start time, such as `08:00`, `08:00:00`, or `8:00 AM`. |
| `End Time` | Yes | End time in a supported time format. |
| `Location` | Yes | Site or location name. |
| `Hours` | Yes | Numeric shift duration. Blank values become `0.0`. |
| `Notes` | Yes | Employee name in historical files; blank in a prediction workbook. |

Example header row:

```text
Date | Day | Shift Type | Start Time | End Time | Location | Hours | Notes
```

Multiple worksheets are supported. The parser keeps the worksheet name as `sheet_name`, while predictions are grouped into location-named output worksheets.

### Historical workbook

```text
Date       Day       Shift Type  Start Time  End Time  Location       Hours  Notes
2026-09-18 Friday    Day         08:00       16:00     Brize Norton   8      Ghulam
```

### Blank prediction workbook

Use the same columns, but leave `Notes` empty for shifts that need assignments:

```text
Date       Day       Shift Type  Start Time  End Time  Location       Hours  Notes
2026-09-25 Friday    Day         08:00       16:00     Brize Norton   8
```

## Prediction behavior

For each target shift, `PatternEngine` checks matches in this order:

1. Same location, shift type, day, start time, and end time.
2. Same location, shift type, start time, and end time, ignoring day.
3. Same location only.
4. Recency weighting, using exponential decay.
5. Candidate frequency and score comparison.
6. Rotation-pattern detection where enough history exists.

Confidence is a percentage from `0` to `100`. Predictions below the `60` percent threshold are marked `needs_review`. Conflicts are checked after predictions are generated; when two assignments overlap for the same person, the lower-confidence assignment is cleared.

AI reasoning is optional. If Gemini is unavailable, no key is configured, or a Gemini request fails, Shift Sense uses a deterministic rule-based explanation instead.

## API reference

### `GET /`

Returns a welcome message.

### `GET /health`

Returns:

```json
{"status": "healthy"}
```

### `POST /upload-historical`

Multipart form upload. Repeat the `files` field for one or more `.xlsx` workbooks.

```bash
curl -X POST http://127.0.0.1:8000/upload-historical \\
  -F "files=@/path/to/week-1.xlsx" \\
  -F "files=@/path/to/week-2.xlsx"
```

The response includes processed filenames, record counts, and assigned week offsets.

### `POST /predict`

Multipart form upload with one blank `.xlsx` workbook in the `file` field.

```bash
curl -X POST http://127.0.0.1:8000/predict \\
  -F "file=@/path/to/blank-week.xlsx"
```

The response includes:

- `predictions`: one result per parsed shift
- `summary`: totals, confident predictions, review count, and resolved conflicts
- `debug_info`: match counts and selected match type
- `download_url`: generated workbook route

### `GET /download/{filename}`

Downloads a generated `.xlsx` file. Only files inside the local `outputs/` directory are served.

### `GET /history`

Returns the current in-memory learning-set count, week breakdown, and whether an AI client is configured.

## Testing

The repository includes core, AI, and integration tests under `backend/tests/`.

Run the executable regression scripts with the project virtual environment:

```bash
.venv/bin/python backend/tests/test_core_logic.py
.venv/bin/python backend/tests/test_integration.py
```

The AI test can be run directly as well:

```bash
.venv/bin/python backend/tests/test_ai_reasoning.py
```

Validate Python syntax:

```bash
.venv/bin/python -m compileall -q backend/app
```

Build the frontend:

```bash
cd frontend
npm run build
```

Before opening a pull request, run the relevant backend checks and the frontend build. Add a regression test for behavior changes, especially changes to parsing, confidence, conflict resolution, or API response shapes.

## Configuration

Copy `.env.example` to `.env` at the repository root if you want to configure Gemini:

```bash
cp .env.example .env
```

Available variables:

| Variable | Required | Purpose |
| --- | --- | --- |
| `GEMINI_API_KEY` | No | Enables Gemini-backed explanations. |
| `GEMINI_MODEL` | No | Overrides the default Gemini model. |

Do not commit `.env`, API keys, real schedules, uploads, generated outputs, or other personal data. The repository `.gitignore` excludes these paths by default.

## Project structure

```text
shift-sense/
├── backend/
│   ├── app/
│   │   ├── ai_reasoning.py    # Optional Gemini layer and fallback explanations
│   │   ├── conflicts.py       # Overlap detection and resolution
│   │   ├── main.py            # FastAPI application and routes
│   │   ├── models.py          # Domain dataclasses
│   │   ├── parsing.py         # Excel parser and output workbook generation
│   │   └── patterns.py        # Historical matching and confidence scoring
│   ├── data/                  # Sample and local historical data
│   ├── requirements.txt
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── App.jsx            # Main React application and workflows
│   │   ├── index.css          # Application design system and responsive styles
│   │   └── main.jsx           # React entry point
│   ├── package.json
│   ├── vite.config.js         # Dev server and `/api` proxy
│   └── index.html
├── .env.example
├── LICENSE
└── README.md
```

## Troubleshooting

### `Cannot connect to localhost:8000`

Start the backend from the repository root:

```bash
.venv/bin/uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Confirm it responds:

```bash
curl http://127.0.0.1:8000/health
```

### Vite chooses port 3001 or another port

Port 3000 is already in use. Open the exact URL printed by `npm run dev`. The proxy still targets the backend on port 8000.

### Upload returns `400` or `500`

Check that the file:

- Has an `.xlsx` extension.
- Contains every required column.
- Has valid dates, times, locations, and shift types.
- Is not empty after parsing.

The backend terminal contains the detailed exception. A bad workbook should return a client error; an unexpected parser or filesystem failure is reported as a server error.

### Gemini returns a 404 or is unavailable

AI reasoning is optional. Remove the invalid `GEMINI_API_KEY` to use the deterministic fallback, or set `GEMINI_MODEL` to a model available to your account. Prediction generation does not require Gemini to succeed.

### Historical data disappears

This is expected after a backend restart: the current pattern engine is in memory. Persistent storage is a future improvement.

## Data and security

- Treat uploaded schedules as sensitive staff data.
- Do not use real personnel data in public issues, tests, screenshots, or pull requests.
- Keep API keys in environment variables and never commit them.
- Generated workbooks and uploads are local runtime artifacts and are ignored by Git.
- The development CORS list is limited to local frontend origins. Review it before deployment.
- The application is intended for local development at present; authentication, authorization, rate limiting, and production object storage are not implemented.

## Contributing

Contributions are welcome. For substantial changes, open an issue first to describe the problem, proposed behavior, and affected area.

### Contribution workflow

1. Fork the repository or create a feature branch from `main`.
2. Keep the change focused and avoid unrelated formatting churn.
3. Update tests and documentation when behavior or setup changes.
4. Run the relevant backend checks and `npm run build`.
5. Review `git diff` and confirm no secrets, real schedule data, uploads, outputs, or build artifacts are included.
6. Use a clear commit message and open a pull request against `main`.

### Commit messages

Use short imperative messages with a conventional prefix where appropriate:

```text
feat: add persistent historical storage
fix: reject workbooks with missing shift columns
docs: clarify local setup
test: cover overnight conflict detection
refactor: isolate prediction response mapping
style: improve history navigation layout
```

Keep commits atomic. A commit should represent one coherent change and should be buildable when practical.

### Pull request checklist

- [ ] The purpose and scope are clear.
- [ ] Tests cover new or changed behavior.
- [ ] `npm run build` passes for frontend changes.
- [ ] Backend regression scripts or relevant tests pass.
- [ ] README or configuration docs are updated when needed.
- [ ] No secrets or real staff schedule data are included.
- [ ] API response and workbook-format changes are called out explicitly.
- [ ] Known limitations and follow-up work are documented.

### Code standards

- Follow the existing Python, React, and CSS patterns before introducing abstractions.
- Keep API contracts explicit and backward-compatible when possible.
- Prefer clear validation errors over silent data changes.
- Preserve confidence semantics as percentages from `0` to `100`.
- Add focused tests around parsing, matching, conflict resolution, and response mapping.
- Keep user-facing copy concise and accessible.

## Known limitations

- Historical learning is held in memory and resets when the backend restarts.
- Uploaded file order is used as a simple week-offset proxy; dates are not used to infer recency.
- Authentication and multi-user isolation are not implemented.
- The output workbook is generated, but cell coloring and advanced formatting are not yet implemented.
- AI reasoning depends on an external Gemini configuration and gracefully falls back when unavailable.
- The project does not currently define a `pytest` configuration or automated CI workflow.

## Roadmap ideas

- Persist historical schedules in a database or durable object store.
- Infer week offsets from workbook dates instead of upload order.
- Add authentication, user workspaces, and data isolation.
- Add workbook color-coding and richer suggestions sheets.
- Add automated CI for backend tests, frontend builds, and linting.
- Add browser-level tests for uploads, predictions, filtering, and downloads.

## License

Shift Sense is licensed under the [MIT License](LICENSE).