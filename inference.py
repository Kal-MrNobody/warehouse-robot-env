import os
import time
import json
import uuid
import sys
import io
from openai import OpenAI

# Force UTF-8 stdout mapping for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from client import ShatterdomeClient
from models import ShatterdomeAction

# ──────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────

API_BASE_URL = os.getenv("API_BASE_URL", "https://api.groq.com/openai/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
HF_TOKEN = os.getenv("HF_TOKEN")

if not HF_TOKEN:
    print("Warning: HF_TOKEN environment variable is not set. Inference may fail if API requires auth.", file=sys.stderr)

llm = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN
)

# ──────────────────────────────────────────────────────────
# AGENT PROMPT
# ──────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
You are the AI brain controlling a logistics robot in an E-Commerce warehouse.
You receive a WMS (Warehouse Management System) HUD showing the layout of the facility.

[R0] is your robot (if empty). [R0*] means your robot is carrying a package.
[P:01] is a Package waiting on the floor.
[Z:A] is Drop Zone A.
[B] is a Battery Charger.
'W' are impassable walls.

Your objective: Pickup packages and drop them off to the designated Drop Zones as listed in your ACTIVE ORDERS.
Beware: Your actions drain the robot's battery. If it hits 0%, you fail. Use [B] to recharge.
Do NOT crash into walls or other robots.

VALID COMMANDS:
move_north, move_south, move_east, move_west, pickup_item, drop_item, recharge, done

Evaluate the grid, look at your position, look at the nearest Package or Drop Zone, and decide the ONE single command to execute.
Output NOTHING ELSE except the exact command word.
"""

def extract_action(text: str) -> str:
    valid_actions = {
        "move_north", "move_south", "move_east", "move_west",
        "pickup_item", "drop_item", "recharge", "done"
    }
    text = text.lower()
    for action in valid_actions:
        if action in text:
            return action
    return "move_north"

def get_action(hud_text: str) -> str:
    try:
        response = llm.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": hud_text},
            ],
            max_tokens=10,
            temperature=0.0,
            timeout=10.0
        )
        content = response.choices[0].message.content.strip()
        return extract_action(content)
    except Exception as e:
        print(f"LLM Error: {e}", file=sys.stderr)
        return "move_north"

# ──────────────────────────────────────────────────────────
# EVALUATION LOOP
# ──────────────────────────────────────────────────────────

def run_evaluation():
    tasks = ["task1_easy", "task2_medium", "task3_hard"]
    
    # Use ENV_URL for local testing or default to hf space for production evaluation
    env_str = os.getenv("ENV_URL", "https://kalx0o-shatterdome-logistics-env.hf.space")

    for task_id in tasks:
        # ── [START] LOG ──
        print(f"[START] task={task_id} env=shatterdome-logistics-env model={MODEL_NAME}")

        success = "false"
        steps_taken = 0
        final_score = 0.0
        reward_history = []
        is_done = False

        try:
            with ShatterdomeClient(base_url=env_str).sync() as env:
                result = env.reset(task_id=task_id, seed=42)
                
                obs = result.observation
                is_done = obs.done

                while not is_done:
                    steps_taken += 1
                    
                    hud_display = obs.hud_display
                    action_str = get_action(hud_display)
                    
                    action_payload = ShatterdomeAction(action=action_str)
                    step_result = env.step(action_payload)
                    
                    obs = step_result.observation
                    is_done = obs.done
                    final_score = obs.grader_score
                    reward_val = round(step_result.reward, 2)
                    reward_history.append(f"{reward_val:.2f}")
                    
                    # ── [STEP] LOG ──
                    print(f"[STEP] step={steps_taken} action={action_str} reward={reward_val:.2f} done={str(is_done).lower()} error=null")
                    
                    if is_done:
                        if final_score > 0.0 and obs.packages_remaining == 0:
                            success = "true"
                        break

        except Exception as e:
            print(f"[STEP] step={steps_taken+1} action=error reward=0.00 done=true error={e}")
        finally:
            rewards_str = ",".join(reward_history) if reward_history else "0.00"
            final_score = max(0.01, min(0.99, final_score))
            print(f"[END] success={success} steps={steps_taken} score={final_score:.3f} rewards={rewards_str}")

if __name__ == "__main__":
    run_evaluation()
