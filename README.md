---
title: Shatterdome Logistics Env
emoji: 🤖
colorFrom: blue
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
---

# Shatterdome Logistics Environment

*A production-ready OpenEnv baseline for the Meta OpenEnv x Scaler Hackathon.*

Welcome to the **Shatterdome Logistics Environment**. E-Commerce fulfillment centers (like Amazon or Flipkart) require intelligent, automated systems to coordinate robot fleets. Your objective is to train or engineer an AI agent capable of guiding warehouse robots to pick up customer packages and deliver them to designated shipping drop-zones without colliding or draining their battery. 

## The Mission

The environment operates on a 10×10 grid inside a fulfillment warehouse.
* **[R]** Robots (Agents)
* **[P]** Packages
* **[Z]** Drop Zones
* **[B]** Battery Chargers
* **W** Impassable walls / racking

### Task Difficulties:
1. **task1_easy**: A basic 1-package delivery in an open warehouse area.
2. **task2_medium**: A 3-package order fulfillment protocol. Structural hazards map the area, and the Robot's battery constantly decays. You must utilize the battery charger to survive.
3. **task3_hard**: Multi-Robot deployment with priority loading sequences. Heavy battery drain and major penalties for robot-on-robot collisions.

---

## Action Space
Your agent must issue one exact command per step:
* `move_north`, `move_south`, `move_east`, `move_west`
* `pickup_item` (picks up a package from current relative position)
* `drop_item` (drops the package into a drop zone)
* `recharge` (powers up battery if on a `[B]` cell)
* `done` (terminates early)

## Observation Space (WMS HUD)
Your agent is provided a rendered structural ASCII map (Warehouse Management System), current active orders, and battery/damage diagnostics on every step to calculate the optimal instruction.

---

## Technical Setup

### 1. Requirements
Ensure you are using Python 3.10+ and have the OpenEnv core installed.
```bash
pip install -r server/requirements.txt
```

### 2. Run the Environment Server
```bash
uvicorn server.app:app --host 0.0.0.0 --port 7860
```
This will start the WebSocket and HTTP endpoints required by the OpenEnv spec.

### 3. Run the Inference Baseline
In a new terminal, configure your keys and trigger the baseline solver:
```bash
export API_BASE_URL="https://api.groq.com/openai/v1"
export MODEL_NAME="llama-3.3-70b-versatile"
export HF_TOKEN="your-hf-token"

python inference.py
```
This produces structured logs `[START]`, `[STEP]`, `[END]` conforming precisely to the hackathon validation requirements.
