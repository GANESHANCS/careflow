#!/bin/bash
set -e

echo "[CAREFLOW] Starting CAREFlow production runtime entrypoint..."

# Execute Alembic migrations if in production or explicitly requested
if [ "$ENVIRONMENT" = "production" ] || [ "$APPLY_MIGRATIONS" = "true" ]; then
    echo "[CAREFLOW] Applying database migrations (alembic upgrade head)..."
    alembic upgrade head
    echo "[CAREFLOW] Migrations applied successfully."
fi

# Execute main process (default: uvicorn)
echo "[CAREFLOW] Launching application process: $@"
exec "$@"
