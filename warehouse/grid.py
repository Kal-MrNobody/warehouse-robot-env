from typing import Dict, List, Optional, Tuple
import copy

try:
    from ..models import OrderItem
    from .robot import RobotAgent
except ImportError:
    from models import OrderItem
    from warehouse.robot import RobotAgent


class WarehouseGrid:
    """
    Holds the entire warehouse state: the base grid, robots, items,
    drop zones, orders, and task configuration.
    """

    def __init__(
        self,
        grid: List[List[str]],
        robots: Dict[int, RobotAgent],
        items: Dict[Tuple[int, int], str],
        dropzones: Dict[Tuple[int, int], str],
        order: List[OrderItem],
        max_steps: int,
        battery_drain: float,
        task_id: str,
    ):
        self.grid = grid
        self.robots = robots
        self.items = items
        self.dropzones = dropzones
        self.order = order
        self.max_steps = max_steps
        self.battery_drain = battery_drain
        self.task_id = task_id
        self.steps_taken = 0
        self.cumulative_penalty = 0.0
        self.episode_history: List[dict] = []

    @classmethod
    def from_task(cls, task_id: str, seed: int = 42) -> "WarehouseGrid":
        """
        Factory method to create a WarehouseGrid for a specific task.
        seed is accepted for API compliance but tasks are deterministic.
        """
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
    def _create_task1(cls) -> "WarehouseGrid":
        grid = [
            ['W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W'],
            ['W', '.', '.', '.', '.', '.', '.', '.', '.', 'W'],
            ['W', '.', '.', '.', '.', '.', '.', '.', '.', 'W'],
            ['W', '.', '.', '.', '.', '.', '.', '.', '.', 'W'],
            ['W', '.', '.', '.', '.', '.', '.', '.', '.', 'W'],
            ['W', '.', '.', '.', '.', '.', '.', '.', '.', 'W'],
            ['W', '.', '.', '.', '.', '.', '.', '.', '.', 'W'],
            ['W', '.', '.', '.', '.', '.', '.', '.', '.', 'W'],
            ['W', '.', '.', '.', '.', '.', '.', 'C', '.', 'W'],
            ['W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W'],
        ]
        robots = {0: RobotAgent(robot_id=0, position=(4, 4))}
        items = {(2, 2): "SKU-001"}
        dropzones = {(2, 7): "ZONE-A"}
        order = [OrderItem(sku="SKU-001", deliver_to="ZONE-A")]
        return cls(
            grid=grid, robots=robots, items=items, dropzones=dropzones,
            order=order, max_steps=25, battery_drain=0.0, task_id="task1_easy",
        )

    @classmethod
    def _create_task2(cls) -> "WarehouseGrid":
        grid = [
            ['W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W'],
            ['W', '.', '.', '.', 'W', '.', '.', '.', '.', 'W'],
            ['W', '.', 'W', '.', 'W', '.', '.', '.', '.', 'W'],
            ['W', '.', '.', '.', '.', '.', '.', '.', '.', 'W'],
            ['W', '.', '.', 'W', '.', '.', '.', '.', '.', 'W'],
            ['W', '.', '.', 'W', '.', '.', '.', '.', '.', 'W'],
            ['W', '.', '.', '.', '.', '.', '.', '.', '.', 'W'],
            ['W', '.', '.', '.', '.', '.', '.', '.', '.', 'W'],
            ['W', '.', '.', '.', '.', '.', '.', 'C', '.', 'W'],
            ['W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W'],
        ]
        robots = {0: RobotAgent(robot_id=0, position=(5, 1))}
        items = {(1, 2): "SKU-001", (4, 5): "SKU-002", (7, 2): "SKU-003"}
        dropzones = {(1, 7): "ZONE-A", (5, 8): "ZONE-B", (8, 7): "ZONE-C"}
        order = [
            OrderItem(sku="SKU-001", deliver_to="ZONE-A"),
            OrderItem(sku="SKU-002", deliver_to="ZONE-B"),
            OrderItem(sku="SKU-003", deliver_to="ZONE-C"),
        ]
        return cls(
            grid=grid, robots=robots, items=items, dropzones=dropzones,
            order=order, max_steps=60, battery_drain=2.0, task_id="task2_medium",
        )

    @classmethod
    def _create_task3(cls) -> "WarehouseGrid":
        grid = [
            ['W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W'],
            ['W', '.', '.', '.', '.', '.', '.', '.', '.', 'W'],
            ['W', '.', 'W', '.', 'W', '.', '.', '.', '.', 'W'],
            ['W', '.', '.', '.', '.', '.', '.', '.', '.', 'W'],
            ['W', '.', 'W', '.', 'W', '.', '.', '.', '.', 'W'],
            ['W', '.', '.', '.', '.', '.', '.', '.', '.', 'W'],
            ['W', '.', '.', '.', '.', '.', '.', '.', '.', 'W'],
            ['W', '.', 'W', '.', 'W', '.', 'W', '.', '.', 'W'],
            ['W', '.', '.', '.', '.', '.', '.', 'C', '.', 'W'],
            ['W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W'],
        ]
        robots = {
            0: RobotAgent(robot_id=0, position=(1, 1)),
            1: RobotAgent(robot_id=1, position=(8, 1)),
        }
        items = {
            (1, 3): "SKU-001", (3, 5): "SKU-002",
            (6, 2): "SKU-003", (8, 5): "SKU-004",
        }
        dropzones = {
            (1, 7): "ZONE-A", (3, 7): "ZONE-B",
            (6, 7): "ZONE-C", (8, 7): "ZONE-D",
        }
        order = [
            OrderItem(sku="SKU-001", deliver_to="ZONE-A", priority=True),
            OrderItem(sku="SKU-002", deliver_to="ZONE-B", priority=True),
            OrderItem(sku="SKU-003", deliver_to="ZONE-C", priority=False),
            OrderItem(sku="SKU-004", deliver_to="ZONE-D", priority=False),
        ]
        return cls(
            grid=grid, robots=robots, items=items, dropzones=dropzones,
            order=order, max_steps=100, battery_drain=1.5, task_id="task3_hard",
        )

    def is_wall(self, row: int, col: int) -> bool:
        """Check if a cell is a wall or out of bounds."""
        if row < 0 or row >= len(self.grid) or col < 0 or col >= len(self.grid[0]):
            return True
        return self.grid[row][col] == 'W'

    def is_charger(self, row: int, col: int) -> bool:
        """Check if a cell contains a charger."""
        if row < 0 or row >= len(self.grid) or col < 0 or col >= len(self.grid[0]):
            return False
        return self.grid[row][col] == 'C'

    def is_occupied_by_other_robot(self, position: Tuple[int, int], robot_id: int) -> bool:
        """Check if another robot occupies the given position."""
        for rid, robot in self.robots.items():
            if rid != robot_id and robot.position == position:
                return True
        return False

    def all_orders_complete(self) -> bool:
        """Check if every order item has been delivered."""
        return all(item.done for item in self.order)

    def items_remaining_count(self) -> int:
        """Count how many order items are still incomplete."""
        return sum(1 for item in self.order if not item.done)

    def items_delivered_count(self) -> int:
        """Count how many order items have been delivered."""
        return sum(1 for item in self.order if item.done)

    def is_sku_in_order(self, sku: str) -> bool:
        """Check if a SKU is part of the current order (not yet delivered)."""
        return any(item.sku == sku and not item.done for item in self.order)

    def get_order_item(self, sku: str) -> Optional[OrderItem]:
        """Get the order item for a given SKU (first incomplete match)."""
        for item in self.order:
            if item.sku == sku and not item.done:
                return item
        return None

    def get_zone_for_sku(self, sku: str) -> Optional[str]:
        """Get the expected drop zone name for a given SKU from the order."""
        for item in self.order:
            if item.sku == sku and not item.done:
                return item.deliver_to
        return None

    def get_zone_name_at(self, position: Tuple[int, int]) -> Optional[str]:
        """Get the drop zone name at a position, or None."""
        return self.dropzones.get(position)

    def get_item_at(self, position: Tuple[int, int]) -> Optional[str]:
        """Get the item SKU at a position, or None."""
        return self.items.get(position)

    def remove_item(self, position: Tuple[int, int]) -> Optional[str]:
        """Remove and return the item at position."""
        return self.items.pop(position, None)

    def get_current_target(self, robot_id: int) -> Optional[Tuple[int, int]]:
        """
        Determine the next target position for a robot.
        - If carrying an item, target is the correct drop zone.
        - If not carrying, target is the nearest incomplete order item's pickup.
        Returns None if no target exists.
        """
        robot = self.robots.get(robot_id)
        if robot is None:
            return None

        # If carrying, find the drop zone for the carried SKU
        if robot.is_carrying():
            sku = robot.carrying
            expected_zone = self.get_zone_for_sku(sku)
            if expected_zone:
                for pos, zone_name in self.dropzones.items():
                    if zone_name == expected_zone:
                        return pos
            # If no matching zone found (wrong pick), just go to first dropzone
            if self.dropzones:
                return next(iter(self.dropzones.keys()))
            return None

        # Not carrying: find the nearest incomplete order item that still exists on grid
        best_pos = None
        best_dist = float('inf')
        rr, rc = robot.position
        for item in self.order:
            if not item.done:
                # Find the item's position on the grid
                for pos, sku in self.items.items():
                    if sku == item.sku:
                        dist = abs(pos[0] - rr) + abs(pos[1] - rc)
                        if dist < best_dist:
                            best_dist = dist
                            best_pos = pos
                        break
        return best_pos

    def manhattan_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        """Compute Manhattan distance between two positions."""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
