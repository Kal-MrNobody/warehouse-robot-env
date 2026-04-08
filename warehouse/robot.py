from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class RobotAgent:
    """A single robot on the warehouse grid."""
    robot_id: int = 0
    position: tuple = (0, 0)
    battery: float = 100.0
    carrying: Optional[str] = None  # SKU being carried, or None

    def move(self, direction: str) -> tuple:
        """Return the candidate position for a move — does NOT apply it yet."""
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

    def drain_battery(self, amount: float) -> bool:
        """Drain battery by amount. Returns True if battery just hit 0."""
        if amount <= 0:
            return False
        self.battery = max(0.0, self.battery - amount)
        return self.battery <= 0.0

    def charge_battery(self, amount: float = 30.0) -> None:
        self.battery = min(100.0, self.battery + amount)

    def pick_up(self, sku: str) -> None:
        self.carrying = sku

    def drop_item(self) -> Optional[str]:
        sku = self.carrying
        self.carrying = None
        return sku

    def is_carrying(self) -> bool:
        return self.carrying is not None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "robot_id": self.robot_id,
            "position": list(self.position),
            "battery": round(self.battery, 1),
            "carrying": self.carrying,
        }
