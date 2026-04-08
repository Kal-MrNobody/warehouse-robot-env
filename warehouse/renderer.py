from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .grid import WarehouseGrid


def render_grid(grid: "WarehouseGrid") -> str:
    """Render the full warehouse state as an ASCII string for LLM consumption."""
    lines = []
    W = 44  # box width (chars)

    # Header
    lines.append("╔" + "═" * W + "╗")
    header = f"  WAREHOUSE - Task: {grid.task_id}  Step {grid.steps_taken}/{grid.max_steps}"
    lines.append("║" + header.ljust(W) + "║")
    lines.append("╠" + "═" * W + "╣")

    # Build robot position lookup
    robot_at = {robot.position: robot for robot in grid.robots.values()}

    # Grid rows
    for r in range(len(grid.grid)):
        cells = []
        for c in range(len(grid.grid[0])):
            pos = (r, c)
            cell = grid.grid[r][c]

            if pos in robot_at:
                bot = robot_at[pos]
                # asterisk means carrying something
                cells.append(f"[R{bot.robot_id}*]" if bot.is_carrying() else f"[R{bot.robot_id}]")
            elif pos in grid.items:
                sku = grid.items[pos]
                cells.append(f"[I:{sku[-3:]}]")
            elif pos in grid.dropzones:
                zone = grid.dropzones[pos]
                cells.append(f"[D:{zone[-1]}]")
            elif cell == "C":
                cells.append("[C]")
            elif cell == "W":
                cells.append(" W ")
            else:
                cells.append(" . ")

        row_str = "  " + " ".join(cells)
        lines.append("║" + row_str.ljust(W) + "║")

    # Robot status
    lines.append("╠" + "═" * W + "╣")
    lines.append("║" + "  ROBOTS".ljust(W) + "║")
    for rid in sorted(grid.robots):
        bot = grid.robots[rid]
        cargo = bot.carrying if bot.carrying else "None"
        line = f"  R{rid} | ({bot.position[0]},{bot.position[1]}) | Cargo: {cargo} | Bat: {bot.battery:.0f}%"
        lines.append("║" + line.ljust(W) + "║")

    # Order list
    lines.append("╠" + "═" * W + "╣")
    lines.append("║" + "  ORDER".ljust(W) + "║")
    for item in grid.order:
        check = "✓" if item.done else " "
        pickup = "  [delivered]"
        if not item.done:
            for pos, sku in grid.items.items():
                if sku == item.sku:
                    pickup = f"  [pickup: ({pos[0]},{pos[1]})]"
                    break
        priority = " ⚡" if item.priority else ""
        lines.append("║" + f"  [{check}] {item.sku} → {item.deliver_to}{pickup}{priority}".ljust(W) + "║")

    # Progress + penalty
    delivered = sum(1 for i in grid.order if i.done)
    total = len(grid.order)
    lines.append("╠" + "═" * W + "╣")
    lines.append("║" + f"  Progress: {delivered}/{total} delivered".ljust(W) + "║")
    lines.append("║" + f"  Penalties so far: {grid.cumulative_penalty:.1f}".ljust(W) + "║")

    # Valid actions reminder
    lines.append("╠" + "═" * W + "╣")
    lines.append("║" + "  VALID ACTIONS:".ljust(W) + "║")
    lines.append("║" + "  move_north  move_south  move_east".ljust(W) + "║")
    lines.append("║" + "  move_west   pick_item   place_item".ljust(W) + "║")
    lines.append("║" + "  charge      done".ljust(W) + "║")
    lines.append("║" + "  → Output EXACTLY ONE action word only.".ljust(W) + "║")
    lines.append("╚" + "═" * W + "╝")

    return "\n".join(lines)
