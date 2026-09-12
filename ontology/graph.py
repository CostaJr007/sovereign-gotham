"""
Sovereign Gotham - Knowledge Graph Manager (NetworkX Core)
Enforces graph topology, semantic navigation, and authorization paths.
"""

from __future__ import annotations

import json
from typing import Any

import networkx as nx

try:
    from .models import (
        BaseOntologyObject,
        LinkType,
        OntologyLink,
        Procedure,
    )
except (ImportError, KeyError):
    from ontology.models import (
        BaseOntologyObject,
        LinkType,
        OntologyLink,
        Procedure,
    )



class GothamKnowledgeGraph:
    """
    In-memory, air-gapped semantic graph engine.
    Backs the Gotham Ontological Decision Layer.
    """

    def __init__(self):
        self._graph = nx.MultiDiGraph()
        self._entities: dict[str, BaseOntologyObject] = {}
        self._links: list[OntologyLink] = []

    @property
    def graph(self) -> nx.MultiDiGraph:
        return self._graph

    @property
    def entities(self) -> dict[str, BaseOntologyObject]:
        return self._entities

    @property
    def links(self) -> list[OntologyLink]:
        return self._links

    def add_object(self, obj: BaseOntologyObject) -> None:
        """Add an ontological entity (Document, Procedure, Operation, Agent_Role, Target_Entity)."""
        self._entities[obj.id] = obj
        self._graph.add_node(
            obj.id,
            entity_type=obj.__class__.__name__,
            data=obj.model_dump()
        )

    def get_object(self, obj_id: str) -> BaseOntologyObject | None:
        """Retrieve an object by ID."""
        return self._entities.get(obj_id)

    def add_link(self, link: OntologyLink) -> None:
        """Add a directed, typed semantic edge between two entities."""
        # Ensure endpoints exist in graph if not already registered
        if not self._graph.has_node(link.source_id):
            self._graph.add_node(link.source_id, entity_type=link.source_type)
        if not self._graph.has_node(link.target_id):
            self._graph.add_node(link.target_id, entity_type=link.target_type)

        self._links.append(link)
        self._graph.add_edge(
            link.source_id,
            link.target_id,
            key=f"{link.link_type}:{len(self._links)}",
            link_type=str(link.link_type),
            confidence=link.confidence,
            notes=link.notes,
            created_at=link.created_at.isoformat()
        )

    def get_links(
        self,
        source_id: str | None = None,
        target_id: str | None = None,
        link_type: LinkType | None = None,
    ) -> list[OntologyLink]:
        """Filter links by source, target, and/or link type."""
        results = []
        for link in self._links:
            if source_id and link.source_id != source_id:
                continue
            if target_id and link.target_id != target_id:
                continue
            if link_type and link.link_type != link_type:
                continue
            results.append(link)
        return results

    def find_subgraph(self, entity_id: str, depth: int = 2) -> dict[str, Any]:
        """Extract an ego-graph neighborhood centered around an entity."""
        if entity_id not in self._graph:
            return {"nodes": [], "edges": []}

        # Ego graph in undirected view to catch both in and out relationships
        undirected = self._graph.to_undirected()
        sub_nodes = set(nx.single_source_shortest_path_length(undirected, entity_id, cutoff=depth).keys())

        nodes_data = []
        for nid in sub_nodes:
            obj = self._entities.get(nid)
            node_type = self._graph.nodes[nid].get("entity_type", "Unknown")
            nodes_data.append({
                "id": nid,
                "type": node_type,
                "data": obj.model_dump() if obj else self._graph.nodes[nid].get("data", {})
            })

        edges_data = []
        for u, v, k, d in self._graph.edges(sub_nodes, data=True, keys=True):
            if v in sub_nodes:
                edges_data.append({
                    "source": u,
                    "target": v,
                    "link_type": d.get("link_type"),
                    "confidence": d.get("confidence", 1.0),
                    "notes": d.get("notes")
                })

        return {"center": entity_id, "nodes": nodes_data, "edges": edges_data}

    def find_authorization_chain(self, agent_role_id: str, procedure_id: str) -> list[OntologyLink]:
        """
        Verify if an agent role has direct or mediated authorization for a procedure.
        Direct: (Agent_Role) -[:AUTHORIZES]-> (Procedure)
        Mediated: (Agent_Role) -[:AUTHORIZES]-> (Operation) -[:EXECUTES]-> (Procedure)
        """
        valid_links = []
        # Check direct link
        direct = self.get_links(source_id=agent_role_id, target_id=procedure_id, link_type=LinkType.AUTHORIZES)
        if direct:
            valid_links.extend(direct)
            return valid_links

        # Check mediated link via Operations
        role_operations = self.get_links(source_id=agent_role_id, link_type=LinkType.AUTHORIZES)
        for ro in role_operations:
            op_id = ro.target_id
            exec_links = self.get_links(source_id=op_id, target_id=procedure_id, link_type=LinkType.EXECUTES)
            if exec_links:
                valid_links.append(ro)
                valid_links.extend(exec_links)
                return valid_links

        return []

    def find_procedures_for_target(self, target_id: str) -> list[tuple[Procedure, float]]:
        """
        Discover procedures targeting this entity directly or via associated operations.
        Returns list of (Procedure, confidence).
        """
        found: dict[str, tuple[Procedure, float]] = {}

        # 1. Direct TARGETS: (Procedure) -[:TARGETS]-> (Target_Entity)
        target_links = self.get_links(target_id=target_id, link_type=LinkType.TARGETS)
        for tl in target_links:
            proc_obj = self.get_object(tl.source_id)
            if isinstance(proc_obj, Procedure):
                found[proc_obj.id] = (proc_obj, tl.confidence)

        # 2. Associated via Operation: (Target) -[:ASSOCIATED_WITH]-> (Operation) -[:EXECUTES]-> (Procedure)
        assoc_links = self.get_links(source_id=target_id, link_type=LinkType.ASSOCIATED_WITH)
        for al in assoc_links:
            op_id = al.target_id
            exec_links = self.get_links(source_id=op_id, link_type=LinkType.EXECUTES)
            for el in exec_links:
                proc_obj = self.get_object(el.target_id)
                if isinstance(proc_obj, Procedure):
                    combined_conf = al.confidence * el.confidence
                    if proc_obj.id not in found or found[proc_obj.id][1] < combined_conf:
                        found[proc_obj.id] = (proc_obj, combined_conf)

        return list(found.values())

    def get_stats(self) -> dict[str, Any]:
        """Summary metrics of the knowledge base."""
        counts = {}
        for obj in self._entities.values():
            t = obj.__class__.__name__
            counts[t] = counts.get(t, 0) + 1
        return {
            "total_entities": len(self._entities),
            "total_links": len(self._links),
            "entities_by_type": counts,
            "density": nx.density(self._graph) if len(self._graph) > 1 else 0.0,
        }

    def to_dict(self) -> dict[str, Any]:
        """Serialize graph to dictionary for local persistence."""
        return {
            "entities": {k: v.model_dump() for k, v in self._entities.items()},
            "links": [l.model_dump() for l in self._links]
        }

    def find_cross_agency_coherence_chain(self, mission_id: str) -> dict[str, Any]:
        """
        Trace the multi-agency problem-solving chain from a MissionContext:
        Signals (NSA) -> Incentive Forensics (FBI) -> Strategic ACH (CIA) -> Phased Directive (DoD).
        """
        chain = {
            "mission_id": mission_id,
            "nsa_signals": [],
            "fbi_actors": [],
            "cia_hypotheses": [],
            "dod_actions": [],
            "coherence_links": [],
        }

        # Collect direct out-links from the mission
        mission_links = self.get_links(source_id=mission_id)
        for ml in mission_links:
            chain["coherence_links"].append(ml.model_dump())
            target_obj = self.get_object(ml.target_id)
            if not target_obj:
                continue
            tname = target_obj.__class__.__name__
            if "NSASignal" in tname:
                chain["nsa_signals"].append(target_obj.model_dump())
            elif "FBIActor" in tname:
                chain["fbi_actors"].append(target_obj.model_dump())
            elif "CIAHypothesis" in tname:
                chain["cia_hypotheses"].append(target_obj.model_dump())
            elif "DoDOperational" in tname or "Procedure" in tname:
                chain["dod_actions"].append(target_obj.model_dump())

        return chain

    def save_to_file(self, file_path: str) -> None:
        """Persist graph to JSON."""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

