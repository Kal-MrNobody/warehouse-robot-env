from typing import Optional, List, Dict, Any
from pydantic import Field, ConfigDict
from openenv.core.env_server import Action, Observation, State


class WarehouseAction(Action):
    model_config = ConfigDict(extra="allow", validate_assignment=True, arbitrary_types_allowed=True)
    action: str = ""


class RobotStatus:
    """Lightweight helper used only in test scripts — not part of the server API."""
    def __init__(self, robot_id=0, position=(0, 0), carrying=None, battery=100.0):
        self.robot_id = robot_id
        self.position = position
        self.carrying = carrying
        self.battery = battery


class OrderItem:
    """Tracks a single order line and whether it's been delivered."""
    def __init__(self, sku="", deliver_to="", priority=False, done=False):
        self.sku = sku
        self.deliver_to = deliver_to
        self.priority = priority
        self.done = done


class WarehouseObservation(Observation):
    """Everything the agent can see after each step."""
    model_config = ConfigDict(extra="allow", validate_assignment=True, arbitrary_types_allowed=True)

    grid_text: str = ""
    robots: List[Dict[str, Any]] = Field(default_factory=list)
    current_order: List[Dict[str, Any]] = Field(default_factory=list)
    items_remaining: int = 0
    steps_taken: int = 0
    max_steps: int = 25
    cumulative_penalty: float = 0.0
    done_reason: Optional[str] = None
    task_id: str = "task1_easy"
    grader_score: float = 0.0


class WarehouseState(State):
    """Internal episode state — not exposed directly to the agent."""
    task_id: str = "task1_easy"
    total_reward: float = 0.0
    items_delivered: int = 0
    collisions: int = 0
    wrong_picks: int = 0
    grader_score: float = 0.0
    battery_deaths: int = 0
