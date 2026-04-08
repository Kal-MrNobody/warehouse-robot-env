from openenv.core.env_server import create_app

try:
    from .environment import WarehouseEnvironment
    from ..models import WarehouseAction, WarehouseObservation
except ImportError:
    from server.environment import WarehouseEnvironment
    from models import WarehouseAction, WarehouseObservation

# create_app already registers /health, /reset, /step, /state, /schema, /ws
app = create_app(
    WarehouseEnvironment,
    WarehouseAction,
    WarehouseObservation,
    env_name="warehouse-robot-env",
    max_concurrent_envs=10,
)

# Server listens on port 7860 (HuggingFace Spaces requirement)
# Start with: uvicorn server.app:app --host 0.0.0.0 --port 7860
