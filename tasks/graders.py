try:
    from models import ShatterdomeState
except ImportError:
    from ..models import ShatterdomeState

class Task1Grader:
    def grade(self, history: list, grid, state: ShatterdomeState) -> float:
        score = 0.0
        if state.packages_secured >= 1:
            score = 1.0  # Perfect
        elif any(e.get("event") == "item_picked_up" for e in history):
            score = 0.5  # Partial credit for getting the package
        
        # Penalize clumsy maneuvering
        score -= 0.05 * state.structural_damage
        return max(0.01, min(0.99, score))

class Task2Grader:
    def grade(self, history: list, grid, state: ShatterdomeState) -> float:
        score = 0.0
        # Base score on packages secured (~0.33 per package)
        score += state.packages_secured * 0.33
        
        # Speed bonus if all 3 secured efficiently
        if state.packages_secured == 3 and len(history) < 36:
            score += 0.1
            
        # Penalties for battery failure and wall hits
        score -= 0.10 * state.structural_damage
        score -= 0.15 * state.battery_deaths
        score -= 0.33 * state.packages_failed
        
        return max(0.01, min(0.99, score))

class Task3Grader:
    def grade(self, history: list, grid, state: ShatterdomeState) -> float:
        score = 0.0
        
        # Score based on priority
        for event in history:
            if event.get("event") == "item_delivered":
                if event.get("priority"):
                    score += 0.25
                else:
                    score += 0.15
                    
        # Multi-agent collision is very bad
        robot_collisions = sum(1 for e in history if e.get("event") == "collision_robot")
        score -= 0.10 * robot_collisions
        score -= 0.33 * state.packages_failed
        
        # Speed bonus for priority targets
        priority_secured = sum(1 for e in history if e.get("event") == "item_delivered" and e.get("priority"))
        if priority_secured == 2 and len(history) < 50:
            score += 0.10
            
        # Battery mastery bonus
        if state.battery_deaths == 0:
            score += 0.05
            
        return max(0.01, min(0.99, score))
