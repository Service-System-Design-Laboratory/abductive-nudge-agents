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
        self._node_counter = 0  # initialized in _init_counter()
        if enabled:
            uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
            user = os.environ.get("NEO4J_USERNAME", "neo4j")
            pw = os.environ.get("NEO4J_PASSWORD", "password123")
            auth = (user, pw) if user else None
            self._driver = GraphDatabase.driver(uri, auth=auth)
            self._init_counter()

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

    # ══════════════════════════════════════════════════════════════
    #  WRITE OPERATIONS — agents dynamically update the PKG
    # ══════════════════════════════════════════════════════════════

    def _init_counter(self):
        """Read the current max node_id number from Neo4j once at startup."""
        with self._driver.session() as s:
            records = s.run(
                """
                MATCH (u:ExpUser {persona_id: $pid})-[:HAS_PKG_NODE]->(n:PKGNode)
                RETURN n.node_id AS nid
                """,
                pid=self.persona_id,
            ).data()
        max_num = 0
        for r in records:
            nid = r["nid"]
            try:
                num = int(nid.lstrip("n"))
                if num > max_num:
                    max_num = num
            except ValueError:
                pass
        self._node_counter = max_num
        logger.info(f"[PKGStore] initialized counter at n{max_num}")

    def _next_node_id(self) -> str:
        """Generate next sequential node_id (thread-safe incrementing)."""
        self._node_counter += 1
        return f"n{self._node_counter}"

    # ── Write: observations & assumptions (ContextAgent) ──────────

    def write_observations(self, observations: list[dict], assumptions: list[dict],
                           run_id: str) -> list[str]:
        """Write O/A extracted by ContextAgent as runtime nodes linked to
        relevant existing PKG nodes. Returns list of new node_ids."""
        if not self.enabled or not self._driver:
            return []

        new_ids = []
        with self._driver.session() as s:
            for obs in observations:
                nid = self._next_node_id(s)
                s.run(
                    """
                    MATCH (u:ExpUser {persona_id: $pid})
                    CREATE (n:PKGNode {
                        node_id: $nid,
                        label: $label,
                        type: 'observation',
                        weight: 0.5,
                        source: 'context_agent',
                        run_id: $run_id
                    })
                    CREATE (u)-[:HAS_PKG_NODE]->(n)
                    """,
                    pid=self.persona_id, nid=nid,
                    label=obs.get("text", "")[:120], run_id=run_id,
                )
                new_ids.append(nid)

                # Link observation to related existing nodes by keyword overlap
                s.run(
                    """
                    MATCH (u:ExpUser {persona_id: $pid})-[:HAS_PKG_NODE]->(obs:PKGNode {node_id: $nid})
                    MATCH (u)-[:HAS_PKG_NODE]->(existing:PKGNode)
                    WHERE existing.node_id <> $nid
                      AND existing.source IS NULL
                      AND any(word IN split($label, ' ') WHERE size(word) >= 2 AND existing.label CONTAINS word)
                    MERGE (obs)-[:PKG_EDGE {rel: 'observed_in'}]->(existing)
                    """,
                    pid=self.persona_id, nid=nid, label=obs.get("text", ""),
                )

            for asm in assumptions:
                nid = self._next_node_id(s)
                s.run(
                    """
                    MATCH (u:ExpUser {persona_id: $pid})
                    CREATE (n:PKGNode {
                        node_id: $nid,
                        label: $label,
                        type: 'assumption',
                        weight: 0.4,
                        source: 'context_agent',
                        run_id: $run_id,
                        status: $status
                    })
                    CREATE (u)-[:HAS_PKG_NODE]->(n)
                    """,
                    pid=self.persona_id, nid=nid,
                    label=asm.get("text", "")[:120], run_id=run_id,
                    status=asm.get("status", "tentative"),
                )
                new_ids.append(nid)

        logger.info(f"[PKGStore] write_observations: {len(observations)} obs + {len(assumptions)} asm → {len(new_ids)} nodes")
        return new_ids

    # ── Write: triggers (ExplorerAgent) ───────────────────────────

    def write_triggers(self, triggers: list[dict], run_id: str) -> list[str]:
        """Write Explorer triggers as PKG nodes linked to conflict sources."""
        if not self.enabled or not self._driver:
            return []

        new_ids = []
        with self._driver.session() as s:
            for trig in triggers:
                nid = self._next_node_id(s)
                s.run(
                    """
                    MATCH (u:ExpUser {persona_id: $pid})
                    CREATE (n:PKGNode {
                        node_id: $nid,
                        label: $label,
                        type: 'trigger',
                        weight: 0.6,
                        trigger_type: $ttype,
                        source: 'explorer_agent',
                        run_id: $run_id
                    })
                    CREATE (u)-[:HAS_PKG_NODE]->(n)
                    """,
                    pid=self.persona_id, nid=nid,
                    label=trig.get("text", "")[:120],
                    ttype=trig.get("type", "focus"),
                    run_id=run_id,
                )
                new_ids.append(nid)

                # Link trigger to related concern/conflict nodes
                s.run(
                    """
                    MATCH (u:ExpUser {persona_id: $pid})-[:HAS_PKG_NODE]->(trig:PKGNode {node_id: $nid})
                    MATCH (u)-[:HAS_PKG_NODE]->(existing:PKGNode)
                    WHERE existing.type IN ['concern', 'value']
                      AND existing.source IS NULL
                      AND any(word IN split($label, ' ') WHERE size(word) >= 2 AND existing.label CONTAINS word)
                    MERGE (trig)-[:PKG_EDGE {rel: 'triggered_by'}]->(existing)
                    """,
                    pid=self.persona_id, nid=nid, label=trig.get("text", ""),
                )
        logger.info(f"[PKGStore] write_triggers: {len(triggers)} triggers → {len(new_ids)} nodes")
        return new_ids

    # ── Write: hypotheses (HypothesisAgent) ───────────────────────

    def write_hypotheses(self, hypotheses: list[dict], run_id: str) -> list[str]:
        """Write hypotheses as PKG nodes with edges to persona_link targets."""
        if not self.enabled or not self._driver:
            return []

        new_ids = []
        with self._driver.session() as s:
            for hyp in hypotheses:
                nid = self._next_node_id(s)
                s.run(
                    """
                    MATCH (u:ExpUser {persona_id: $pid})
                    CREATE (n:PKGNode {
                        node_id: $nid,
                        label: $label,
                        type: 'hypothesis',
                        weight: $conf,
                        hypothesis_id: $hid,
                        source: 'hypothesis_agent',
                        run_id: $run_id
                    })
                    CREATE (u)-[:HAS_PKG_NODE]->(n)
                    """,
                    pid=self.persona_id, nid=nid,
                    label=hyp.get("text", "")[:150],
                    conf=hyp.get("confidence", 0.5),
                    hid=hyp.get("hypothesis_id", ""),
                    run_id=run_id,
                )
                new_ids.append(nid)

                # Create edges to persona_link nodes
                for link_id in hyp.get("persona_link", []):
                    s.run(
                        """
                        MATCH (u:ExpUser {persona_id: $pid})-[:HAS_PKG_NODE]->(hyp:PKGNode {node_id: $nid})
                        MATCH (u)-[:HAS_PKG_NODE]->(target:PKGNode {node_id: $link_id})
                        MERGE (hyp)-[:PKG_EDGE {rel: 'grounded_in'}]->(target)
                        """,
                        pid=self.persona_id, nid=nid, link_id=link_id,
                    )

                # Link to observations in this run
                for obs_id in hyp.get("observation_link", []):
                    s.run(
                        """
                        MATCH (u:ExpUser {persona_id: $pid})-[:HAS_PKG_NODE]->(hyp:PKGNode {node_id: $nid})
                        MATCH (u)-[:HAS_PKG_NODE]->(obs:PKGNode)
                        WHERE obs.type = 'observation' AND obs.run_id = $run_id
                        WITH hyp, obs, obs.node_id AS obs_nid ORDER BY obs_nid LIMIT 1
                        MERGE (hyp)-[:PKG_EDGE {rel: 'explains'}]->(obs)
                        """,
                        pid=self.persona_id, nid=nid, run_id=run_id,
                    )

        logger.info(f"[PKGStore] write_hypotheses: {len(hypotheses)} hypotheses → {len(new_ids)} nodes")
        return new_ids

    # ── Write: judge diagnostics (批評家) ─────────────────────────

    def write_judgements(self, judgements: list[dict], run_id: str) -> list[str]:
        """Write judge diagnostics as PKG nodes linked to hypothesis nodes."""
        if not self.enabled or not self._driver:
            return []

        new_ids = []
        with self._driver.session() as s:
            for j in judgements:
                nid = self._next_node_id(s)
                s.run(
                    """
                    MATCH (u:ExpUser {persona_id: $pid})
                    CREATE (n:PKGNode {
                        node_id: $nid,
                        label: $label,
                        type: 'judgement',
                        weight: 0.5,
                        target_hypothesis: $target_hid,
                        source: 'judge_agent',
                        run_id: $run_id
                    })
                    CREATE (u)-[:HAS_PKG_NODE]->(n)
                    """,
                    pid=self.persona_id, nid=nid,
                    label=j.get("diagnostic", "")[:150],
                    target_hid=j.get("hypothesis_id", ""),
                    run_id=run_id,
                )
                new_ids.append(nid)

                # Link judgement to the hypothesis it evaluates
                s.run(
                    """
                    MATCH (u:ExpUser {persona_id: $pid})-[:HAS_PKG_NODE]->(judge:PKGNode {node_id: $nid})
                    MATCH (u)-[:HAS_PKG_NODE]->(hyp:PKGNode)
                    WHERE hyp.type = 'hypothesis' AND hyp.hypothesis_id = $hid AND hyp.run_id = $run_id
                    MERGE (judge)-[:PKG_EDGE {rel: 'evaluates'}]->(hyp)
                    """,
                    pid=self.persona_id, nid=nid,
                    hid=j.get("hypothesis_id", ""), run_id=run_id,
                )

        logger.info(f"[PKGStore] write_judgements: {len(judgements)} judgements → {len(new_ids)} nodes")
        return new_ids

    # ── Write: decision (DecisionAgent) ───────────────────────────

    def write_decision(self, decision: dict, run_id: str) -> str:
        """Write the selected hypothesis decision as a PKG node."""
        if not self.enabled or not self._driver:
            return ""

        with self._driver.session() as s:
            nid = self._next_node_id(s)
            s.run(
                """
                MATCH (u:ExpUser {persona_id: $pid})
                CREATE (n:PKGNode {
                    node_id: $nid,
                    label: $label,
                    type: 'decision',
                    weight: 0.7,
                    selected_hypothesis_id: $sel_hid,
                    rationale: $rationale,
                    source: 'decision_agent',
                    run_id: $run_id
                })
                CREATE (u)-[:HAS_PKG_NODE]->(n)
                """,
                pid=self.persona_id, nid=nid,
                label=f"決定: {decision.get('selected_hypothesis_id', '')} を選択",
                sel_hid=decision.get("selected_hypothesis_id", ""),
                rationale=decision.get("rationale", "")[:200],
                run_id=run_id,
            )

            # Link decision → selected hypothesis node
            s.run(
                """
                MATCH (u:ExpUser {persona_id: $pid})-[:HAS_PKG_NODE]->(dec:PKGNode {node_id: $nid})
                MATCH (u)-[:HAS_PKG_NODE]->(hyp:PKGNode)
                WHERE hyp.type = 'hypothesis' AND hyp.hypothesis_id = $hid AND hyp.run_id = $run_id
                MERGE (dec)-[:PKG_EDGE {rel: 'selected'}]->(hyp)
                """,
                pid=self.persona_id, nid=nid,
                hid=decision.get("selected_hypothesis_id", ""), run_id=run_id,
            )

        logger.info(f"[PKGStore] write_decision: selected {decision.get('selected_hypothesis_id', '')} → {nid}")
        return nid

    # ── Cleanup: remove runtime nodes from a run ──────────────────

    def cleanup_run(self, run_id: str):
        """Remove all runtime-generated nodes from a specific run.
        Useful to reset PKG before re-running."""
        if not self.enabled or not self._driver:
            return
        with self._driver.session() as s:
            result = s.run(
                """
                MATCH (u:ExpUser {persona_id: $pid})-[:HAS_PKG_NODE]->(n:PKGNode {run_id: $run_id})
                DETACH DELETE n
                RETURN count(n) AS deleted
                """,
                pid=self.persona_id, run_id=run_id,
            ).single()
            count = result["deleted"] if result else 0
        logger.info(f"[PKGStore] cleanup_run({run_id}): deleted {count} runtime nodes")
