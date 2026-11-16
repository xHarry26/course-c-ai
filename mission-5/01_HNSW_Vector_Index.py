#!/usr/bin/env python3
"""
=============================================================================
MISSION 5 — DELIVERABLE 01: SYSTEMS ARCHITECT (LEAD ENGINEER)
HNSW Multi-Layer Skip Graph Indexing & Latency Benchmarking
USSE Noosphere — Cognitive Subsystem Core (Sector SEC-05-M01)
=============================================================================
Author: Systems Architect (Lead Engineer) — Squadron Turing
Focus: Multi-Layer Proximity Graphs, Logarithmic Routing, L2/Cosine Distance
       & Scalability Latency Benchmarks
=============================================================================
"""

import math
import random
import time
from typing import List, Dict, Tuple, Set
import numpy as np

# Set deterministic seed
random.seed(42)
np.random.seed(42)

class VectorMetrics:
    """NumPy-accelerated distance metrics for high-dimensional vector spaces."""
    @staticmethod
    def cosine_similarity(u: np.ndarray, v: np.ndarray) -> float:
        norm_u = np.linalg.norm(u)
        norm_v = np.linalg.norm(v)
        if norm_u == 0.0 or norm_v == 0.0:
            return 0.0
        return float(np.dot(u, v) / (norm_u * norm_v))

    @staticmethod
    def cosine_distance(u: np.ndarray, v: np.ndarray) -> float:
        return 1.0 - VectorMetrics.cosine_similarity(u, v)

    @staticmethod
    def euclidean_l2_distance(u: np.ndarray, v: np.ndarray) -> float:
        return float(np.linalg.norm(u - v))

class HNSWVectorIndex:
    """
    Hierarchical Navigable Small World (HNSW) Vector Index.
    Implements multi-layer skip-graph hierarchy according to Malkov & Yashunin (2018).
    """
    def __init__(self, dim: int, M: int = 16, ef_construction: int = 64, ef_search: int = 32, metric: str = "cosine"):
        self.dim = dim
        self.M = M
        self.M0 = 2 * M
        self.ef_construction = ef_construction
        self.ef_search = ef_search
        self.metric = metric
        self.mL = 1.0 / math.log(M)

        # Graph adjacency: layer -> node_id -> set of neighbor node_ids
        self.graphs: Dict[int, Dict[int, Set[int]]] = {}
        # Vector storage: node_id -> numpy ndarray
        self.vectors: Dict[int, np.ndarray] = {}
        # Metadata storage: node_id -> dict
        self.metadata: Dict[int, Dict] = {}
        # Entry point node ID and max layer
        self.entry_point: int = None
        self.max_layer: int = -1

    def _dist(self, u: np.ndarray, v: np.ndarray) -> float:
        if self.metric == "cosine":
            return VectorMetrics.cosine_distance(u, v)
        return VectorMetrics.euclidean_l2_distance(u, v)

    def _assign_random_layer(self) -> int:
        """Assigns maximum layer via exponential decay P(l) = -ln(unif(0,1)) * mL."""
        r = random.uniform(1e-7, 1.0)
        return int(-math.log(r) * self.mL)

    def insert(self, node_id: int, vector: np.ndarray, meta: Dict = None):
        """Inserts a new vector node into the hierarchical proximity graph."""
        vec = np.asarray(vector, dtype=np.float32)
        self.vectors[node_id] = vec
        self.metadata[node_id] = meta or {}
        target_layer = self._assign_random_layer()

        for l in range(target_layer + 1):
            if l not in self.graphs:
                self.graphs[l] = {}
            self.graphs[l][node_id] = set()

        if self.entry_point is None:
            self.entry_point = node_id
            self.max_layer = target_layer
            return

        curr_obj = self.entry_point
        # Step 1: Top-down greedy skip routing through express layers
        for l in range(self.max_layer, target_layer, -1):
            changed = True
            while changed:
                changed = False
                curr_dist = self._dist(vec, self.vectors[curr_obj])
                for neighbor in self.graphs[l].get(curr_obj, []):
                    dist = self._dist(vec, self.vectors[neighbor])
                    if dist < curr_dist:
                        curr_dist = dist
                        curr_obj = neighbor
                        changed = True

        # Step 2: Bidirectional connection construction from target_layer down to layer 0
        for l in range(min(self.max_layer, target_layer), -1, -1):
            candidates = self._search_layer_candidates(vec, curr_obj, l, self.ef_construction)
            max_links = self.M0 if l == 0 else self.M
            selected = [c[0] for c in candidates[:max_links]]

            for neighbor in selected:
                self.graphs[l][node_id].add(neighbor)
                self.graphs[l][neighbor].add(node_id)
                if len(self.graphs[l][neighbor]) > max_links:
                    self._prune_neighbors(neighbor, l, max_links)

            if candidates:
                curr_obj = candidates[0][0]

        if target_layer > self.max_layer:
            self.entry_point = node_id
            self.max_layer = target_layer

    def _search_layer_candidates(self, query_vec: np.ndarray, entry: int, layer: int, ef: int) -> List[Tuple[int, float]]:
        v_dist = self._dist(query_vec, self.vectors[entry])
        visited = {entry}
        candidates = [(entry, v_dist)]
        results = [(entry, v_dist)]

        while candidates:
            candidates.sort(key=lambda x: x[1])
            curr_node, curr_dist = candidates.pop(0)

            results.sort(key=lambda x: x[1])
            if curr_dist > results[-1][1] and len(results) >= ef:
                break

            for neighbor in self.graphs[layer].get(curr_node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    dist = self._dist(query_vec, self.vectors[neighbor])
                    if dist < results[-1][1] or len(results) < ef:
                        candidates.append((neighbor, dist))
                        results.append((neighbor, dist))
                        results.sort(key=lambda x: x[1])
                        if len(results) > ef:
                            results.pop()
        return results

    def _prune_neighbors(self, node: int, layer: int, max_links: int):
        neighbors = list(self.graphs[layer][node])
        scored = [(nbr, self._dist(self.vectors[node], self.vectors[nbr])) for nbr in neighbors]
        scored.sort(key=lambda x: x[1])
        self.graphs[layer][node] = {nbr for nbr, _ in scored[:max_links]}

    def query(self, query_vec: np.ndarray, k: int = 5) -> List[Tuple[int, float, Dict]]:
        if self.entry_point is None:
            return []
        q_vec = np.asarray(query_vec, dtype=np.float32)
        curr_obj = self.entry_point

        # Greedy skip hop down through layers
        for l in range(self.max_layer, 0, -1):
            changed = True
            while changed:
                changed = False
                curr_dist = self._dist(q_vec, self.vectors[curr_obj])
                for neighbor in self.graphs[l].get(curr_obj, []):
                    dist = self._dist(q_vec, self.vectors[neighbor])
                    if dist < curr_dist:
                        curr_dist = dist
                        curr_obj = neighbor
                        changed = True

        # Base layer beam search
        candidates = self._search_layer_candidates(q_vec, curr_obj, 0, max(self.ef_search, k))
        candidates.sort(key=lambda x: x[1])
        top_k = []
        for node_id, dist in candidates[:k]:
            sim = 1.0 - dist if self.metric == "cosine" else -dist
            top_k.append((node_id, sim, self.metadata.get(node_id, {})))
        return top_k

def benchmark_hnsw_vs_brute_force(num_vectors: int = 300, dim: int = 16):
    """Benchmarks HNSW query latency against brute-force exhaustive search."""
    print(f"\n--- Benchmarking HNSW vs Flat Brute-Force Search (N={num_vectors}, Dim={dim}) ---")
    data = np.random.randn(num_vectors, dim).astype(np.float32)
    # Normalize rows
    norms = np.linalg.norm(data, axis=1, keepdims=True)
    data = data / np.maximum(norms, 1e-7)

    hnsw = HNSWVectorIndex(dim=dim, M=8, ef_construction=32, ef_search=16, metric="cosine")
    print(f"Building HNSW index with {num_vectors} vectors...")
    t0 = time.time()
    for i in range(num_vectors):
        hnsw.insert(i, data[i], {"id": f"DOC-{i}"})
    build_time = time.time() - t0
    print(f"HNSW Build Time: {build_time:.3f}s (Layers: {hnsw.max_layer + 1})")

    # Sample queries
    num_queries = 25
    queries = np.random.randn(num_queries, dim).astype(np.float32)
    q_norms = np.linalg.norm(queries, axis=1, keepdims=True)
    queries = queries / np.maximum(q_norms, 1e-7)

    # 1. Brute-Force Flat Search
    t0 = time.time()
    for q in queries:
        dots = np.dot(data, q)
        top5_flat = np.argsort(dots)[-5:][::-1]
    flat_time = (time.time() - t0) / num_queries * 1000.0  # ms per query

    # 2. HNSW Search
    t0 = time.time()
    recalls = []
    for q in queries:
        hnsw_res = hnsw.query(q, k=5)
        hnsw_ids = {r[0] for r in hnsw_res}
        dots = np.dot(data, q)
        true_top5 = set(np.argsort(dots)[-5:][::-1])
        recalls.append(len(hnsw_ids.intersection(true_top5)) / 5.0)
    hnsw_time = (time.time() - t0) / num_queries * 1000.0  # ms per query

    avg_recall = sum(recalls) / len(recalls)
    speedup = flat_time / max(hnsw_time, 1e-5)

    print(f"  • Flat Exhaustive Search Latency : {flat_time:.4f} ms/query")
    print(f"  • HNSW Approximate Search Latency: {hnsw_time:.4f} ms/query")
    print(f"  • Latency Speedup Factor         : {speedup:.1f}x faster")
    print(f"  • Top-5 Empirical Recall         : {avg_recall * 100:.2f}%")
    return flat_time, hnsw_time, avg_recall

if __name__ == "__main__":
    print("[SYSTEMS ARCHITECT] Starting HNSW Vector Indexing Pipeline...")
    flat_ms, hnsw_ms, recall = benchmark_hnsw_vs_brute_force(num_vectors=300, dim=16)
    assert recall >= 0.70, f"HNSW recall {recall} below 70% threshold!"
    print("✓ [SYSTEMS ARCHITECT] HNSW Multi-Layer Skip Graph Verified with High Recall.")
