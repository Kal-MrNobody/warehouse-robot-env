"""
inference.py — Baseline agent for the Warehouse Robot RL environment.

Runs all three tasks and emits structured [START], [STEP], [END] logs.

Environment variables:
    API_BASE_URL  LLM endpoint          (default: HF router)
    MODEL_NAME    Model identifier       (default: Llama-3.1-8B-Instruct)
    HF_TOKEN      HuggingFace API key
    ENV_URL       Server URL             (default: http://localhost:7860)
"""

import os
import sys
from typing import List, Optional

from openai import OpenAI
from client import WarehouseEnv
from models import WarehouseAction

# ── Config ───────────────────────────────────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/Llama-3.1-8B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("API_KEY", "")
ENV_URL = os.getenv("ENV_URL", "http://localhost:7860")
BENCHMARK = "warehouse-robot-env"

llm = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN or "dummy")

SYSTEM_PROMPT = (
    "You are a warehouse robot controller. "
    "Read the ASCII warehouse grid and output EXACTLY ONE action word — nothing else.\n\n"
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


# ── Structured stdout logging ────────────────────────────────────────

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    done_val = str(done).lower()
    error_val = error if error else "null"
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}",
        flush=True,
    )


# ── LLM call ─────────────────────────────────────────────────────────

def get_action(observation_text: str) -> str:
    """Query the LLM and return a valid action string."""
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


# ── Episode runner ───────────────────────────────────────────────────

def run_task(task_id: str, max_steps: int, seed: int = 42) -> float:
    """Run one episode, emit structured logs, return grader score."""

    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=task_id, env=BENCHMARK, model=MODEL_NAME)

    try:
        with WarehouseEnv(base_url=ENV_URL).sync() as env:
            result = env.reset(task_id=task_id, seed=seed)

            for step_num in range(1, max_steps + 1):
                if result.done:
                    break

                action = get_action(result.observation.grid_text)
                result = env.step(WarehouseAction(action=action))

                step_reward = result.observation.reward or 0.0
                done = result.done
                error = None

                rewards.append(step_reward)
                steps_taken = step_num

                log_step(
                    step=step_num,
                    action=action,
                    reward=step_reward,
                    done=done,
                    error=error,
                )

                if done:
                    break

            score = result.observation.grader_score
            score = min(max(score, 0.0), 1.0)
            success = score > 0.0

    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return score


# ── Main ─────────────────────────────────────────────────────────────

def main():
    tasks = [
        ("task1_easy",   25),
        ("task2_medium", 60),
        ("task3_hard",  100),
    ]

    scores = {}
    for task_id, max_steps in tasks:
        scores[task_id] = run_task(task_id, max_steps)

    avg = sum(scores.values()) / len(scores)
    print("\n--- Results ---", flush=True)
    for tid, sc in scores.items():
        print(f"  {tid:<20} {sc:.4f}", flush=True)
    print(f"  {'average':<20} {avg:.4f}", flush=True)


if __name__ == "__main__":
    main()
