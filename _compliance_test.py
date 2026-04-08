"""
Full hackathon compliance test — mirrors the official pre-submission checklist.
Run this before submitting.
"""
import requests
import json
import os
import sys
import io
import re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE = "https://kalx0o-warehouse-robot-env.hf.space"
REPO = "d:\\warehouse_robot_env"

PASS = 0
FAIL = 0

def ok(label, detail=""):
    global PASS
    PASS += 1
    print(f"  [PASS] {label}")
    if detail:
        print(f"         {detail}")

def fail(label, detail=""):
    global FAIL
    FAIL += 1
    print(f"  [FAIL] {label}")
    if detail:
        print(f"         {detail}")

print("=" * 50)
print("  HACKATHON PRE-SUBMISSION COMPLIANCE CHECK")
print("=" * 50)

# ── 1. HF SPACE DEPLOYS ──────────────────────────────
print("\n[1] HF Space deploys and responds")

r = requests.get(BASE + "/health", timeout=15)
if r.status_code == 200 and r.json().get("status") == "healthy":
    ok("/health returns 200", r.json())
else:
    fail("/health", f"Got {r.status_code}")

r2 = requests.post(BASE + "/reset", json={}, timeout=20)
if r2.status_code == 200:
    ok("POST /reset returns 200 (validator check #1)")
else:
    fail("POST /reset", f"Got {r2.status_code}")

# reset with task_id
for task_id in ["task1_easy", "task2_medium", "task3_hard"]:
    r = requests.post(BASE + "/reset", json={"task_id": task_id, "seed": 42}, timeout=20)
    if r.status_code == 200:
        ok(f"POST /reset task={task_id}")
    else:
        fail(f"POST /reset task={task_id}", f"Got {r.status_code}")

# ── 2. OPENENV SPEC COMPLIANCE ───────────────────────
print("\n[2] OpenEnv spec compliance")

# typed models schema
r3 = requests.get(BASE + "/schema", timeout=10)
schema = r3.json()
has_action = "action" in schema
has_obs = "observation" in schema
has_state = "state" in schema
if has_action and has_obs and has_state:
    ok("Schema has typed Action + Observation + State")
else:
    fail("Schema missing models", f"keys={list(schema.keys())}")

# check action fields
action_schema = schema.get("action", {}).get("properties", {})
if "action" in action_schema:
    ok("WarehouseAction has 'action' field")
else:
    fail("WarehouseAction missing 'action' field")

# check observation fields
obs_schema = schema.get("observation", {}).get("properties", {})
required_obs = ["grid_text", "items_remaining", "steps_taken", "done", "reward",
                "task_id", "grader_score", "current_order", "robots"]
missing = [f for f in required_obs if f not in obs_schema]
if not missing:
    ok("WarehouseObservation has all required fields")
else:
    fail("WarehouseObservation missing fields", str(missing))

# state endpoint
r4 = requests.post(BASE + "/reset", json={"task_id": "task1_easy", "seed": 42}, timeout=20)
r5 = requests.get(BASE + "/state", timeout=10)
state_ok = r5.status_code == 200
if state_ok:
    ok("GET /state returns 200", str(r5.json())[:100])
else:
    fail("GET /state", f"Got {r5.status_code}: {r5.text[:100]}")

# metadata
r6 = requests.get(BASE + "/metadata", timeout=10)
if r6.status_code == 200:
    ok("GET /metadata returns 200")
else:
    fail("GET /metadata", f"Got {r6.status_code}")

# openenv.yaml
yaml_path = os.path.join(REPO, "openenv.yaml")
if os.path.exists(yaml_path):
    import yaml
    with open(yaml_path) as f:
        cfg = yaml.safe_load(f)
    tasks = cfg.get("tasks", [])
    if len(tasks) >= 3:
        ok(f"openenv.yaml has {len(tasks)} tasks")
    else:
        fail("openenv.yaml", f"Only {len(tasks)} tasks (need 3+)")
    if cfg.get("name") and cfg.get("version"):
        ok("openenv.yaml has name + version")
    else:
        fail("openenv.yaml missing name or version")
else:
    fail("openenv.yaml not found")

# ── 3. DOCKERFILE ────────────────────────────────────
print("\n[3] Dockerfile")
df_path = os.path.join(REPO, "Dockerfile")
if os.path.exists(df_path):
    with open(df_path) as f:
        df_content = f.read()
    has_port = "7860" in df_content
    has_cmd = "CMD" in df_content or "ENTRYPOINT" in df_content
    ok("Root Dockerfile exists")
    ok("Exposes port 7860") if has_port else fail("Missing EXPOSE 7860")
    ok("Has CMD/ENTRYPOINT") if has_cmd else fail("Missing CMD or ENTRYPOINT")
else:
    fail("Root Dockerfile not found")

# ── 4. INFERENCE SCRIPT ──────────────────────────────
print("\n[4] Baseline inference script")
inf_path = os.path.join(REPO, "inference.py")
if os.path.exists(inf_path):
    with open(inf_path, encoding="utf-8") as f:
        inf_content = f.read()
    ok("inference.py exists at root")
    if "from openai import OpenAI" in inf_content:
        ok("Uses OpenAI client")
    else:
        fail("Missing OpenAI client")
    if "API_BASE_URL" in inf_content and "MODEL_NAME" in inf_content and "HF_TOKEN" in inf_content:
        ok("Reads API_BASE_URL, MODEL_NAME, HF_TOKEN from env vars")
    else:
        fail("Missing env var reads")
    if "[START]" in inf_content and "[STEP]" in inf_content and "[END]" in inf_content:
        ok("Contains [START], [STEP], [END] log markers")
    else:
        fail("Missing structured log markers")
    # Check exact format
    start_ok = re.search(r'\[START\]\s+task=', inf_content)
    step_ok = re.search(r'\[STEP\]\s+step=', inf_content)
    end_ok = re.search(r'\[END\]\s+success=', inf_content)
    if start_ok and step_ok and end_ok:
        ok("Log format matches spec: key=value style")
    else:
        fail("Log format mismatch — check [START]/[STEP]/[END] field names")
else:
    fail("inference.py not found at root")

# ── 5. 3+ TASKS WITH GRADERS ─────────────────────────
print("\n[5] 3+ tasks with graders")
graders_path = os.path.join(REPO, "tasks", "graders.py")
if os.path.exists(graders_path):
    with open(graders_path, encoding="utf-8") as f:
        grader_content = f.read()
    for cls in ["Task1Grader", "Task2Grader", "Task3Grader"]:
        if f"class {cls}" in grader_content:
            ok(f"{cls} exists")
        else:
            fail(f"{cls} missing")

# Test grader scores via API — simulate a full episode and check score is in [0,1]
for task_id in ["task1_easy", "task2_medium", "task3_hard"]:
    r = requests.post(BASE + "/reset", json={"task_id": task_id, "seed": 42}, timeout=20)
    obs = r.json().get("observation", {})
    score = obs.get("grader_score", -1)
    if 0.0 <= score <= 1.0:
        ok(f"{task_id} grader_score={score} in [0.0, 1.0]")
    else:
        fail(f"{task_id} grader_score out of range", f"score={score}")

# ── 6. REWARD FUNCTION ───────────────────────────────
print("\n[6] Reward function — non-sparse signal")
r_reset = requests.post(BASE + "/reset", json={"task_id": "task1_easy", "seed": 42}, timeout=20)
rewards_seen = set()
for act in ["move_north", "move_south", "move_east", "pick_item", "place_item"]:
    r_step = requests.post(BASE + "/step", json={"action": {"action": act}}, timeout=15)
    if r_step.status_code == 200:
        rew = r_step.json().get("reward")
        if rew is not None:
            rewards_seen.add(round(float(rew), 2))
if len(rewards_seen) >= 2:
    ok(f"Reward varies across actions: {sorted(rewards_seen)}")
else:
    fail("Reward may be sparse", f"Only seen: {rewards_seen}")

# ── 7. README ─────────────────────────────────────────
print("\n[7] README completeness")
readme_path = os.path.join(REPO, "README.md")
if os.path.exists(readme_path):
    with open(readme_path, encoding="utf-8") as f:
        readme = f.read()
    checks = {
        "environment description": any(w in readme.lower() for w in ["warehouse", "robot", "description"]),
        "action space": "action" in readme.lower(),
        "observation space": "observation" in readme.lower(),
        "tasks": "task" in readme.lower(),
        "setup instructions": any(w in readme.lower() for w in ["install", "run", "quickstart", "setup"]),
    }
    for label, passed in checks.items():
        ok(f"README has {label}") if passed else fail(f"README missing {label}")
else:
    fail("README.md not found")

# ── SUMMARY ──────────────────────────────────────────
print()
print("=" * 50)
total = PASS + FAIL
print(f"  Results: {PASS}/{total} checks passed")
if FAIL == 0:
    print("  ALL PASSED — READY TO SUBMIT!")
else:
    print(f"  {FAIL} check(s) FAILED — fix above")
print("=" * 50)
print()
print("  GitHub:   https://github.com/Kal-MrNobody/warehouse-robot-env")
print("  HF Space: https://huggingface.co/spaces/KalX0o/warehouse-robot-env")
