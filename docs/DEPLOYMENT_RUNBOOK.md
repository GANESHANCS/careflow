# CAREFlow India — Production Deployment Runbook

## Overview
This runbook provides technical procedures for deploying, configuring, monitoring, and maintaining the **CAREFlow India** production healthcare analytics platform across containerized or bare-metal environments.

---

## 1. Prerequisites & System Requirements

### Hardware Sizing
| Node Role | Minimum Spec | Recommended Production Spec |
| :--- | :--- | :--- |
| **Backend & Ingestion Engine** | 2 vCPU, 4 GB RAM | 4 vCPU, 8–16 GB RAM |
| **PostgreSQL Database** | 2 vCPU, 4 GB RAM, 50 GB SSD | 4 vCPU, 16 GB RAM, 200+ GB SSD (RAID-1/RAID-10) |
| **Frontend Nginx Ingress** | 1 vCPU, 1 GB RAM | 2 vCPU, 2–4 GB RAM |

### Software Prerequisites
* **Operating System**: Linux (Ubuntu 22.04 LTS or Debian 12 recommended)
* **Docker Engine**: Docker 24.0+ & Docker Compose v2.20+
* **Python Runtime**: Python 3.12+ (if deploying without Docker)
* **Node.js**: Node 24+ / npm 11+ (for frontend compilation)
* **PostgreSQL Engine**: PostgreSQL 16+

---

## 2. Environment Variables & Secrets Management

CAREFlow requires distinct configuration in `production` mode, enforced strictly at startup by Pydantic Settings in `backend/app/core/config.py`.

### Required Production Environment Variables
| Variable | Description | Example / Constraint |
| :--- | :--- | :--- |
| `ENVIRONMENT` | Runtime mode | Must be strictly `"production"` |
| `DEBUG` | Verbose debug flag | Forced to `False` in production |
| `SECRET_KEY` | Cryptographic JWT signing key | **Mandatory**: Random hex string $\ge 32$ chars. Never commit to Git! |
| `DATABASE_URL` | SQLAlchemy PostgreSQL URI | `postgresql+psycopg://user:password@host:5432/dbname` (SQLite strictly forbidden) |
| `CORS_ORIGINS` | Permitted browser origins | JSON array of valid domains: `["https://careflow.gov.in"]` |
| `LOG_LEVEL` | Logging threshold | `"INFO"` or `"WARNING"` |
| `DB_POOL_SIZE` | Connection pool size | `10` to `20` |
| `DB_MAX_OVERFLOW` | Burst connection ceiling | `20` to `40` |
| `DB_POOL_RECYCLE` | Pool recycling interval | `1800` (seconds) |

### Generating a Secure Cryptographic Secret
Run the following Python one-liner to generate a cryptographically secure 64-character signing secret:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 3. Production Docker Compose Deployment

CAREFlow provides a multi-container stack orchestrated via `docker-compose.yml`:
1. **`careflow_postgres`**: PostgreSQL 16 Alpine container with healthchecks and persistent volume `postgres_data`.
2. **`careflow_backend`**: FastAPI Python 3.12-slim container running as non-root user `careflow`, with `scripts/entrypoint.sh` executing database migrations before uvicorn startup.
3. **`careflow_frontend`**: Nginx Alpine container serving optimized Vite static bundles with SPA routing fallback and reverse proxying `/api` requests to backend.

### Deployment Step-by-Step

#### Step 1: Clone Repository and Prepare Environment
```bash
git clone https://github.com/careflow-india/careflow.git /opt/careflow
cd /opt/careflow
cp .env.example .env
```

#### Step 2: Configure Production `.env`
Edit `.env` to supply production secrets:
```env
ENVIRONMENT=production
DEBUG=false
SECRET_KEY="<your_generated_64_char_secret_key>"
POSTGRES_USER=careflow_prod_user
POSTGRES_PASSWORD="<strong_db_password>"
POSTGRES_DB=careflow_prod_db
DATABASE_URL=postgresql+psycopg://careflow_prod_user:<strong_db_password>@postgres:5432/careflow_prod_db
CORS_ORIGINS=["https://careflow.gov.in","http://localhost:80"]
```

#### Step 3: Validate Compose Configuration
Verify environment interpolation without deploying:
```bash
docker compose config
```

#### Step 4: Build and Launch Containers
```bash
docker compose build --no-cache
docker compose up -d
```

#### Step 5: Verify Service Health
```bash
docker compose ps
docker compose logs -f backend
```
Verify that:
1. `postgres` reaches `healthy` status.
2. `backend` entrypoint executes `alembic upgrade head` and outputs `[CAREFLOW] Migrations applied successfully.`
3. `backend` container passes healthcheck (`curl -f http://localhost:8000/api/health`).
4. `frontend` is listening on port 80 and proxying `/api` calls.

---

## 4. Reverse Proxy & HTTPS / TLS Termination

In production, frontend traffic must terminate through an edge reverse proxy (e.g. Cloudflare, AWS ALB, Nginx, or Caddy) with TLS 1.3 encryption.

### Production Nginx TLS Host Configuration Template
```nginx
server {
    listen 80;
    server_name careflow.gov.in;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name careflow.gov.in;

    ssl_certificate /etc/letsencrypt/live/careflow.gov.in/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/careflow.gov.in/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Forward to CAREFlow frontend container
    location / {
        proxy_pass http://127.0.0.1:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

---

## 5. Database Provisioning & Admin Bootstrapping

In production mode (`ENVIRONMENT="production"`), automatic schema generation and development account seeding are strictly disabled. The database is initialized deterministically via Alembic migrations, followed by explicit administrator bootstrapping.

### 5.1 Initialize Schema via Migrations
```bash
docker compose exec backend alembic upgrade head
```

### 5.2 Seed Core Indicator Registry
```bash
docker compose exec backend python scripts/seed_indicators.py
```

### 5.3 Bootstrap Initial Production Administrator
CAREFlow provides an explicit, secure CLI command (`scripts/bootstrap_admin.py`) for creating the initial production administrator. To prevent accidental lockouts or predictable credentials, credentials must be supplied via environment variables or hidden interactive prompts.

**Password Security Policy**:
- Minimum 12 characters
- At least one uppercase letter (`A-Z`)
- At least one lowercase letter (`a-z`)
- At least one numeric digit (`0-9`)
- At least one special symbol (e.g. `!@#$%^&*`)

#### Method A: Interactive Prompt (Recommended for Operators)
Execute the script interactively inside the running backend container. Passwords are entered via hidden prompts and never echoed to the terminal or saved in shell history:
```bash
docker compose exec -it backend python scripts/bootstrap_admin.py --username admin --email admin@careflow.gov.in
```

#### Method B: Automated Deployment (Environment Variables)
In continuous deployment or automated provisioning pipelines, pass credentials via ephemeral environment variables:
```bash
docker compose exec \
  -e ADMIN_USERNAME="admin" \
  -e ADMIN_PASSWORD="<your_secure_password_here>" \
  -e ADMIN_EMAIL="admin@careflow.gov.in" \
  backend python scripts/bootstrap_admin.py
```

### 5.4 Verification & Idempotency Guarantees
- **Idempotency**: Running `scripts/bootstrap_admin.py` after an administrator account already exists will exit cleanly with status code `0` (`[NOTICE] Bootstrap skipped: Administrator account already exists. No modifications made.`). Existing passwords are never overwritten or reset.
- **Login Verification**: Verify credentials against the authentication endpoint:
  ```bash
  curl -s -X POST http://localhost:8000/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username": "admin", "password": "<your_secure_password_here>"}' \
    | grep -o '"access_token":'
  ```
  A successful response returns a signed JWT `access_token` and confirmed `ADMIN` role.

---

## 6. Persistence & Backup Strategy

### Persistent Volumes
* **PostgreSQL Data**: `postgres_data` volume (`/var/lib/postgresql/data`)
* **Uploaded Spreadsheets**: `uploads_data` volume (`/app/data/uploads`)

### Database Backup Procedure
Execute daily automated pg_dump backups:
```bash
docker compose exec -T postgres pg_dump -U careflow_prod_user -d careflow_prod_db -F c -b -v -f /tmp/backup.dump
docker cp careflow_postgres:/tmp/backup.dump /var/backups/careflow/careflow_$(date +%Y%m%d_%H%M%S).dump
```

### Database Restore Procedure
```bash
docker compose exec -T postgres pg_restore -U careflow_prod_user -d careflow_prod_db -v -c /tmp/backup.dump
```

---

## 7. Rollback Procedures

If a deployment failure or unexpected defect is detected in a new release:
1. Revert to previous Docker image or Git release tag:
   ```bash
   git checkout tags/v1.0.0
   docker compose build
   docker compose up -d
   ```
2. If database schema downgrade is required:
   ```bash
   docker compose exec backend alembic downgrade -1
   ```
3. Confirm system status:
   ```bash
   curl -I https://careflow.gov.in/api/health
   ```

---

## 8. Database Architecture & Canonical Path Selection

### Canonical Development Database Path
* **Canonical Path**: `D:\careflow\careflow_dev.db` (located at workspace root).
* **Connection String**: `sqlite:///./careflow_dev.db`.
* **Path Resolution Rationale**: In Python SQLite URIs, `./careflow_dev.db` resolves relative to the current working directory of the application process. When launched from the repository root (`D:\careflow`), it directly binds to `D:\careflow\careflow_dev.db`.
* **Path Audit Note**: The `data/` directory contains subdirectories for `raw/`, `interim/`, `processed/`, `uploads/`, and `backups/`. Standalone SQLite `.db` files should not be manually created inside `data/` without explicit configuration to prevent path confusion.

### Production PostgreSQL Architecture
In production (`ENVIRONMENT="production"`), SQLite is strictly prohibited by configuration validation (`validate_environment_and_security`). All persistent storage must use a production PostgreSQL cluster running with connection pooling parameters:
* `DB_POOL_SIZE`: 10–20 connections
* `DB_MAX_OVERFLOW`: 20–40 connections
* `DB_POOL_RECYCLE`: 1800 seconds (30 minutes)
* Connection driver: Psycopg v3 (`postgresql+psycopg://`)

---

## 9. Backup Verification & Integrity Audit Procedures

Before any persistent data transformation or database migration, an atomic backup must be captured and verified.

### SQLite Online Backup Procedure (Development / Staging)
To avoid database locks during live reads, utilize SQLite's native streaming backup API:
```bash
python -c "
import sqlite3, os
src = 'careflow_dev.db'
dst = 'data/backups/careflow_dev_backup_' + os.popen('date /t').read().strip().replace('/', '') + '.db'
src_conn = sqlite3.connect(f'file:{src}?mode=ro', uri=True)
dst_conn = sqlite3.connect(dst)
src_conn.backup(dst_conn)
dst_conn.close(); src_conn.close()
ver_conn = sqlite3.connect(f'file:{dst}?mode=ro', uri=True)
print('Integrity:', ver_conn.execute('PRAGMA integrity_check;').fetchall())
print('District Observations:', ver_conn.execute('SELECT COUNT(*) FROM district_observations;').fetchone()[0])
ver_conn.close()
"
```

### PostgreSQL Verification Procedure (Production)
```bash
# 1. Capture snapshot
pg_dump -U careflow_prod_user -d careflow_prod_db -F c -b -v -f /var/backups/careflow/careflow_pre_migration.dump

# 2. Verify dump integrity
pg_restore -l /var/backups/careflow/careflow_pre_migration.dump > /dev/null
echo \"Backup catalog verification exit code: $?\"
```

---

## 10. HMIS Import Recovery & Operational Troubleshooting

### Ingestion Worker Stalls & Crash Recovery
* **Stale Timeout**: The background worker polls for jobs in status `PROCESSING` whose `heartbeat_at` has not been updated within `WORKER_STALE_TIMEOUT_SECONDS` (default: 300 seconds).
* **Automatic Re-queueing**: Stale jobs are automatically cleaned up and re-queued up to `WORKER_MAX_RETRIES` (default: 3).
* **Manual Job Re-queue**: Administrators can manually retry failed or stalled jobs via:
  ```bash
  curl -X POST http://localhost:8000/api/imports/{job_code}/retry \
    -H \"Authorization: Bearer <ADMIN_JWT_TOKEN>\"
  ```

### Rollback Dependency Conflict (HTTP 409)
* When an administrator requests a rollback of an import job (`POST /api/imports/{job_code}/rollback`), CAREFlow verifies whether subsequent completed imports modified the same observation rows.
* If a dependent subsequent job exists, the rollback is rejected with `HTTP 409 Conflict` to prevent overwriting more recent valid data.
* **Resolution**: Roll back the subsequent dependent job first, and then roll back the target historical job.

---

## 11. Local Clean-Terminal Startup & Demonstration Runbook

### Environment Requirements
* **Python**: Version 3.12+ (local runtime: Python 3.12.7 in `d:\careflow\.venv`)
* **Node.js**: Version 24+ / npm 11+ (local runtime: Node 24 with Vite 8 & React 19)
* **Database**: `careflow_dev.db` (SQLite 3.40+, 213 MB, pre-populated with 175,872 official Tamil Nadu FY 2015–16 HMIS records and synthetic facility fixtures)

### Terminal 1: Backend API Server Startup
Open a clean PowerShell / terminal in `D:\careflow`:
```powershell
# 1. Activate Python virtual environment
.\.venv\Scripts\Activate.ps1

# 2. Verify database migration head status (expected: d3e4f5a6b7c8 head)
python -m alembic current

# 3. Verify database integrity
python -c "import sqlite3; con = sqlite3.connect('careflow_dev.db'); print(con.execute('PRAGMA integrity_check;').fetchall()); con.close()"

# 4. Launch FastAPI server with live reload and background worker
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
* Backend URL: `http://127.0.0.1:8000`
* Interactive API Documentation: `http://127.0.0.1:8000/docs`
* High-frequency Liveness Probe: `http://127.0.0.1:8000/api/healthz`
* Deep Readiness Probe: `http://127.0.0.1:8000/api/readyz`

### Terminal 2: React Frontend Startup
Open a second clean terminal in `D:\careflow\frontend`:
```powershell
cd D:\careflow\frontend

# 1. Verify dependencies and run static lint
npm run lint

# 2. Launch Vite development server
npm run dev
```
* Frontend Application URL: `http://localhost:5173`

### Pre-Seeded Demonstration Accounts (Development Mode Only)
| Username | Password | Role | Permissions |
| :--- | :--- | :--- | :--- |
| `admin` | `careflow_admin_dev_2026` | `ADMIN` | Unrestricted: HMIS uploads, rollbacks, directory watcher scan, anomaly reviews, facility management |
| `analyst` | `careflow_analyst_dev_2026` | `ANALYST` | Operational: HMIS uploads, anomaly review status transitions, analytics exports |
| `viewer` | `careflow_viewer_dev_2026` | `VIEWER` | Read-only: Workspace analytics, observation tables, streaming CSV downloads |

### Safe Local Recovery Procedure from Startup Failures
If ordinary startup failures occur (e.g. port collision or stale background process), **NEVER delete or reset `careflow_dev.db`**. Follow this safe recovery sequence:
1. **Detect Stale Listening Processes**:
   ```powershell
   Get-NetTCPConnection -LocalPort 8000,5173 -ErrorAction SilentlyContinue | Select-Object LocalPort,OwningProcess
   ```
2. **Gracefully Terminate Only Stale PIDs**:
   ```powershell
   Stop-Process -Id <PID> -Force
   ```
3. **Handle SQLite Transient Lock Files**:
   Ensure no abandoned `-wal` or `-shm` write locks exist, and recheck database integrity:
   ```powershell
   python -c "import sqlite3; con = sqlite3.connect('careflow_dev.db'); print(con.execute('PRAGMA integrity_check;').fetchall()); con.close()"
   ```
4. **Restart Cleanly**: Relaunch backend and frontend from fresh terminal windows.

### Clinical Data Architecture & Stream Isolation
When demonstrating the platform to evaluators, explicitly highlight the structural isolation between data tiers:
1. **Official State HMIS Data Tier (`district_observations`)**:
   * **Scope**: 175,872 consolidated administrative records across all 32 revenue districts of Tamil Nadu for FY 2015–16.
   * **Indicators**: 261 official MoHFW parameter lines (S.No. 1.1 through 14.12.1).
   * **Integrity**: Missing observations are strictly differentiated from genuine zero reports (`value_type="ZERO"` vs `value_type="MISSING"`). Non-additive stock metrics (such as bed capacities) are explicitly labeled and prevented from summation.
2. **Facility Demonstration Tier (`facilities`, `observations`, `forecasts`)**:
   * **Scope**: 9 demonstration health facilities, 362 observations, 108 model forecasts.
   * **Labeling**: All facility fixtures are explicitly prefixed with `Synthetic` / `SYNTHETIC` to eliminate any ambiguity.
