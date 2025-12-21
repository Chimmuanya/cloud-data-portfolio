from pathlib import Path

BASE_DIR = Path(__file__).parent
DDL_DIR = BASE_DIR / "sql" / "ddl"
QUERY_DIR = BASE_DIR / "sql" / "queries"

# Any DDL whose filename matches these will be skipped by the runner
# (views are infrastructure, not runtime artifacts)
SKIP_DDL_PREFIXES = {
    "ddl_who_indicators",
    "ddl_worldbank_indicators",
}

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
        return {}

    ddls: dict[str, str] = {}

    for p in files:
        stem = p.stem

        # Skip logical views (managed outside Lambda)
        if stem in SKIP_DDL_PREFIXES:
            print(f"Skipping view DDL in Lambda: {stem}")
            continue

        ddls[stem] = p.read_text(encoding="utf-8")

    return ddls


def load_queries() -> dict[str, str]:
    if not QUERY_DIR.exists():
        raise FileNotFoundError(
            f"Query directory missing in Lambda environment: {QUERY_DIR}"
        )

    files = sorted(QUERY_DIR.glob("*.sql"))
    if not files:
        print(f"Warning: No query .sql files found in {QUERY_DIR}")
        return {}

    return {p.stem: p.read_text(encoding="utf-8") for p in files}
