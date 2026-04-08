from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class RobotAgent:
    """
    Represents a single robot in the warehouse.
    Tracks position, battery level, and cargo state.
    """
    robot_id: int = 0
    position: tuple = (0, 0)
    battery: float = 100.0
    carrying: Optional[str] = None  # SKU string or None

    def move(self, direction: str) -> tuple:
        """
        Compute the new position based on direction.
        Does NOT modify self.position — caller decides if move is valid.
        Returns the candidate (row, col) position.

        Coordinate system:
          move_north → row - 1
          move_south → row + 1
          move_west  → col - 1
          move_east  → col + 1
        """
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
        """
        Drain battery by amount. Returns True if battery reached 0.
        Battery is clamped to 0.0 minimum.
        """
        if amount <= 0:
            return False
        self.battery = max(0.0, self.battery - amount)
        return self.battery <= 0.0

    def charge_battery(self, amount: float = 30.0) -> None:
        """
        Charge battery by amount, capped at 100.0.
        """
        self.battery = min(100.0, self.battery + amount)

    def pick_up(self, sku: str) -> None:
        """
        Set carrying to the given SKU string.
        """
        self.carrying = sku

    def drop_item(self) -> Optional[str]:
        """
        Drop the currently carried item. Returns the SKU that was dropped,
        or None if not carrying anything.
        """
        sku = self.carrying
        self.carrying = None
        return sku

    def is_carrying(self) -> bool:
        """Check if robot is currently carrying an item."""
        return self.carrying is not None

    def to_dict(self) -> Dict[str, Any]:
        """
        Returns a JSON-serializable dict for inclusion in observations.
        """
        return {
            "robot_id": self.robot_id,
            "position": list(self.position),
            "battery": round(self.battery, 1),
            "carrying": self.carrying,
        }
