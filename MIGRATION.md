# Database Migration Guide: SQLite → PostgreSQL + PGVector

## Overview

Project Gappy is designed to support both SQLite (for local development) and PostgreSQL + PGVector (for production).

## Prerequisites

- PostgreSQL 14+
- pgvector extension installed
- `psycopg2-binary` and `pgvector` Python packages (already in `pyproject.toml`)

## Step-by-step Migration

### 1. Export data from SQLite (if you have existing data)

```bash
cd /app/gappy
python -c "
from sqlmodel import create_engine, Session, select
from app.models import *
import json

engine = create_engine('sqlite:///./gappy.db')
with Session(engine) as session:
    # Export logic here
    print('Export your data manually or use a tool like pgloader')
"
```

### 2. Create PostgreSQL Database

```sql
CREATE DATABASE gappy;
CREATE EXTENSION IF NOT EXISTS vector;
```

### 3. Update Environment Variable

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/gappy"
```

### 4. Run Table Creation

```bash
python -c "
from app.core.database import create_db_and_tables
create_db_and_tables()
print('Tables created successfully')
"
```

### 5. (Optional) Use Alembic for Future Migrations

If you need versioned migrations later:

```bash
pip install alembic
alembic init alembic
# Configure alembic.ini and env.py
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

## Recommended Production Setup (Zeabur / Docker)

Use the following `DATABASE_URL`:

```
postgresql://<user>:<password>@<host>:<port>/<dbname>?sslmode=require
```

Make sure the `vector` extension is enabled in your PostgreSQL instance.

## Rollback

To go back to SQLite:

```bash
export DATABASE_URL="sqlite:///./gappy.db"
```

---

**Note**: The current implementation uses `SQLModel.metadata.create_all()`, which is sufficient for early development. For production, consider switching to Alembic.
