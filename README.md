# Project Gappy

Regulatory Gap Analysis System for HKMA compliance.

## Overview

Project Gappy is a high-accuracy AI-powered system designed to perform gap analysis between HKMA regulations and internal banking SOPs.

**Key Features**
- Real PDF ingestion using PyMuPDF
- Structured requirement extraction
- Evidence-anchored gap analysis
- Enforced two-person review workflow (Compliance Officer → Compliance Supervisor)
- Minimalist, professional web interface

## Tech Stack

- **Backend**: FastAPI + SQLModel + SQLite (prototype)
- **LLM**: LiteLLM abstraction layer
- **Frontend**: Minimalist web portal (Jinja2 + Tailwind)
- **Task Queue**: Celery + Redis (ready)
- **Vector Store**: PGVector (ready for production)

## Quick Start (Local)

```bash
pip install -e .
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

Access:
- Dashboard: http://localhost:8080/dashboard
- Upload: http://localhost:8080/upload
- Run Analysis: http://localhost:8080/run-analysis
- Report: http://localhost:8080/report

## Docker

```bash
docker-compose up --build
```

## Zeabur Deployment

1. Push this repository to GitHub
2. Create a new service in Zeabur from the GitHub repo
3. Zeabur will auto-detect the `Dockerfile`
4. Set port to `8080`
5. Deploy

## Workflow

1. Upload HKMA regulations and internal SOPs
2. Run gap analysis
3. Compliance Officer reviews findings
4. Compliance Supervisor performs final review

## License

Internal use only.