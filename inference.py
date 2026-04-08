"""
Baseline inference agent for the Warehouse Robot RL environment.

Connects to the running server via WebSocket, runs all three tasks,
and prints structured logs that the evaluator parses.

Required env vars:
    API_BASE_URL  – LLM endpoint          (default: HF router)
    MODEL_NAME    – model identifier       (default: Llama-3.1-8B-Instruct)
    HF_TOKEN      – Hugging Face API key
"""

import os
import sys
import json
import time

from openai import OpenAI
from client import WarehouseEnv
from models import WarehouseAction

# ── configuration ────────────────────────────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/Llama-3.1-8B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN", "")
ENV_URL = os.getenv("ENV_URL", "http://localhost:7860")

if not HF_TOKEN:
    print("WARNING: HF_TOKEN not set – LLM calls will fail.", file=sys.stderr)

llm = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

SYSTEM_PROMPT = (
    "You are a warehouse robot controller. "
    "Read the ASCII warehouse grid and output EXACTLY ONE action word.\n\n"
    "Valid actions: move_north  move_south  move_east  move_west  "
    "pick_item  place_item  charge  done\n\n"
    "Strategy:\n"
    "- Navigate toward the nearest incomplete order item.\n"
    "- When on the item cell and item is in the order -> pick_item.\n"
    "- After picking, navigate to the correct drop zone -> place_item.\n"
    "- If battery < 15% and on charger cell -> charge.\n"
    "- When all items delivered -> done.\n"
    "- Avoid walls and other robots."
)

VALID_ACTIONS = [
    "move_north", "move_south", "move_east", "move_west",
    "pick_item", "place_item", "charge", "done",
]


def query_llm(observation_text: str) -> str:
    """Send the grid observation to the LLM and extract a valid action."""
    for attempt in range(2):
        try:
            response = llm.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": observation_text},
                ],
                max_tokens=10,
                temperature=0.0,
            )
            raw = response.choices[0].message.content.strip().lower()
            for action in VALID_ACTIONS:
                if action in raw:
                    return action
        except Exception as exc:
            print(f"  LLM error (attempt {attempt + 1}): {exc}", file=sys.stderr)
    return "move_north"


def run_task(task_id: str, max_steps: int, seed: int = 42) -> dict:
    """Run a single episode and return summary dict."""
    with WarehouseEnv(base_url=ENV_URL).sync() as env:
        result = env.reset(task_id=task_id, seed=seed)

        # ── [START] log ──
        start_payload = {
            "task_id": task_id,
            "seed": seed,
            "max_steps": max_steps,
            "items_remaining": result.observation.items_remaining,
        }
        print(f"[START] {json.dumps(start_payload)}", flush=True)

        total_reward = 0.0
        final_step = 0

        for step_idx in range(max_steps):
            action = query_llm(result.observation.grid_text)
            result = env.step(WarehouseAction(action=action))

            reward = result.observation.reward if result.observation.reward else 0.0
            total_reward += reward
            final_step = step_idx + 1

            # ── [STEP] log ──
            step_payload = {
                "task_id": task_id,
                "step": final_step,
                "action": action,
                "reward": round(reward, 4),
                "total_reward": round(total_reward, 4),
                "done": result.done,
                "items_remaining": result.observation.items_remaining,
            }
            print(f"[STEP] {json.dumps(step_payload)}", flush=True)

            if result.done:
                break

        score = result.observation.grader_score

        # ── [END] log ──
        end_payload = {
            "task_id": task_id,
            "score": round(score, 4),
            "total_reward": round(total_reward, 4),
            "steps_used": final_step,
            "max_steps": max_steps,
            "done_reason": result.observation.done_reason,
        }
        print(f"[END] {json.dumps(end_payload)}", flush=True)

        return end_payload


def main():
    tasks = [
        ("task1_easy", 25),
        ("task2_medium", 60),
        ("task3_hard", 100),
    ]
    results = {}

    for task_id, steps in tasks:
        summary = run_task(task_id, steps)
        results[task_id] = summary["score"]

    # Final summary
    avg_score = sum(results.values()) / len(results)
    print("\n--- Final Results ---")
    for tid, sc in results.items():
        print(f"  {tid:<20} {sc:.4f}")
    print(f"  {'average':<20} {avg_score:.4f}")


if __name__ == "__main__":
    main()
