# S-001: Add a /version endpoint

Status: Testing
Branch: story/S-001-version-endpoint
Requested: add a /version endpoint
Date: 2026-07-12

<!-- Status flow: Draft → Approved → In Progress → In Review → Testing → Done -->

## User story

As a developer/operator running the sentiment API, I want a `GET /version` endpoint, so
that I can quickly confirm which app version a running instance (e.g. on Azure) is
serving and whether it has a sentiment model loaded, without having to inspect logs.

## Acceptance criteria

<!-- Each criterion must be verifiable by a pytest test or an explicit manual check. -->

- [ ] AC1: `GET /version` returns HTTP 200.
- [ ] AC2: The JSON response includes a `"version"` key whose value is a non-empty string
      (e.g. `"0.1.0"`), sourced from a single version constant defined in `src/app.py`.
- [ ] AC3: The JSON response includes a `"model_loaded"` boolean key that is `true` when
      the app has successfully loaded a model during startup (the normal case in tests,
      since the FastAPI `lifespan` trains/loads the model before the app serves
      requests).
- [ ] AC4: The JSON response includes a `"model_path"` string key equal to the filename
      of the model artifact the app loaded (e.g. `"sentiment_model.joblib"`, matching
      `DEFAULT_MODEL.name` from `src/train.py`).

## Affected files

- `src/app.py` — add an `APP_VERSION` constant and a `GET /version` route that reads
  `_state` (populated in `lifespan`) to report load status and model path; existing file,
  already defines `app`, `_state`, `DEFAULT_MODEL`, and the `/health` route this endpoint
  sits alongside.
- `tests/test_app.py` — new file; no API-level tests exist yet (only
  `tests/test_preprocessing.py` and `tests/test_model.py`), so this story's tests for
  `/version` (and any FastAPI `TestClient` setup they need) will live here. `httpx` is
  already in `requirements.txt`, enabling `fastapi.testclient.TestClient`.

## Out of scope

- Reporting git commit hash, build timestamp, or CI build number (no such metadata is
  captured anywhere in the repo today).
- Adding richer model metadata to the saved bundle itself (e.g. training date, dataset
  version/hash, metric scores) — would require changing `save_model`/`load_model` in
  `src/model.py` and `src/train.py`, which is a separate, larger change.
- API URL versioning (e.g. moving routes under `/v1/...`).
- Automating version bumps (e.g. reading from `pyproject.toml`/`setup.cfg`, git tags, or
  wiring a release process) — a single hardcoded constant is enough for this prototype.
- Exposing `/version` details on the static frontend (`static/index.html`).

## Implementation notes

_(coder appends: what was built, decisions made, deviations from the plan)_

- **2026-07-12 (coder):** Added `APP_VERSION = "0.1.0"` constant and a `GET /version`
  route in `src/app.py`, placed alongside `/health`. The route returns
  `{"version": APP_VERSION, "model_loaded": _state.get("model") is not None,
  "model_path": DEFAULT_MODEL.name}`. Used `_state.get("model") is not None` so the
  endpoint reports `false` gracefully if the model were ever absent, instead of raising
  a KeyError. No deviations from the story; `tests/test_app.py` intentionally left to
  the tester agent. Full existing suite passes (15 passed). Manually smoke-tested with
  `TestClient`: `200 {"version": "0.1.0", "model_loaded": true, "model_path":
  "sentiment_model.joblib"}`.

## Review findings

_(reviewer appends: Blocker / Suggestion / Nit items with file:line, then the fix outcome)_

- **2026-07-12 (reviewer): APPROVED — no Blockers, Suggestions, or Nits.**
  - AC1 met: `GET /version` returns 200 (verified with `TestClient`).
  - AC2 met: single `APP_VERSION = "0.1.0"` constant in `src/app.py`, used in the response.
  - AC3 met: `model_loaded` via `_state.get("model") is not None`; `True` after lifespan
    startup, degrades to `false` (no KeyError) if the model were absent.
  - AC4 met: `model_path` is `DEFAULT_MODEL.name` → `"sentiment_model.joblib"`.
  - Diff is 11 additive lines confined to `src/app.py`, placed alongside `/health`,
    defined before the catch-all static mount (not shadowed), and touches nothing on the
    Out-of-scope list.

## Test results

_(tester appends: pass/fail per acceptance criterion + full pytest summary)_

- **2026-07-12 (tester):** Added `tests/test_app.py` (new file) with a module-scoped
  `TestClient` fixture used as a context manager so the `lifespan` trains/loads the model
  before requests are made. Tests derived from the acceptance criteria wording, not from
  reading `src/app.py` beforehand.

  | AC | Test(s) | Result |
  |----|---------|--------|
  | AC1: `GET /version` returns HTTP 200 | `test_version_returns_200` | PASS |
  | AC2: `"version"` key is a non-empty string | `test_version_key_is_non_empty_string` | PASS |
  | AC3: `"model_loaded"` boolean is `true` after lifespan startup | `test_model_loaded_is_true` | PASS |
  | AC4: `"model_path"` equals `DEFAULT_MODEL.name` | `test_model_path_matches_default_model_name` | PASS |

  Full suite: `19 passed, 12 warnings in 1.90s` (15 pre-existing tests in
  `tests/test_model.py` and `tests/test_preprocessing.py` + 4 new in `tests/test_app.py`).
  No implementation findings — all ACs met as coded.
