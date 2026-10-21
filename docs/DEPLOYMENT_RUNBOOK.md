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
