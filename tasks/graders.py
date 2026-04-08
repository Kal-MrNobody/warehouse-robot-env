"""
Graders for each warehouse task.

Each grader receives the episode history, the final grid state, and the
episode state object, then returns a float in [0.0, 1.0].
"""


class Task1Grader:
    task_id = "task1_easy"

    def grade(self, episode_history: list, grid, state) -> float:
        # Full credit if the item actually reached the drop zone
        if state.items_delivered >= 1:
            score = 1.0
        # Partial credit for at least picking it up
        elif any(e.get("event") == "correct_pick" for e in episode_history):
            score = 0.5
        else:
            score = 0.0

        # Small penalty per wall collision — shouldn't be bumping into walls
        score -= 0.05 * state.collisions
        return max(0.0, min(1.0, score))


class Task2Grader:
    task_id = "task2_medium"

    def grade(self, episode_history: list, grid, state) -> float:
        # ~0.33 per item delivered (3 items total)
        score = state.items_delivered * 0.33

        # Speed bonus: finishing all 3 before 60% of the step budget
        if state.items_delivered == 3 and state.step_count < 36:
            score += 0.1

        # Collision penalty
        score -= 0.1 * state.collisions

        # Battery mismanagement is a real problem in medium tasks
        score -= 0.15 * state.battery_deaths

        return max(0.0, min(1.0, score))


class Task3Grader:
    task_id = "task3_hard"

    def grade(self, episode_history: list, grid, state) -> float:
        score = 0.0

        priority_delivered = 0
        for item in grid.order:
            if item.done:
                if item.priority:
                    score += 0.25   # priority items are worth more
                    priority_delivered += 1
                else:
                    score += 0.15

        # Robot-robot collisions are heavily penalised in multi-robot tasks
        robot_collisions = sum(
            1 for e in episode_history if e.get("event") == "collision_robot"
        )
        score -= 0.1 * robot_collisions

        # Bonus for clearing priority orders quickly (within first 50 steps)
        priority_events = [
            e for e in episode_history
            if e.get("event") == "correct_delivery" and e.get("priority", False)
        ]
        if priority_delivered == 2 and all(e["step"] < 50 for e in priority_events):
            score += 0.1

        # Clean battery management bonus
        if state.battery_deaths == 0:
            score += 0.05

        return max(0.0, min(1.0, score))
