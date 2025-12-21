#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Set environment
os.environ['MODE'] = 'LOCAL'
os.environ['PYTHONPATH'] = str(Path.cwd() / 'src')

print("=" * 60)
print("DUCKDB DEBUG SCRIPT")
print("=" * 60)

# Import config
sys.path.insert(0, 'src')
from _shared.common.config import LOCAL_CLEAN_DIR, PROJECT_ROOT

print(f"\n1. PROJECT_ROOT: {PROJECT_ROOT}")
print(f"2. LOCAL_CLEAN_DIR: {LOCAL_CLEAN_DIR}")
print(f"3. LOCAL_CLEAN_DIR exists: {LOCAL_CLEAN_DIR.exists()}")

if LOCAL_CLEAN_DIR.exists():
    print(f"\n4. Contents of LOCAL_CLEAN_DIR:")
    items = list(LOCAL_CLEAN_DIR.iterdir())
    print(f"   Total items: {len(items)}")
    
    for item in items:
        print(f"\n   - {item.name}")
        print(f"     is_dir: {item.is_dir()}")
        
        if item.is_dir():
            parquet_files = list(item.glob("year=*/data.parquet"))
            print(f"     parquet files: {len(parquet_files)}")
            
            # Test the exact code from local_duckdb.py
            import duckdb
            con = duckdb.connect(database=":memory:")
            
            name = item.name
            parquet_glob = str(item / "year=*/data.parquet")
            
            print(f"     Attempting to register with glob: {parquet_glob}")
            
            try:
                con.execute(f"""
                    CREATE OR REPLACE VIEW test_db."{name}" AS
                    SELECT * FROM read_parquet('{parquet_glob}')
                """)
                print(f"     ✅ SUCCESS: Registered {name}")
                
                # Test query
                result = con.execute(f'SELECT COUNT(*) as cnt FROM test_db."{name}"').fetchone()
                print(f"     Row count: {result[0]}")
                
            except Exception as e:
                print(f"     ❌ FAILED: {e}")

else:
    print(f"\n❌ LOCAL_CLEAN_DIR DOES NOT EXIST!")

print("\n" + "=" * 60)
print("Now testing the actual function...")
print("=" * 60)

try:
    from athena_runner.local_duckdb import run_duckdb_queries
    print("\n✅ Successfully imported run_duckdb_queries")
    
    # Don't run it yet, just check what it would do
    print("\nInspecting LOCAL_CLEAN_DIR from within the module...")
    from athena_runner.local_duckdb import LOCAL_CLEAN_DIR as MODULE_CLEAN_DIR
    print(f"Module's LOCAL_CLEAN_DIR: {MODULE_CLEAN_DIR}")
    print(f"Module's LOCAL_CLEAN_DIR exists: {MODULE_CLEAN_DIR.exists()}")
    
    if MODULE_CLEAN_DIR.exists():
        print(f"Module sees {len(list(MODULE_CLEAN_DIR.iterdir()))} items")
    
except Exception as e:
    print(f"\n❌ Error importing: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
