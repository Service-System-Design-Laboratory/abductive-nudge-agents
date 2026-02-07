"""
PKGStore — Dynamic Neo4j query layer for per-agent PKG access.

Each agent calls a purpose-specific method that runs a Cypher query
against Neo4j and returns only the relevant subgraph/information.
No full-dump. No text serialization. Graph DB is queried at runtime.
"""
from __future__ import annotations
import logging
import os
from typing import Optional

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()
logger = logging.getLogger("newresearch")


class PKGStore:
    """Live Neo4j connection for dynamic PKG queries."""

    def __init__(self, persona_id: str = "P1", enabled: bool = True):
        self.persona_id = persona_id
        self.enabled = enabled
        self._driver = None
        if enabled:
            uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
            user = os.environ.get("NEO4J_USERNAME", "neo4j")
            pw = os.environ.get("NEO4J_PASSWORD", "password123")
            auth = (user, pw) if user else None
            self._driver = GraphDatabase.driver(uri, auth=auth)

    def close(self):
        if self._driver:
            self._driver.close()

    # ── Query: keyword-based subgraph (ContextAgent) ──────────────

    def find_relevant_nodes(self, keywords: list[str]) -> str:
        """Find PKG nodes whose label contains any keyword,
        then return those nodes + their 1-hop neighborhood as text.
        Used by ContextAgent to ground O/A extraction in persona context."""
        if not self.enabled or not self._driver:
            return "(実験条件によりPKG無効)"

        with self._driver.session() as s:
            records = s.run(
                """
                MATCH (u:ExpUser {persona_id: $pid})-[:HAS_PKG_NODE]->(n:PKGNode)
                WHERE any(kw IN $keywords WHERE n.label CONTAINS kw)
                OPTIONAL MATCH (n)-[r:PKG_EDGE]-(neighbor:PKGNode)
                RETURN n.node_id AS nid, n.label AS label, n.type AS type,
                       n.weight AS weight,
                       collect(DISTINCT {
                           neighbor: neighbor.label,
                           rel: r.rel,
                           dir: CASE WHEN startNode(r) = n THEN '-->' ELSE '<--' END
                       }) AS edges
                """,
                pid=self.persona_id,
                keywords=keywords,
            ).data()

        if not records:
            # Fallback: return top-weight nodes if no keyword match
            return self.get_top_nodes(5)

        return self._format_subgraph(records, f"キーワード {keywords} に関連するPKG部分グラフ")

    # ── Query: conflicts & anomalies (ExplorerAgent) ──────────────

    def find_conflicts_and_concerns(self) -> str:
        """Find conflict edges (conflicts_with, amplifies, causes)
        and high-weight concern nodes. Used by ExplorerAgent for
        trigger detection via PKG structural anomalies."""
        if not self.enabled or not self._driver:
            return "(実験条件によりPKG無効)"

        with self._driver.session() as s:
            # Conflict/tension edges
            conflict_records = s.run(
                """
                MATCH (u:ExpUser {persona_id: $pid})-[:HAS_PKG_NODE]->(src:PKGNode)
                      -[r:PKG_EDGE]->(dst:PKGNode)
                WHERE r.rel IN ['conflicts_with', 'causes', 'amplifies']
                RETURN src.label AS src, r.rel AS rel, dst.label AS dst,
                       src.type AS src_type, dst.type AS dst_type
                """,
                pid=self.persona_id,
            ).data()

            # High-weight concerns
            concern_records = s.run(
                """
                MATCH (u:ExpUser {persona_id: $pid})-[:HAS_PKG_NODE]->(n:PKGNode)
                WHERE n.type = 'concern' AND n.weight >= 0.7
                RETURN n.label AS label, n.weight AS weight
                ORDER BY n.weight DESC
                """,
                pid=self.persona_id,
            ).data()

        lines = ["## PKG 構造的緊張点"]
        if conflict_records:
            for r in conflict_records:
                lines.append(f"  {r['src']} ({r['src_type']}) --[{r['rel']}]--> {r['dst']} ({r['dst_type']})")
        else:
            lines.append("  (構造的対立なし)")

        if concern_records:
            lines.append("")
            lines.append("## 高関心度の懸念ノード")
            for r in concern_records:
                lines.append(f"  {r['label']} (weight={r['weight']})")

        result = "\n".join(lines)
        logger.info(f"[PKGStore] find_conflicts_and_concerns: {len(conflict_records)} conflicts, {len(concern_records)} concerns")
        return result

    # ── Query: paths between concepts (HypothesisAgent) ───────────

    def find_paths(self, concept_a: str, concept_b: str, max_depth: int = 3) -> str:
        """Find shortest paths between two PKG nodes by label substring.
        Used by HypothesisAgent to discover reasoning chains."""
        if not self.enabled or not self._driver:
            return "(実験条件によりPKG無効)"

        with self._driver.session() as s:
            records = s.run(
                """
                MATCH (a:PKGNode), (b:PKGNode)
                WHERE a.label CONTAINS $ca AND b.label CONTAINS $cb
                MATCH path = shortestPath((a)-[:PKG_EDGE*1..3]-(b))
                RETURN [n IN nodes(path) | n.label] AS node_labels,
                       [r IN relationships(path) | r.rel] AS rels
                LIMIT 3
                """,
                ca=concept_a,
                cb=concept_b,
            ).data()

        if not records:
            return f"({concept_a} と {concept_b} の間にパスなし)"

        lines = [f"## {concept_a} → {concept_b} のPKGパス"]
        for rec in records:
            labels = rec["node_labels"]
            rels = rec["rels"]
            chain = labels[0]
            for i, rel in enumerate(rels):
                chain += f" --[{rel}]--> {labels[i+1]}"
            lines.append(f"  {chain}")

        return "\n".join(lines)

    # ── Query: verify persona_link (批評家) ───────────────────────

    def verify_persona_links(self, node_ids: list[str]) -> str:
        """Check which node_ids actually exist in PKG and return their
        context (neighbors). Used by 批評家 to validate hypothesis grounding."""
        if not self.enabled or not self._driver:
            return "(実験条件によりPKG無効)"

        with self._driver.session() as s:
            records = s.run(
                """
                MATCH (u:ExpUser {persona_id: $pid})-[:HAS_PKG_NODE]->(n:PKGNode)
                WHERE n.node_id IN $nids
                OPTIONAL MATCH (n)-[r:PKG_EDGE]-(neighbor:PKGNode)
                RETURN n.node_id AS nid, n.label AS label, n.type AS type,
                       collect(DISTINCT {
                           neighbor: neighbor.label,
                           rel: r.rel
                       }) AS edges
                """,
                pid=self.persona_id,
                nids=node_ids,
            ).data()

        found = {r["nid"] for r in records}
        missing = [nid for nid in node_ids if nid not in found]

        lines = ["## persona_link 検証結果"]
        for r in records:
            edge_text = ", ".join(f"{e['rel']}→{e['neighbor']}" for e in r["edges"] if e["neighbor"])
            lines.append(f"  ✓ {r['nid']}: {r['label']} ({r['type']}) [{edge_text}]")
        for nid in missing:
            lines.append(f"  ✗ {nid}: PKGに存在しない")

        return "\n".join(lines)

    # ── Query: interests & values for response (DialogueAgent) ────

    def get_interests_and_values(self) -> str:
        """Return the persona's interests and values with their relationships.
        Used by DialogueAgent to personalize the EAST nudge response."""
        if not self.enabled or not self._driver:
            return "(実験条件によりPKG無効)"

        with self._driver.session() as s:
            records = s.run(
                """
                MATCH (u:ExpUser {persona_id: $pid})-[:HAS_PKG_NODE]->(n:PKGNode)
                WHERE n.type IN ['interest', 'value']
                OPTIONAL MATCH (n)-[r:PKG_EDGE]-(m:PKGNode)
                RETURN n.label AS label, n.type AS type, n.weight AS weight,
                       collect(DISTINCT {neighbor: m.label, rel: r.rel}) AS connections
                ORDER BY n.weight DESC
                """,
                pid=self.persona_id,
            ).data()

        lines = ["## ペルソナの関心・価値観 (EAST個人化用)"]
        for r in records:
            conns = [f"{c['rel']}→{c['neighbor']}" for c in r["connections"] if c["neighbor"]]
            conn_text = f" [{', '.join(conns)}]" if conns else ""
            lines.append(f"  {r['label']} (type={r['type']}, weight={r['weight']}){conn_text}")

        return "\n".join(lines)

    # ── Query: top-weight nodes (fallback) ────────────────────────

    def get_top_nodes(self, limit: int = 5) -> str:
        """Return highest-weight nodes with their edges. Fallback query."""
        if not self.enabled or not self._driver:
            return "(実験条件によりPKG無効)"

        with self._driver.session() as s:
            records = s.run(
                """
                MATCH (u:ExpUser {persona_id: $pid})-[:HAS_PKG_NODE]->(n:PKGNode)
                OPTIONAL MATCH (n)-[r:PKG_EDGE]-(m:PKGNode)
                RETURN n.node_id AS nid, n.label AS label, n.type AS type,
                       n.weight AS weight,
                       collect(DISTINCT {
                           neighbor: m.label,
                           rel: r.rel,
                           dir: CASE WHEN startNode(r) = n THEN '-->' ELSE '<--' END
                       }) AS edges
                ORDER BY n.weight DESC
                LIMIT $lim
                """,
                pid=self.persona_id,
                lim=limit,
            ).data()

        return self._format_subgraph(records, "PKG 主要ノード (weight上位)")

    # ── Formatting helper ─────────────────────────────────────────

    def _format_subgraph(self, records: list[dict], title: str) -> str:
        lines = [f"## {title}"]
        for r in records:
            lines.append(f"  [{r['nid']}] {r['label']} (type={r['type']}, weight={r['weight']})")
            for e in r.get("edges", []):
                if e.get("neighbor"):
                    lines.append(f"      {e.get('dir', '-->')} [{e['rel']}] {e['neighbor']}")
        return "\n".join(lines)
