---
title: Warehouse Robot Env
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# Warehouse Robot RL Environment

A production-ready, OpenEnv-compliant reinforcement learning environment for training AI-controlled warehouse robots. Built for the real-world logistics/robotics domain.

## Problem Statement

Modern warehouses (Amazon, Flipkart, Delhivery) are deploying AI-controlled robots at scale. Untrained agents cause catastrophic failures:

- **Wrong Item Picks** — Robots pick incorrect SKUs, causing order errors and returns
- **Robot Collisions** — Multi-robot warehouses suffer from path conflicts and physical damage
- **Infinite Movement Loops** — Agents get stuck in repetitive patterns, blocking aisles
- **Battery Drain** — Robots strand mid-task when battery management is ignored

These failures cost millions per year in damaged goods, stranded robots, and SLA breaches. This environment provides a safe, deterministic simulator to train agents **before** deploying to real hardware.

## Environment Description

A 2D 10×10 grid warehouse where AI agents control robots to:

1. **Navigate** around walls and obstacles
2. **Pick items** from shelf locations (identified by SKU)
3. **Deliver items** to designated drop zones
4. **Manage battery** by visiting charging stations
5. **Avoid collisions** with walls and other robots

The environment supports 3 difficulty levels with increasing complexity: single-item delivery, multi-item with battery constraints, and multi-robot coordination with priority orders.

## Action Space

| Action | Description | Reward Impact |
|--------|-------------|---------------|
| `move_north` | Move robot up (row - 1) | +0.05 closer / -0.05 farther / -0.20 wall |
| `move_south` | Move robot down (row + 1) | +0.05 closer / -0.05 farther / -0.20 wall |
| `move_east` | Move robot right (col + 1) | +0.05 closer / -0.05 farther / -0.20 wall |
| `move_west` | Move robot left (col - 1) | +0.05 closer / -0.05 farther / -0.20 wall |
| `pick_item` | Pick up item at current cell | +0.20 correct / -0.30 wrong / -0.10 invalid |
| `place_item` | Place item at current drop zone | +0.50 correct / -0.30 wrong / -0.10 invalid |
| `charge` | Charge battery at charger cell | +0.05 on charger / -0.10 not on charger |
| `done` | Signal episode completion | Ends episode immediately |

## Observation Space

The observation is an ASCII-rendered grid with full state information, designed for LLM agents:

```
╔════════════════════════════════════════════╗
║  WAREHOUSE - Task: task1_easy  Step 3/25   ║
╠════════════════════════════════════════════╣
║   W   W   W   W   W   W   W   W   W   W   ║
║   W   .   .   .   .   .   .   .   .   W   ║
║   W   . [I:001]  .   .   .  [D:A]  .   W   ║
║   W   .   .   .   .   .   .   .   .   W   ║
║   W   .   .   .  [R0]  .   .   .   .   W   ║
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

## Tasks

| Task ID | Difficulty | Description | Max Steps | Robots | Items | Battery Drain |
|---------|-----------|-------------|-----------|--------|-------|---------------|
| `task1_easy` | Easy | Single item pickup and delivery, clear path | 25 | 1 | 1 | None |
| `task2_medium` | Medium | Three items, static obstacles, battery management | 60 | 1 | 3 | 2.0/step |
| `task3_hard` | Hard | Two robots, four items (two priority), collision avoidance | 100 | 2 | 4 | 1.5/step |

## Reward Function

### Positive Rewards

| Event | Reward |
|-------|--------|
| Correct item picked up (SKU matches order) | +0.20 |
| Item delivered to correct drop zone | +0.50 |
| ALL order items delivered (bonus) | +1.00 |
| Moving closer to current target (Manhattan) | +0.05 |
| Charging on charger cell | +0.05 |

### Negative Rewards

| Event | Reward |
|-------|--------|
| Moving away from current target | -0.05 |
| Invalid action string | -0.10 |
| pick_item when not on item cell | -0.10 |
| pick_item when already carrying | -0.10 |
| place_item when not carrying | -0.10 |
| place_item when not on drop zone | -0.10 |
| Wall collision | -0.20 |
| Picked wrong SKU (not in order) | -0.30 |
| Delivered to wrong drop zone (item lost) | -0.30 |
| Battery reached 0 (robot stranded) | -0.40 |
| Robot-robot collision (Task 3) | -0.50 |
| Per remaining incomplete order at step limit | -0.10 |

### Grader Score

Each task has a separate grader that computes a score in `[0.0, 1.0]` at episode end, evaluating delivery completion, efficiency, battery management, and collision avoidance.

## Setup & Usage

### Install Dependencies

```bash
pip install openenv-core fastapi uvicorn openai websockets pydantic
```

### Start Server

```bash
cd warehouse_robot_env
uvicorn server.app:app --host 0.0.0.0 --port 7860
```

### Docker

```bash
# Build
docker build -t warehouse-env -f server/Dockerfile .

# Run
docker run -p 7860:7860 warehouse-env
```

### Health Check

```bash
curl http://localhost:7860/health
# → {"status":"healthy","service":"warehouse-robot-env"}
```

### Python Usage (Sync)

```python
from client import WarehouseEnv
from models import WarehouseAction

with WarehouseEnv(base_url="http://localhost:7860").sync() as env:
    result = env.reset(task_id="task1_easy", seed=42)
    print(result.observation.grid_text)

    result = env.step(WarehouseAction(action="move_north"))
    print(f"Reward: {result.observation.reward}")
    print(f"Done: {result.observation.done}")
```

### Python Usage (Async)

```python
import asyncio
from client import WarehouseEnv
from models import WarehouseAction

async def main():
    async with WarehouseEnv(base_url="http://localhost:7860") as env:
        result = await env.reset(task_id="task2_medium", seed=42)
        result = await env.step(WarehouseAction(action="move_east"))
        print(result.observation.grid_text)

asyncio.run(main())
```

### Run Baseline Agent

```bash
# Set environment variables
export HF_TOKEN=your_token_here
export MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct

# Run inference
python inference.py
```

## Baseline Scores

| Task | Expected Score | Notes |
|------|---------------|-------|
| `task1_easy` | 0.7 - 1.0 | Simple navigation + pick + deliver |
| `task2_medium` | 0.3 - 0.7 | Requires pathfinding around obstacles + battery management |
| `task3_hard` | 0.1 - 0.5 | Multi-robot coordination is challenging for current LLMs |

## Real-World Motivation

This environment directly models challenges faced by warehouse robotics companies:

- **Amazon Robotics** (Kiva Systems): 750,000+ robots across fulfillment centers. Training in simulation before deployment prevents $millions in damaged inventory.
- **Flipkart**: India's largest e-commerce company uses AI-controlled robots in its warehouses for order fulfillment.
- **Delhivery**: Uses autonomous sorting robots that must navigate shared spaces without collisions.

Key real-world parallels:
- **Battery management** → Real robots must return to charging stations before dying
- **Collision avoidance** → Multi-robot warehouses require coordinated pathfinding
- **Priority orders** → Same-day/next-day orders must be fulfilled first
- **Wrong picks** → Picking errors cascade into returns, refunds, and customer churn

By training agents in this simulator, companies can validate robot behavior **before** deploying to production warehouses, reducing failures by orders of magnitude.

## Architecture

```
warehouse_robot_env/
├── inference.py          ← Baseline LLM agent
├── openenv.yaml          ← OpenEnv manifest
├── README.md             ← This file
├── __init__.py           ← Package exports
├── models.py             ← Dataclass models (Action, Observation, State)
├── client.py             ← EnvClient WebSocket client
├── warehouse/
│   ├── grid.py           ← 10x10 grid with task configs
│   ├── robot.py          ← RobotAgent: position, battery, cargo
│   └── renderer.py       ← ASCII renderer for LLM consumption
├── tasks/
│   └── graders.py        ← Task-specific grading functions
└── server/
    ├── app.py            ← FastAPI server via create_app()
    ├── environment.py    ← Core Environment class
    ├── requirements.txt  ← Python dependencies
    └── Dockerfile        ← Multi-stage Docker build

```

## License

MIT
