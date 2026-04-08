from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class JaegerAgent:
    """A PPDC Jaeger deployed in the Shatterdome."""
    jaeger_id: int = 0
    position: tuple = (0, 0)
    reactor_power: float = 100.0
    carrying: Optional[str] = None  # Plasma Core being carried

    def maneuver(self, direction: str) -> tuple:
        """Calculate trajectory for next maneuver."""
        r, c = self.position
        if direction == "move_north":
            return (r - 1, c)
        elif direction == "move_south":
            return (r + 1, c)
        elif direction == "move_west":
            return (r, c - 1)
        elif direction == "move_east":
            return (r, c + 1)
        return self.position

    def drain_reactor(self, amount: float) -> bool:
        """Decrease reactor power. Returns True if critical failure (0)."""
        if amount <= 0:
            return False
        self.reactor_power = max(0.0, self.reactor_power - amount)
        return self.reactor_power <= 0.0

    def recharge_reactor(self, amount: float = 30.0) -> None:
        self.reactor_power = min(100.0, self.reactor_power + amount)

    def load_core(self, core_id: str) -> None:
        self.carrying = core_id

    def deploy_core(self) -> Optional[str]:
        core_id = self.carrying
        self.carrying = None
        return core_id

    def is_carrying(self) -> bool:
        return self.carrying is not None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "jaeger_id": self.jaeger_id,
            "position": list(self.position),
            "reactor_power": round(self.reactor_power, 1),
            "carrying": self.carrying,
        }
