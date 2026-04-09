from typing import Tuple, Optional

class RobotAgent:
    """Represents a single automated logistics robot in the warehouse."""
    def __init__(self, robot_id: int, position: Tuple[int, int], max_battery: float = 100.0):
        self.robot_id = robot_id
        self.position = position
        self.battery_level = max_battery
        self.max_battery = max_battery
        self.carrying: Optional[str] = None

    def maneuver(self, command: str) -> Tuple[int, int]:
        row, col = self.position
        if command == "move_north":
            return (row - 1, col)
        elif command == "move_south":
            return (row + 1, col)
        elif command == "move_east":
            return (row, col + 1)
        elif command == "move_west":
            return (row, col - 1)
        return self.position

    def pickup_item(self, item_id: str):
        self.carrying = item_id

    def drop_item(self):
        self.carrying = None

    def drain_battery(self, amount: float) -> bool:
        """Returns True if battery is fully depleted."""
        self.battery_level = max(0.0, self.battery_level - amount)
        return self.battery_level <= 0

    def recharge_battery(self, amount: float = 20.0):
        self.battery_level = min(self.max_battery, self.battery_level + amount)

    def is_carrying(self) -> bool:
        return self.carrying is not None

    def to_dict(self) -> dict:
        return {
            "robot_id": self.robot_id,
            "position": list(self.position),
            "battery_level": self.battery_level,
            "carrying": self.carrying
        }
