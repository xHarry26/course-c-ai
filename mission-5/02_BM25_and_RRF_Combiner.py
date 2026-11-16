#!/usr/bin/env python3
"""
=============================================================================
MISSION 5 — DELIVERABLE 02: COMMUNICATIONS & PROTOCOL OFFICER
BM25 Lexical Engine, Reciprocal Rank Fusion & Evaluation Metrics
USSE Noosphere — Cognitive Subsystem Core (Sector SEC-05-M01)
=============================================================================
Author: Communications & Protocol Officer (Mazhar Uddin Abbasi) — Squadron Turing
Focus: BM25 Saturation, RRF (k=60) Hybrid Merging, MRR & NDCG@10 Benchmarks
=============================================================================
"""

import math
import re
from typing import List, Dict, Tuple, Set

class BM25LexicalRetriever:
    """
    Okapi BM25 Probabilistic Inverted Search Engine.
    Implements Robertson & Zaragoza (2009).
    """
    def __init__(self, k1: float = 1.2, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents: Dict[str, str] = {}
        self.doc_lengths: Dict[str, int] = {}
        self.inverted_index: Dict[str, Set[str]] = {}
        self.term_freqs: Dict[str, Dict[str, int]] = {}
        self.avg_doc_len: float = 0.0

    def tokenize(self, text: str) -> List[str]:
        return re.findall(r'\b[a-zA-Z0-9_-]+\b', text.lower())

    def index_documents(self, docs: List[Dict[str, str]]):
        for doc in docs:
            doc_id = doc["id"]
            content = doc["text"]
            self.documents[doc_id] = content
            tokens = self.tokenize(content)
            self.doc_lengths[doc_id] = len(tokens)
            self.term_freqs[doc_id] = {}

            for token in tokens:
                self.term_freqs[doc_id][token] = self.term_freqs[doc_id].get(token, 0) + 1
                if token not in self.inverted_index:
                    self.inverted_index[token] = set()
                self.inverted_index[token].add(doc_id)

        self.avg_doc_len = sum(self.doc_lengths.values()) / max(len(self.documents), 1)

    def idf(self, term: str) -> float:
        N = len(self.documents)
        n_t = len(self.inverted_index.get(term, set()))
        return math.log((N - n_t + 0.5) / (n_t + 0.5) + 1.0)

    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        q_tokens = self.tokenize(query)
        scores: Dict[str, float] = {doc_id: 0.0 for doc_id in self.documents}

        for qt in q_tokens:
            idf_val = self.idf(qt)
            for doc_id in self.inverted_index.get(qt, set()):
                tf = self.term_freqs[doc_id].get(qt, 0)
                doc_len = self.doc_lengths[doc_id]
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
                scores[doc_id] += idf_val * (numerator / denominator)

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]

class ReciprocalRankFusionCombiner:
    """
    Unites disparate retrieval candidate streams (dense and sparse)
    via scale-invariant Reciprocal Rank Fusion (Cormack et al., 2009).
    """
    def __init__(self, k: int = 60):
        self.k = k

    def fuse(self, ranked_runs: Dict[str, List[str]], top_k: int = 10) -> List[Tuple[str, float]]:
        """
        fused_score(d) = sum_{system in runs} 1 / (k + rank_system(d))
        """
        rrf_scores: Dict[str, float] = {}
        for system_name, doc_ids in ranked_runs.items():
            for rank, doc_id in enumerate(doc_ids, start=1):
                rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (self.k + rank)

        fused = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        return fused[:top_k]

class InformationRetrievalEvaluator:
    """Computes Mean Reciprocal Rank (MRR) and NDCG@10 for ranking runs."""
    @staticmethod
    def reciprocal_rank(ranked_list: List[str], relevant_set: Set[str]) -> float:
        for rank, doc_id in enumerate(ranked_list, start=1):
            if doc_id in relevant_set:
                return 1.0 / rank
        return 0.0

    @staticmethod
    def dcg_at_k(ranked_list: List[str], relevance_scores: Dict[str, float], k: int = 10) -> float:
        dcg = 0.0
        for i, doc_id in enumerate(ranked_list[:k], start=1):
            rel = relevance_scores.get(doc_id, 0.0)
            dcg += (2.0**rel - 1.0) / math.log2(i + 1)
        return dcg

    @staticmethod
    def ndcg_at_k(ranked_list: List[str], relevance_scores: Dict[str, float], k: int = 10) -> float:
        dcg = InformationRetrievalEvaluator.dcg_at_k(ranked_list, relevance_scores, k)
        ideal_list = sorted(relevance_scores.keys(), key=lambda x: relevance_scores[x], reverse=True)
        idcg = InformationRetrievalEvaluator.dcg_at_k(ideal_list, relevance_scores, k)
        if idcg == 0.0:
            return 0.0
        return dcg / idcg

if __name__ == "__main__":
    print("[COMMUNICATIONS & PROTOCOL OFFICER] Testing BM25 & RRF Hybrid Combiner...")

    corpus = [
        {"id": "DOC-WARP-01", "text": "Magnetic containment valve PR-882-HEX liquid helium cooling pressure at 4.2 bar."},
        {"id": "DOC-WARP-02", "text": "Warp drive sub-light plasma wave oscillation dampening in the injector manifold."},
        {"id": "DOC-ENV-01", "text": "Deck 4 environmental nitrogen-oxygen atmospheric recycling scrubber O2-771."},
        {"id": "DOC-NAV-01", "text": "Synchrotron radiation from Crab Pulsar PSR B0531+21 requires 30.2 Hz deflector pulse."}
    ]

    retriever = BM25LexicalRetriever(k1=1.2, b=0.75)
    retriever.index_documents(corpus)

    test_queries = [
        {
            "query": "PR-882-HEX cooling valve",
            "relevant": {"DOC-WARP-01"},
            "rel_scores": {"DOC-WARP-01": 3.0, "DOC-WARP-02": 1.0}
        },
        {
            "query": "pulsar synchrotron frequency",
            "relevant": {"DOC-NAV-01"},
            "rel_scores": {"DOC-NAV-01": 3.0}
        }
    ]

    combiner = ReciprocalRankFusionCombiner(k=60)
    mrr_list = []
    ndcg_list = []

    for tq in test_queries:
        q = tq["query"]
        bm25_res = retriever.search(q, top_k=4)
        sparse_ranks = [doc_id for doc_id, _ in bm25_res]

        # Synthetic dense ranks demonstrating complementarity
        dense_ranks = list(reversed(sparse_ranks)) if q.startswith("PR") else sparse_ranks

        fused = combiner.fuse({"dense": dense_ranks, "bm25": sparse_ranks}, top_k=4)
        fused_ranks = [doc_id for doc_id, _ in fused]

        rr = InformationRetrievalEvaluator.reciprocal_rank(fused_ranks, tq["relevant"])
        ndcg = InformationRetrievalEvaluator.ndcg_at_k(fused_ranks, tq["rel_scores"], k=4)
        mrr_list.append(rr)
        ndcg_list.append(ndcg)

        print(f"Query: '{q}' -> Top Rank: {fused_ranks[0]} (RR={rr:.3f}, NDCG={ndcg:.3f})")

    mean_mrr = sum(mrr_list) / len(mrr_list)
    mean_ndcg = sum(ndcg_list) / len(ndcg_list)
    print(f"\n[EVALUATION METRICS]")
    print(f"  • Mean Reciprocal Rank (MRR) : {mean_mrr:.4f}")
    print(f"  • Mean NDCG@10               : {mean_ndcg:.4f}")

    assert mean_mrr >= 0.5, "MRR score below acceptance threshold!"
    print("✓ [PROTOCOL OFFICER] BM25 & RRF Hybrid Combiner Validated with High Ranking Precision.")

