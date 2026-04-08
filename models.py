from typing import Optional, List, Dict, Any
from pydantic import Field, ConfigDict
from openenv.core.env_server import Action, Observation, State

class ShatterdomeAction(Action):
    """The action spaces for controlling a Jaeger."""
    model_config = ConfigDict(extra="allow", validate_assignment=True, arbitrary_types_allowed=True)
    action: str = ""

class JaegerStatus:
    """Internal tracker for a deployed Jaeger."""
    def __init__(self, jaeger_id=0, position=(0, 0), carrying=None, reactor=100.0):
        self.jaeger_id = jaeger_id
        self.position = position
        self.carrying = carrying
        self.reactor = reactor

class CoreLoad:
    """Tracks a single plasma core load objective."""
    def __init__(self, core_id="", deploy_to="", priority=False, done=False):
        self.core_id = core_id
        self.deploy_to = deploy_to
        self.priority = priority
        self.done = done

class ShatterdomeObservation(Observation):
    """Data sent down from the Conn-Pod to the Ranger."""
    model_config = ConfigDict(extra="allow", validate_assignment=True, arbitrary_types_allowed=True)

    hud_display: str = ""
    jaegers: List[Dict[str, Any]] = Field(default_factory=list)
    active_directives: List[Dict[str, Any]] = Field(default_factory=list)
    cores_remaining: int = 0
    cycles_elapsed: int = 0
    max_cycles: int = 25
    cumulative_stress: float = 0.0
    drift_status: Optional[str] = None
    task_id: str = "task1_easy"
    grader_score: float = 0.0

class ShatterdomeState(State):
    """Deep neural handshake state — internal simulation."""
    task_id: str = "task1_easy"
    total_reward: float = 0.0
    cores_secured: int = 0
    structural_damage: int = 0
    misfires: int = 0
    grader_score: float = 0.0
    reactor_criticals: int = 0
