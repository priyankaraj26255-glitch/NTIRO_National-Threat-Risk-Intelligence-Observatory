
# NTIRO
National Threat & Risk Intelligence Observatory

## Overview
NTIRO is a public-data intelligence and decision-support platform
designed to help analyze threats and risks using transparent,
evidence-based indicators.

## Current Features
- FastAPI application
- Root endpoint (`/`)
- Health endpoint (`/health`)
- Automated API tests

## Technology Stack
- Python
- FastAPI
- Uvicorn
- Pytest
- HTTPX

## Run Locally
Activate the project's virtual environment, then run:

```powershell
python -m uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` to explore the API.

## Run Tests
```powershell
python -m pytest -v
```
