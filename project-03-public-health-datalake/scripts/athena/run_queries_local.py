#!/usr/bin/env python3
"""
Local DuckDB analytics runner for Project 3.

Consumes:
- local_data/clean/*.parquet
- local_sql/duckdb/queries/*.sql

Produces:
- evidence/athena/*.csv
"""

import duckdb
from pathlib import Path
from datetime import datetime

CLEAN_DIR = Path("local_data/clean")
SQL_DIR = Path("local_sql/duckdb/queries")
OUT_DIR = Path("evidence/athena")

OUT_DIR.mkdir(parents=True, exist_ok=True)

con = duckdb.connect(database=":memory:")

# ------------------------------------------------------------------
# Register Parquet datasets
# ------------------------------------------------------------------
print("Registering Parquet datasets")

con.execute(f"""
CREATE VIEW who_indicators AS
SELECT * FROM read_parquet('{CLEAN_DIR}/who/**/*.parquet', hive_partitioning=1);
""")

con.execute(f"""
CREATE VIEW worldbank_indicators AS
SELECT * FROM read_parquet('{CLEAN_DIR}/worldbank/**/*.parquet', hive_partitioning=1);
""")

con.execute(f"""
CREATE VIEW who_outbreaks AS
SELECT * FROM read_parquet('{CLEAN_DIR}/who_outbreaks/**/*.parquet');
""")

# ------------------------------------------------------------------
# Run SQL queries
# ------------------------------------------------------------------
ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

for sql_file in sorted(SQL_DIR.glob("*.sql")):
    name = sql_file.stem
    print(f"Running {name}")

    query = sql_file.read_text()
    df = con.execute(query).df()

    out = OUT_DIR / f"{name}-{ts}.csv"
    df.to_csv(out, index=False)

    print(f"  → wrote {out}")

print("\nLocal DuckDB analytics completed.")
