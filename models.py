from pydantic import BaseModel, Field
from typing import List, Optional, Any
from openenv.core.env_server import Action, Observation, State

class ShatterdomeAction(Action):
    action: str = Field(
        ...,
        description="The exact command for the logistics robot. Valid commands: move_north, move_south, move_east, move_west, pickup_item, drop_item, recharge, done."
    )

class RobotStatus(BaseModel):
    robot_id: int
    position: list[int]
    battery_level: float
    carrying: Optional[str]

class OrderLoad(BaseModel):
    package_id: str
    dropzone: str
    done: bool = False
    priority: bool = False
    weight: str = "normal"
    fragile: bool = False
    deadline: Optional[int] = None
    failed: bool = False

class ShatterdomeObservation(Observation):
    hud_display: str = Field(description="ASCII representation of the facility logistics grid.")
    robots: List[dict] = Field(description="List of active robots and their status.")
    active_orders: List[dict] = Field(description="Pending e-commerce delivery objectives.")
    packages_remaining: int
    cycles_elapsed: int
    max_cycles: int
    cumulative_stress: float
    grader_score: float = 0.0
    reward: float = 0.0
    done: bool = False

class ShatterdomeState(State):
    task_id: str
    packages_secured: int = 0
    structural_damage: int = 0
    misfires: int = 0
    battery_deaths: int = 0
    packages_failed: int = 0
    grader_score: float = 0.0
    total_reward: float = 0.0
