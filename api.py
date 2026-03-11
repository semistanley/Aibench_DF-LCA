"""FastAPI Backend Entry Point - Choose between simple and full API."""
# Option 1: Full API with async SQLAlchemy, JWT auth, etc.
from api.main import app as full_app

# Option 2: Simple API with SimpleEvaluator and SQLite
try:
    from simple_api import app as simple_app
    HAS_SIMPLE_API = True
except ImportError:
    HAS_SIMPLE_API = False

# Default to full API
app = full_app

__all__ = ["app", "full_app"]

# Usage:
#   Full API:  uvicorn api:app --host 0.0.0.0 --port 8000
#   Simple API: uvicorn simple_api:app --host 0.0.0.0 --port 8000
#
# Or import directly:
#   from api.main import app as full_app
#   from simple_api import app as simple_app
