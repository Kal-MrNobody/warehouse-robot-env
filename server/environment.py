from typing import Optional, Any
from uuid import uuid4

from openenv.core.env_server import Environment

try:
    from ..models import WarehouseAction, WarehouseObservation, WarehouseState
    from ..warehouse.grid import WarehouseGrid
    from ..warehouse.renderer import render_grid
    from ..tasks.graders import Task1Grader, Task2Grader, Task3Grader
except ImportError:
    from models import WarehouseAction, WarehouseObservation, WarehouseState
    from warehouse.grid import WarehouseGrid
    from warehouse.renderer import render_grid
    from tasks.graders import Task1Grader, Task2Grader, Task3Grader


VALID_ACTIONS = {
    "move_north", "move_south", "move_east", "move_west",
    "pick_item", "place_item", "charge", "done",
}

MOVEMENT_ACTIONS = {"move_north", "move_south", "move_east", "move_west"}


class WarehouseEnvironment(Environment):
    """
    OpenEnv-compliant warehouse robot environment.
    Manages a 2D grid warehouse where robots pick and deliver items.
    """
    SUPPORTS_CONCURRENT_SESSIONS = True

    GRADERS = {
        "task1_easy": Task1Grader,
        "task2_medium": Task2Grader,
        "task3_hard": Task3Grader,
    }

    def __init__(self):
        super().__init__()
        self._grid = None
        self._state = None

    def reset(
        self,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
        **kwargs: Any,
    ) -> WarehouseObservation:
        """
        Initialize a new episode for the given task.
        task_id is passed via kwargs (e.g., reset(task_id="task1_easy")).
        """
        task_id = kwargs.get("task_id", "task1_easy")
        effective_seed = seed if seed is not None else 42

        # 1. Load grid from task definition
        self._grid = WarehouseGrid.from_task(task_id, effective_seed)

        # 2. Reset episode history
        self._grid.episode_history = []

        # 3. Create new WarehouseState with fresh uuid4 episode_id
        eid = episode_id if episode_id else str(uuid4())
        self._state = WarehouseState(
            episode_id=eid,
            step_count=0,
            task_id=task_id,
            total_reward=0.0,
            items_delivered=0,
            collisions=0,
            wrong_picks=0,
            grader_score=0.0,
            battery_deaths=0,
        )

        # 4. Return initial observation
        return self._build_observation(reward=None, done=False)

    def step(
        self,
        action: WarehouseAction,
        timeout_s: Optional[float] = None,
        **kwargs: Any,
    ) -> WarehouseObservation:
        """
        Execute one action and return the resulting observation.
        All reward computation happens here.
        """
        action_str = action.action.strip().lower()
        reward = 0.0
        done = False
        done_reason = None

        # We operate on robot 0 by default (multi-robot: actions would need robot_id)
        # For task3 with 2 robots, we alternate or use robot 0
        # Simplified: always control robot 0 (agent controls primary robot)
        robot_id = 0
        robot = self._grid.robots[robot_id]

        # ── 1. Validate action string ──
        if action_str not in VALID_ACTIONS:
            reward -= 0.10
            self._grid.cumulative_penalty += 0.10
            self._grid.episode_history.append({
                "step": self._state.step_count,
                "event": "invalid_action",
                "action": action_str,
            })
            # Still increment step count for invalid actions
            self._state.step_count += 1
            self._grid.steps_taken += 1
            self._state.total_reward += reward

            # Check step limit
            if self._state.step_count >= self._grid.max_steps:
                done = True
                done_reason = "step_limit_exceeded"
                penalty = 0.10 * self._grid.items_remaining_count()
                reward -= penalty
                self._state.total_reward += (-penalty)
                self._grid.cumulative_penalty += penalty
                self._run_grader()

            return self._build_observation(reward, done, done_reason)

        # ── 2. Movement actions ──
        if action_str in MOVEMENT_ACTIONS:
            # Check if robot battery is dead
            if robot.battery <= 0:
                reward -= 0.40
                self._grid.cumulative_penalty += 0.40
                self._state.battery_deaths += 1
                self._grid.episode_history.append({
                    "step": self._state.step_count,
                    "event": "battery_dead_move",
                    "robot_id": robot_id,
                })
            else:
                # Compute target for distance shaping
                target_before = self._grid.get_current_target(robot_id)
                dist_before = None
                if target_before:
                    dist_before = self._grid.manhattan_distance(
                        robot.position, target_before
                    )

                # Compute candidate position
                candidate = robot.move(action_str)

                # Check wall collision
                if self._grid.is_wall(candidate[0], candidate[1]):
                    reward -= 0.20
                    self._grid.cumulative_penalty += 0.20
                    self._state.collisions += 1
                    self._grid.episode_history.append({
                        "step": self._state.step_count,
                        "event": "collision_wall",
                        "robot_id": robot_id,
                        "position": list(robot.position),
                    })
                else:
                    # Check robot-robot collision (Task 3)
                    if self._grid.is_occupied_by_other_robot(candidate, robot_id):
                        reward -= 0.50
                        self._grid.cumulative_penalty += 0.50
                        self._grid.episode_history.append({
                            "step": self._state.step_count,
                            "event": "collision_robot",
                            "robot_id": robot_id,
                            "position": list(candidate),
                        })
                        # Robot still moves (both occupy same cell = collision)
                        robot.position = candidate
                    else:
                        # Valid move
                        robot.position = candidate

                    # Distance shaping reward
                    target_after = self._grid.get_current_target(robot_id)
                    if target_before and target_after:
                        dist_after = self._grid.manhattan_distance(
                            robot.position, target_after
                        )
                        if dist_before is not None:
                            if dist_after < dist_before:
                                reward += 0.05
                            elif dist_after > dist_before:
                                reward -= 0.05
                                self._grid.cumulative_penalty += 0.05

                # Drain battery
                if self._grid.battery_drain > 0:
                    battery_died = robot.drain_battery(self._grid.battery_drain)
                    if battery_died:
                        reward -= 0.40
                        self._grid.cumulative_penalty += 0.40
                        self._state.battery_deaths += 1
                        self._grid.episode_history.append({
                            "step": self._state.step_count,
                            "event": "battery_died",
                            "robot_id": robot_id,
                        })

        # ── 3. pick_item ──
        elif action_str == "pick_item":
            if robot.battery <= 0:
                reward -= 0.40
                self._grid.cumulative_penalty += 0.40
                self._state.battery_deaths += 1
                self._grid.episode_history.append({
                    "step": self._state.step_count,
                    "event": "battery_dead_action",
                    "robot_id": robot_id,
                })
            elif robot.is_carrying():
                reward -= 0.10
                self._grid.cumulative_penalty += 0.10
                self._grid.episode_history.append({
                    "step": self._state.step_count,
                    "event": "pick_already_carrying",
                    "robot_id": robot_id,
                })
            else:
                item_sku = self._grid.get_item_at(robot.position)
                if item_sku is None:
                    reward -= 0.10
                    self._grid.cumulative_penalty += 0.10
                    self._grid.episode_history.append({
                        "step": self._state.step_count,
                        "event": "pick_no_item",
                        "robot_id": robot_id,
                        "position": list(robot.position),
                    })
                elif not self._grid.is_sku_in_order(item_sku):
                    # Picked item NOT in current order
                    reward -= 0.30
                    self._grid.cumulative_penalty += 0.30
                    self._state.wrong_picks += 1
                    robot.pick_up(item_sku)
                    self._grid.remove_item(robot.position)
                    self._grid.episode_history.append({
                        "step": self._state.step_count,
                        "event": "wrong_pick",
                        "robot_id": robot_id,
                        "sku": item_sku,
                    })
                else:
                    # Correct pick
                    reward += 0.20
                    robot.pick_up(item_sku)
                    self._grid.remove_item(robot.position)
                    self._grid.episode_history.append({
                        "step": self._state.step_count,
                        "event": "correct_pick",
                        "robot_id": robot_id,
                        "sku": item_sku,
                    })

        # ── 4. place_item ──
        elif action_str == "place_item":
            if robot.battery <= 0:
                reward -= 0.40
                self._grid.cumulative_penalty += 0.40
                self._state.battery_deaths += 1
                self._grid.episode_history.append({
                    "step": self._state.step_count,
                    "event": "battery_dead_action",
                    "robot_id": robot_id,
                })
            elif not robot.is_carrying():
                reward -= 0.10
                self._grid.cumulative_penalty += 0.10
                self._grid.episode_history.append({
                    "step": self._state.step_count,
                    "event": "place_not_carrying",
                    "robot_id": robot_id,
                })
            else:
                zone_name = self._grid.get_zone_name_at(robot.position)
                if zone_name is None:
                    reward -= 0.10
                    self._grid.cumulative_penalty += 0.10
                    self._grid.episode_history.append({
                        "step": self._state.step_count,
                        "event": "place_not_on_zone",
                        "robot_id": robot_id,
                        "position": list(robot.position),
                    })
                else:
                    carried_sku = robot.carrying
                    expected_zone = self._grid.get_zone_for_sku(carried_sku)

                    if expected_zone and zone_name == expected_zone:
                        # Correct delivery
                        reward += 0.50
                        robot.drop_item()
                        order_item = self._grid.get_order_item(carried_sku)
                        if order_item:
                            is_priority = order_item.priority
                            order_item.done = True
                        else:
                            is_priority = False
                        self._state.items_delivered += 1
                        self._grid.episode_history.append({
                            "step": self._state.step_count,
                            "event": "correct_delivery",
                            "robot_id": robot_id,
                            "sku": carried_sku,
                            "zone": zone_name,
                            "priority": is_priority,
                        })
                    else:
                        # Wrong drop zone — item is lost
                        reward -= 0.30
                        self._grid.cumulative_penalty += 0.30
                        robot.drop_item()
                        self._grid.episode_history.append({
                            "step": self._state.step_count,
                            "event": "wrong_delivery",
                            "robot_id": robot_id,
                            "sku": carried_sku,
                            "zone": zone_name,
                            "expected_zone": expected_zone,
                        })

        # ── 5. charge ──
        elif action_str == "charge":
            if self._grid.is_charger(robot.position[0], robot.position[1]):
                robot.charge_battery(30.0)
                reward += 0.05
                self._grid.episode_history.append({
                    "step": self._state.step_count,
                    "event": "charged",
                    "robot_id": robot_id,
                    "battery": robot.battery,
                })
            else:
                # Not on charger cell — treat as wasted action
                reward -= 0.10
                self._grid.cumulative_penalty += 0.10
                self._grid.episode_history.append({
                    "step": self._state.step_count,
                    "event": "charge_not_on_charger",
                    "robot_id": robot_id,
                })

        # ── 6. done ──
        elif action_str == "done":
            done = True
            done_reason = "agent_called_done"
            self._grid.episode_history.append({
                "step": self._state.step_count,
                "event": "agent_done",
                "robot_id": robot_id,
            })

        # ── 7. Post-action processing ──
        self._state.step_count += 1
        self._grid.steps_taken += 1
        self._state.total_reward += reward

        # Check if all orders complete
        if not done and self._grid.all_orders_complete():
            done = True
            done_reason = "all_orders_complete"
            reward += 1.00  # bonus
            self._state.total_reward += 1.00
            self._grid.episode_history.append({
                "step": self._state.step_count,
                "event": "all_orders_complete",
            })

        # Check step limit
        if not done and self._state.step_count >= self._grid.max_steps:
            done = True
            done_reason = "step_limit_exceeded"
            remaining_penalty = 0.10 * self._grid.items_remaining_count()
            reward -= remaining_penalty
            self._state.total_reward -= remaining_penalty
            self._grid.cumulative_penalty += remaining_penalty
            self._grid.episode_history.append({
                "step": self._state.step_count,
                "event": "step_limit_exceeded",
                "remaining_items": self._grid.items_remaining_count(),
            })

        # If done, run grader
        if done:
            self._run_grader()

        return self._build_observation(reward, done, done_reason)

    def _run_grader(self) -> None:
        """Run the appropriate grader and store the score."""
        grader_cls = self.GRADERS.get(self._state.task_id)
        if grader_cls:
            grader = grader_cls()
            score = grader.grade(
                self._grid.episode_history,
                self._grid,
                self._state,
            )
            self._state.grader_score = max(0.0, min(1.0, score))

    @property
    def state(self) -> WarehouseState:
        return self._state

    def _build_observation(self, reward, done, done_reason=None) -> WarehouseObservation:
        """
        Constructs a full WarehouseObservation from current grid state.
        """
        grid_text = render_grid(self._grid)

        robots_list = []
        for rid in sorted(self._grid.robots.keys()):
            robots_list.append(self._grid.robots[rid].to_dict())

        order_list = []
        for item in self._grid.order:
            order_list.append({
                "sku": item.sku,
                "deliver_to": item.deliver_to,
                "priority": item.priority,
                "done": item.done,
            })

        return WarehouseObservation(
            done=done,
            reward=reward,
            metadata={
                "episode_id": self._state.episode_id,
                "task_id": self._state.task_id,
                "total_reward": round(self._state.total_reward, 3),
            },
            grid_text=grid_text,
            robots=robots_list,
            current_order=order_list,
            items_remaining=self._grid.items_remaining_count(),
            steps_taken=self._grid.steps_taken,
            max_steps=self._grid.max_steps,
            cumulative_penalty=round(self._grid.cumulative_penalty, 3),
            done_reason=done_reason,
            task_id=self._state.task_id,
            grader_score=self._state.grader_score,
        )
