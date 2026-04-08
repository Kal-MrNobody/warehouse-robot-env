from openenv.core.env_server import create_app

try:
    from .environment import WarehouseEnvironment
    from ..models import WarehouseAction, WarehouseObservation
except ImportError:
    from server.environment import WarehouseEnvironment
    from models import WarehouseAction, WarehouseObservation

# Pass CLASS not instance. create_app handles instantiation internally.
app = create_app(
    WarehouseEnvironment,
    WarehouseAction,
    WarehouseObservation,
    env_name="warehouse-robot-env",
    max_concurrent_envs=10,
)

# Required by hackathon: /health endpoint must return 200
from fastapi import FastAPI


@app.get("/health")
def health():
    return {"status": "healthy", "service": "warehouse-robot-env"}


# Server runs on port 7860 (HuggingFace Spaces requirement)
# Start with: uvicorn server.app:app --host 0.0.0.0 --port 7860
