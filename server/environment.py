from openenv.core.env_server import Environment
try:
    from models import ShatterdomeAction, ShatterdomeObservation, ShatterdomeState
except ImportError:
    from ..models import ShatterdomeAction, ShatterdomeObservation, ShatterdomeState

from shatterdome.grid import ShatterdomeGrid
from shatterdome.renderer import HUD_Renderer

import uuid

# Load graders dynamically
def load_graders():
    try:
        from tasks.graders import Task1Grader, Task2Grader, Task3Grader
    except ImportError:
        from ..tasks.graders import Task1Grader, Task2Grader, Task3Grader
    return {
        "task1_easy": Task1Grader,
        "task2_medium": Task2Grader,
        "task3_hard": Task3Grader,
    }

class ShatterdomeEnvironment(Environment):
    SUPPORTS_CONCURRENT_SESSIONS = True

    VALID_ACTIONS = {
        "move_north", "move_south", "move_east", "move_west",
        "pickup_item", "drop_item", "recharge", "done"
    }

    GRADERS = load_graders()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._grid = None
        self._state = None
        self._session_id = str(uuid.uuid4())

    def reset(self, task_id: str = "task1_easy", seed: int = 42) -> ShatterdomeObservation:
        self._grid = ShatterdomeGrid.from_task(task_id, seed)
        self._state = ShatterdomeState(task_id=task_id)
        self._grid.episode_history = []
        return self._build_observation(reward=0.0, done=False)

    def state(self) -> ShatterdomeState:
        return self._state

    def _build_observation(self, reward: float = 0.0, done: bool = False) -> ShatterdomeObservation:
        score = self._state.grader_score if done else 0.0
        
        robots_data = [r.to_dict() for r in self._grid.robots.values()]
        active_orders = [{"package_id": o.package_id, "dropzone": o.dropzone, "done": o.done, "weight": o.weight, "fragile": o.fragile, "deadline": o.deadline} for o in self._grid.orders if not o.failed]
        
        return ShatterdomeObservation(
            hud_display=HUD_Renderer.render(self._grid),
            robots=robots_data,
            active_orders=active_orders,
            packages_remaining=self._grid.packages_remaining_count(),
            cycles_elapsed=self._grid.steps_taken,
            max_cycles=self._grid.max_steps,
            cumulative_stress=round(self._grid.cumulative_stress, 2),
            grader_score=score,
            reward=reward,
            done=done
        )

    def step(self, action: ShatterdomeAction) -> ShatterdomeObservation:
        cmd = action.action.lower()
        reward = 0.0
        done = False

        if cmd not in self.VALID_ACTIONS:
            reward -= 0.10
            self._grid.episode_history.append({"event": "invalid_command", "cmd": cmd})
            return self._finalize_step(reward, done)

        if cmd == "done":
            done = True
            return self._finalize_step(reward, done)

        r_id = 0
        robot = self._grid.robots[r_id]

        if robot.battery_level <= 0:
            reward -= 0.40
            self._grid.episode_history.append({"event": "battery_offline", "robot_id": r_id})
        elif cmd.startswith("move_"):
            target_pos = robot.maneuver(cmd)
            
            if self._grid.is_wall(target_pos[0], target_pos[1]):
                reward -= 0.20
                self._state.structural_damage += 1
                self._grid.episode_history.append({"event": "collision_wall", "pos": target_pos})
                if robot.is_carrying():
                    order = self._grid.get_order(robot.carrying)
                    if order and order.fragile:
                        self._grid.fail_order(robot.carrying)
                        robot.drop_item()
                        reward -= 3.0
                        self._state.packages_failed += 1
                        self._grid.episode_history.append({"event": "fragile_broken"})
            elif self._grid.is_occupied_by_other_robot(target_pos, r_id):
                reward -= 0.50
                self._grid.episode_history.append({"event": "collision_robot"})
                if robot.is_carrying():
                    order = self._grid.get_order(robot.carrying)
                    if order and order.fragile:
                        self._grid.fail_order(robot.carrying)
                        robot.drop_item()
                        reward -= 3.0
                        self._state.packages_failed += 1
                        self._grid.episode_history.append({"event": "fragile_broken"})
            else:
                target_before = self._grid.get_current_target(r_id)
                dist_before = self._grid.manhattan_distance(robot.position, target_before) if target_before else 0

                robot.position = target_pos

                target_after = self._grid.get_current_target(r_id)
                dist_after = self._grid.manhattan_distance(robot.position, target_after) if target_after else 0

                if target_after and dist_after < dist_before:
                    reward += 0.05
                elif target_after and dist_after > dist_before:
                    reward -= 0.05

        elif cmd == "pickup_item":
            curr_pos = robot.position
            item_id = self._grid.get_item_at(curr_pos)

            if item_id is None:
                reward -= 0.10
                self._grid.episode_history.append({"event": "misfire_pickup", "pos": curr_pos})
                self._state.misfires += 1
            else:
                if robot.is_carrying():
                    reward -= 0.10
                else:
                    if self._grid.is_item_in_orders(item_id):
                        reward += 0.20
                        self._grid.remove_item(curr_pos)
                        robot.pickup_item(item_id)
                        self._grid.episode_history.append({"event": "item_picked_up", "item_id": item_id})
                    else:
                        reward -= 0.30
                        self._state.misfires += 1

        elif cmd == "drop_item":
            if not robot.is_carrying():
                reward -= 0.10
                self._state.misfires += 1
            else:
                curr_zone = self._grid.get_dropzone_name_at(robot.position)
                if curr_zone is None:
                    reward -= 0.10
                else:
                    item_id = robot.carrying
                    order = self._grid.get_order(item_id)
                    if order and order.dropzone == curr_zone:
                        reward += 0.50
                        order.done = True
                        robot.drop_item()
                        self._state.packages_secured += 1
                        self._grid.episode_history.append({"event": "item_delivered", "item_id": item_id, "priority": order.priority})
                    else:
                        reward -= 0.30
                        self._state.misfires += 1

        elif cmd == "recharge":
            if self._grid.is_battery_charger(robot.position[0], robot.position[1]):
                reward += 0.05
                robot.recharge_battery()
            else:
                reward -= 0.10

        drain = self._grid.battery_drain
        if robot.is_carrying():
            o = self._grid.get_order(robot.carrying)
            if o and o.weight == "heavy":
                drain *= 3.0
        died = robot.drain_battery(drain)
        if died:
            reward -= 0.40
            self._state.battery_deaths += 1
            self._grid.episode_history.append({"event": "battery_depleted"})

        self._grid.steps_taken += 1
        
        for order in self._grid.orders:
            if order.deadline and self._grid.steps_taken >= order.deadline and not order.done and not order.failed:
                self._grid.fail_order(order.package_id)
                reward -= 2.0
                self._state.packages_failed += 1
                self._grid.episode_history.append({"event": "deadline_missed", "item_id": order.package_id})
                for r in self._grid.robots.values():
                    if r.carrying == order.package_id:
                        r.drop_item()

        if self._grid.all_orders_complete():
            reward += 1.00
            done = True
        elif self._grid.steps_taken >= self._grid.max_steps:
            reward -= 0.10 * self._grid.packages_remaining_count()
            done = True

        return self._finalize_step(reward, done)

    def _finalize_step(self, reward: float, done: bool) -> ShatterdomeObservation:
        self._state.total_reward += reward
        if done:
            grader_cls = self.GRADERS.get(self._grid.task_id)
            if grader_cls:
                score = grader_cls().grade(self._grid.episode_history, self._grid, self._state)
                self._state.grader_score = score
        return self._build_observation(reward=round(reward, 2), done=done)
