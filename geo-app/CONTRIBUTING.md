# Contributing to geo-app (IAInmobiliaria)

This document covers everything you need to contribute to the geo-app project: project structure, environment setup, testing, code style, and PR guidelines.

---

## Project Structure

```
geo-app/
├── app/                        # Angular 17 frontend (standalone components)
│   ├── src/app/
│   │   ├── components/         # Reusable UI components
│   │   ├── pages/              # Page-level components (mapa, etc.)
│   │   ├── services/           # Angular services (API, analytics, map-state, etc.)
│   │   └── models/             # TypeScript interfaces
│   └── ...
├── python_services/            # FastAPI backend + ML pipeline
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # Environment & path configuration
│   ├── ml_model/               # ML model code, config, and artifacts
│   │   ├── predictor.py        # PlusvaliaPredictorModel class
│   │   └── model_config.yaml   # Externalized hyperparameters & thresholds
│   ├── integrations/           # External API clients (INEGI, OSM, etc.)
│   └── tests/                  # Pytest test suite
├── CONTRIBUTING.md             # This file
└── README.md
```

---

## Development Environment Setup

### Prerequisites

- **Node.js** >= 18 and **npm** >= 9
- **Python** >= 3.10
- **Angular CLI** (`npm install -g @angular/cli`)

### Backend (FastAPI + ML)

```bash
cd python_services
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

Start the API server:

```bash
uvicorn main:app --reload --port 8000
```

### Frontend (Angular)

```bash
cd app
npm install
npm start
```

The app will be available at `http://localhost:4200` and will proxy API requests to `http://localhost:8000`.

---

## Running Tests

### Python (backend + ML)

```bash
cd python_services
python -m pytest tests/ -v --cov
```

To run a single test file:

```bash
python -m pytest tests/test_predictor.py -v
```

### Angular (frontend)

```bash
cd app
ng test           # Unit tests with Karma
ng lint           # ESLint check
```

---

## Code Style

### Python

- **Ruff** is used for linting and formatting. Configuration lives in `pyproject.toml`.
- Run `ruff check .` and `ruff format .` before committing.
- Type hints are expected on all public functions.

### Angular / TypeScript

- **Prettier** handles formatting. Configuration is in `.prettierrc`.
  - Single quotes, trailing commas (ES5), 100-char print width, 2-space indentation, semicolons.
- **ESLint** with `@angular-eslint` and `@typescript-eslint` plugins. Configuration is in `.eslintrc.json`.
  - Run `ng lint` before committing. Fix all errors; address warnings when possible.
- **Strict mode** is enabled in `tsconfig.json`. Do not disable it.
- Avoid `any` -- use proper interfaces from `src/app/models/interfaces.ts`.
- Components must be **standalone** (`standalone: true`).
- All `*ngFor` directives must include a `trackBy` function.
- Component selectors use the `app-` prefix in kebab-case (e.g., `app-stats-dashboard`).

### EditorConfig

An `.editorconfig` file is provided. Line endings must be LF (`\n`), not CRLF.

---

## Security Note: Supabase Anon Key

The Supabase **anon key** is intentionally committed to the repository and is **not a secret**. It is a public key designed to be used in client-side code. All data access is protected by **Row-Level Security (RLS)** policies on the Supabase side. The **service role key**, however, is a secret and must never be committed -- it is loaded from environment variables in `python_services/config.py`.

---

## Branch Naming Convention

| Prefix       | Purpose                           | Example                        |
|--------------|-----------------------------------|--------------------------------|
| `feature/`   | New feature                       | `feature/price-history-chart`  |
| `fix/`       | Bug fix                           | `fix/heatmap-render-error`     |
| `refactor/`  | Code refactoring (no new feature) | `refactor/api-service-types`   |
| `chore/`     | Tooling, config, dependencies     | `chore/eslint-setup`           |
| `docs/`      | Documentation only                | `docs/contributing-guide`      |
| `test/`      | Adding or fixing tests            | `test/api-service-unit-tests`  |

Branch names use lowercase and hyphens. Keep them short and descriptive.

---

## Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short description>

[optional body]

[optional footer]
```

**Types:** `feat`, `fix`, `refactor`, `chore`, `docs`, `test`, `style`, `perf`

**Scope** (optional): component or service name -- `mapa`, `api-service`, `predictor`, `ml-model`, etc.

**Examples:**

```
feat(mapa): add real-time price overlay toggle
fix(api-service): handle empty response from heatmap endpoint
refactor(predictor): load thresholds from model_config.yaml
```

---

## Pull Request Guidelines

1. Create a branch from `main` following the naming convention above.
2. Make your changes, ensuring:
   - `ng lint` passes with no errors.
   - `ng build --configuration production` succeeds.
   - `python -m pytest tests/ -v` passes.
   - `ruff check .` reports no errors.
3. Push your branch and open a PR against `main`.
4. **PR title** should follow the commit message format (e.g., `feat(mapa): add polygon selection tool`).
5. **PR description** must include:
   - A summary of what changed and why.
   - Screenshots or screen recordings for UI changes.
   - Steps to test the changes.
6. At least **one approval** is required before merging.
7. **Squash-merge** into `main` to keep a clean history.

---

## Editor Setup (VS Code recommended)

Install these extensions:

- ESLint (`dbaeumer.vscode-eslint`)
- Prettier (`esbenp.prettier-vscode`)
- EditorConfig (`editorconfig.editorconfig`)
- Angular Language Service (`angular.ng-template`)
- Python (`ms-python.python`)
- Ruff (`charliermarsh.ruff`)

Workspace settings (`.vscode/settings.json`):

```json
{
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "explicit"
  },
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff"
  }
}
```
