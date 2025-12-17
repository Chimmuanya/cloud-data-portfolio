from pathlib import Path

BASE_DIR = Path(__file__).parent
DDL_DIR = BASE_DIR / "sql" / "ddl"
QUERY_DIR = BASE_DIR / "sql" / "queries"

def load_ddls() -> dict[str, str]:
    # --- SANITY CHECK ---
    if not DDL_DIR.exists():
        raise FileNotFoundError(
            f"DDL directory missing in Lambda environment: {DDL_DIR}. "
            "Check if 'sql/' folder was included in the deployment package."
        )

    files = sorted(DDL_DIR.glob("*.sql"))
    if not files:
        print(f"Warning: No .sql files found in {DDL_DIR}")

    return {p.stem: p.read_text(encoding="utf-8") for p in files}

def load_queries() -> dict[str, str]:
    if not QUERY_DIR.exists():
        raise FileNotFoundError(f"Query directory missing: {QUERY_DIR}")

    files = sorted(QUERY_DIR.glob("*.sql"))
    return {p.stem: p.read_text(encoding="utf-8") for p in files}
