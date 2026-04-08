---
title: Shatterdome Logistics Env
emoji: 🤖
colorFrom: blue
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
---

# Shatterdome Logistics Environment (PPDC)

*A production-ready OpenEnv baseline for the Meta OpenEnv x Scaler Hackathon.*

Welcome to the **Shatterdome Logistics Environment**. The Pan Pacific Defense Corps (PPDC) requires an intelligent neural handshake to coordinate Jaeger base deployments. Kaiju attacks leave little room for error. Your objective is to train or engineer an agent capable of guiding Jaegers to secure Plasma Cores and deploy them into assigned Jaeger Bays. 

## The Mission

The environment operates on a 10×10 grid inside a Shatterdome.
* **[J]** Jaegers (Agents)
* **[C]** Plasma Cores
* **[B]** Jaeger Bays
* **[R]** Reactor Chargers
* **W** Impassable walls

### Task Difficulties:
1. **task1_easy**: A basic 1-core logistical drop in an open hangar.
2. **task2_medium**: A 3-core loadout protocol. Structural hazards map the area, and the Jaeger's reactor constantly decays. You must utilize the reactor charger to survive.
3. **task3_hard**: Multi-Jaeger deployment with priority loading sequences. Heavy reactor drain and major penalties for Jaeger-on-Jaeger collisions.

---

## Action Space
Your agent must issue one exact command per step:
* `move_north`, `move_south`, `move_east`, `move_west`
* `load_core` (picks up a core from current relative position)
* `deploy_core` (drops the core into a bay)
* `recharge` (powers up reactor if on an `[R]` cell)
* `done` (terminates early)

## Observation Space (CONN-POD HUD)
Your agent is provided a rendered structural ASCII map, current core directives, and reactor/stress diagnostic metrics on every step to calculate the optimal neural command.

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
