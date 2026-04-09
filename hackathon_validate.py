import subprocess
import requests
import sys

PING_URL = "https://kalx0o-shatterdome-logistics-env.hf.space"

def run_cmd(cmd):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FAILED (Exit {result.returncode})")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        return False
    print("PASSED")
    return True

print("=== 1. Testing HF Space Ping ===")
try:
    resp = requests.post(f"{PING_URL}/reset", json={}, timeout=30)
    if resp.status_code == 200:
        print("PASSED: HF Space /reset returned 200")
    else:
        print(f"FAILED: HF Space returned {resp.status_code}")
except Exception as e:
    print(f"FAILED: Connection error {e}")

print("\n=== 2. Testing Docker Build ===")
# Note: Since Docker daemon on Windows might be down or not mapped, we'll try it but it might fail locally.
# However, the HuggingFace space screenshot shows it building successfully!
run_cmd("docker build . -t test-env")

print("\n=== 3. Testing Inference Baseline ===")
# We will test against the live endpoint if possible.
import os
os.environ["ENV_URL"] = PING_URL
os.environ["HF_TOKEN"] = "dummy-hackathon-token"
run_cmd("python inference.py > inference_output.txt")

try:
    with open("inference_output.txt", "r", encoding="utf-8") as f:
        content = f.read().strip()
        lines = content.split("\n")
        print("\nLog Format Check:")
        if len(lines) > 0:
            print("First two lines:")
            for l in lines[:2]: print(l)
            print("Last two lines:")
            for l in lines[-2:]: print(l)
            
            # Verify exact [START], [STEP], [END] presence
            has_start = any("[START]" in l for l in lines)
            has_end = any("[END]" in l for l in lines)
            has_step = any("[STEP]" in l for l in lines)
            if has_start and has_end and has_step:
                print("PASSED: [START], [STEP], and [END] tags found in output.")
            else:
                print("FAILED: Missing required logging tags in output.")
        else:
            print("FAILED: Inference output is empty")
except Exception as e:
    print(f"FAILED: Could not read inference output: {e}")
