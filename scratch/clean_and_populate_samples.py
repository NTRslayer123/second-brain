#!/usr/bin/env python3
"""
Cleans out all captured and classified user files from raw/ and wiki/
and populates clean non-sensitive example data for GitHub demonstration.
"""

import os
import sys
import shutil
import json
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).parent.parent.resolve()
RAW_DIR = BASE_DIR / "raw"
WIKI_DIR = BASE_DIR / "wiki"


def clean_directory(dir_path: Path):
    if not dir_path.exists():
        dir_path.mkdir(parents=True, exist_ok=True)
        return
    for item in dir_path.iterdir():
        if item.name == ".gitkeep":
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()


def create_gitkeep(dir_path: Path):
    dir_path.mkdir(parents=True, exist_ok=True)
    gitkeep = dir_path / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.write_text("# Keep directory in git\n", encoding="utf-8")


def main():
    print(f"Cleaning raw/ and wiki/ in {BASE_DIR}...")
    clean_directory(RAW_DIR)
    clean_directory(WIKI_DIR)

    # Ensure PARA subfolders and gitkeeps exist
    for sub in ["Projects", "Areas", "Resources", "Archives"]:
        create_gitkeep(WIKI_DIR / sub)
    create_gitkeep(RAW_DIR)

    # Clean example items
    examples = [
        {
            "id": "20260730_000001_p1sample",
            "timestamp": "2026-07-30T00:00:01.000000+00:00",
            "type": "note",
            "source": "CLI / User Note",
            "title": "Project SecondSelf AI Knowledge Base",
            "category": "Projects",
            "tags": ["ai", "second-brain", "python"],
            "summary": "Building SecondSelf personal AI knowledge base with PARA classification and vector auto-linking.",
            "content": "# Project SecondSelf AI Knowledge Base\n\nBuilding an open-source personal AI Second Brain system with autonomous PARA classification, dense vector auto-linking, interactive force-directed graph visualizer, and RAG Q&A synthesis."
        },
        {
            "id": "20260730_000002_r1sample",
            "timestamp": "2026-07-30T00:00:02.000000+00:00",
            "type": "link",
            "source": "https://example.com/python-embeddings-guide",
            "title": "Python Microservices and Vector Embeddings Guide",
            "category": "Resources",
            "tags": ["python", "embeddings", "microservices"],
            "summary": "Comprehensive reference guide to building vector embeddings and similarity search pipelines in Python.",
            "content": "# Python Microservices and Vector Embeddings Guide\n\nReference material covering Sentence Transformers, dense vector embeddings, cosine similarity computation, and building fast microservices in Python."
        },
        {
            "id": "20260730_000003_a1sample",
            "timestamp": "2026-07-30T00:00:03.000000+00:00",
            "type": "note",
            "source": "CLI / User Note",
            "title": "Personal Knowledge Management System Standards",
            "category": "Areas",
            "tags": ["pkm", "standards", "productivity"],
            "summary": "Ongoing standards and principles for organizing personal knowledge using the PARA method.",
            "content": "# Personal Knowledge Management System Standards\n\nOngoing area of responsibility focused on maintaining high-quality notes, tagging standards, and PARA structure for personal knowledge management."
        },
        {
            "id": "20260730_000004_ar1sample",
            "timestamp": "2026-07-30T00:00:04.000000+00:00",
            "type": "file",
            "source": "docs/legacy_export_2023.txt",
            "title": "Legacy Note Taking App Export 2023",
            "category": "Archives",
            "tags": ["legacy", "notes", "archived"],
            "summary": "Archived reference notes exported from a legacy note-taking application.",
            "content": "# Legacy Note Taking App Export 2023\n\nHistoric archive of notes exported from previous note-taking applications prior to adopting SecondSelf."
        }
    ]

    for ex in examples:
        # Create raw capture directory
        raw_cap_dir = RAW_DIR / ex["id"]
        raw_cap_dir.mkdir(parents=True, exist_ok=True)
        
        meta_payload = {
            "id": ex["id"],
            "timestamp": ex["timestamp"],
            "type": ex["type"],
            "source": ex["source"],
            "title": ex["title"],
            "char_count": len(ex["content"]),
            "content_file": "content.md",
            "captured_via": "capture.py"
        }
        (raw_cap_dir / "metadata.json").write_text(json.dumps(meta_payload, indent=2), encoding="utf-8")
        (raw_cap_dir / "content.md").write_text(ex["content"], encoding="utf-8")

        # Create classified markdown in wiki/{category}/{id}.md
        wiki_cat_dir = WIKI_DIR / ex["category"]
        wiki_cat_dir.mkdir(parents=True, exist_ok=True)
        
        fm = [
            "---",
            f'id: "{ex["id"]}"',
            f'title: "{ex["title"]}"',
            f'category: "{ex["category"]}"',
            f'tags: {json.dumps(ex["tags"])}',
            f'summary: "{ex["summary"]}"',
            f'created_at: "{ex["timestamp"]}"',
            "auto_links: []",
            "---",
            "",
            ex["content"],
            ""
        ]
        (wiki_cat_dir / f"{ex['id']}.md").write_text("\n".join(fm), encoding="utf-8")

    print(f"✅ Created {len(examples)} clean non-sensitive example items in raw/ and wiki/.")


if __name__ == "__main__":
    main()
