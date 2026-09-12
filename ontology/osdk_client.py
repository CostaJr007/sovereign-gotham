"""
Sovereign Gotham - Fluent Ontology SDK Client
Implements the Palantir OSDK (@osdk/client) query builder paradigm in Python.
Enables chained queries: client.objects(Document).where(...).pivot_to(LinkType.REGISTERS, Operation).fetch()
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from ontology.graph import GothamKnowledgeGraph
from ontology.models import LinkType

T = TypeVar("T", bound=BaseModel)
R = TypeVar("R", bound=BaseModel)


class ObjectSet(Generic[T]):
    """
    Represents a lazy, chainable query set over Gotham Ontological Objects.
    Mirrors Palantir Foundry's OSDK ObjectSet interface.
    """

    def __init__(
        self,
        graph: GothamKnowledgeGraph,
        target_class: type[T],
        current_ids: list[str] | None = None,
        filters: list[Callable[[T], bool]] | None = None,
    ):
        self.graph = graph
        self.target_class = target_class
        self.class_name = target_class.__name__
        self._filters: list[Callable[[T], bool]] = list(filters) if filters else []

        if current_ids is None:
            # Collect all node IDs matching this class name in the graph
            self._ids = [
                node_id
                for node_id, data in self.graph.graph.nodes(data=True)
                if data.get("entity_type") == self.class_name or data.get("type") == self.class_name
            ]
            # Also catch any entities registered in entities dict
            for eid, obj in self.graph.entities.items():
                if isinstance(obj, self.target_class) and eid not in self._ids:
                    self._ids.append(eid)
        else:
            self._ids = list(current_ids)

    def where(
        self,
        predicate: Callable[[T], bool] | None = None,
        **kwargs: Any,
    ) -> ObjectSet[T]:
        """
        Applies property filters to the ObjectSet.
        Supports keyword field matching and callable predicates.
        """
        new_filters = list(self._filters)

        if predicate:
            new_filters.append(predicate)

        if kwargs:
            def field_filter(obj: T) -> bool:
                for key, expected in kwargs.items():
                    val = getattr(obj, key, None)
                    if hasattr(val, "value"):  # Handle enum values
                        val = val.value
                    expected_val = expected.value if hasattr(expected, "value") else expected
                    if val != expected_val:
                        return False
                return True

            new_filters.append(field_filter)

        return ObjectSet(
            graph=self.graph,
            target_class=self.target_class,
            current_ids=self._ids,
            filters=new_filters,
        )

    def pivot_to(
        self,
        link_type: LinkType | str,
        target_class: type[R],
        direction: str = "out",
    ) -> ObjectSet[R]:
        """
        Traverses relationships to linked objects (Palantir OSDK .pivotTo() pattern).
        Example: Document.pivot_to(LinkType.REGISTERS, Operation)
        """
        link_val = link_type.value if isinstance(link_type, LinkType) else str(link_type)
        target_class_name = target_class.__name__
        resolved_target_ids: set[str] = set()

        # Materialize currently matching source objects
        source_objects = self.fetch()
        active_source_ids = {obj.id for obj in source_objects if hasattr(obj, "id")}

        for src_id in active_source_ids:
            if not self.graph.graph.has_node(src_id):
                continue

            # Check outgoing edges
            if direction in ("out", "both"):
                for _, tgt_id, edge_data in self.graph.graph.out_edges(src_id, data=True):
                    if edge_data.get("link_type") == link_val:
                        tgt_node = self.graph.graph.nodes.get(tgt_id, {})
                        tgt_type = tgt_node.get("entity_type") or tgt_node.get("type")
                        tgt_obj = self.graph.entities.get(tgt_id)
                        if tgt_type == target_class_name or (tgt_obj and isinstance(tgt_obj, target_class)):
                            resolved_target_ids.add(tgt_id)

            # Check incoming edges
            if direction in ("in", "both"):
                for orig_id, _, edge_data in self.graph.graph.in_edges(src_id, data=True):
                    if edge_data.get("link_type") == link_val:
                        orig_node = self.graph.graph.nodes.get(orig_id, {})
                        orig_type = orig_node.get("entity_type") or orig_node.get("type")
                        orig_obj = self.graph.entities.get(orig_id)
                        if orig_type == target_class_name or (orig_obj and isinstance(orig_obj, target_class)):
                            resolved_target_ids.add(orig_id)

        return ObjectSet(
            graph=self.graph,
            target_class=target_class,
            current_ids=sorted(list(resolved_target_ids)),
        )

    def fetch(self, limit: int | None = None) -> list[T]:
        """
        Materializes and returns validated Pydantic models satisfying all filters.
        """
        results: list[T] = []
        for entity_id in self._ids:
            raw_obj = self.graph.get_object(entity_id)
            if raw_obj is None:
                continue

            # Ensure type safety
            if not isinstance(raw_obj, self.target_class):
                continue

            match = True
            for flt in self._filters:
                try:
                    if not flt(raw_obj):
                        match = False
                        break
                except Exception:
                    match = False
                    break

            if match:
                results.append(raw_obj)
                if limit is not None and len(results) >= limit:
                    break

        return results

    def first(self) -> T | None:
        """Returns the first matching object or None."""
        batch = self.fetch(limit=1)
        return batch[0] if batch else None

    def count(self) -> int:
        """Returns the total number of matching objects."""
        return len(self.fetch())


class SovereignOSDKClient:
    """
    Unified client for querying and traversing the Sovereign Gotham dynamic ontology.
    """

    def __init__(self, graph: GothamKnowledgeGraph):
        self.graph = graph

    def objects(self, entity_class: type[T]) -> ObjectSet[T]:
        """Spawns an ObjectSet for the requested entity class."""
        return ObjectSet(self.graph, entity_class)
