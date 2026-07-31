#!/usr/bin/env python3
"""
SecondSelf — Vector Embeddings Visualizer & Inspector
Loads and displays the dense vector embeddings stored in `embeddings.npy`,
mapping each vector row to its corresponding markdown note in `wiki/`.

Usage:
  python view_embeddings.py                # Overview of all note vectors
  python view_embeddings.py --index 0      # Detailed 384-dim vector for note at index 0
  python view_embeddings.py --similarity   # Pairwise cosine similarity matrix preview
"""

import sys
import os
import argparse
from pathlib import Path

# Ensure UTF-8 output encoding for Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Load numpy defensively
try:
    import numpy as np
except ImportError:
    print("[Error] 'numpy' package is required. Install using: pip install numpy", file=sys.stderr)
    sys.exit(1)

# Base directory
BASE_DIR = Path(__file__).parent.resolve()
EMBEDDINGS_CACHE_PATH = BASE_DIR / "embeddings.npy"
WIKI_DIR = BASE_DIR / "wiki"


def parse_yaml_frontmatter(content: str) -> tuple[dict, str]:
    """Parses YAML frontmatter block."""
    import re
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
            metadata[key.strip()] = val.strip().strip('"').strip("'")
    return metadata, body


def get_wiki_notes_list() -> list[dict]:
    """Scans wiki/ for markdown notes in deterministic sorted order."""
    if not WIKI_DIR.exists():
        return []
    md_files = sorted(list(WIKI_DIR.rglob("*.md")))
    notes = []
    for f in md_files:
        if f.name.startswith("."):
            continue
        try:
            raw_text = f.read_text(encoding="utf-8")
            meta, _ = parse_yaml_frontmatter(raw_text)
            notes.append({
                "id": meta.get("id") or f.stem,
                "title": meta.get("title") or f.stem,
                "category": meta.get("category") or f.parent.name,
                "file_path": f
            })
        except Exception:
            notes.append({"id": f.stem, "title": f.stem, "category": f.parent.name, "file_path": f})
    return notes


def view_embeddings(index: int | None = None, show_sim: bool = False, dim_preview: int = 6):
    if not EMBEDDINGS_CACHE_PATH.exists():
        print(f"[Error] Embeddings file '{EMBEDDINGS_CACHE_PATH.name}' not found at {EMBEDDINGS_CACHE_PATH}", file=sys.stderr)
        print("Run 'python link.py' first to generate vector embeddings.", file=sys.stderr)
        sys.exit(1)

    # Load matrix
    try:
        embeddings = np.load(EMBEDDINGS_CACHE_PATH)
    except Exception as e:
        print(f"[Error] Failed to load '{EMBEDDINGS_CACHE_PATH}': {e}", file=sys.stderr)
        sys.exit(1)

    file_size_kb = EMBEDDINGS_CACHE_PATH.stat().st_size / 1024.0
    num_vectors, num_dims = embeddings.shape
    notes = get_wiki_notes_list()

    print("\n==================================================")
    print("      SecondSelf Vector Embeddings Viewer        ")
    print("==================================================")
    print(f"[File]     Target File : {EMBEDDINGS_CACHE_PATH.name}")
    print(f"[Shape]    Matrix Shape: {num_vectors} Notes x {num_dims} Dimensions")
    print(f"[Size]     File Size   : {file_size_kb:.2f} KB")
    print(f"[Dtype]    Data Type   : {embeddings.dtype}")
    print("--------------------------------------------------\n")

    # If specific index requested
    if index is not None:
        if index < 0 or index >= num_vectors:
            print(f"[Error] Index {index} is out of bounds (0 to {num_vectors - 1}).", file=sys.stderr)
            sys.exit(1)

        vec = embeddings[index]
        note = notes[index] if index < len(notes) else {}
        note_id = note.get("id", f"Note #{index}")
        title = note.get("title", "Unknown Title")
        category = note.get("category", "Uncategorized")

        print(f"[INSPECT] VECTOR AT INDEX [{index}]")
        print(f"   Note ID  : {note_id}")
        print(f"   Title    : {title}")
        print(f"   Category : {category}")
        print(f"   L2 Norm  : {np.linalg.norm(vec):.4f} (Vector Magnitude)")
        print(f"   Min / Max: {vec.min():.4f} / {vec.max():.4f}")
        print(f"   Mean / SD: {vec.mean():.4f} / {vec.std():.4f}")
        print("\n--- Vector Values (384 Float32 Array) ---")
        
        for row_start in range(0, num_dims, 8):
            chunk = vec[row_start:row_start + 8]
            formatted_chunk = "  ".join([f"{v:+.4f}" for v in chunk])
            print(f"[{row_start:03d}-{row_start+len(chunk)-1:03d}]:  {formatted_chunk}")

        print("\n==================================================\n")
        return

    # Print summary table of all vectors
    print("-" * 105)
    print(f"{'Idx':<4} | {'Note ID':<26} | {'PARA Category':<10} | {'L2 Norm':<7} | {'Preview (First 6 Dimensions)':<48}")
    print("-" * 105)

    for i in range(num_vectors):
        vec = embeddings[i]
        note = notes[i] if i < len(notes) else {}
        note_id = note.get("id", f"note_{i}")
        category = note.get("category", "N/A")
        
        note_id_str = (note_id[:24] + "..") if len(note_id) > 26 else note_id
        norm_str = f"{np.linalg.norm(vec):.3f}"
        
        preview_vals = " ".join([f"{v:+.3f}" for v in vec[:dim_preview]])
        print(f"{i:<4} | {note_id_str:<26} | {category:<10} | {norm_str:<7} | [{preview_vals} ...]")

    print("-" * 105 + "\n")

    # Display pairwise similarity preview if requested
    if show_sim:
        print("--- Pairwise Cosine Similarity Matrix (Top 5x5 Submatrix Preview) ---")
        sims = np.dot(embeddings, embeddings.T)
        sims = np.clip(sims, 0.0, 1.0)
        sub_size = min(5, num_vectors)
        
        header = "       " + " ".join([f"[{j:02d}]  " for j in range(sub_size)])
        print(header)
        for i in range(sub_size):
            row_str = f"[{i:02d}]  " + " ".join([f"{sims[i, j]:.3f} " for j in range(sub_size)])
            print(row_str)
        print("-" * 50 + "\n")


def main():
    parser = argparse.ArgumentParser(description="View and inspect dense vector embeddings stored in embeddings.npy")
    parser.add_argument("-i", "--index", type=int, default=None, help="Specific vector row index to inspect in full 384-dim detail")
    parser.add_argument("-s", "--similarity", action="store_true", help="Display top 5x5 pairwise similarity matrix")
    
    args = parser.parse_args()
    view_embeddings(index=args.index, show_sim=args.similarity)


if __name__ == "__main__":
    main()
