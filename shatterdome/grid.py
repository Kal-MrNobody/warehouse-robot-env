from typing import Dict, List, Optional, Tuple
import copy

try:
    from ..models import CoreLoad
    from .jaeger import JaegerAgent
except ImportError:
    from models import CoreLoad
    from shatterdome.jaeger import JaegerAgent

class ShatterdomeGrid:
    """
    Holds the entire simulation state of the Shatterdome: the base grid, Jaegers,
    Plasma Cores, Jaeger Bays, objectives (directives), and task config.
    """

    def __init__(
        self,
        grid: List[List[str]],
        jaegers: Dict[int, JaegerAgent],
        cores: Dict[Tuple[int, int], str],
        bays: Dict[Tuple[int, int], str],
        directives: List[CoreLoad],
        max_steps: int,
        reactor_drain: float,
        task_id: str,
    ):
        self.grid = grid
        self.jaegers = jaegers
        self.cores = cores
        self.bays = bays
        self.directives = directives
        self.max_steps = max_steps
        self.reactor_drain = reactor_drain
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
            ['W', '.', '.', '.', '.', '.', '.', 'R', '.', 'W'],
            ['W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W'],
        ]
        jaegers = {0: JaegerAgent(jaeger_id=0, position=(4, 4))}
        cores = {(2, 2): "CORE-01"}
        bays = {(2, 7): "BAY-A"}
        directives = [CoreLoad(core_id="CORE-01", deploy_to="BAY-A")]
        return cls(
            grid=grid, jaegers=jaegers, cores=cores, bays=bays,
            directives=directives, max_steps=25, reactor_drain=0.0, task_id="task1_easy",
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
            ['W', '.', '.', '.', '.', '.', '.', 'R', '.', 'W'],
            ['W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W'],
        ]
        jaegers = {0: JaegerAgent(jaeger_id=0, position=(5, 1))}
        cores = {(1, 2): "CORE-01", (4, 5): "CORE-02", (7, 2): "CORE-03"}
        bays = {(1, 7): "BAY-A", (5, 8): "BAY-B", (8, 7): "BAY-C"}
        directives = [
            CoreLoad(core_id="CORE-01", deploy_to="BAY-A"),
            CoreLoad(core_id="CORE-02", deploy_to="BAY-B"),
            CoreLoad(core_id="CORE-03", deploy_to="BAY-C"),
        ]
        return cls(
            grid=grid, jaegers=jaegers, cores=cores, bays=bays,
            directives=directives, max_steps=60, reactor_drain=2.0, task_id="task2_medium",
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
            ['W', '.', '.', '.', '.', '.', '.', 'R', '.', 'W'],
            ['W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W'],
        ]
        jaegers = {
            0: JaegerAgent(jaeger_id=0, position=(1, 1)),
            1: JaegerAgent(jaeger_id=1, position=(8, 1)),
        }
        cores = {
            (1, 3): "CORE-01", (3, 5): "CORE-02",
            (6, 2): "CORE-03", (8, 5): "CORE-04",
        }
        bays = {
            (1, 7): "BAY-A", (3, 7): "BAY-B",
            (6, 7): "BAY-C", (8, 7): "BAY-D",
        }
        directives = [
            CoreLoad(core_id="CORE-01", deploy_to="BAY-A", priority=True),
            CoreLoad(core_id="CORE-02", deploy_to="BAY-B", priority=True),
            CoreLoad(core_id="CORE-03", deploy_to="BAY-C", priority=False),
            CoreLoad(core_id="CORE-04", deploy_to="BAY-D", priority=False),
        ]
        return cls(
            grid=grid, jaegers=jaegers, cores=cores, bays=bays,
            directives=directives, max_steps=100, reactor_drain=1.5, task_id="task3_hard",
        )

    def is_wall(self, row: int, col: int) -> bool:
        if row < 0 or row >= len(self.grid) or col < 0 or col >= len(self.grid[0]):
            return True
        return self.grid[row][col] == 'W'

    def is_reactor_charger(self, row: int, col: int) -> bool:
        if row < 0 or row >= len(self.grid) or col < 0 or col >= len(self.grid[0]):
            return False
        return self.grid[row][col] == 'R'

    def is_occupied_by_other_jaeger(self, position: Tuple[int, int], jaeger_id: int) -> bool:
        for jid, jaeger in self.jaegers.items():
            if jid != jaeger_id and jaeger.position == position:
                return True
        return False

    def all_directives_complete(self) -> bool:
        return all(d.done for d in self.directives)

    def cores_remaining_count(self) -> int:
        return sum(1 for d in self.directives if not d.done)

    def cores_secured_count(self) -> int:
        return sum(1 for d in self.directives if d.done)

    def is_core_in_directives(self, core_id: str) -> bool:
        return any(d.core_id == core_id and not d.done for d in self.directives)

    def get_directive(self, core_id: str) -> Optional[CoreLoad]:
        for d in self.directives:
            if d.core_id == core_id and not d.done:
                return d
        return None

    def get_bay_for_core(self, core_id: str) -> Optional[str]:
        for d in self.directives:
            if d.core_id == core_id and not d.done:
                return d.deploy_to
        return None

    def get_bay_name_at(self, position: Tuple[int, int]) -> Optional[str]:
        return self.bays.get(position)

    def get_core_at(self, position: Tuple[int, int]) -> Optional[str]:
        return self.cores.get(position)

    def remove_core(self, position: Tuple[int, int]) -> Optional[str]:
        return self.cores.pop(position, None)

    def get_current_target(self, jaeger_id: int) -> Optional[Tuple[int, int]]:
        """
        Determine the next target position for a Jaeger for reward shaping.
        - If carrying a core, target is the correct bay.
        - If not carrying, target is the nearest incomplete core.
        """
        jaeger = self.jaegers.get(jaeger_id)
        if jaeger is None:
            return None

        if jaeger.is_carrying():
            core_id = jaeger.carrying
            expected_bay = self.get_bay_for_core(core_id)
            if expected_bay:
                for pos, bay_name in self.bays.items():
                    if bay_name == expected_bay:
                        return pos
            if self.bays: # fallback
                return next(iter(self.bays.keys()))
            return None

        best_pos = None
        best_dist = float('inf')
        rr, rc = jaeger.position
        for d in self.directives:
            if not d.done:
                for pos, cid in self.cores.items():
                    if cid == d.core_id:
                        dist = abs(pos[0] - rr) + abs(pos[1] - rc)
                        if dist < best_dist:
                            best_dist = dist
                            best_pos = pos
                        break
        return best_pos

    def manhattan_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
