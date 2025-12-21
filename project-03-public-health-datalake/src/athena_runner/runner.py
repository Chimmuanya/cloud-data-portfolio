# src/athena_runner/runner.py

import time
from common.config import MODE
from common.logging import setup_logging

logger = setup_logging(__name__)

def run_all():
    """
    Unified analytics runner.

    LOCAL  >> DuckDB
    CLOUD  >> Athena
    """
    if MODE == "LOCAL":
        logger.info("MODE=LOCAL >> running DuckDB analytics")
        from athena_runner.local_duckdb import run_duckdb_queries
        run_duckdb_queries()
        return {
            "status": "success",
            "engine": "duckdb",
        }

    # ---------------- CLOUD (ATHENA) ----------------
    logger.info("MODE=CLOUD >> running Athena analytics")

    from sql_loader import load_ddls, load_queries
    from athena import run_athena_query

    ddls = load_ddls()
    queries = load_queries()

    executed_ddls = []
    executed_queries = []

    for name, ddl in ddls.items():
        logger.info("Executing DDL: %s", name)
        qid = run_athena_query(
            sql=ddl.strip(),
            output_prefix=f"ddl/{name}/",
        )
        executed_ddls.append({"name": name, "qid": qid})

    if ddls:
        logger.info("Cooldown for Glue propagation...")
        time.sleep(3)

    for name, sql in queries.items():
        logger.info("Executing Athena query: %s", name)
        qid = run_athena_query(
            sql=sql.strip(),
            output_prefix=f"athena/{name}/",
        )
        executed_queries.append({"name": name, "qid": qid})

    return {
        "status": "success",
        "engine": "athena",
        "ddls": executed_ddls,
        "queries": executed_queries,
    }
