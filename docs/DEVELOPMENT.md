# CAREFlow Development Guide

## Environment Requirements
- **Python**: Python 3.12.x (Verified with Python 3.12.7)
- **Node.js**: Node 24+ / npm 11+
- **Database**: PostgreSQL (or local SQLite adapter for testing)

## Backend Operations
```bash
# Activate virtual environment
.\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run pytest suite
pytest

# Start Uvicorn development server
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

## Frontend Operations
```bash
cd frontend

# Install dependencies
npm install

# Run Vite dev server
npm run dev

# Run production build check
npm run build
```

## Testing Protocol
Before committing code:
1. Run backend tests: `pytest`
2. Run frontend build verification: `cd frontend && npm run build`
3. Verify git status to ensure no secrets or temporary caches are staged.
