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
        "load_core", "deploy_core", "recharge", "done"
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
        return self._build_observation(reward=None, done=False)

    def state(self) -> ShatterdomeState:
        return self._state

    def _build_observation(self, reward: float = None, done: bool = False) -> ShatterdomeObservation:
        score = self._state.grader_score if done else 0.0
        
        jaegers_data = [j.to_dict() for j in self._grid.jaegers.values()]
        active_directives = [{"core_id": d.core_id, "deploy_to": d.deploy_to, "done": d.done} for d in self._grid.directives]
        
        return ShatterdomeObservation(
            hud_display=HUD_Renderer.render(self._grid),
            jaegers=jaegers_data,
            active_directives=active_directives,
            cores_remaining=self._grid.cores_remaining_count(),
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

        # For multi-agent tasks, we default to Jaeger 0 logic for simplicity,
        # but in hard task, we could alternate or let action spec include jaeger_id.
        # Since hackathon baseline is single string action, we control Jaeger 0.
        j_id = 0
        jaeger = self._grid.jaegers[j_id]

        if jaeger.reactor_power <= 0:
            reward -= 0.40
            self._grid.episode_history.append({"event": "reactor_offline", "jaeger_id": j_id})
        elif cmd.startswith("move_"):
            target_pos = jaeger.maneuver(cmd)
            
            if self._grid.is_wall(target_pos[0], target_pos[1]):
                reward -= 0.20
                self._state.structural_damage += 1
                self._grid.episode_history.append({"event": "structural_damage", "pos": target_pos})
            elif self._grid.is_occupied_by_other_jaeger(target_pos, j_id):
                reward -= 0.50
                self._grid.episode_history.append({"event": "collision_jaeger"})
            else:
                target_before = self._grid.get_current_target(j_id)
                dist_before = self._grid.manhattan_distance(jaeger.position, target_before) if target_before else 0

                jaeger.position = target_pos

                target_after = self._grid.get_current_target(j_id)
                dist_after = self._grid.manhattan_distance(jaeger.position, target_after) if target_after else 0

                if target_after and dist_after < dist_before:
                    reward += 0.05
                elif target_after and dist_after > dist_before:
                    reward -= 0.05

        elif cmd == "load_core":
            curr_pos = jaeger.position
            core_id = self._grid.get_core_at(curr_pos)

            if core_id is None:
                reward -= 0.10
                self._grid.episode_history.append({"event": "misfire_load", "pos": curr_pos})
                self._state.misfires += 1
            else:
                if jaeger.is_carrying():
                    reward -= 0.10
                else:
                    if self._grid.is_core_in_directives(core_id):
                        reward += 0.20
                        self._grid.remove_core(curr_pos)
                        jaeger.load_core(core_id)
                        self._grid.episode_history.append({"event": "core_loaded", "core_id": core_id})
                    else:
                        reward -= 0.30
                        self._state.misfires += 1

        elif cmd == "deploy_core":
            if not jaeger.is_carrying():
                reward -= 0.10
                self._state.misfires += 1
            else:
                curr_bay = self._grid.get_bay_name_at(jaeger.position)
                if curr_bay is None:
                    reward -= 0.10
                else:
                    core_id = jaeger.carrying
                    directive = self._grid.get_directive(core_id)
                    if directive and directive.deploy_to == curr_bay:
                        reward += 0.50
                        directive.done = True
                        jaeger.deploy_core()
                        self._state.cores_secured += 1
                        self._grid.episode_history.append({"event": "core_deployed_correctly", "core_id": core_id, "priority": directive.priority})
                    else:
                        reward -= 0.30
                        self._state.misfires += 1

        elif cmd == "recharge":
            if self._grid.is_reactor_charger(jaeger.position[0], jaeger.position[1]):
                reward += 0.05
                jaeger.recharge_reactor()
            else:
                reward -= 0.10

        died = jaeger.drain_reactor(self._grid.reactor_drain)
        if died:
            reward -= 0.40
            self._state.reactor_criticals += 1
            self._grid.episode_history.append({"event": "reactor_critical_failure"})

        self._grid.steps_taken += 1
        
        if self._grid.all_directives_complete():
            reward += 1.00
            done = True
        elif self._grid.steps_taken >= self._grid.max_steps:
            reward -= 0.10 * self._grid.cores_remaining_count()
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
