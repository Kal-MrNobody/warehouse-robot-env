from openenv.core.env_client import EnvClient, StepResult
from openenv.core.env_server import State

try:
    from .models import ShatterdomeAction, ShatterdomeObservation, ShatterdomeState
except ImportError:
    from models import ShatterdomeAction, ShatterdomeObservation, ShatterdomeState

class ShatterdomeClient(EnvClient[ShatterdomeAction, ShatterdomeObservation, State]):
    """
    WebSocket client for the Shatterdome environment.
    """
    def _step_payload(self, action: ShatterdomeAction) -> dict:
        return {"action": action.action}

    def _parse_result(self, payload: dict) -> StepResult[ShatterdomeObservation]:
        obs_data = payload.get("observation", {})
        top_reward = payload.get("reward")
        top_done = payload.get("done", False)
        
        obs_data["reward"] = top_reward
        obs_data["done"] = top_done
        obs = ShatterdomeObservation(**obs_data)
        return StepResult(observation=obs, reward=top_reward, done=top_done)

    def _parse_state(self, payload: dict) -> ShatterdomeState:
        return ShatterdomeState(**payload)
