#!/usr/bin/env python3
import os
from pathlib import Path

# Set environment
os.environ['MODE'] = 'LOCAL'
os.environ['PYTHONPATH'] = str(Path.cwd() / 'src')

# Import config
from athena_runner.common.config import LOCAL_CLEAN_DIR, PROJECT_ROOT

print(f"PROJECT_ROOT: {PROJECT_ROOT}")
print(f"LOCAL_CLEAN_DIR: {LOCAL_CLEAN_DIR}")
print(f"LOCAL_CLEAN_DIR exists: {LOCAL_CLEAN_DIR.exists()}")
print(f"LOCAL_CLEAN_DIR is absolute: {LOCAL_CLEAN_DIR.is_absolute()}")

if LOCAL_CLEAN_DIR.exists():
    print("\nContents of LOCAL_CLEAN_DIR:")
    for item in LOCAL_CLEAN_DIR.iterdir():
        print(f"  - {item.name} (is_dir: {item.is_dir()})")
        if item.is_dir():
            parquet_files = list(item.glob("**/*.parquet"))
            print(f"    Parquet files: {len(parquet_files)}")
            if parquet_files:
                print(f"    Example: {parquet_files[0]}")
else:
    print(f"\nERROR: Directory does not exist!")
    print(f"Current working directory: {Path.cwd()}")
