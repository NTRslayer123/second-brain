#!/usr/bin/env python3
"""
SecondSelf — RAG Q&A Search Engine (Phase 5: The Oracle)
Retrieves top-K relevant wiki notes using dense vector embedding similarity
and synthesizes concise, cited answers via Groq LLM (Llama 3.1 8B Instant).
"""

from __future__ import annotations

import os
import sys
import json
import re
from pathlib import Path

# Load environment variables from .env if python-dotenv is installed
try:
    # pyrefly: ignore [missing-import]
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except ImportError:
    pass

# Try importing numpy
try:
    # pyrefly: ignore [missing-import]
    import numpy as np  # type: ignore
except ImportError:
    np = None

# Try importing groq client
try:
    # pyrefly: ignore [missing-import]
    import groq  # type: ignore
except ImportError:
    groq = None

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Base directories
BASE_DIR = Path(__file__).parent.resolve()
WIKI_DIR = BASE_DIR / "wiki"
EMBEDDINGS_CACHE_PATH = BASE_DIR / "embeddings.npy"

# Import vector loader from link.py
import link

# Default parameters
DEFAULT_TOP_K = 3
DEFAULT_MIN_SIMILARITY = 0.20
MODEL_NAME = "llama-3.1-8b-instant"
FALLBACK_MODEL = "llama-3.3-70b-versatile"


def get_groq_client():
    """Initializes and returns Groq client using GROQ_API_KEY from environment or st.secrets."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        try:
            import streamlit as st  # type: ignore
            api_key = st.secrets.get("GROQ_API_KEY")
        except Exception:
            pass

    if not api_key:
        return None
    if groq is None:
        return None
    try:
        return groq.Groq(api_key=api_key)
    except Exception as e:
        print(f"[Warning] Failed to initialize Groq client: {e}", file=sys.stderr)
        return None


def retrieve_context(query: str, top_k: int = DEFAULT_TOP_K, min_similarity: float = DEFAULT_MIN_SIMILARITY) -> list[dict]:
    """
    Encodes query string into dense vector, computes cosine similarity against all wiki notes,
    and returns top-K matching notes sorted by highest similarity score.
    """
    notes = link.load_wiki_notes()
    if not notes or np is None:
        return []

    # Get embedding model from link module
    model = link.get_model()
    if model is None:
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            texts = []
            for note in notes:
                tags_str = " ".join(note["tags"]) if isinstance(note["tags"], list) else str(note["tags"])
                combined_text = f"{note['title']}. {note['summary']}. Tags: {tags_str}. {note['body']}"
                texts.append(combined_text)

            vectorizer = TfidfVectorizer(stop_words='english')
            tfidf_matrix = vectorizer.fit_transform(texts + [query.strip()]).toarray()
            norms = np.linalg.norm(tfidf_matrix, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            tfidf_norm = tfidf_matrix / norms
            doc_embeddings = tfidf_norm[:-1]
            query_embedding = tfidf_norm[-1]
            similarities = np.dot(doc_embeddings, query_embedding)
            similarities = np.clip(similarities, 0.0, 1.0)
        except Exception as e:
            print(f"[Warning] TF-IDF retrieval fallback failed: {e}", file=sys.stderr)
            return []
    else:
        # 1. Encode query prompt
        query_text = query.strip()
        query_embedding = model.encode([query_text], convert_to_numpy=True, normalize_embeddings=True)[0]

        # 2. Get or generate document embeddings
        doc_embeddings = link.generate_embeddings(notes)
        if doc_embeddings is None or getattr(doc_embeddings, 'size', 0) == 0:
            return []

        # 3. Compute cosine similarity scores between query and document vectors
        similarities = np.dot(doc_embeddings, query_embedding)
        similarities = np.clip(similarities, 0.0, 1.0)

    # 4. Rank notes by similarity score
    ranked_results = []
    for idx, score in enumerate(similarities):
        sim_val = float(score)
        if sim_val >= min_similarity:
            note_item = dict(notes[idx])
            note_item["similarity"] = round(sim_val, 4)
            ranked_results.append(note_item)

    # Sort descending by similarity
    ranked_results.sort(key=lambda x: x["similarity"], reverse=True)
    return ranked_results[:top_k]


def construct_rag_prompt(query: str, retrieved_notes: list[dict]) -> tuple[str, str]:
    """
    Constructs (system_instruction, context_user_prompt) for LLM synthesis.
    """
    system_instruction = (
        "You are SecondSelf, a personal AI Second Brain assistant. "
        "Answer the user's question clearly, concisely, and accurately based strictly on the provided notes context. "
        "Always cite the titles of the source notes used in your response in markdown format e.g. [Note Title]."
    )

    context_parts = []
    for i, note in enumerate(retrieved_notes, 1):
        tags_str = ", ".join(note["tags"]) if note["tags"] else "None"
        context_parts.append(
            f"--- SOURCE NOTE {i} ---\n"
            f"Title: {note['title']}\n"
            f"Category: {note['category']}\n"
            f"Tags: {tags_str}\n"
            f"Summary: {note['summary']}\n"
            f"Content:\n{note['body']}\n"
        )

    context_block = "\n".join(context_parts)
    user_prompt = (
        f"USER QUESTION: {query}\n\n"
        f"RELEVANT SECOND BRAIN NOTES CONTEXT:\n{context_block}\n\n"
        f"Synthesize a clear, helpful answer to the question using the context above. Cite source note titles."
    )

    return system_instruction, user_prompt


def ask(query: str, top_k: int = DEFAULT_TOP_K, min_similarity: float = DEFAULT_MIN_SIMILARITY) -> dict:
    """
    Main entrypoint: retrieves relevant context notes, synthesizes answer via Groq LLM (or local fallback),
    and returns structured result dict.
    """
    retrieved_notes = retrieve_context(query, top_k=top_k, min_similarity=min_similarity)

    if not retrieved_notes:
        return {
            "query": query,
            "answer": "No relevant notes found in your Second Brain matching this query topic.",
            "sources": [],
            "confidence": 0.0,
            "retrieved_count": 0
        }

    top_confidence = retrieved_notes[0]["similarity"]
    sources = [
        {
            "id": n["id"],
            "title": n["title"],
            "category": n["category"],
            "similarity": n["similarity"],
            "file_path": str(n["file_path"])
        }
        for n in retrieved_notes
    ]

    client = get_groq_client()

    if client is not None:
        sys_msg, user_msg = construct_rag_prompt(query, retrieved_notes)
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": sys_msg},
                    {"role": "user", "content": user_msg}
                ],
                temperature=0.3,
                max_tokens=800
            )
            answer_text = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[Notice] Groq API call failed: {e}. Switching to local synthesis fallback.", file=sys.stderr)
            answer_text = generate_local_synthesis(query, retrieved_notes)
    else:
        answer_text = generate_local_synthesis(query, retrieved_notes)

    return {
        "query": query,
        "answer": answer_text,
        "sources": sources,
        "confidence": top_confidence,
        "retrieved_count": len(retrieved_notes)
    }


def generate_local_synthesis(query: str, retrieved_notes: list[dict]) -> str:
    """Generates structured local context summary when Groq API key is unavailable."""
    lines = [
        f"Based on {len(retrieved_notes)} relevant notes retrieved from your Second Brain:\n"
    ]
    for note in retrieved_notes:
        sim_pct = int(note['similarity'] * 100)
        lines.append(f"• **[{note['title']}]** ({note['category']} - {sim_pct}% match):")
        lines.append(f"  {note['summary'] or note['body'][:150] + '...'}\n")

    return "\n".join(lines)


def main():
    print("\n==========================================")
    print("  PHASE 5: RAG Q&A Search Engine (ask.py)")
    print("==========================================")

    if len(sys.argv) > 1:
        query_text = " ".join(sys.argv[1:])
    else:
        query_text = "What notes do I have about Python microservices and embeddings?"

    print(f"🔍 Searching Second Brain for: \"{query_text}\"...\n")

    result = ask(query_text)

    print(f"🤖 AI Synthesized Answer:")
    print(f"------------------------------------------")
    print(result["answer"])
    print(f"------------------------------------------\n")

    print(f"📚 Retrieved Source Notes ({result['retrieved_count']} matches | Top Match Confidence: {int(result['confidence']*100)}%):")
    for s in result["sources"]:
        print(f"   • [{s['category']}] {s['title']} (Similarity: {int(s['similarity']*100)}%)")
    print("==========================================\n")


if __name__ == "__main__":
    main()
