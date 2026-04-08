from openenv.core.env_client import EnvClient, StepResult
from openenv.core.env_server import State

try:
    from .models import WarehouseAction, WarehouseObservation, WarehouseState
except ImportError:
    from models import WarehouseAction, WarehouseObservation, WarehouseState


class WarehouseEnv(EnvClient[WarehouseAction, WarehouseObservation, State]):
    """
    WebSocket client for the warehouse robot env.

    Usage:
        with WarehouseEnv(base_url="http://localhost:7860").sync() as env:
            result = env.reset(task_id="task1_easy", seed=42)
            result = env.step(WarehouseAction(action="move_north"))
    """

    def _step_payload(self, action: WarehouseAction) -> dict:
        return {"action": action.action}

    def _parse_result(self, payload: dict) -> StepResult[WarehouseObservation]:
        obs_data = payload.get("observation", {})
        top_reward = payload.get("reward")
        top_done = payload.get("done", False)
        obs_data["reward"] = top_reward
        obs_data["done"] = top_done
        obs = WarehouseObservation(**obs_data)
        return StepResult(observation=obs, reward=top_reward, done=top_done)

    def _parse_state(self, payload: dict) -> WarehouseState:
        return WarehouseState(**payload)
