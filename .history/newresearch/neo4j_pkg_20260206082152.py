"""
Neo4j PKG reader — loads Persona + PKG from Neo4j at runtime.
Replaces the hardcoded PKG in scenarios.py.
"""
from __future__ import annotations
import logging
import os

from dotenv import load_dotenv
from neo4j import GraphDatabase

from newresearch.schemas import Persona, PKGData, PKGNode, PKGEdge

load_dotenv()
logger = logging.getLogger("newresearch")


def _get_driver():
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    user = os.environ.get("NEO4J_USERNAME", "neo4j")
    pw = os.environ.get("NEO4J_PASSWORD", "password123")
    auth = (user, pw) if user else None
    return GraphDatabase.driver(uri, auth=auth)


def load_persona_from_neo4j(persona_id: str = "P1") -> Persona:
    """
    Read ExpUser + PKGNode/PKG_EDGE from Neo4j and return a Persona object.
    Raises RuntimeError if data is missing.
    """
    driver = _get_driver()
    try:
        with driver.session() as s:
            # 1. Read ExpUser
            user_rec = s.run(
                "MATCH (u:ExpUser {persona_id: $pid}) RETURN u",
                pid=persona_id,
            ).single()
            if not user_rec:
                raise RuntimeError(
                    f"ExpUser '{persona_id}' not found in Neo4j. "
                    f"Run `python -m newresearch.seed_pkg` first."
                )
            user = dict(user_rec["u"])

            # 2. Read PKGNodes
            node_records = s.run(
                """
                MATCH (u:ExpUser {persona_id: $pid})-[:HAS_PKG_NODE]->(n:PKGNode)
                RETURN n ORDER BY n.node_id
                """,
                pid=persona_id,
            ).data()
            nodes = []
            for rec in node_records:
                d = dict(rec["n"])
                nodes.append(PKGNode(
                    id=d["node_id"],
                    label=d["label"],
                    type=d["type"],
                    weight=d.get("weight", 0.5),
                ))

            # 3. Read PKG edges
            edge_records = s.run(
                """
                MATCH (u:ExpUser {persona_id: $pid})-[:HAS_PKG_NODE]->(src:PKGNode)
                      -[r:PKG_EDGE]->(dst:PKGNode)
                RETURN src.node_id AS src, dst.node_id AS dst, r.rel AS rel
                """,
                pid=persona_id,
            ).data()
            edges = []
            for rec in edge_records:
                edges.append(PKGEdge(
                    src=rec["src"],
                    dst=rec["dst"],
                    rel=rec["rel"],
                ))

            logger.info(
                f"[Neo4j] Loaded persona '{user['name']}' "
                f"({len(nodes)} nodes, {len(edges)} edges)"
            )

            return Persona(
                persona_id=persona_id,
                name=user["name"],
                summary=user["summary"],
                pkg=PKGData(enabled=True, nodes=nodes, edges=edges),
            )
    finally:
        driver.close()
