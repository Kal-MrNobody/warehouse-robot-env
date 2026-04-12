---
title: Shatterdome Logistics Env
emoji: 🤖
colorFrom: blue
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
---

# 📦 Shatterdome Logistics: A Physics-Aware Warehouse RL Training Environment

## Project Overview
**GitHub:** https://github.com/Kal-MrNobody/shatterdome-logistics-env  
**HF Space (Live API):** https://huggingface.co/spaces/KalX0o/shatterdome-logistics-env  
**Tagline:** A deterministic warehouse simulation designed to train autonomous AI agents against real-world E-Commerce logistics constraints.

---

## The Problem
Modern fulfillment centers deploying autonomous robots face a critical gap: 
AI agents trained on toy environments fail catastrophically in production. 
They drain batteries mid-route, damage fragile shipments, miss SLA deadlines, 
and collide with other robots — costing operators millions per incident.

Shatterdome Logistics provides a safe, reproducible training ground where 
agents learn to handle these failure modes before touching real hardware.

---

## Environment Design

**Full OpenEnv spec compliance:** `step()`, `reset()`, `state()` endpoints 
with typed Pydantic models extending OpenEnv base classes, wrapped in a 
FastAPI server running in a Docker container on HuggingFace Spaces.

**Physics engine beyond basic pathfinding:**

- **SLA Countdown Engine:** Priority packages carry strict step deadlines. 
  Miss the deadline and the order is cancelled with a grading penalty.
- **Dynamic Battery-Weight Mechanics:** Packages spawn with `weight: heavy` 
  attributes. Carrying heavy freight multiplies battery drain by 3.0x per step, 
  forcing the agent to plan charger detours proactively.
- **Fragility Collision Physics:** Packages flagged `fragile: true` shatter 
  on any wall or robot collision while being carried — irreversible failure.
- **WMS HUD Renderer:** A custom renderer outputs an intuitive ASCII 
  Warehouse Management System display rather than raw coordinate arrays, 
  optimized for LLM spatial reasoning.

---

## Tasks

| ID | Difficulty | Description | Max Steps |
|---|---|---|---|
| task1_easy | Easy | Single package delivery, clear path, battery monitoring | 25 |
| task2_medium | Medium | 3 packages, heavy weights, battery drain active, SLA deadline | 60 |
| task3_hard | Hard | 2 robots, 4 packages (2 fragile+priority), collision avoidance | 100 |

Grader scores are returned as floats in [0.0, 1.0] per task.

---

## Baseline Results

| Task | Grader Score | Model |
|---|---|---|
| task1_easy | 0.010 | llama-3.3-70b-versatile |
| task2_medium | 0.010 | llama-3.3-70b-versatile |
| task3_hard | 0.010 | llama-3.3-70b-versatile |

---

## Setup & Quickstart

```bash
# Clone and install
git clone https://github.com/Kal-MrNobody/shatterdome-logistics-env
cd shatterdome-logistics-env
uv run uvicorn server.app:app --host 0.0.0.0 --port 7860

# Run baseline (separate terminal)
export HF_TOKEN="your_token"
export ENV_URL="http://localhost:7860"
python inference.py

# Or via Docker
docker build -t shatterdome-env .
docker run -p 7860:7860 shatterdome-env
```

Dependencies locked via `uv.lock` for full reproducibility.
