"""
Seed the fixed experiment persona (田中翔太) PKG into Neo4j.

Usage:
    python -m newresearch.seed_pkg          # seed
    python -m newresearch.seed_pkg --check  # verify
    python -m newresearch.seed_pkg --clear  # delete then re-seed

Neo4j label scheme (newresearch-specific):
    (:ExpUser {persona_id, name, summary})
    (:PKGNode {node_id, label, type, weight})
    (:ExpUser)-[:HAS_PKG_NODE]->(:PKGNode)
    (:PKGNode)-[:{rel}]->(:PKGNode)        ← edge.rel as type
"""
from __future__ import annotations
import argparse
import logging
import os

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()
logger = logging.getLogger("newresearch")

# ── Persona definition (single source of truth for content) ───────

PERSONA_DEF = {
    "persona_id": "P1",
    "name": "田中 翔太",
    "summary": (
        "学部4年生（情報工学・AI専攻）。HCIと対話システムに興味があり、"
        "実装力が強み。研究の社会的意義や将来性に漠然とした不安を感じている。"
        "趣味はプログラミングとボードゲーム。内向的だが少人数の議論は好む。"
    ),
}

PKG_NODES = [
    {"node_id": "n1",  "label": "HCI",            "type": "interest", "weight": 0.9},
    {"node_id": "n2",  "label": "対話システム",     "type": "interest", "weight": 0.85},
    {"node_id": "n3",  "label": "実装力",          "type": "skill",    "weight": 0.9},
    {"node_id": "n4",  "label": "プログラミング",   "type": "skill",    "weight": 0.85},
    {"node_id": "n5",  "label": "研究の意義",       "type": "concern",  "weight": 0.8},
    {"node_id": "n6",  "label": "将来性への不安",   "type": "concern",  "weight": 0.75},
    {"node_id": "n7",  "label": "ユーザー価値の重視", "type": "value",  "weight": 0.8},
    {"node_id": "n8",  "label": "ボードゲーム",     "type": "interest", "weight": 0.5},
    {"node_id": "n9",  "label": "少人数の議論",     "type": "interest", "weight": 0.6},
    {"node_id": "n10", "label": "AI技術動向",       "type": "interest", "weight": 0.7},
]

PKG_EDGES = [
    {"src": "n1",  "dst": "n2",  "rel": "related_to"},
    {"src": "n2",  "dst": "n3",  "rel": "requires"},
    {"src": "n3",  "dst": "n4",  "rel": "is_a"},
    {"src": "n5",  "dst": "n6",  "rel": "causes"},
    {"src": "n1",  "dst": "n7",  "rel": "motivates"},
    {"src": "n7",  "dst": "n5",  "rel": "conflicts_with"},
    {"src": "n10", "dst": "n6",  "rel": "amplifies"},
]


def _get_driver():
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    user = os.environ.get("NEO4J_USERNAME", "neo4j")
    pw = os.environ.get("NEO4J_PASSWORD", "password123")
    auth = (user, pw) if user else None
    return GraphDatabase.driver(uri, auth=auth)


def clear(driver):
    """Remove all newresearch-specific nodes."""
    with driver.session() as s:
        s.run("MATCH (n:ExpUser) DETACH DELETE n")
        s.run("MATCH (n:PKGNode) DETACH DELETE n")
    logger.info("Cleared ExpUser / PKGNode nodes")


def seed(driver):
    """Write persona + PKG nodes + edges."""
    with driver.session() as s:
        # 1. Create ExpUser
        s.run(
            """
            MERGE (u:ExpUser {persona_id: $pid})
            SET u.name    = $name,
                u.summary = $summary
            """,
            pid=PERSONA_DEF["persona_id"],
            name=PERSONA_DEF["name"],
            summary=PERSONA_DEF["summary"],
        )

        # 2. Create PKGNode and link to ExpUser
        for node in PKG_NODES:
            s.run(
                """
                MATCH (u:ExpUser {persona_id: $pid})
                MERGE (n:PKGNode {node_id: $nid})
                SET n.label  = $label,
                    n.type   = $type,
                    n.weight = $weight
                MERGE (u)-[:HAS_PKG_NODE]->(n)
                """,
                pid=PERSONA_DEF["persona_id"],
                nid=node["node_id"],
                label=node["label"],
                type=node["type"],
                weight=node["weight"],
            )

        # 3. Create edges between PKGNodes
        for edge in PKG_EDGES:
            s.run(
                """
                MATCH (src:PKGNode {node_id: $src})
                MATCH (dst:PKGNode {node_id: $dst})
                MERGE (src)-[r:PKG_EDGE {rel: $rel}]->(dst)
                """,
                src=edge["src"],
                dst=edge["dst"],
                rel=edge["rel"],
            )

    logger.info(
        f"Seeded persona '{PERSONA_DEF['name']}' with "
        f"{len(PKG_NODES)} nodes, {len(PKG_EDGES)} edges"
    )


def check(driver) -> bool:
    """Verify the seed data exists and return True if valid."""
    with driver.session() as s:
        user = s.run(
            "MATCH (u:ExpUser {persona_id: $pid}) RETURN u",
            pid=PERSONA_DEF["persona_id"],
        ).single()
        if not user:
            print("✗ ExpUser not found")
            return False
        print(f"✓ ExpUser: {dict(user['u'])['name']}")

        nodes = s.run(
            """
            MATCH (u:ExpUser {persona_id: $pid})-[:HAS_PKG_NODE]->(n:PKGNode)
            RETURN n ORDER BY n.node_id
            """,
            pid=PERSONA_DEF["persona_id"],
        ).data()
        print(f"✓ PKGNode count: {len(nodes)}")
        for n in nodes:
            d = dict(n["n"])
            print(f"    {d['node_id']}: {d['label']} ({d['type']}, w={d['weight']})")

        edges = s.run(
            """
            MATCH (u:ExpUser {persona_id: $pid})-[:HAS_PKG_NODE]->(src:PKGNode)
                  -[r:PKG_EDGE]->(dst:PKGNode)
            RETURN src.node_id AS src, dst.node_id AS dst, r.rel AS rel
            """,
            pid=PERSONA_DEF["persona_id"],
        ).data()
        print(f"✓ PKG edges: {len(edges)}")
        for e in edges:
            print(f"    {e['src']} -[{e['rel']}]-> {e['dst']}")

    return len(nodes) == len(PKG_NODES) and len(edges) == len(PKG_EDGES)


def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description="Seed PKG into Neo4j")
    parser.add_argument("--check", action="store_true", help="Verify only")
    parser.add_argument("--clear", action="store_true", help="Clear + re-seed")
    args = parser.parse_args()

    driver = _get_driver()
    try:
        if args.check:
            ok = check(driver)
            raise SystemExit(0 if ok else 1)
        if args.clear:
            clear(driver)
        seed(driver)
        check(driver)
    finally:
        driver.close()


if __name__ == "__main__":
    main()
