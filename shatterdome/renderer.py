from .grid import ShatterdomeGrid

class HUD_Renderer:
    """Renders the ShatterdomeGrid into an ASCII string for the LLM."""

    @staticmethod
    def render(world: ShatterdomeGrid) -> str:
        lines = []
        width = len(world.grid[0])
        lines.append("╔" + "═" * (width * 4 + 2) + "╗")
        lines.append(f"║  CONN-POD HUD - Directive: {world.task_id}  Cycle {world.steps_taken}/{world.max_steps}".ljust(width * 4 + 3) + "║")
        lines.append("╠" + "═" * (width * 4 + 2) + "╣")

        for r in range(len(world.grid)):
            row_str = "║ "
            for c in range(len(world.grid[r])):
                cell_type = world.grid[r][c]
                pos = (r, c)
                
                # Render Jaegers
                jaeger_here = None
                for jid, jaeger in world.jaegers.items():
                    if jaeger.position == pos:
                        jaeger_here = jaeger
                        break
                
                if jaeger_here:
                    symbol = f"[J{jaeger_here.jaeger_id}*]" if jaeger_here.is_carrying() else f"[J{jaeger_here.jaeger_id}]"
                    row_str += symbol.center(4)
                elif pos in world.cores:
                    core_id = world.cores[pos][-2:] # CORE-01 -> 01
                    row_str += f"[C:{core_id}]".center(4)
                elif pos in world.bays:
                    bay_id = world.bays[pos][-1:] # BAY-A -> A
                    row_str += f"[B:{bay_id}]".center(4)
                elif cell_type == "R":
                    row_str += "[R]".center(4)
                else:
                    row_str += cell_type.center(4)
            row_str += " ║"
            lines.append(row_str)

        lines.append("╠" + "═" * (width * 4 + 2) + "╣")
        lines.append("║  DIRECTIVES".ljust(width * 4 + 3) + "║")
        for directive in world.directives:
            status = "[x]" if directive.done else "[ ]"
            pri = "⚡ " if directive.priority else ""
            
            pickup_loc = "N/A"
            for p, cid in world.cores.items():
                if cid == directive.core_id:
                    pickup_loc = str(p)
                    break
            
            for jaeger in world.jaegers.values():
                if jaeger.carrying == directive.core_id:
                    pickup_loc = f"Carried by J{jaeger.jaeger_id}"
                    break
                    
            line = f"║  {status} {pri}{directive.core_id} → {directive.deploy_to}  [pickup: {pickup_loc}]"
            lines.append(line.ljust(width * 4 + 3) + "║")

        lines.append("╠" + "═" * (width * 4 + 2) + "╣")
        
        # Power / status row
        for jid, jaeger in world.jaegers.items():
            stat_line = f"║  J{jid} Reactor: {jaeger.reactor_power:.1f}% | Stress: {world.cumulative_stress:.2f}"
            lines.append(stat_line.ljust(width * 4 + 3) + "║")

        lines.append("╠" + "═" * (width * 4 + 2) + "╣")
        lines.append("║  VALID COMMANDS:".ljust(width * 4 + 3) + "║")
        lines.append("║  move_north  move_south  move_east".ljust(width * 4 + 3) + "║")
        lines.append("║  move_west   load_core   deploy_core".ljust(width * 4 + 3) + "║")
        lines.append("║  recharge    done".ljust(width * 4 + 3) + "║")
        lines.append("║  → Neural Handshake: Output EXACTLY ONE command word only.".ljust(width * 4 + 3) + "║")
        lines.append("╚" + "═" * (width * 4 + 2) + "╝")

        return "\n".join(lines)
