# src/athena_runner/runner.py

import time
from sql_loader import load_ddls, load_queries
from athena import run_athena_query, athena # Import the client too
from common.logging import setup_logging

logger = setup_logging(__name__)

def run_all():
    ddls = load_ddls()
    queries = load_queries()

    executed_ddls = []
    executed_queries = []

    # 1. Run DDLs sequentially
    for name, ddl in ddls.items():
        logger.info(f"Executing DDL: {name}")
        qid = run_athena_query(
            sql=ddl.strip(),  # Good to strip whitespace
            output_prefix=f"ddl/{name}/",
        )
        executed_ddls.append({"name": name, "qid": qid})

    # --- Metadata Propagation Cooldown ---
    if ddls and queries:  # Only sleep if we have both DDLs and downstream queries
        logger.info("DDLs completed. Applying 3-second cooldown for Glue Catalog propagation...")
        time.sleep(3)

    # 2. Run analytics queries sequentially
    for name, sql in queries.items():
        logger.info(f"Executing Analysis Query: {name}")
        qid = run_athena_query(
            sql=sql.strip(),
            output_prefix=f"athena/{name}/",
        )
        executed_queries.append({"name": name, "qid": qid})

    total_ddls = len(executed_ddls)
    total_queries = len(executed_queries)
    logger.info(f"Run complete: {total_ddls} DDLs, {total_queries} analysis queries executed.")

    return {
        "status": "success",
        "ddls": executed_ddls,
        "queries": executed_queries,
        "summary": {
            "ddls_executed": total_ddls,
            "queries_executed": total_queries,
        }
    }
