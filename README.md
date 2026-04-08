---
title: Warehouse Robot Env
emoji: 🤖
colorFrom: indigo
colorTo: cyan
sdk: docker
app_port: 7860
pinned: false
---

# Warehouse Robot RL Environment

An OpenEnv-compliant reinforcement learning environment where an AI agent controls warehouse robots to pick items from shelves and deliver them to drop zones — before their battery runs out or the step budget expires.

Built for the real-world logistics domain. The core challenge: navigating cluttered warehouse floors, handling priority orders, and coordinating multiple robots without collisions.

---

## Why This?

Modern warehouses run hundreds of autonomous robots, and the failure modes are expensive:

- A robot picks the wrong SKU → customer gets the wrong item → return + refund
- Two robots collide → one is stuck, blocking an aisle for hours
- A robot runs out of battery mid-task → manual rescue required

Training RL agents in simulation before putting them on real hardware is the standard approach at Amazon, Flipkart, Delhivery. This environment replicates those failure scenarios so agents can learn to avoid them cheaply.

---

## Environment

10×10 grid. Wall border. Shelves, charger cells, and drop zones placed inside.

The agent receives an ASCII text observation at each step:

```
╔════════════════════════════════════════════╗
║  WAREHOUSE - Task: task1_easy  Step 3/25   ║
╠════════════════════════════════════════════╣
║   W   W   W   W   W   W   W   W   W   W   ║
║   W   .   .   .   .   .   .   .   .   W   ║
║   W  [I:001] .   .   .   .  [D:A]  .   W  ║
║   W   .   .   .   .   .   .   .   .   W   ║
║   W   .   .   .  [R0]  .   .   .   .   W  ║
║   W   .   .   .   .   .   .   .   .   W   ║
║   W   W   W   W   W   W   W   W   W   W   ║
╠════════════════════════════════════════════╣
║  ROBOTS                                    ║
║  R0 | (4,4) | Cargo: None | Bat: 100%     ║
╠════════════════════════════════════════════╣
║  ORDER                                     ║
║  [ ] SKU-001 → ZONE-A  [pickup: (2,2)]    ║
╠════════════════════════════════════════════╣
║  Progress: 0/1 delivered                   ║
║  Penalties so far: 0.0                     ║
╠════════════════════════════════════════════╣
║  VALID ACTIONS:                            ║
║  move_north  move_south  move_east         ║
║  move_west   pick_item   place_item        ║
║  charge      done                          ║
║  → Output EXACTLY ONE action word only.    ║
╚════════════════════════════════════════════╝
```

---

## Tasks

| Task | Difficulty | max_steps | Robots | Items | Battery drain |
|------|-----------|-----------|--------|-------|---------------|
| `task1_easy` | Easy | 25 | 1 | 1 | None |
| `task2_medium` | Medium | 60 | 1 | 3 | 2.0 / step |
| `task3_hard` | Hard | 100 | 2 | 4 (2 priority) | 1.5 / step |

---

## Actions & Rewards

| Action | Effect |
|--------|--------|
| `move_north/south/east/west` | Move one cell. +0.05 if closer to target, -0.05 if farther, -0.20 on wall |
| `pick_item` | +0.20 correct, -0.30 wrong SKU, -0.10 invalid |
| `place_item` | +0.50 correct zone, -0.30 wrong zone, -0.10 invalid |
| `charge` | +0.05 on charger cell, -0.10 off charger |
| `done` | Ends episode |

All deliveries complete → **+1.00 bonus**.

Battery at 0 → **-0.40 per action** (robot is stranded).

---

## Grader Scores (0.0 – 1.0)

Each task has its own grader:

- **task1_easy**: 1.0 for full delivery, 0.5 for picking up, -0.05 per wall collision
- **task2_medium**: 0.33 per item, +0.1 speed bonus, penalties for collisions and battery deaths
- **task3_hard**: 0.25 per priority item, 0.15 per regular item, collision and efficiency bonuses

---

## Quickstart

```bash
pip install openenv-core fastapi uvicorn pydantic openai websockets requests

# Start server
uvicorn server.app:app --host 0.0.0.0 --port 7860

# Run baseline agent (needs HF_TOKEN set)
export HF_TOKEN=your_token_here
python inference.py
```

Or with Docker:

```bash
docker build -t warehouse-env .
docker run -p 7860:7860 -e HF_TOKEN=your_token warehouse-env
```

---

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Server info + task list |
| `/health` | GET | `{"status": "healthy"}` |
| `/reset` | POST | Start new episode |
| `/step` | POST | Execute action |
| `/state` | GET | Current episode state |
| `/schema` | GET | Action/observation JSON schema |
| `/docs` | GET | Swagger UI |
| `/ws` | WS | WebSocket session (used by inference.py) |

---

## Project Structure

```
warehouse_robot_env/
├── inference.py          ← Baseline LLM agent (evaluator runs this)
├── openenv.yaml          ← OpenEnv manifest
├── Dockerfile            ← Docker build (HF Spaces)
├── README.md
├── __init__.py
├── models.py             ← Action, Observation, State classes
├── client.py             ← WebSocket client helper
├── warehouse/
│   ├── grid.py           ← Grid setup for each task
│   ├── robot.py          ← Robot state and movement
│   └── renderer.py       ← ASCII renderer for LLM consumption
├── tasks/
│   └── graders.py        ← Per-task scoring functions
└── server/
    ├── app.py            ← FastAPI app (create_app wrapper)
    ├── environment.py    ← Core Environment class
    └── requirements.txt
```

---

## License

MIT
