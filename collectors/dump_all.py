"""
Export ALL data from Redis to a permanent JSONL file.
"""

import redis
import json
from pathlib import Path

REDIS_KEY = "collector:incoming"

# Connect to Redis
try:
    r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
    r.ping()
    print("Connected to Redis")
except Exception as e:
    print("❌ Could not connect to Redis:", e)
    exit()

# Prepare export directory
output_dir = Path("data_output/export")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "redis_dump.jsonl"

# Get queue length
length = r.llen(REDIS_KEY)
print(f"📦 Total messages to export: {length}")

with open(output_file, "w", encoding="utf-8") as f:
    for i in range(length):
        msg = r.lindex(REDIS_KEY, i)
        if msg:
            f.write(msg + "\n")

print(f"✅ Export complete! Saved to: {output_file}")
