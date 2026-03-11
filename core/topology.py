from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Set, Tuple


@dataclass(frozen=True)
class Edge:
    src: str
    dst: str


class DPUTopology:
    """
    Directed graph G=(V,E) over DPU ids.

    Paper concept:
      - Topology is a directed graph of DPU communications
      - Data link is a directed acyclic subgraph for a chosen output DPU,
        containing that node and all upstream nodes that reach it.
    """

    def __init__(self, nodes: Iterable[str] = (), edges: Iterable[Edge] = ()):
        self.nodes: Set[str] = set(nodes)
        self.edges: Set[Edge] = set(edges)

        self._in: Dict[str, List[str]] = {}
        for e in self.edges:
            self.nodes.add(e.src)
            self.nodes.add(e.dst)
            self._in.setdefault(e.dst, []).append(e.src)

    def upstream_closure(self, output_node_id: str) -> Set[str]:
        seen: Set[str] = set()
        stack: List[str] = [output_node_id]
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            for parent in self._in.get(cur, []):
                if parent not in seen:
                    stack.append(parent)
        return seen

    def data_link_subgraph(self, output_node_id: str) -> Tuple[Set[str], Set[Edge]]:
        v_prime = self.upstream_closure(output_node_id)
        e_prime = {e for e in self.edges if e.src in v_prime and e.dst in v_prime}
        return v_prime, e_prime

