from .grid import ShatterdomeGrid

class HUD_Renderer:
    """Renders the ShatterdomeGrid into an ASCII string for the LLM."""

    @staticmethod
    def render(world: ShatterdomeGrid) -> str:
        lines = []
        width = len(world.grid[0])
        lines.append("╔" + "═" * (width * 4 + 2) + "╗")
        lines.append(f"║  WMS HUD - Order: {world.task_id}  Cycle {world.steps_taken}/{world.max_steps}".ljust(width * 4 + 3) + "║")
        lines.append("╠" + "═" * (width * 4 + 2) + "╣")

        for r in range(len(world.grid)):
            row_str = "║ "
            for c in range(len(world.grid[r])):
                cell_type = world.grid[r][c]
                pos = (r, c)
                
                # Render Robots
                robot_here = None
                for rid, robot in world.robots.items():
                    if robot.position == pos:
                        robot_here = robot
                        break
                
                if robot_here:
                    symbol = f"[R{robot_here.robot_id}*]" if robot_here.is_carrying() else f"[R{robot_here.robot_id}]"
                    row_str += symbol.center(4)
                elif pos in world.items:
                    item_id = world.items[pos][-2:] # PKG-01 -> 01
                    row_str += f"[P:{item_id}]".center(4)
                elif pos in world.dropzones:
                    zone_id = world.dropzones[pos][-1:] # ZONE-A -> A
                    row_str += f"[Z:{zone_id}]".center(4)
                elif cell_type == "B":
                    row_str += "[B]".center(4)
                else:
                    row_str += cell_type.center(4)
            row_str += " ║"
            lines.append(row_str)

        lines.append("╠" + "═" * (width * 4 + 2) + "╣")
        lines.append("║  ACTIVE ORDERS".ljust(width * 4 + 3) + "║")
        for order in world.orders:
            status = "[x]" if order.done else "[ ]"
            pri = "⚡ " if order.priority else ""
            
            pickup_loc = "N/A"
            for p, iid in world.items.items():
                if iid == order.package_id:
                    pickup_loc = str(p)
                    break
            
            for robot in world.robots.values():
                if robot.carrying == order.package_id:
                    pickup_loc = f"Carried by R{robot.robot_id}"
                    break
                    
            line = f"║  {status} {pri}{order.package_id} → {order.dropzone}  [pickup: {pickup_loc}]"
            lines.append(line.ljust(width * 4 + 3) + "║")

        lines.append("╠" + "═" * (width * 4 + 2) + "╣")
        
        # Power / status row
        for rid, robot in world.robots.items():
            stat_line = f"║  R{rid} Battery: {robot.battery_level:.1f}% | Damage: {world.cumulative_stress:.2f}"
            lines.append(stat_line.ljust(width * 4 + 3) + "║")

        lines.append("╠" + "═" * (width * 4 + 2) + "╣")
        lines.append("║  VALID COMMANDS:".ljust(width * 4 + 3) + "║")
        lines.append("║  move_north  move_south  move_east".ljust(width * 4 + 3) + "║")
        lines.append("║  move_west   pickup_item drop_item".ljust(width * 4 + 3) + "║")
        lines.append("║  recharge    done".ljust(width * 4 + 3) + "║")
        lines.append("║  → Output EXACTLY ONE command word only.".ljust(width * 4 + 3) + "║")
        lines.append("╚" + "═" * (width * 4 + 2) + "╝")

        return "\n".join(lines)
