class Task1Grader:
    """Grader for task1_easy: Single item pickup and delivery, clear path, 25 steps."""
    task_id = "task1_easy"
    description = "Single item pickup and delivery, clear path, 25 steps"

    def grade(self, episode_history: list, grid, state) -> float:
        score = 0.0
        # 1.0 if SKU-001 was delivered to ZONE-A
        if state.items_delivered >= 1:
            score = 1.0
        # 0.5 partial credit if robot at least picked up the item
        elif any(e.get("event") == "correct_pick" for e in episode_history):
            score = 0.5
        # -0.05 per wall collision (can't go below 0)
        score -= 0.05 * state.collisions
        return max(0.0, min(1.0, score))


class Task2Grader:
    """Grader for task2_medium: Three items, obstacles, battery management, 60 steps."""
    task_id = "task2_medium"
    description = "Three items, static obstacles, battery management, 60 steps"

    def grade(self, episode_history: list, grid, state) -> float:
        # 0.33 per item delivered
        score = state.items_delivered * 0.33
        # Time bonus: +0.1 if all 3 delivered before step 36 (60% of 60)
        if state.items_delivered == 3 and state.step_count < 36:
            score += 0.1
        # Collision penalty
        score -= 0.1 * state.collisions
        # Battery mismanagement penalty
        score -= 0.15 * state.battery_deaths
        return max(0.0, min(1.0, score))


class Task3Grader:
    """Grader for task3_hard: 2 robots, 4 items (2 priority), collision avoidance, 100 steps."""
    task_id = "task3_hard"
    description = "2 robots, 4 items (2 priority), collision avoidance, 100 steps"

    def grade(self, episode_history: list, grid, state) -> float:
        score = 0.0
        # Count priority vs regular deliveries from the order list
        priority_delivered = 0
        regular_delivered = 0
        for item in grid.order:
            if item.done:
                if item.priority:
                    score += 0.25    # priority item worth more
                    priority_delivered += 1
                else:
                    score += 0.15    # regular item
                    regular_delivered += 1
        # Robot-robot collision penalty (severe)
        robot_collisions = sum(
            1 for e in episode_history if e.get("event") == "collision_robot"
        )
        score -= 0.1 * robot_collisions
        # Priority efficiency bonus: all priority items done before step 50
        priority_events = [
            e for e in episode_history
            if e.get("event") == "correct_delivery" and e.get("priority", False)
        ]
        if priority_delivered == 2 and all(
            e["step"] < 50 for e in priority_events
        ):
            score += 0.1
        # Clean battery management bonus
        if state.battery_deaths == 0:
            score += 0.05
        return max(0.0, min(1.0, score))
