#!/usr/bin/env python3
"""
Cleans out all captured and classified user files from raw/ and wiki/
and populates a random set of 10 to 25 realistic example notes for demonstration.
"""

import os
import sys
import shutil
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).parent.parent.resolve()
RAW_DIR = BASE_DIR / "raw"
WIKI_DIR = BASE_DIR / "wiki"

# Pool of 30 realistic topics spanning Projects, Areas, Resources, and Archives
SAMPLE_POOL = [
    {
        "title": "SecondSelf AI Knowledge Base Engine",
        "category": "Projects",
        "type": "note",
        "source": "CLI / User Note",
        "tags": ["ai", "second-brain", "python"],
        "summary": "Building SecondSelf personal AI knowledge base with PARA classification and vector auto-linking.",
        "content": "# SecondSelf AI Knowledge Base Engine\n\nBuilding an open-source personal AI Second Brain system with autonomous PARA classification, dense vector auto-linking, interactive force-directed graph visualizer, and RAG Q&A synthesis."
    },
    {
        "title": "Python Microservices and Vector Embeddings Guide",
        "category": "Resources",
        "type": "link",
        "source": "https://example.com/python-embeddings-guide",
        "tags": ["python", "embeddings", "microservices"],
        "summary": "Comprehensive reference guide to building vector embeddings and similarity search pipelines in Python.",
        "content": "# Python Microservices and Vector Embeddings Guide\n\nReference material covering Sentence Transformers, dense vector embeddings, cosine similarity computation, and building fast microservices in Python."
    },
    {
        "title": "Personal Knowledge Management System Standards",
        "category": "Areas",
        "type": "note",
        "source": "CLI / User Note",
        "tags": ["pkm", "standards", "productivity"],
        "summary": "Ongoing standards and principles for organizing personal knowledge using the PARA method.",
        "content": "# Personal Knowledge Management System Standards\n\nOngoing area of responsibility focused on maintaining high-quality notes, tagging standards, and PARA structure for personal knowledge management."
    },
    {
        "title": "Legacy Note Taking App Export 2023",
        "category": "Archives",
        "type": "file",
        "source": "docs/legacy_export_2023.txt",
        "tags": ["legacy", "notes", "archived"],
        "summary": "Archived reference notes exported from a legacy note-taking application.",
        "content": "# Legacy Note Taking App Export 2023\n\nHistoric archive of notes exported from previous note-taking applications prior to adopting SecondSelf."
    },
    {
        "title": "FastAPI & Async Architecture Patterns",
        "category": "Resources",
        "type": "link",
        "source": "https://fastapi.tiangolo.com/async/",
        "tags": ["fastapi", "python", "async", "web"],
        "summary": "Best practices for asynchronous request handling and background worker queues in FastAPI.",
        "content": "# FastAPI & Async Architecture Patterns\n\nGuide to writing high-throughput async endpoints, background tasks, and dependency injection in modern Python APIs."
    },
    {
        "title": "Q3 Fitness & Strength Training Protocol",
        "category": "Projects",
        "type": "note",
        "source": "CLI / User Note",
        "tags": ["fitness", "health", "workout"],
        "summary": "12-week progressive overload strength training program and macro nutrition plan.",
        "content": "# Q3 Fitness & Strength Training Protocol\n\nActive project tracking 4-day compound lifting routine (Squat, Bench, Deadlift, Overhead Press) and daily protein intake targets."
    },
    {
        "title": "Personal Financial Portfolio & Index Fund Strategy",
        "category": "Areas",
        "type": "note",
        "source": "CLI / User Note",
        "tags": ["finance", "investing", "budget"],
        "summary": "Long-term asset allocation strategy across broad market index funds and emergency savings.",
        "content": "# Personal Financial Portfolio & Index Fund Strategy\n\nOngoing financial management rules: 70% low-cost total stock market ETF, 20% international equities, and 10% cash reserve."
    },
    {
        "title": "DevOps & CI/CD GitHub Actions Pipeline Workflow",
        "category": "Resources",
        "type": "note",
        "source": "CLI / User Note",
        "tags": ["devops", "github-actions", "ci-cd"],
        "summary": "Reusable workflow configuration for automated testing, linting, and Docker container deployment.",
        "content": "# DevOps & CI/CD GitHub Actions Pipeline Workflow\n\nStep-by-step guide for setting up GitHub Actions workflows with matrix builds, caching dependencies, and publishing releases."
    },
    {
        "title": "Designing Data-Intensive Applications Summary",
        "category": "Resources",
        "type": "note",
        "source": "CLI / User Note",
        "tags": ["books", "architecture", "distributed-systems"],
        "summary": "Key takeaways on reliable, scalable, and maintainable distributed system architectures.",
        "content": "# Designing Data-Intensive Applications Summary\n\nNotes on partition strategies, consensus protocols (Raft/Paxos), transactions, event sourcing, and stream processing."
    },
    {
        "title": "Old WordPress Blog Migration Backup 2021",
        "category": "Archives",
        "type": "file",
        "source": "archives/wp_backup_2021.sql",
        "tags": ["wordpress", "archive", "blog"],
        "summary": "Decommissioned database dump and blog post assets from previous website version.",
        "content": "# Old WordPress Blog Migration Backup 2021\n\nSQL export and content media archive from legacy blog server decommissioned in December 2021."
    },
    {
        "title": "React 19 & Next.js Server Components Migration",
        "category": "Projects",
        "type": "note",
        "source": "CLI / User Note",
        "tags": ["react", "nextjs", "frontend", "javascript"],
        "summary": "Refactoring web dashboard frontend to leverage Next.js App Router and Server Actions.",
        "content": "# React 19 & Next.js Server Components Migration\n\nProject roadmap for upgrading UI components, optimizing client bundle size, and implementing streaming server side rendering."
    },
    {
        "title": "Cybersecurity & OAuth2 / JWT Auth Standards",
        "category": "Areas",
        "type": "note",
        "source": "CLI / User Note",
        "tags": ["security", "auth", "oauth2", "jwt"],
        "summary": "Standard operating procedures for token refresh rotation, PKCE flows, and password hashing.",
        "content": "# Cybersecurity & OAuth2 / JWT Auth Standards\n\nSecurity guidelines: using Argon2id for password hashing, short-lived JWT access tokens (15 min), and HttpOnly secure cookies."
    },
    {
        "title": "Vector Databases Comparison: Qdrant vs ChromaDB vs Milvus",
        "category": "Resources",
        "type": "link",
        "source": "https://example.com/vector-db-benchmark",
        "tags": ["vector-database", "ai", "chromadb", "qdrant"],
        "summary": "Benchmarking indexing speed, HNSW recall accuracy, and memory overhead across vector databases.",
        "content": "# Vector Databases Comparison: Qdrant vs ChromaDB vs Milvus\n\nComparative analysis of vector storage engines for similarity retrieval, filtering metadata, and scaling embeddings in production."
    },
    {
        "title": "Home Office Desk Setup & Ergonomics Upgrade",
        "category": "Projects",
        "type": "note",
        "source": "CLI / User Note",
        "tags": ["hardware", "setup", "ergonomics"],
        "summary": "Planning standing desk installation, monitor arm mounting, and cable management system.",
        "content": "# Home Office Desk Setup & Ergonomics Upgrade\n\nHardware checklist: Dual 4K monitor arms, standing desk frame, ergonomic chair adjustment, and under-desk cable raceway."
    },
    {
        "title": "Japanese Language Learning & Kanji Flashcards",
        "category": "Areas",
        "type": "note",
        "source": "CLI / User Note",
        "tags": ["language", "japanese", "anki", "learning"],
        "summary": "Daily spaced-repetition review routine using Anki for JLPT N3 vocabulary and kanji mastery.",
        "content": "# Japanese Language Learning & Kanji Flashcards\n\nOngoing daily area: 20 new Anki cards per day, listening comprehension podcasts, and reading news articles."
    },
    {
        "title": "Decommissioned Redis Cache Cluster v5.0",
        "category": "Archives",
        "type": "file",
        "source": "archives/redis_v5_config.conf",
        "tags": ["redis", "cache", "archived"],
        "summary": "Legacy Redis cluster configuration files replaced by key-value memory store in 2024.",
        "content": "# Decommissioned Redis Cache Cluster v5.0\n\nHistorical configuration settings, memory eviction policies, and cluster sharding topology from legacy caching tier."
    },
    {
        "title": "RAG Pipeline Evaluation Metrics & Hallucination Prevention",
        "category": "Projects",
        "type": "note",
        "source": "CLI / User Note",
        "tags": ["rag", "ai", "llm", "evaluation"],
        "summary": "Implementing Ragas framework to evaluate context relevance, groundedness, and answer faithfulness.",
        "content": "# RAG Pipeline Evaluation Metrics & Hallucination Prevention\n\nTechnical initiative to measure context precision, context recall, and response generation accuracy for SecondSelf search."
    },
    {
        "title": "Kubernetes Pod Resource Optimization & Autoscaling",
        "category": "Resources",
        "type": "link",
        "source": "https://kubernetes.io/docs/concepts/workloads/autoscaling/",
        "tags": ["kubernetes", "k8s", "devops", "cloud"],
        "summary": "Configuring Horizontal Pod Autoscaler (HPA) and setting CPU/Memory request boundaries.",
        "content": "# Kubernetes Pod Resource Optimization & Autoscaling\n\nGuide to avoiding OOMKilled errors, setting appropriate resource requests/limits, and scaling cluster nodes with Karpenter."
    },
    {
        "title": "Weekly Meal Prep & Low-GI Nutrition Routine",
        "category": "Areas",
        "type": "note",
        "source": "CLI / User Note",
        "tags": ["nutrition", "health", "cooking"],
        "summary": "Standard weekly grocery list, batch cooking prep ideas, and balanced meal timing.",
        "content": "# Weekly Meal Prep & Low-GI Nutrition Routine\n\nOngoing health routine focusing on high-protein, whole-food ingredients, batch cooking quinoa and grilled chicken on Sundays."
    },
    {
        "title": "Completed 2023 Tax Return & Expense Receipts",
        "category": "Archives",
        "type": "file",
        "source": "finance/taxes_2023.pdf",
        "tags": ["tax", "finance", "archived"],
        "summary": "Filed tax documentation, deduction receipts, and W-2 forms for tax year 2023.",
        "content": "# Completed 2023 Tax Return & Expense Receipts\n\nArchived record of tax filings, accountant correspondence, and itemized deduction records for 2023."
    },
    {
        "title": "Rust Language Memory Safety & Ownership Model Notes",
        "category": "Resources",
        "type": "note",
        "source": "CLI / User Note",
        "tags": ["rust", "programming", "memory-safety"],
        "summary": "Deep dive into Rust borrow checker, lifetimes, smart pointers (Rc, Arc, RefCell), and concurrency safety.",
        "content": "# Rust Language Memory Safety & Ownership Model Notes\n\nStudy notes explaining Rust compile-time memory guarantees without a garbage collector, data races prevention, and trait bounds."
    },
    {
        "title": "Tokyo & Kyoto Travel Itinerary Planning",
        "category": "Projects",
        "type": "note",
        "source": "CLI / User Note",
        "tags": ["travel", "japan", "vacation"],
        "summary": "Flight booking details, hotel reservations, day trips to Nara/Arashiyama, and JR rail pass routes.",
        "content": "# Tokyo & Kyoto Travel Itinerary Planning\n\nActive travel plan covering 10 days in Japan: Akihabara tech tour, Fushimi Inari shrine, bullet train connections, and food guide."
    },
    {
        "title": "System Monitoring & Observability with Prometheus & Grafana",
        "category": "Areas",
        "type": "note",
        "source": "CLI / User Note",
        "tags": ["monitoring", "grafana", "prometheus", "devops"],
        "summary": "Maintaining real-time alerts, dashboard metrics, latency histograms, and error rates.",
        "content": "# System Monitoring & Observability with Prometheus & Grafana\n\nArea of responsibility maintaining SLI/SLO dashboards, Prometheus metric exporters, and P99 latency alerts for infrastructure."
    },
    {
        "title": "Archived Django 3.2 Backend Codebase Documentation",
        "category": "Archives",
        "type": "file",
        "source": "docs/django_v3_docs.md",
        "tags": ["django", "python", "legacy"],
        "summary": "API documentation for deprecated Django 3.2 monolithic service replaced by FastAPI in 2024.",
        "content": "# Archived Django 3.2 Backend Codebase Documentation\n\nDocumentation covering legacy Django ORM models, Celery background tasks, and REST framework serializers."
    },
    {
        "title": "Deep Work & Focus Time Management System",
        "category": "Areas",
        "type": "note",
        "source": "CLI / User Note",
        "tags": ["productivity", "time-management", "deep-work"],
        "summary": "Time-blocking routines, 90-minute focus blocks, notification batching, and distraction minimization.",
        "content": "# Deep Work & Focus Time Management System\n\nDaily framework based on Cal Newport's Deep Work: morning uninterrupted coding block, shutdown ritual, and digital minimalism."
    },
    {
        "title": "LLM Quantization & Local Inference with Ollama & GGUF",
        "category": "Resources",
        "type": "link",
        "source": "https://example.com/llm-quantization-guide",
        "tags": ["llm", "ai", "ollama", "quantization"],
        "summary": "Running Llama-3 and Mistral models locally using 4-bit GGUF quantization and llama.cpp.",
        "content": "# LLM Quantization & Local Inference with Ollama & GGUF\n\nPractical guide on RAM requirements, context window limits, GPU offloading layers, and running local AI inference."
    },
    {
        "title": "Smart Home Automation Setup with Home Assistant",
        "category": "Projects",
        "type": "note",
        "source": "CLI / User Note",
        "tags": ["iot", "smart-home", "automation"],
        "summary": "Integrating Zigbee temperature sensors, smart lighting scenes, and local privacy-first automations.",
        "content": "# Smart Home Automation Setup with Home Assistant\n\nProject tracking Home Assistant OS installation on Raspberry Pi, Zigbee mesh network pairing, and voice assistant integration."
    },
    {
        "title": "Guitar Music Theory & Pentatonic Soloing Practice",
        "category": "Areas",
        "type": "note",
        "source": "CLI / User Note",
        "tags": ["music", "guitar", "practice"],
        "summary": "Daily 30-minute practice regime covering minor pentatonic scale positions, CAGED system, and metronome drills.",
        "content": "# Guitar Music Theory & Pentatonic Soloing Practice\n\nOngoing musical hobby log: alternate picking exercises, chord inversions across fretboard, and improvising over backing tracks."
    },
    {
        "title": "Web Scraping & DOM Parsing Techniques with BeautifulSoup",
        "category": "Resources",
        "type": "note",
        "source": "CLI / User Note",
        "tags": ["python", "web-scraping", "html"],
        "summary": "Handling dynamic web pages, user-agent headers, proxy rotation, and clean HTML text extraction.",
        "content": "# Web Scraping & DOM Parsing Techniques with BeautifulSoup\n\nSnippet library for parsing HTML tables, handling HTTP 429 rate limits, and extracting clean markdown body text."
    },
    {
        "title": "Deprecated Node.js Express API Server 2022",
        "category": "Archives",
        "type": "file",
        "source": "archives/express_api_2022.tar.gz",
        "tags": ["nodejs", "express", "archived"],
        "summary": "Archived repository snapshot of Express.js REST API service migrated to Python.",
        "content": "# Deprecated Node.js Express API Server 2022\n\nSource code tarball and package.json manifest for historical Node.js backend replaced during stack unification."
    }
]


def clean_directory(dir_path: Path):
    """Removes all files and subdirectories inside dir_path except .gitkeep."""
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
    """Ensures directory exists and contains a .gitkeep file."""
    dir_path.mkdir(parents=True, exist_ok=True)
    gitkeep = dir_path / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.write_text("# Keep directory in git\n", encoding="utf-8")


def generate_unique_id(index: int, total: int) -> tuple[str, str]:
    """Generates a timestamp ID and ISO timestamp string."""
    now = datetime.now(timezone.utc) - timedelta(minutes=(total - index) * 15)
    id_str = now.strftime("%Y%m%d_%H%M%S") + f"_{random.randint(100000, 999999):x}"
    iso_str = now.isoformat()
    return id_str, iso_str


def main():
    # Pick a random number of sample items between 10 and 25
    count = random.randint(10, 25)
    
    print(f"Cleaning raw/ and wiki/ in {BASE_DIR}...")
    clean_directory(RAW_DIR)
    clean_directory(WIKI_DIR)

    # Ensure PARA subfolders and gitkeeps exist
    for sub in ["Projects", "Areas", "Resources", "Archives"]:
        create_gitkeep(WIKI_DIR / sub)
    create_gitkeep(RAW_DIR)

    # Select `count` unique random samples from SAMPLE_POOL
    selected_samples = random.sample(SAMPLE_POOL, min(count, len(SAMPLE_POOL)))

    category_counts = {"Projects": 0, "Areas": 0, "Resources": 0, "Archives": 0}

    print(f"Populating {len(selected_samples)} random sample notes across PARA categories...")

    for i, ex in enumerate(selected_samples):
        note_id, timestamp_str = generate_unique_id(i, len(selected_samples))
        category = ex["category"]
        category_counts[category] += 1

        # 1. Create raw capture directory & files
        raw_cap_dir = RAW_DIR / note_id
        raw_cap_dir.mkdir(parents=True, exist_ok=True)

        meta_payload = {
            "id": note_id,
            "timestamp": timestamp_str,
            "type": ex["type"],
            "source": ex["source"],
            "title": ex["title"],
            "char_count": len(ex["content"]),
            "content_file": "content.md",
            "captured_via": "capture.py"
        }
        (raw_cap_dir / "metadata.json").write_text(json.dumps(meta_payload, indent=2), encoding="utf-8")
        (raw_cap_dir / "content.md").write_text(ex["content"], encoding="utf-8")

        # 2. Create classified markdown file in wiki/{category}/{id}.md
        wiki_cat_dir = WIKI_DIR / category
        wiki_cat_dir.mkdir(parents=True, exist_ok=True)

        fm = [
            "---",
            f'id: "{note_id}"',
            f'title: "{ex["title"]}"',
            f'category: "{category}"',
            f'tags: {json.dumps(ex["tags"])}',
            f'summary: "{ex["summary"]}"',
            f'created_at: "{timestamp_str}"',
            "auto_links: []",
            "---",
            "",
            ex["content"],
            ""
        ]
        (wiki_cat_dir / f"{note_id}.md").write_text("\n".join(fm), encoding="utf-8")

    print(f"✅ Randomly populated {len(selected_samples)} example items into raw/ and wiki/:")
    for cat, cnt in category_counts.items():
        print(f"   • {cat}: {cnt} items")


if __name__ == "__main__":
    main()
