# CAREFlow System Architecture

## Architecture Overview

```
                                    +-----------------------+
                                    |    React / TS / Vite  |
                                    |  Frontend Dashboard   |
                                    +-----------+-----------+
                                                |
                                          HTTP / REST
                                                v
                                    +-----------------------+
                                    |     FastAPI Engine    |
                                    | (app/api/endpoints/)  |
                                    +-----------+-----------+
                                                |
                                          Service Layer
                                    (app/services/*_service)|
                                                v
                                        Repository Layer
                                    (app/repositories/*_repo)
                                                |
                                          SQLAlchemy 2.0
                                                v
                                    +-----------------------+
                                    |  PostgreSQL / SQLite  |
                                    +-----------------------+
```

---

## 4-Tier Backend Layering Pattern

1. **API Router / Endpoints Layer (`backend/app/api/`)**:
   - Handles HTTP route registration, query parameter validation (via Pydantic schemas), and exception handling.
   - Database queries are **never** executed directly in route handlers.

2. **Service Layer (`backend/app/services/`)**:
   - Encapsulates business logic, data loaders, pipeline runners, and indicator seeders.

3. **Repository Layer (`backend/app/repositories/`)**:
   - Abstracts database queries, complex filters, joins, and pagination.

4. **Data Access Layer (`backend/app/db/`)**:
   - SQLAlchemy 2.0 ORM models (`backend/app/db/models/`), SessionLocal factory, and Alembic migrations.
