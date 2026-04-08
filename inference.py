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

ENV_URL = os.getenv("ENV_URL", "http://localhost:7860")
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.groq.com/openai/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
HF_TOKEN = os.getenv("HF_TOKEN")

if not HF_TOKEN:
    print("Warning: HF_TOKEN environment variable is not set. Inference may fail if API requires auth.")

llm = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN or "dummy-key-for-local"
)

# ──────────────────────────────────────────────────────────
# AGENT PROMPT
# ──────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
You are the AI co-pilot for a PPDC Jaeger in the Shatterdome.
You receive a CONN-POD HUD which shows the layout of the facility.

[J0] is your Jaeger (if empty). [J0*] means your Jaeger is carrying a Plasma Core.
[C:01] is a Plasma Core on the floor.
[B:A] is Jaeger Bay A.
[R] is a Reactor Charger.
'W' are impassable walls.

Your objective: Secure Plasma Cores and deploy them to the designated Jaeger Bays as listed in your DIRECTIVES.
Beware: Your actions drain the Jaeger's reactor. If it hits 0%, you fail. Use [R] to recharge.
Do NOT crash into walls or other Jaegers.

VALID COMMANDS:
move_north, move_south, move_east, move_west, load_core, deploy_core, recharge, done

Evaluate the grid, look at your position, look at the nearest Core or Bay, and decide the ONE single command to execute.
Output NOTHING ELSE except the exact command word.
"""

def extract_action(text: str) -> str:
    valid_actions = {
        "move_north", "move_south", "move_east", "move_west",
        "load_core", "deploy_core", "recharge", "done"
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

    for task_id in tasks:
        # ── [START] LOG ──
        print(f"[START] task={task_id} env=shatterdome-logistics-env model={MODEL_NAME}")

        success = "false"
        steps_taken = 0
        final_score = 0.0
        reward_history = []
        is_done = False

        try:
            with ShatterdomeClient(base_url=ENV_URL).sync() as env:
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
                        if final_score > 0.0 and obs.cores_remaining == 0:
                            success = "true"
                        break

        except Exception as e:
            print(f"[STEP] step={steps_taken+1} action=error reward=0.00 done=true error={e}")
        finally:
            rewards_str = ",".join(reward_history) if reward_history else "0.00"
            # ── [END] LOG ──
            print(f"[END] success={success} steps={steps_taken} score={final_score:.2f} rewards={rewards_str}")

if __name__ == "__main__":
    run_evaluation()
