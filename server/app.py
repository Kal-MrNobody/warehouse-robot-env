from openenv.core.env_server import create_app

try:
    from .environment import WarehouseEnvironment
    from ..models import WarehouseAction, WarehouseObservation
except ImportError:
    from server.environment import WarehouseEnvironment
    from models import WarehouseAction, WarehouseObservation

# create_app registers: /health /reset /step /state /schema /metadata /ws /mcp
app = create_app(
    WarehouseEnvironment,
    WarehouseAction,
    WarehouseObservation,
    env_name="warehouse-robot-env",
    max_concurrent_envs=10,
)


@app.get("/")
def root():
    """Root endpoint — confirms the server is alive."""
    return {
        "env": "warehouse-robot-env",
        "version": "0.1.0",
        "status": "running",
        "tasks": ["task1_easy", "task2_medium", "task3_hard"],
        "endpoints": ["/health", "/reset", "/step", "/state", "/schema", "/docs"],
    }


@app.get("/state")
def state_fallback():
    """
    Fallback state endpoint for stateless HTTP callers.
    Full state is available per-session via the WebSocket (/ws) interface.
    """
    return {
        "episode_id": None,
        "step_count": 0,
        "note": "Use WebSocket /ws for session-persistent state.",
    }
