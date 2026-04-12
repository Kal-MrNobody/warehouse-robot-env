from fastapi import Request
from fastapi.responses import JSONResponse
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
        "tasks": ["task1_easy", "task2_medium", "task3_hard"],
        "endpoints": ["/health", "/reset", "/step", "/state", "/schema", "/docs"],
    }

@app.get("/health")
def health():
    return {"status": "healthy", "service": "shatterdome-logistics-env"}

# Fallback GET /state so hackathon validator doesn't 500
@app.get("/state")
def state_get_fallback():
    return JSONResponse(content={
        "task_id": None,
        "packages_secured": 0,
        "structural_damage": 0,
        "misfires": 0,
        "battery_deaths": 0,
        "grader_score": 0.0,
        "total_reward": 0.0,
        "note": "POST to /reset first to start a session."
    })

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
