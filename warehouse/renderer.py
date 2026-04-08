from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .grid import WarehouseGrid


def render_grid(grid: "WarehouseGrid") -> str:
    """
    Renders the current warehouse state as LLM-readable ASCII.
    Called by _build_observation() on every step.
    """
    lines = []
    width = 44

    # ── Header ──
    lines.append("╔" + "═" * width + "╗")
    header = f"  WAREHOUSE - Task: {grid.task_id}  Step {grid.steps_taken}/{grid.max_steps}"
    lines.append("║" + header.ljust(width) + "║")
    lines.append("╠" + "═" * width + "╣")

    # ── Build position lookup maps ──
    robot_positions = {}
    for rid, robot in grid.robots.items():
        robot_positions[robot.position] = robot

    # ── Grid rendering ──
    for r in range(len(grid.grid)):
        row_cells = []
        for c in range(len(grid.grid[0])):
            pos = (r, c)
            cell = grid.grid[r][c]

            # Priority: robot > item > dropzone > charger > wall/floor
            if pos in robot_positions:
                robot = robot_positions[pos]
                if robot.is_carrying():
                    row_cells.append(f"[R{robot.robot_id}*]")
                else:
                    row_cells.append(f"[R{robot.robot_id}]")
            elif pos in grid.items:
                sku = grid.items[pos]
                short = sku[-3:]  # last 3 chars
                row_cells.append(f"[I:{short}]")
            elif pos in grid.dropzones:
                zone = grid.dropzones[pos]
                short = zone[-1]  # last char
                row_cells.append(f"[D:{short}]")
            elif cell == 'C':
                row_cells.append("[C]")
            elif cell == 'W':
                row_cells.append(" W ")
            else:
                row_cells.append(" . ")

        row_str = "  " + " ".join(row_cells)
        lines.append("║" + row_str.ljust(width) + "║")

    # ── Robots section ──
    lines.append("╠" + "═" * width + "╣")
    lines.append("║" + "  ROBOTS".ljust(width) + "║")
    for rid in sorted(grid.robots.keys()):
        robot = grid.robots[rid]
        cargo_str = robot.carrying if robot.carrying else "None"
        robot_line = (
            f"  R{rid} | ({robot.position[0]},{robot.position[1]}) | "
            f"Cargo: {cargo_str} | Bat: {robot.battery:.0f}%"
        )
        lines.append("║" + robot_line.ljust(width) + "║")

    # ── Order section ──
    lines.append("╠" + "═" * width + "╣")
    lines.append("║" + "  ORDER".ljust(width) + "║")
    for item in grid.order:
        check = "✓" if item.done else " "
        # Find pickup position for this item
        pickup_str = ""
        for pos, sku in grid.items.items():
            if sku == item.sku:
                pickup_str = f"  [pickup: ({pos[0]},{pos[1]})]"
                break
        if item.done:
            pickup_str = "  [delivered]"
        priority_str = " ⚡" if item.priority else ""
        order_line = f"  [{check}] {item.sku} → {item.deliver_to}{pickup_str}{priority_str}"
        lines.append("║" + order_line.ljust(width) + "║")

    # ── Progress section ──
    delivered = sum(1 for item in grid.order if item.done)
    total = len(grid.order)
    lines.append("╠" + "═" * width + "╣")
    progress_line = f"  Progress: {delivered}/{total} delivered"
    lines.append("║" + progress_line.ljust(width) + "║")
    penalty_line = f"  Penalties so far: {grid.cumulative_penalty:.1f}"
    lines.append("║" + penalty_line.ljust(width) + "║")

    # ── Valid actions section ──
    lines.append("╠" + "═" * width + "╣")
    lines.append("║" + "  VALID ACTIONS:".ljust(width) + "║")
    lines.append("║" + "  move_north  move_south  move_east".ljust(width) + "║")
    lines.append("║" + "  move_west   pick_item   place_item".ljust(width) + "║")
    lines.append("║" + "  charge      done".ljust(width) + "║")
    lines.append("║" + "  → Output EXACTLY ONE action word only.".ljust(width) + "║")
    lines.append("╚" + "═" * width + "╝")

    return "\n".join(lines)
