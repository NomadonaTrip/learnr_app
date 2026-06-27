"""
Verify the prerequisite knowledge graph is populated and healthy.

Exits 0 if all invariants hold, 1 otherwise. Safe to run in CI after
build_prerequisite_graph.py or after any concept re-extraction.

Usage:
    python scripts/verify_prerequisite_graph.py --course-id <UUID>
"""
import argparse
import asyncio
import os
import sys
from pathlib import Path
from uuid import UUID

import networkx as nx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Match build_prerequisite_graph.py bootstrap: make `src` importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "apps" / "api"))


async def verify(course_id: UUID) -> list[str]:
    """Return a list of failure messages (empty list == healthy)."""
    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://learnr:learnr123@localhost:5432/learnr_dev",
    )
    engine = create_async_engine(database_url, echo=False)
    failures: list[str] = []

    async with engine.connect() as conn:
        concept_count = (
            await conn.execute(
                text("SELECT count(*) FROM concepts WHERE course_id = :cid"),
                {"cid": str(course_id)},
            )
        ).scalar_one()
        if concept_count == 0:
            return [
                "No concepts for this course. Run scripts/extract_babok_concepts.py first."
            ]

        edge_rows = (
            await conn.execute(
                text(
                    """
                    SELECT cp.concept_id, cp.prerequisite_concept_id
                    FROM concept_prerequisites cp
                    JOIN concepts c ON c.id = cp.concept_id
                    WHERE c.course_id = :cid
                    """
                ),
                {"cid": str(course_id)},
            )
        ).all()

        if len(edge_rows) == 0:
            failures.append("0 prerequisite edges — run build_prerequisite_graph.py.")

        self_loops = sum(1 for a, b in edge_rows if a == b)
        if self_loops:
            failures.append(f"{self_loops} self-loop edges found.")

        depth_distinct = (
            await conn.execute(
                text(
                    "SELECT count(DISTINCT prerequisite_depth) FROM concepts "
                    "WHERE course_id = :cid"
                ),
                {"cid": str(course_id)},
            )
        ).scalar_one()
        if edge_rows and depth_distinct <= 1:
            failures.append(
                "prerequisite_depth has a single value — depths not computed."
            )

        graph = nx.DiGraph()
        graph.add_edges_from((str(a), str(b)) for a, b in edge_rows)
        if not nx.is_directed_acyclic_graph(graph):
            failures.append("Graph contains cycles (not a DAG).")

        roots = [n for n in graph.nodes if graph.out_degree(n) == 0]
        if edge_rows and not roots:
            failures.append("No root concepts (every node has a prerequisite).")

        avg_prereqs = (len(edge_rows) / concept_count) if concept_count else 0
        max_depth = (
            await conn.execute(
                text(
                    "SELECT COALESCE(max(prerequisite_depth), 0) FROM concepts "
                    "WHERE course_id = :cid"
                ),
                {"cid": str(course_id)},
            )
        ).scalar_one()

        print(f"concepts={concept_count} edges={len(edge_rows)} "
              f"avg_prereqs={avg_prereqs:.2f} max_depth={max_depth} roots={len(roots)}")

    await engine.dispose()
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify prerequisite graph health")
    parser.add_argument(
        "--course-id",
        default="1b8a4860-156f-4d06-8393-85c4088db2d9",
        help="Course UUID (defaults to CBAP)",
    )
    args = parser.parse_args()
    failures = asyncio.run(verify(UUID(args.course_id)))
    if failures:
        print("FAIL:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("OK: prerequisite graph is healthy.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
