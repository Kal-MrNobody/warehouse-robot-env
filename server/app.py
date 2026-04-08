from openenv.core.env_server import create_app

try:
    from .environment import ShatterdomeEnvironment
    from ..models import ShatterdomeAction, ShatterdomeObservation
except ImportError:
    from server.environment import ShatterdomeEnvironment
    from models import ShatterdomeAction, ShatterdomeObservation

app = create_app(
    ShatterdomeEnvironment,
    ShatterdomeAction,
    ShatterdomeObservation,
    env_name="shatterdome-logistics-env",
    max_concurrent_envs=10,
)

@app.get("/")
def root():
    return {
        "env": "shatterdome-logistics-env",
        "version": "1.0.0",
        "status": "online",
        "directives": ["task1_easy", "task2_medium", "task3_hard"],
        "endpoints": ["/health", "/reset", "/step", "/state", "/schema", "/docs"],
    }

@app.get("/state")
def state_fallback():
    return {
        "episode_id": None,
        "step_count": 0,
        "note": "Use WebSocket /ws for session-persistent state.",
    }
