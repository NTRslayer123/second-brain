# Phase-Wise Implementation Plan: SecondSelf (AI Second Brain)

**Project Name**: SecondSelf — Your Personal AI Second Brain  
**Derived From**: [docs/architecture.md](file:///g:/My%20Drive/AI/docs/architecture.md) & [docs/Problem_statement.md](file:///g:/My%20Drive/AI/docs/Problem_statement.md)  
**Version**: 1.0.0  

---

## Overview

This implementation plan outlines the step-by-step development of **SecondSelf**, structured into **10 distinct phases (Phase 0 through Phase 9)**. Each phase maps to a verifiable milestone, taking raw unstructured captures (notes, URLs, PDFs) through autonomous LLM classification, dense vector auto-linking, interactive force-directed graph visualization, RAG Q&A synthesis, and final public deployment.

```
Phase 0: Environment & Scaffold Setup
  ↓
Phase 1: Capture Pipeline (capture.py) ── [🏅 Milestone: The Archivist]
  ↓
Phase 2: PARA LLM Classifier (classify.py)
  ↓
Phase 3: Vector Auto-Linker (link.py) ───── [🏅 Milestone: The Librarian]
  ↓
Phase 4: Graph Data & Visualizer (build_graph.py) ── [🏅 Milestone: The Cartographer]
  ↓
Phase 5: RAG Q&A Engine (ask.py)
  ↓
Phase 6: Unified Streamlit UI (app.py) ──── [🏅 Milestone: The Oracle]
  ↓
Phase 7: Comprehensive Local Testing & Validation
  ↓
Phase 8: Public Cloud Deployment (Streamlit Cloud / HF Spaces)
  ↓
Phase 9: Final E2E Verification & Documentation
```

---

## Phase 0: Repository Setup & Environment Scaffolding

### Goal
Initialize the repository workspace, configuration files, directory structures, and Python dependency environment.

### Target Deliverables & Files
- [NEW] `raw/` directory (holds raw capture JSON payloads)
- [NEW] `wiki/` directory (holds processed Markdown notes with frontmatter)
- [NEW] `requirements.txt` (core dependencies: `streamlit`, `groq`, `sentence-transformers`, `trafilatura`, `pypdf`, `pyvis`, `numpy`, `python-dotenv`)
- [NEW] `.env.example` (template for API keys like `GROQ_API_KEY`)
- [NEW] `.gitignore` (ignore `.env`, `__pycache__`, local cache files)

### Tasks
1. Create `raw/` and `wiki/` empty directories with `.gitkeep` files.
2. Define dependencies in `requirements.txt`.
3. Create `.env.example` containing `GROQ_API_KEY=your_groq_api_key_here`.
4. Create `.gitignore` to prevent committing sensitive keys or temporary vector cache files.

### Verification Criteria
- `python -m pip install -r requirements.txt` succeeds cleanly.
- `raw/` and `wiki/` directories exist on the local filesystem.

---

## Phase 1: Capture Engine (`capture.py`) — Milestone: The Archivist

### Goal
Build a unified capture interface capable of ingesting plain text notes, web URLs, and local files (TXT, MD, PDF), assigning ISO timestamps and unique IDs, and persisting them to `raw/`.

### Target Deliverables & Files
- [NEW] `capture.py`

### Key Modules & Functions to Implement
- `generate_capture_id() -> str`: Output format `YYYYMMDD_HHMMSS_{short_hash}`.
- `extract_url_content(url: str) -> str`: Use `trafilatura` or `requests` + `BeautifulSoup` to scrape body text.
- `extract_file_content(filepath: str) -> str`: Parse `.txt`, `.md`, or `.pdf` (using `pypdf`).
- `capture(content_or_path: str, source_type: str) -> str`: Core entrypoint saving payload to `raw/{timestamp}_{id}.json`.
- `main()` CLI wrapper: Support command-line execution (`python capture.py "note or URL or filepath"`).

### Verification Criteria
- Command `python capture.py "Remember to review system design patterns"` saves a JSON payload into `raw/`.
- Command `python capture.py "https://example.com"` successfully scrapes article text into `raw/`.
- 10+ real capture items populated in `raw/`.
- 🏅 **Badge Achieved**: *The Archivist*

---

## Phase 2: Autonomous Classifier (`classify.py`)

### Goal
Leverage Groq API (`llama-3.1-8b-instant`) to auto-classify raw captures into **PARA categories** (*Projects, Areas, Resources, Archives*), extract relevant tags, generate a 1-line summary, and write structured Markdown files to `wiki/`.

### Target Deliverables & Files
- [NEW] `classify.py`

### Key Modules & Functions to Implement
- `get_groq_client()`: Initializes client reading `GROQ_API_KEY`.
- `classify_raw_content(raw_text: str) -> dict`: Sends prompt with strict JSON schema instructions (`category`, `tags`, `summary`, `title`).
- `process_raw_to_wiki(raw_file_path: str) -> str`: Transforms `raw/*.json` into `wiki/*.md` with standard YAML frontmatter.
- `batch_classify_all()`: Processes all unclassified items in `raw/`.

### Verification Criteria
- Input raw payload is correctly formatted into YAML frontmatter + Markdown body.
- PARA category is strictly restricted to one of: `Projects`, `Areas`, `Resources`, `Archives`.
- Output written cleanly to `wiki/{timestamp}_{id}.md`.

---

## Phase 3: Dense Vector Auto-Link Engine (`link.py`) — Milestone: The Librarian

### Goal
Compute dense sentence embeddings (`all-MiniLM-L6-v2`) for all wiki notes, calculate cosine similarity between document vectors, and insert bidirectional links (`[[note_id]]`) when similarity exceeds a threshold (e.g., $0.65$).

### Target Deliverables & Files
- [NEW] `link.py`

### Key Modules & Functions to Implement
- `load_wiki_notes() -> List[dict]`: Parses YAML frontmatter and Markdown content from all files in `wiki/`.
- `generate_embeddings(notes: List[dict]) -> np.ndarray`: Encodes `title + summary + content` using `SentenceTransformer('all-MiniLM-L6-v2')`.
- `compute_similarity_matrix(embeddings: np.ndarray) -> np.ndarray`: Computes pairwise cosine similarity matrix.
- `auto_link_wiki(similarity_threshold: float = 0.65)`: Updates frontmatter `auto_links` and appends inline Markdown links `[[note_id]]` to related notes.

### Verification Criteria
- 15+ real captured notes in `wiki/` auto-link based on semantic content without manual intervention.
- Bidirectional relationship consistency (if Note A links to Note B, Note B references Note A).
- 🏅 **Badge Achieved**: *The Librarian*

---

## Phase 4: Graph Data Model & Interactive Visualizer (`build_graph.py`) — Milestone: The Cartographer

### Goal
Parse `wiki/` notes and auto-links, transform them into a graph schema (`nodes` and `edges`), export to `graph.json`, and render an interactive force-directed visual graph using PyVis / Vis.js.

### Target Deliverables & Files
- [NEW] `build_graph.py`
- [NEW] `graph.json`

### Key Modules & Functions to Implement
- `generate_graph_data() -> dict`: Parses `wiki/*.md` frontmatter, creating nodes with PARA color-coding and edges with similarity weights. Saves to `graph.json`.
- `create_pyvis_html(graph_data: dict) -> str`: Renders dynamic PyVis HTML string with custom physics, drag, zoom, and hover cards displaying note summaries.

### Node Styling Guidelines
- **Projects**: `#FF6B6B` (Coral)
- **Areas**: `#4D96FF` (Blue)
- **Resources**: `#6BCB77` (Green)
- **Archives**: `#9D9D9D` (Gray)

### Verification Criteria
- `graph.json` contains valid JSON with non-empty `nodes` and `edges` arrays.
- Interactive HTML graph renders in browser with hover tooltips, drag/zoom behavior, and pulse/force physics.
- 🏅 **Badge Achieved**: *The Cartographer*

---

## Phase 5: RAG Q&A Search Engine (`ask.py`)

### Goal
Build a Retrieval-Augmented Generation (RAG) search pipeline (`ask(query)`) that embeds user questions, retrieves top-$k$ relevant notes from `wiki/`, and synthesizes concise answers via Groq LLM with source note citations.

### Target Deliverables & Files
- [NEW] `ask.py`

### Key Modules & Functions to Implement
- `retrieve_context(query: str, top_k: int = 3) -> List[dict]`: Encodes prompt, computes cosine similarity against cached note embeddings, and returns top-$k$ matching notes.
- `ask(query: str) -> dict`: Constructs system context prompt, calls Groq API (`llama-3.1-8b-instant`), and formats final response with source note titles.

### Verification Criteria
- `python ask.py "What notes do I have about Python design patterns?"` returns a synthesized answer referencing captured notes.
- Graceful response when no relevant notes match query threshold.

---

## Phase 6: Unified Streamlit Interface (`app.py`) — Milestone: The Oracle

### Goal
Assemble all components into a polished Streamlit application containing a sidebar capture form, interactive graph tab, ask-anything search bar tab, and note browser tab.

### Target Deliverables & Files
- [NEW] `app.py`
- [NEW] `.streamlit/config.toml`

### Layout Architecture
- **Sidebar**: Text/URL/File Ingestion Form + Pipeline Status Counters.
- **Tab 1: Living Brain**: Full-screen PyVis HTML interactive graph rendered via `st.components.v1.html`.
- **Tab 2: Ask Your Brain**: Search bar + Instant RAG Answer response card + Citation expandable accordions.
- **Tab 3: Wiki Explorer**: Browse organized Markdown notes by PARA category.

### Verification Criteria
- Full pipeline operable inside Streamlit app: Capture $\rightarrow$ Classify $\rightarrow$ Link $\rightarrow$ Graph Update $\rightarrow$ Ask.
- 🏅 **Badge Achieved**: *The Oracle*

---

## Phase 7: Local End-to-End Testing & Validation

### Goal
Stress-test the end-to-end SecondSelf system on 15+ real-world user notes, articles, and documents locally before deployment.

### Tasks
1. Execute full pipeline on diverse inputs (technical notes, bookmark URLs, PDF cheat sheets).
2. Validate auto-classification accuracy across all 4 PARA categories.
3. Check vector auto-linking similarity thresholds to ensure no false auto-link clutter.
4. Verify RAG answer accuracy against known captured content.

### Verification Criteria
- Zero unhandled exceptions during ingestion, classification, linking, graph generation, or RAG search.
- 15+ real notes successfully linked and visualized on the living graph.

---

## Phase 8: Production Cloud Deployment

### Goal
Deploy the completed Streamlit application to Streamlit Community Cloud (or Hugging Face Spaces) with environment secrets configured.

### Deliverables
- Live public URL accessible to anyone without login.
- Configured Streamlit Cloud Secret `GROQ_API_KEY`.

### Tasks
1. Commit and push repository to GitHub (`secondself`).
2. Connect repository to Streamlit Cloud / HF Spaces.
3. Configure `GROQ_API_KEY` in environment secrets management.
4. Verify deployment build log and dependencies installation.

### Verification Criteria
- Public deployment URL renders application cleanly without key leaks or build failures.

---

## Phase 9: Documentation & Final Deliverables

### Goal
Finalize user documentation, README setup instructions, badges checklist, and repository polish.

### Target Deliverables & Files
- [MODIFY] `README.md` (System overview, setup instructions, badge checklist, public URL link)

### Verification Criteria
- Public GitHub repo contains clean README with step-by-step setup guide.
- Live URL tested and functional.
- All 4 Weekly Badges verified complete:
  - [x] 🏅 **The Archivist** (Week 1)
  - [x] 🏅 **The Librarian** (Week 2)
  - [x] 🏅 **The Cartographer** (Week 3)
  - [x] 🏅 **The Oracle** (Week 4)

---

## Summary Matrix of Component Deliverables

| Phase | Core Component | File Target | Primary Metric / Outcome |
| :--- | :--- | :--- | :--- |
| **Phase 0** | Scaffold Setup | `requirements.txt`, `.env.example` | Dependencies installed, dirs ready |
| **Phase 1** | Capture Engine | `capture.py` | 10+ raw captures saved to `raw/` |
| **Phase 2** | Classifier | `classify.py` | Auto-classification into PARA categories |
| **Phase 3** | Auto-Linker | `link.py` | Dense embeddings similarity links in `wiki/` |
| **Phase 4** | Graph Builder | `build_graph.py`, `graph.json` | Dynamic PyVis interactive graph |
| **Phase 5** | RAG Search | `ask.py` | Vector retrieval + LLM synthesis |
| **Phase 6** | Streamlit UI | `app.py` | Unified application interface |
| **Phase 7** | Local Testing | Local System Verification | 15+ real items validated end-to-end |
| **Phase 8** | Public Deployment| Streamlit Cloud / HF Spaces | Live Public URL active |
| **Phase 9** | Final Docs | `README.md` | Complete documentation & badge audit |
