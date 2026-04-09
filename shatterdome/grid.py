from typing import Dict, List, Optional, Tuple
import copy

try:
    from ..models import OrderLoad
    from .robot import RobotAgent
except ImportError:
    from models import OrderLoad
    from shatterdome.robot import RobotAgent

class ShatterdomeGrid:
    """
    Holds the entire simulation state of the Shatterdome Logistics Center: 
    the base grid, Robots, Packages, Drop Zones, orders, and task config.
    """

    def __init__(
        self,
        grid: List[List[str]],
        robots: Dict[int, RobotAgent],
        items: Dict[Tuple[int, int], str],
        dropzones: Dict[Tuple[int, int], str],
        orders: List[OrderLoad],
        max_steps: int,
        battery_drain: float,
        task_id: str,
    ):
        self.grid = grid
        self.robots = robots
        self.items = items
        self.dropzones = dropzones
        self.orders = orders
        self.max_steps = max_steps
        self.battery_drain = battery_drain
        self.task_id = task_id
        
        self.steps_taken = 0
        self.cumulative_stress = 0.0
        self.episode_history: List[dict] = []

    @classmethod
    def from_task(cls, task_id: str, seed: int = 42) -> "ShatterdomeGrid":
        if task_id == "task1_easy":
            return cls._create_task1()
        elif task_id == "task2_medium":
            return cls._create_task2()
        elif task_id == "task3_hard":
            return cls._create_task3()
        else:
            raise ValueError(f"Unknown task_id: {task_id}. "
                             f"Valid: task1_easy, task2_medium, task3_hard")

    @classmethod
    def _create_task1(cls) -> "ShatterdomeGrid":
        grid = [
            ['W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W'],
            ['W', '.', '.', '.', '.', '.', '.', '.', '.', 'W'],
            ['W', '.', '.', '.', '.', '.', '.', '.', '.', 'W'],
            ['W', '.', '.', '.', '.', '.', '.', '.', '.', 'W'],
            ['W', '.', '.', '.', '.', '.', '.', '.', '.', 'W'],
            ['W', '.', '.', '.', '.', '.', '.', '.', '.', 'W'],
            ['W', '.', '.', '.', '.', '.', '.', '.', '.', 'W'],
            ['W', '.', '.', '.', '.', '.', '.', '.', '.', 'W'],
            ['W', '.', '.', '.', '.', '.', '.', 'B', '.', 'W'],
            ['W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W'],
        ]
        robots = {0: RobotAgent(robot_id=0, position=(4, 4))}
        items = {(2, 2): "PKG-01"}
        dropzones = {(2, 7): "ZONE-A"}
        orders = [OrderLoad(package_id="PKG-01", dropzone="ZONE-A")]
        return cls(
            grid=grid, robots=robots, items=items, dropzones=dropzones,
            orders=orders, max_steps=25, battery_drain=0.0, task_id="task1_easy",
        )

    @classmethod
    def _create_task2(cls) -> "ShatterdomeGrid":
        grid = [
            ['W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W'],
            ['W', '.', '.', '.', 'W', '.', '.', '.', '.', 'W'],
            ['W', '.', 'W', '.', 'W', '.', '.', '.', '.', 'W'],
            ['W', '.', '.', '.', '.', '.', '.', '.', '.', 'W'],
            ['W', '.', '.', 'W', '.', '.', '.', '.', '.', 'W'],
            ['W', '.', '.', 'W', '.', '.', '.', '.', '.', 'W'],
            ['W', '.', '.', '.', '.', '.', '.', '.', '.', 'W'],
            ['W', '.', '.', '.', '.', '.', '.', '.', '.', 'W'],
            ['W', '.', '.', '.', '.', '.', '.', 'B', '.', 'W'],
            ['W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W'],
        ]
        robots = {0: RobotAgent(robot_id=0, position=(5, 1))}
        items = {(1, 2): "PKG-01", (4, 5): "PKG-02", (7, 2): "PKG-03"}
        dropzones = {(1, 7): "ZONE-A", (5, 8): "ZONE-B", (8, 7): "ZONE-C"}
        orders = [
            OrderLoad(package_id="PKG-01", dropzone="ZONE-A"),
            OrderLoad(package_id="PKG-02", dropzone="ZONE-B"),
            OrderLoad(package_id="PKG-03", dropzone="ZONE-C"),
        ]
        return cls(
            grid=grid, robots=robots, items=items, dropzones=dropzones,
            orders=orders, max_steps=60, battery_drain=2.0, task_id="task2_medium",
        )

    @classmethod
    def _create_task3(cls) -> "ShatterdomeGrid":
        grid = [
            ['W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W'],
            ['W', '.', '.', '.', '.', '.', '.', '.', '.', 'W'],
            ['W', '.', 'W', '.', 'W', '.', '.', '.', '.', 'W'],
            ['W', '.', '.', '.', '.', '.', '.', '.', '.', 'W'],
            ['W', '.', 'W', '.', 'W', '.', '.', '.', '.', 'W'],
            ['W', '.', '.', '.', '.', '.', '.', '.', '.', 'W'],
            ['W', '.', '.', '.', '.', '.', '.', '.', '.', 'W'],
            ['W', '.', 'W', '.', 'W', '.', 'W', '.', '.', 'W'],
            ['W', '.', '.', '.', '.', '.', '.', 'B', '.', 'W'],
            ['W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W'],
        ]
        robots = {
            0: RobotAgent(robot_id=0, position=(1, 1)),
            1: RobotAgent(robot_id=1, position=(8, 1)),
        }
        items = {
            (1, 3): "PKG-01", (3, 5): "PKG-02",
            (6, 2): "PKG-03", (8, 5): "PKG-04",
        }
        dropzones = {
            (1, 7): "ZONE-A", (3, 7): "ZONE-B",
            (6, 7): "ZONE-C", (8, 7): "ZONE-D",
        }
        orders = [
            OrderLoad(package_id="PKG-01", dropzone="ZONE-A", priority=True),
            OrderLoad(package_id="PKG-02", dropzone="ZONE-B", priority=True),
            OrderLoad(package_id="PKG-03", dropzone="ZONE-C", priority=False),
            OrderLoad(package_id="PKG-04", dropzone="ZONE-D", priority=False),
        ]
        return cls(
            grid=grid, robots=robots, items=items, dropzones=dropzones,
            orders=orders, max_steps=100, battery_drain=1.5, task_id="task3_hard",
        )

    def is_wall(self, row: int, col: int) -> bool:
        if row < 0 or row >= len(self.grid) or col < 0 or col >= len(self.grid[0]):
            return True
        return self.grid[row][col] == 'W'

    def is_battery_charger(self, row: int, col: int) -> bool:
        if row < 0 or row >= len(self.grid) or col < 0 or col >= len(self.grid[0]):
            return False
        return self.grid[row][col] == 'B'

    def is_occupied_by_other_robot(self, position: Tuple[int, int], robot_id: int) -> bool:
        for rid, robot in self.robots.items():
            if rid != robot_id and robot.position == position:
                return True
        return False

    def all_orders_complete(self) -> bool:
        return all(o.done for o in self.orders)

    def packages_remaining_count(self) -> int:
        return sum(1 for o in self.orders if not o.done)

    def packages_secured_count(self) -> int:
        return sum(1 for o in self.orders if o.done)

    def is_item_in_orders(self, item_id: str) -> bool:
        return any(o.package_id == item_id and not o.done for o in self.orders)

    def get_order(self, item_id: str) -> Optional[OrderLoad]:
        for o in self.orders:
            if o.package_id == item_id and not o.done:
                return o
        return None

    def get_dropzone_for_item(self, item_id: str) -> Optional[str]:
        for o in self.orders:
            if o.package_id == item_id and not o.done:
                return o.dropzone
        return None

    def get_dropzone_name_at(self, position: Tuple[int, int]) -> Optional[str]:
        return self.dropzones.get(position)

    def get_item_at(self, position: Tuple[int, int]) -> Optional[str]:
        return self.items.get(position)

    def remove_item(self, position: Tuple[int, int]) -> Optional[str]:
        return self.items.pop(position, None)

    def get_current_target(self, robot_id: int) -> Optional[Tuple[int, int]]:
        """
        Determine the next target position for a robot for reward shaping.
        """
        robot = self.robots.get(robot_id)
        if robot is None:
            return None

        if robot.is_carrying():
            item_id = robot.carrying
            expected_zone = self.get_dropzone_for_item(item_id)
            if expected_zone:
                for pos, zone_name in self.dropzones.items():
                    if zone_name == expected_zone:
                        return pos
            if self.dropzones: # fallback
                return next(iter(self.dropzones.keys()))
            return None

        best_pos = None
        best_dist = float('inf')
        rr, rc = robot.position
        for o in self.orders:
            if not o.done:
                for pos, i_id in self.items.items():
                    if i_id == o.package_id:
                        dist = abs(pos[0] - rr) + abs(pos[1] - rc)
                        if dist < best_dist:
                            best_dist = dist
                            best_pos = pos
                        break
        return best_pos

    def manhattan_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
