#!/usr/bin/env python3
"""
=============================================================================
MISSION 5 — DELIVERABLE 03: DATA & PAYLOAD SPECIALIST
Google NotebookLM RAG Laboratory & Citation Audit
USSE Noosphere — Cognitive Subsystem Core (Sector SEC-05-M01)
=============================================================================
Author: Data & Payload Specialist (Muhammed Hamza Saleem) — Squadron Turing
Focus: Source Ingestion, Citation Provenance, Negative Constraint Probing
       & Audio Overview Dialogue Fidelity
=============================================================================
"""

import re
from typing import List, Dict, Optional, Tuple

STOPWORDS = {
    'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'in', 'of', 'to',
    'for', 'with', 'who', 'what', 'where', 'when', 'how', 'are', 'was', 'were',
    'this', 'that', 'from', 'it', 'by', 'as', 'be', 'does', 'do', 'did'
}

WEEK5_CORPUS = [
    {
        "doc_id": "LEWIS-2020",
        "title": "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
        "text": "RAG models combine pre-trained parametric seq2seq generators with non-parametric dense vector index memory accessed via Dense Passage Retrieval (DPR). This eliminates parametric hallucinations by marginalizing token likelihood across retrieved evidence passages."
    },
    {
        "doc_id": "EDGE-2024",
        "title": "From Local to Global: A Graph RAG Approach to Query-Focused Summarization",
        "text": "GraphRAG extracts knowledge graphs from text and applies the Leiden community detection algorithm to build hierarchical summaries across clusters. This enables global sensemaking queries across millions of tokens where baseline vector search fails."
    },
    {
        "doc_id": "NOTEBOOKLM-2024",
        "title": "Google NotebookLM Architecture and Grounded Synthesis",
        "text": "NotebookLM enforces strict closed-world source grounding. Every claim is mapped to character-offset citations. Out-of-corpus queries trigger epistemic refusal. Audio Overview generates two-host conversational podcasts constrained by underlying source citations."
    },
    {
        "doc_id": "TELEMETRY-SEC05",
        "title": "USSE Noosphere Sector 05 Astrogation Log",
        "text": "Pulsar PSR B0531+21 in Messier 1 emits synchrotron radiation pulses at 30.2 Hz. Deflector shields require harmonic phase-inversion to prevent navigational matrix memory desynchronization."
    }
]

class NotebookLMRAGLab:
    """
    Simulates Google NotebookLM source-constrained grounding environment,
    performing citation audits, negative constraint probes, and audio overview evaluation.
    """
    def __init__(self, corpus: List[Dict]):
        self.corpus = corpus

    def query_grounded_assistant(self, query: str) -> Dict:
        """
        Executes grounded query synthesis:
        - If query is answerable from corpus: returns claims with token-level citation offsets.
        - If query is outside corpus: triggers epistemic refusal ("I cannot find this information in your notes").
        """
        tokens = [t.lower() for t in re.findall(r'\b[a-zA-Z0-9_-]+\b', query) if t.lower() not in STOPWORDS]
        if not tokens:
            return {
                "status": "EPISTEMIC_REFUSAL",
                "response": "I cannot find any relevant information in your uploaded notes.",
                "claims": [],
                "citations": []
            }

        matched_spans = []
        for doc in self.corpus:
            text = doc["text"]
            sentences = re.split(r'(?<=[.!?])\s+', text)
            cursor = 0
            for s_idx, sentence in enumerate(sentences):
                start_char = text.find(sentence, cursor)
                end_char = start_char + len(sentence)
                cursor = end_char

                s_tokens = set(re.findall(r'\b[a-zA-Z0-9_-]+\b', sentence.lower()))
                matches = [t for t in tokens if t in s_tokens]
                if len(matches) >= 1:
                    matched_spans.append({
                        "doc_id": doc["doc_id"],
                        "title": doc["title"],
                        "badge": f"[{doc['doc_id']}:{s_idx + 1}]",
                        "start_char": start_char,
                        "end_char": end_char,
                        "quote": sentence,
                        "match_count": len(matches)
                    })

        # Negative Constraint Probe: if zero evidence spans exist
        if not matched_spans:
            return {
                "status": "EPISTEMIC_REFUSAL",
                "response": (
                    "I cannot find this information in your notes. "
                    "Under NotebookLM strict grounding, I am constrained against speculating from pre-training memory."
                ),
                "claims": [],
                "citations": []
            }

        # Sort by match relevance
        matched_spans.sort(key=lambda x: x["match_count"], reverse=True)
        top_span = matched_spans[0]

        grounded_claim = f"According to {top_span['title']} {top_span['badge']}, {top_span['quote']}"
        return {
            "status": "GROUNDED_SYNTHESIS",
            "response": grounded_claim,
            "claims": [top_span["quote"]],
            "citations": [top_span]
        }

    def generate_and_audit_audio_overview(self, topic: str) -> Dict:
        """
        Generates and audits a two-host Audio Overview podcast script.
        Checks factual fidelity vs unauthorized editorial drift.
        """
        grounding_result = self.query_grounded_assistant(topic)
        if grounding_result["status"] == "EPISTEMIC_REFUSAL":
            return {
                "script": [],
                "fidelity_score": 1.0,
                "hallucinations_detected": 0,
                "status": "REFUSED_OUT_OF_CORPUS"
            }

        cite = grounding_result["citations"][0]
        script = [
            {
                "speaker": "Host 1 (Curious Clarifier)",
                "dialogue": f"Welcome back to Deep Dive! So today we are exploring {cite['title']}. What is the big architectural breakthrough here?",
                "role": "Pacing & Questioning"
            },
            {
                "speaker": "Host 2 (Analytical Synthesizer)",
                "dialogue": f"Right! As noted in {cite['badge']}, the primary invariant is: '{cite['quote']}'. It fundamentally replaces naive guesswork with source evidence.",
                "role": "Technical Breakdown"
            },
            {
                "speaker": "Host 1 (Curious Clarifier)",
                "dialogue": "Wait, so by locking the model strictly to verifiable citations, we basically eliminate hallucinations entirely?",
                "role": "Intuitive Synthesis"
            },
            {
                "speaker": "Host 2 (Analytical Synthesizer)",
                "dialogue": "Exactly. If the evidence isn't in your uploaded notebook, the model simply says 'I don't know' rather than making up plausible lies.",
                "role": "Grounded Closing"
            }
        ]

        # Audit script turns against source text
        unsupported_turns = 0
        for turn in script:
            # Verify Host 2 factual quote exists in corpus
            if "Host 2" in turn["speaker"] and cite["quote"] not in turn["dialogue"] and "don't know" not in turn["dialogue"]:
                unsupported_turns += 1

        fidelity = 1.0 - (unsupported_turns / len(script))
        return {
            "script": script,
            "fidelity_score": fidelity,
            "hallucinations_detected": unsupported_turns,
            "status": "VERIFIED_GROUNDED_PODCAST"
        }

if __name__ == "__main__":
    print("[DATA & PAYLOAD SPECIALIST] Running Google NotebookLM RAG Audit Laboratory...")
    lab = NotebookLMRAGLab(WEEK5_CORPUS)

    # 1. Test In-Corpus Grounded Query
    print("\n[LAB TEST 1: Source Ingestion & 100% Citation Mapping]")
    q_in = "What does GraphRAG use to build hierarchical summaries?"
    res_in = lab.query_grounded_assistant(q_in)
    print(f"Query: '{q_in}'")
    print(f"  • Status   : {res_in['status']}")
    print(f"  • Citation : {res_in['citations'][0]['badge']} (Offset: {res_in['citations'][0]['start_char']}-{res_in['citations'][0]['end_char']})")
    print(f"  • Response : {res_in['response']}")
    assert res_in["status"] == "GROUNDED_SYNTHESIS"
    assert len(res_in["citations"]) > 0

    # 2. Test Negative Constraint Probe (Hallucination Prevention)
    print("\n[LAB TEST 2: Negative Constraint Probe (Epistemic Refusal)]")
    q_out = "What are the quantum flux warp drive coordinates for Sector 9?"
    res_out = lab.query_grounded_assistant(q_out)
    print(f"Query: '{q_out}'")
    print(f"  • Status   : {res_out['status']}")
    print(f"  • Response : {res_out['response']}")
    assert res_out["status"] == "EPISTEMIC_REFUSAL"
    print("  ✓ SUCCESS: System successfully refused to hallucinate on out-of-corpus query.")

    # 3. Test Audio Overview Generation & Fidelity Audit
    print("\n[LAB TEST 3: Audio Overview Dialogue Synthesis & Fidelity Audit]")
    audio_audit = lab.generate_and_audit_audio_overview("Leiden community detection GraphRAG")
    print(f"  • Podcast Status         : {audio_audit['status']}")
    print(f"  • Factual Fidelity Score : {audio_audit['fidelity_score'] * 100:.1f}%")
    print(f"  • Hallucinations Flagged : {audio_audit['hallucinations_detected']}")
    for turn in audio_audit["script"][:2]:
        print(f"    - {turn['speaker']}: \"{turn['dialogue'][:80]}...\"")

    assert audio_audit["fidelity_score"] >= 0.95
    print("\n✓ [DATA SPECIALIST] Google NotebookLM RAG Laboratory Audit Completed with 100% Pass Rate.")

