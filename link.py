#!/usr/bin/env python3
"""
SecondSelf — Dense Vector Auto-Link Engine (Phase 3: The Librarian)
Computes dense sentence embeddings (all-MiniLM-L6-v2) for all wiki notes,
calculates pairwise cosine similarity, and inserts bidirectional markdown links ([[note_id]]).
"""

from __future__ import annotations

import os
import sys
import json
import re
import tempfile
from pathlib import Path
# Try importing numpy with fallback handling
try:
    # pyrefly: ignore [missing-import]
    import numpy as np  # type: ignore
except ImportError:
    np = None

# Load environment variables from .env if python-dotenv is installed
try:
    # pyrefly: ignore [missing-import]
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except ImportError:
    pass

# Try importing sentence_transformers
try:
    # pyrefly: ignore [missing-import]
    from sentence_transformers import SentenceTransformer  # type: ignore
except ImportError:
    SentenceTransformer = None

# Base directories
BASE_DIR = Path(__file__).parent.resolve()
WIKI_DIR = BASE_DIR / "wiki"
EMBEDDINGS_CACHE_PATH = BASE_DIR / "embeddings.npy"

DEFAULT_MODEL_NAME = "BAAI/bge-small-en-v1.5"
DEFAULT_THRESHOLD = float(os.getenv("AUTO_LINK_THRESHOLD", "0.48"))

_MODEL_CACHE = None


def get_model():
    """Lazy loader for SentenceTransformer model."""
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE

    if SentenceTransformer is None:
        print("[Error] 'sentence-transformers' package is not installed.", file=sys.stderr)
        return None

    try:
        print(f"[Notice] Loading embedding model '{DEFAULT_MODEL_NAME}'...")
        _MODEL_CACHE = SentenceTransformer(DEFAULT_MODEL_NAME)
        return _MODEL_CACHE
    except Exception as e:
        print(f"[Error] Failed to load SentenceTransformer model: {e}", file=sys.stderr)
        return None


def parse_yaml_frontmatter(content: str) -> tuple[dict, str]:
    """
    Parses frontmatter block (between --- and ---) and body content.
    Returns (frontmatter_dict, body_content_text).
    """
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
    if not match:
        return {}, content

    frontmatter_raw = match.group(1)
    body = match.group(2)
    metadata = {}

    for line in frontmatter_raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()
            
            # Simple string unquoting
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1].replace('\\"', '"').replace('\\\\', '\\')
            elif val.startswith("'") and val.endswith("'"):
                val = val[1:-1]
            
            # Parse simple list representation [item1, item2]
            if val.startswith("[") and val.endswith("]"):
                inner = val[1:-1].strip()
                if not inner:
                    val = []
                else:
                    items = [i.strip().strip('"').strip("'") for i in inner.split(",") if i.strip()]
                    val = items
            
            metadata[key] = val

    return metadata, body


def strip_related_notes_section(body: str) -> str:
    """Strips any existing '## Related Brain Notes' section from the markdown body."""
    pattern = r"\n*##\s+Related Brain Notes\s*\n.*$"
    cleaned = re.sub(pattern, "", body, flags=re.DOTALL)
    return cleaned.strip()


def load_wiki_notes() -> list[dict]:
    """
    Recursively scans wiki/ directory (and PARA subfolders) for all .md files.
    Returns structured list of note dictionaries.
    """
    if not WIKI_DIR.exists():
        print(f"[Notice] Wiki directory '{WIKI_DIR}' does not exist.", file=sys.stderr)
        return []

    md_files = list(WIKI_DIR.rglob("*.md"))
    notes = []

    for file_path in sorted(md_files):
        if file_path.name.startswith("."):
            continue
        try:
            raw_text = file_path.read_text(encoding="utf-8")
            meta, body = parse_yaml_frontmatter(raw_text)
            
            note_id = meta.get("id") or file_path.stem
            title = meta.get("title") or file_path.stem
            category = meta.get("category") or "Resources"
            summary = meta.get("summary") or ""
            tags = meta.get("tags") if isinstance(meta.get("tags"), list) else []
            clean_body = strip_related_notes_section(body)

            notes.append({
                "id": note_id,
                "title": title,
                "category": category,
                "summary": summary,
                "tags": tags,
                "body": clean_body,
                "file_path": file_path,
                "meta": meta,
                "raw_text": raw_text
            })
        except Exception as e:
            print(f"[Warning] Failed to load wiki note {file_path}: {e}", file=sys.stderr)

    return notes


def generate_embeddings(notes: list[dict]) -> np.ndarray | None:
    """
    Encodes combined text (title + summary + tags + body) into dense vectors.
    """
    if np is None:
        print("[Error] 'numpy' package is not installed.", file=sys.stderr)
        return None

    if not notes:
        return np.empty((0, 384))

    texts = []
    for note in notes:
        tags_str = " ".join(note["tags"]) if isinstance(note["tags"], list) else str(note["tags"])
        combined_text = f"{note['title']}. {note['summary']}. Tags: {tags_str}. {note['body']}"
        texts.append(combined_text)

    model = get_model()
    if model is None:
        print("[Warning] SentenceTransformer unavailable. Returning dummy zero vectors.", file=sys.stderr)
        return np.zeros((len(notes), 384))

    embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    
    # Cache matrix to local disk
    try:
        np.save(EMBEDDINGS_CACHE_PATH, embeddings)
    except Exception as e:
        print(f"[Warning] Failed to cache embeddings matrix: {e}", file=sys.stderr)

    return embeddings


def compute_similarity_matrix(embeddings: np.ndarray | None) -> np.ndarray | None:
    """Computes pairwise cosine similarity matrix."""
    if np is None or embeddings is None or getattr(embeddings, 'size', 0) == 0:
        return np.empty((0, 0)) if np is not None else None
    # Normalized embeddings dot product equals cosine similarity
    sim_matrix = np.dot(embeddings, embeddings.T)
    # Clip numerical precision artifacts to [0.0, 1.0]
    return np.clip(sim_matrix, 0.0, 1.0)



def format_yaml_val(val) -> str:
    """Formats Python values into safe YAML string representation."""
    if isinstance(val, str):
        escaped = val.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{escaped}"'
    elif isinstance(val, list):
        if not val:
            return "[]"
        formatted_items = [format_yaml_val(item) for item in val]
        return "[" + ", ".join(formatted_items) + "]"
    return str(val)


def format_auto_links_yaml(links: list[dict]) -> str:
    """Formats auto_links list into YAML frontmatter block."""
    if not links:
        return "auto_links: []"
    
    lines = ["auto_links:"]
    for link in links:
        lines.append(f'  - id: {format_yaml_val(link["id"])}')
        lines.append(f'    title: {format_yaml_val(link["title"])}')
        lines.append(f'    similarity: {link["similarity"]}')
    return "\n".join(lines)


def update_note_file(note: dict, links: list[dict]):
    """
    Rewrites markdown file updating frontmatter auto_links and
    appending/updating the '## Related Brain Notes' section.
    """
    file_path = note["file_path"]
    note_id = note["id"]
    title = note["title"]
    category = note["category"]
    tags = note["tags"]
    summary = note["summary"]
    created_at = note["meta"].get("created_at", "")

    # Format Frontmatter
    fm_lines = [
        "---",
        f"id: {format_yaml_val(note_id)}",
        f"title: {format_yaml_val(title)}",
        f"category: {format_yaml_val(category)}",
        f"tags: {format_yaml_val(tags)}",
        f"summary: {format_yaml_val(summary)}",
        f"created_at: {format_yaml_val(created_at)}",
        format_auto_links_yaml(links),
        "---"
    ]
    frontmatter_str = "\n".join(fm_lines)

    # Clean Body
    clean_body = strip_related_notes_section(note["body"])

    # Construct Related Notes Section
    related_section = ""
    if links:
        rel_lines = ["", "## Related Brain Notes"]
        for link in links:
            rel_lines.append(f'- [[{link["id"]}]] - {link["title"]} (Similarity: {link["similarity"]})')
        related_section = "\n".join(rel_lines)

    full_content = f"{frontmatter_str}\n\n{clean_body}{related_section}\n"

    # Atomic Write
    target_dir = file_path.parent
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=target_dir, delete=False) as tf:
        tf.write(full_content)
        temp_name = tf.name

    os.replace(temp_name, file_path)


def auto_link_wiki(similarity_threshold: float = DEFAULT_THRESHOLD) -> dict:
    """
    Core entrypoint: loads all wiki notes, computes vector similarity,
    and updates bidirectional links across wiki notes.
    """
    print(f"\n--- Running Dense Vector Auto-Link Engine (Threshold: {similarity_threshold}) ---")
    notes = load_wiki_notes()
    if not notes:
        print("[Notice] No wiki notes found to auto-link.")
        return {"total_notes": 0, "linked_notes": 0, "total_edges": 0}

    print(f"Loaded {len(notes)} wiki notes. Computing sentence embeddings...")
    embeddings = generate_embeddings(notes)
    sim_matrix = compute_similarity_matrix(embeddings)

    if sim_matrix is None or np is None:
        print("[Warning] Vector engine unavailable (missing dependencies). Skipping auto-linking.")
        return {"total_notes": len(notes), "linked_notes": 0, "total_edges": 0}

    num_notes = len(notes)

    links_by_note = {i: [] for i in range(num_notes)}
    total_edges = 0

    # Discover links above similarity threshold
    for i in range(num_notes):
        for j in range(num_notes):
            if i == j:
                continue
            sim_score = float(sim_matrix[i, j])
            if sim_score >= similarity_threshold:
                links_by_note[i].append({
                    "id": notes[j]["id"],
                    "title": notes[j]["title"],
                    "similarity": round(sim_score, 2)
                })

    linked_notes_count = 0
    # Update note files
    for i in range(num_notes):
        # Sort links by highest similarity first
        links = sorted(links_by_note[i], key=lambda x: x["similarity"], reverse=True)
        if links:
            linked_notes_count += 1
            total_edges += len(links)
        update_note_file(notes[i], links)

    # Pairwise bidirectional edges count = total_edges // 2
    unique_connections = total_edges // 2
    print("\n--- Auto-Link Processing Complete ---")
    print(f"Total Notes Processed : {num_notes}")
    print(f"Notes with Auto-Links : {linked_notes_count}")
    print(f"Bidirectional Links   : {unique_connections}")

    return {
        "total_notes": num_notes,
        "linked_notes": linked_notes_count,
        "total_edges": unique_connections
    }


def main():
    threshold = DEFAULT_THRESHOLD
    if len(sys.argv) > 1:
        try:
            threshold = float(sys.argv[1])
        except ValueError:
            print(f"[Warning] Invalid threshold argument '{sys.argv[1]}'. Using default {DEFAULT_THRESHOLD}.")

    auto_link_wiki(similarity_threshold=threshold)


if __name__ == "__main__":
    main()
