"""
inference.py — Baseline agent for the Warehouse Robot RL environment.

Runs all three tasks sequentially and emits structured [START], [STEP],
and [END] log lines to stdout for automated evaluation.

Environment variables:
    API_BASE_URL  LLM endpoint          (default: HuggingFace router)
    MODEL_NAME    Model identifier       (default: Llama-3.1-8B-Instruct)
    HF_TOKEN      HuggingFace API key
    ENV_URL       Environment server URL (default: http://localhost:7860)
"""

import json
import os
import sys

from openai import OpenAI
from client import WarehouseEnv
from models import WarehouseAction

# ── Config from environment variables ────────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/Llama-3.1-8B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN", "")
ENV_URL = os.getenv("ENV_URL", "http://localhost:7860")

llm = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN or "dummy")

SYSTEM_PROMPT = (
    "You are a warehouse robot controller. "
    "Read the ASCII warehouse grid carefully and output EXACTLY ONE action word — nothing else.\n\n"
    "Valid actions: move_north  move_south  move_east  move_west  "
    "pick_item  place_item  charge  done\n\n"
    "Strategy:\n"
    "- Navigate toward the nearest item listed in ORDER that hasn't been delivered.\n"
    "- When standing on an item cell and that SKU is in the order -> pick_item.\n"
    "- After picking, navigate to the correct ZONE shown in the order -> place_item.\n"
    "- If battery < 15% and currently on a charger cell [C] -> charge.\n"
    "- If all items are delivered -> done.\n"
    "- Never move into walls (W cells)."
)

VALID_ACTIONS = [
    "move_north", "move_south", "move_east", "move_west",
    "pick_item", "place_item", "charge", "done",
]


def get_action(observation_text: str) -> str:
    """Query the LLM and extract a valid action string."""
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
            print(f"LLM error (attempt {attempt + 1}): {exc}", file=sys.stderr, flush=True)
    return "move_north"


def run_task(task_id: str, max_steps: int, seed: int = 42) -> float:
    """Run one episode and return the grader score."""

    with WarehouseEnv(base_url=ENV_URL).sync() as env:
        result = env.reset(task_id=task_id, seed=seed)

        # [START] — emitted once per episode
        print(
            "[START] " + json.dumps({
                "task_id": task_id,
                "seed": seed,
                "max_steps": max_steps,
                "items_remaining": result.observation.items_remaining,
            }),
            flush=True,
        )

        cumulative_reward = 0.0

        for step_num in range(1, max_steps + 1):
            action = get_action(result.observation.grid_text)
            result = env.step(WarehouseAction(action=action))

            step_reward = result.observation.reward or 0.0
            cumulative_reward += step_reward

            # [STEP] — emitted after each action
            print(
                "[STEP] " + json.dumps({
                    "task_id": task_id,
                    "step": step_num,
                    "action": action,
                    "reward": round(step_reward, 4),
                    "cumulative_reward": round(cumulative_reward, 4),
                    "items_remaining": result.observation.items_remaining,
                    "done": result.done,
                }),
                flush=True,
            )

            if result.done:
                break

        score = result.observation.grader_score

        # [END] — emitted once per episode
        print(
            "[END] " + json.dumps({
                "task_id": task_id,
                "score": round(score, 4),
                "cumulative_reward": round(cumulative_reward, 4),
                "steps_taken": result.observation.steps_taken,
                "max_steps": max_steps,
                "done_reason": result.observation.done_reason,
            }),
            flush=True,
        )

    return score


def main():
    tasks = [
        ("task1_easy",   25),
        ("task2_medium", 60),
        ("task3_hard",  100),
    ]

    scores = {}
    for task_id, max_steps in tasks:
        scores[task_id] = run_task(task_id, max_steps)

    # Summary
    avg = sum(scores.values()) / len(scores)
    print("\n--- Results ---", flush=True)
    for tid, sc in scores.items():
        print(f"  {tid:<20} {sc:.4f}", flush=True)
    print(f"  {'average':<20} {avg:.4f}", flush=True)


if __name__ == "__main__":
    main()
