try:
    from models import ShatterdomeState
except ImportError:
    from ..models import ShatterdomeState

class Task1Grader:
    def grade(self, history: list, grid, state: ShatterdomeState) -> float:
        # Easy task: Just get the core to the bay
        score = 0.0
        if state.cores_secured >= 1:
            score = 1.0  # Perfect
        elif any(e.get("event") == "core_loaded" for e in history):
            score = 0.5  # Partial credit for getting the core
        
        # Penalize clumsy maneuvering
        score -= 0.05 * state.structural_damage
        return max(0.0, min(1.0, score))

class Task2Grader:
    def grade(self, history: list, grid, state: ShatterdomeState) -> float:
        # Medium task: 3 cores to load, reactor drains
        score = 0.0
        # Base score on cores secured (~0.33 per core)
        score += state.cores_secured * 0.33
        
        # Speed bonus if all 3 secured efficiently (expected ~36 cycles)
        if state.cores_secured == 3 and len(history) < 36:
            score += 0.1
            
        # Penalties for reactor failure and wall hits
        score -= 0.10 * state.structural_damage
        score -= 0.15 * state.reactor_criticals
        
        return max(0.0, min(1.0, score))

class Task3Grader:
    def grade(self, history: list, grid, state: ShatterdomeState) -> float:
        # Hard task: Multiple Jaegers, priority cores
        score = 0.0
        
        # Score based on priority
        for event in history:
            if event.get("event") == "core_deployed_correctly":
                if event.get("priority"):
                    score += 0.25
                else:
                    score += 0.15
                    
        # Multi-agent collision is very bad
        jaeger_collisions = sum(1 for e in history if e.get("event") == "collision_jaeger")
        score -= 0.10 * jaeger_collisions
        
        # Speed bonus for priority targets (under 50 cycles)
        priority_secured = sum(1 for e in history if e.get("event") == "core_deployed_correctly" and e.get("priority"))
        if priority_secured == 2 and len(history) < 50:
            score += 0.10
            
        # Reactor mastery bonus
        if state.reactor_criticals == 0:
            score += 0.05
            
        return max(0.0, min(1.0, score))
