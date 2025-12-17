"""
local_test_ingest.py
Verifies the Ingest Lambda logic by running it in LOCAL mode.
This ensures APIs are reachable and files are written to the correct local path.
"""

import json
import os
import sys
from pathlib import Path

# 1. Add 'src' to path so we can import our modules
sys.path.append(str(Path(__file__).parent / "src"))

# 2. Force LOCAL mode for testing, even if environment is set otherwise
os.environ["MODE"] = "LOCAL"

from ingest.app import lambda_handler
from common.config import LOCAL_RAW_DIR

def run_test():
    print(f"Starting Local Ingest Test...")
    print(f"Target Directory: {LOCAL_RAW_DIR.absolute()}")

    # 3. Invoke the handler with an empty event (simulating a manual trigger)
    response = lambda_handler({}, None)

    # 4. Parse the result
    body = json.loads(response["body"])

    print("\n--- Test Results ---")
    print(f"Status: {body['status']}")
    print(f"Attempted: {body['datasets_attempted']}")

    success_count = 0
    for res in body["results"]:
        dataset = res.get("dataset")
        if "error" in res:
            print(f"{dataset}: FAILED - {res['error']}")
        else:
            success_count += 1
            print(f"{dataset}: SUCCESS (Stored at: {res.get('path')})")

    # 5. Summary
    print("\n--- Summary ---")
    if success_count == body['datasets_attempted']:
        print("ALL DATASETS INGESTED SUCCESSFULLY")
    else:
        print(f"{success_count}/{body['datasets_attempted']} datasets succeeded.")

    # 6. Verify directory actually contains files
    files = list(LOCAL_RAW_DIR.glob("*"))
    print(f"Total files now in raw directory: {len(files)}")

if __name__ == "__main__":
    try:
        run_test()
    except KeyboardInterrupt:
        print("\nTest cancelled by user.")
        sys.exit(1)
