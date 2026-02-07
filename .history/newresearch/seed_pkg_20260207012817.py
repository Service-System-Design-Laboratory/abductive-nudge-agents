"""
Seed experiment personas (3 Nemotron-based) PKG into Neo4j.

Usage:
    python -m newresearch.seed_pkg          # seed all 3 personas
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

# ══════════════════════════════════════════════════════════════
# Persona definitions — derived from Nemotron-Personas-Japan
# 3 personas selected for diversity:
#   P01: 杉浦泰章 (47M, 郵便局, 新潟) — ローカル・自然志向
#   P05: 鈴木弥一 (53M, 遊技場経営, 千葉) — データ・節約志向
#   P07: 岡田咲弥 (27F, 農業, 宮城) — 計画的・地域文化志向
# ══════════════════════════════════════════════════════════════

PERSONA_DEFS = [
    # ── P01: 杉浦 泰章 ──────────────────────────────────────────
    {
        "persona_id": "P01",
        "name": "杉浦 泰章",
        "summary": (
            "47歳、郵便局中堅（新潟県）。紙ベースの業務と地域行事への参加を通じて、"
            "柔軟な信頼構築と穏やかな健康維持を実現する、実直な暮らしと協調性に根ざす人。"
            "里山祭と稲刈り体験を中心に、自然と地域行事の結びつきを深く味わう"
            "ローカルツアー型の旅を好む。趣味は書道・読書・散歩・米作り。"
        ),
        "nodes": [
            {"node_id": "p01_n1",  "label": "里山散策",         "type": "interest", "weight": 0.9},
            {"node_id": "p01_n2",  "label": "地域行事・祭り",    "type": "interest", "weight": 0.85},
            {"node_id": "p01_n3",  "label": "書道",             "type": "interest", "weight": 0.7},
            {"node_id": "p01_n4",  "label": "自然との調和",      "type": "value",    "weight": 0.9},
            {"node_id": "p01_n5",  "label": "地域住民との信頼",   "type": "value",    "weight": 0.85},
            {"node_id": "p01_n6",  "label": "紙ベース管理",      "type": "skill",    "weight": 0.8},
            {"node_id": "p01_n7",  "label": "ローカルツアー",     "type": "interest", "weight": 0.85},
            {"node_id": "p01_n8",  "label": "伝統調理法",        "type": "interest", "weight": 0.6},
            {"node_id": "p01_n9",  "label": "デジタル苦手",      "type": "concern",  "weight": 0.7},
            {"node_id": "p01_n10", "label": "退職後の文化活動",   "type": "concern",  "weight": 0.65},
        ],
        "edges": [
            {"src": "p01_n1",  "dst": "p01_n4",  "rel": "motivates"},
            {"src": "p01_n2",  "dst": "p01_n5",  "rel": "strengthens"},
            {"src": "p01_n4",  "dst": "p01_n7",  "rel": "drives"},
            {"src": "p01_n7",  "dst": "p01_n1",  "rel": "includes"},
            {"src": "p01_n5",  "dst": "p01_n2",  "rel": "requires"},
            {"src": "p01_n6",  "dst": "p01_n9",  "rel": "related_to"},
            {"src": "p01_n8",  "dst": "p01_n4",  "rel": "expresses"},
            {"src": "p01_n10", "dst": "p01_n2",  "rel": "motivates"},
        ],
    },

    # ── P05: 鈴木 弥一 ──────────────────────────────────────────
    {
        "persona_id": "P05",
        "name": "鈴木 弥一",
        "summary": (
            "53歳、遊技場中小経営者（千葉県）。データ分析と節約志向で事業最適化と"
            "健康管理を同時に実現し、少人数競争型の静かなリーダーシップで社会的価値を拡大する。"
            "低予算で地方の祭りや郷土料理を巡り、少人数で深く地域交流を楽しむ旅を好む。"
            "趣味はレトロゲーム収集・模型鉄道・歴史小説・低予算料理・家庭菜園。"
        ),
        "nodes": [
            {"node_id": "p05_n1",  "label": "データ分析",        "type": "skill",    "weight": 0.9},
            {"node_id": "p05_n2",  "label": "節約志向",          "type": "value",    "weight": 0.9},
            {"node_id": "p05_n3",  "label": "コスト最適化",       "type": "skill",    "weight": 0.85},
            {"node_id": "p05_n4",  "label": "レトロゲーム",       "type": "interest", "weight": 0.7},
            {"node_id": "p05_n5",  "label": "模型鉄道",          "type": "interest", "weight": 0.65},
            {"node_id": "p05_n6",  "label": "低予算旅行",        "type": "interest", "weight": 0.85},
            {"node_id": "p05_n7",  "label": "少人数交流",        "type": "value",    "weight": 0.75},
            {"node_id": "p05_n8",  "label": "歴史小説",          "type": "interest", "weight": 0.6},
            {"node_id": "p05_n9",  "label": "2号店出店計画",      "type": "concern",  "weight": 0.8},
            {"node_id": "p05_n10", "label": "家庭菜園",          "type": "interest", "weight": 0.5},
        ],
        "edges": [
            {"src": "p05_n1",  "dst": "p05_n3",  "rel": "enables"},
            {"src": "p05_n2",  "dst": "p05_n6",  "rel": "drives"},
            {"src": "p05_n3",  "dst": "p05_n9",  "rel": "motivates"},
            {"src": "p05_n6",  "dst": "p05_n7",  "rel": "includes"},
            {"src": "p05_n4",  "dst": "p05_n5",  "rel": "related_to"},
            {"src": "p05_n2",  "dst": "p05_n3",  "rel": "requires"},
            {"src": "p05_n8",  "dst": "p05_n4",  "rel": "related_to"},
            {"src": "p05_n10", "dst": "p05_n2",  "rel": "supports"},
        ],
    },

    # ── P07: 岡田 咲弥 ──────────────────────────────────────────
    {
        "persona_id": "P07",
        "name": "岡田 咲弥",
        "summary": (
            "27歳、農業（宮城県）。計画的な農業運営と地域文化への敬意を基盤に、"
            "リスク回避と協調性のバランスで持続可能な有機野菜ブランドを追求する。"
            "季節祭りの開催地や近隣里山を徒歩で巡り、地域の食材と文化行事を体感する"
            "ローカルツーリズムの探求者。趣味は季節祭り参加・郷土料理研究・田園散歩・"
            "野菜料理実験・編み物。"
        ),
        "nodes": [
            {"node_id": "p07_n1",  "label": "計画的運営",        "type": "skill",    "weight": 0.9},
            {"node_id": "p07_n2",  "label": "地域文化への敬意",   "type": "value",    "weight": 0.9},
            {"node_id": "p07_n3",  "label": "有機野菜ブランド",   "type": "concern",  "weight": 0.85},
            {"node_id": "p07_n4",  "label": "季節祭り参加",      "type": "interest", "weight": 0.85},
            {"node_id": "p07_n5",  "label": "郷土料理研究",      "type": "interest", "weight": 0.8},
            {"node_id": "p07_n6",  "label": "リスク回避",        "type": "value",    "weight": 0.75},
            {"node_id": "p07_n7",  "label": "先輩農家への敬意",   "type": "value",    "weight": 0.8},
            {"node_id": "p07_n8",  "label": "土壌管理",          "type": "skill",    "weight": 0.85},
            {"node_id": "p07_n9",  "label": "保存食研究",        "type": "interest", "weight": 0.7},
            {"node_id": "p07_n10", "label": "田園散歩",          "type": "interest", "weight": 0.6},
        ],
        "edges": [
            {"src": "p07_n1",  "dst": "p07_n3",  "rel": "drives"},
            {"src": "p07_n2",  "dst": "p07_n4",  "rel": "motivates"},
            {"src": "p07_n2",  "dst": "p07_n7",  "rel": "includes"},
            {"src": "p07_n4",  "dst": "p07_n5",  "rel": "related_to"},
            {"src": "p07_n5",  "dst": "p07_n9",  "rel": "extends"},
            {"src": "p07_n6",  "dst": "p07_n1",  "rel": "motivates"},
            {"src": "p07_n8",  "dst": "p07_n3",  "rel": "supports"},
            {"src": "p07_n10", "dst": "p07_n2",  "rel": "strengthens"},
        ],
    },
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
    """Write all personas + PKG nodes + edges."""
    for pdef in PERSONA_DEFS:
        _seed_one(driver, pdef)


def _seed_one(driver, pdef: dict):
    """Seed a single persona."""
    pid = pdef["persona_id"]
    with driver.session() as s:
        # 1. Create ExpUser
        s.run(
            """
            MERGE (u:ExpUser {persona_id: $pid})
            SET u.name    = $name,
                u.summary = $summary
            """,
            pid=pid,
            name=pdef["name"],
            summary=pdef["summary"],
        )

        # 2. Create PKGNode and link to ExpUser
        for node in pdef["nodes"]:
            s.run(
                """
                MATCH (u:ExpUser {persona_id: $pid})
                MERGE (n:PKGNode {node_id: $nid})
                SET n.label  = $label,
                    n.type   = $type,
                    n.weight = $weight
                MERGE (u)-[:HAS_PKG_NODE]->(n)
                """,
                pid=pid,
                nid=node["node_id"],
                label=node["label"],
                type=node["type"],
                weight=node["weight"],
            )

        # 3. Create edges between PKGNodes
        for edge in pdef["edges"]:
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
        f"Seeded persona '{pdef['name']}' ({pid}) with "
        f"{len(pdef['nodes'])} nodes, {len(pdef['edges'])} edges"
    )


def check(driver) -> bool:
    """Verify the seed data exists and return True if valid."""
    all_ok = True
    for pdef in PERSONA_DEFS:
        pid = pdef["persona_id"]
        with driver.session() as s:
            user = s.run(
                "MATCH (u:ExpUser {persona_id: $pid}) RETURN u",
                pid=pid,
            ).single()
            if not user:
                print(f"✗ ExpUser '{pid}' not found")
                all_ok = False
                continue
            print(f"✓ ExpUser: {dict(user['u'])['name']} ({pid})")

            nodes = s.run(
                """
                MATCH (u:ExpUser {persona_id: $pid})-[:HAS_PKG_NODE]->(n:PKGNode)
                RETURN n ORDER BY n.node_id
                """,
                pid=pid,
            ).data()
            print(f"  ✓ PKGNode count: {len(nodes)}")
            for n in nodes:
                d = dict(n["n"])
                print(f"      {d['node_id']}: {d['label']} ({d['type']}, w={d['weight']})")

            edges = s.run(
                """
                MATCH (u:ExpUser {persona_id: $pid})-[:HAS_PKG_NODE]->(src:PKGNode)
                      -[r:PKG_EDGE]->(dst:PKGNode)
                RETURN src.node_id AS src, dst.node_id AS dst, r.rel AS rel
                """,
                pid=pid,
            ).data()
            print(f"  ✓ PKG edges: {len(edges)}")
            for e in edges:
                print(f"      {e['src']} -[{e['rel']}]-> {e['dst']}")

            if len(nodes) != len(pdef["nodes"]) or len(edges) != len(pdef["edges"]):
                all_ok = False

    return all_ok


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
