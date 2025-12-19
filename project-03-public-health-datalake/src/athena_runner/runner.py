# src/athena_runner/runner.py
import time
from sql_loader import load_ddls, load_queries
from athena import run_athena_query
from common.logging import setup_logging

logger = setup_logging(__name__)

def run_all():
    ddls = load_ddls()
    queries = load_queries()

    executed_ddls = []
    executed_queries = []

    # ------------------------------------------------------------
    # 1. Run DDLs sequentially (NO MSCK — tables use projection)
    # ------------------------------------------------------------
    for name, ddl in ddls.items():
        logger.info(f"Executing DDL: {name}")

        qid = run_athena_query(
            sql=ddl.strip(),
            output_prefix=f"ddl/{name}/",
        )
        executed_ddls.append({"name": name, "qid": qid})

    # Small cooldown for Glue catalog propagation
    if ddls:
        logger.info(
            "DDLs completed. Applying 3-second cooldown for Glue catalog propagation..."
        )
        time.sleep(3)

    # ------------------------------------------------------------
    # 2. Run analytics queries sequentially
    # ------------------------------------------------------------
    for name, sql in queries.items():
        logger.info(f"Executing Analysis Query: {name}")

        qid = run_athena_query(
            sql=sql.strip(),
            output_prefix=f"athena/{name}/",
        )
        executed_queries.append({"name": name, "qid": qid})

    logger.info(
        "Run complete: %d DDLs executed, %d analysis queries executed.",
        len(executed_ddls),
        len(executed_queries),
    )

    return {
        "status": "success",
        "ddls": executed_ddls,
        "queries": executed_queries,
        "summary": {
            "ddls_executed": len(executed_ddls),
            "queries_executed": len(executed_queries),
        },
    }
