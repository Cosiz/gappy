# Project Gappy

Regulatory Gap Analysis System for HKMA compliance.

## Overview

Project Gappy is a high-accuracy AI-powered system designed to perform gap analysis between HKMA regulations and internal banking SOPs.

## Quick Start (Local)

```bash
pip install -e .
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

## Docker

```bash
docker-compose up --build
```

## Zeabur Deployment

See [ZEABUR.md](./ZEABUR.md) for detailed deployment instructions.

## License

Internal use only.