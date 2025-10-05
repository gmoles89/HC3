# Historia Clínica Cardiológica (v3)

Single-file Streamlit app that models a cardiology clinical history form. Uses Pydantic for validation and pandas for in-memory table editing.

## Pydantic v2 compatibility

This project targets Pydantic v2. A notable change in Pydantic v2 is that export methods were simplified and some previously supported keyword arguments were removed from convenience helpers like `model_dump_json()`.

Specifically, `model_dump_json(..., ensure_ascii=...)` is no longer supported. If you need control over JSON encoding options (for example to preserve non-ASCII characters), use `model_dump()` to get a plain Python dict and then call `json.dumps(...)` with the options you need:

```python
import json

# hc is a HistoriaClinica instance
data = json.dumps(hc.model_dump(), indent=2, ensure_ascii=False)
```

The app centralizes this behavior in `historia_as_json(hc)` which returns a JSON string with `ensure_ascii=False`.

## Running tests locally

1. Create and activate a virtual environment (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install development dependencies:

```powershell
pip install -r requirements-dev.txt
pip install pydantic pandas streamlit
```

3. Run tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## CI

A GitHub Actions workflow is included at `.github/workflows/python-tests.yml` that installs dependencies and runs `pytest` on push and pull_request to `main`/`master`.
