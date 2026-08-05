# SecondSelf — Your Personal AI Second Brain

> Capture anything (notes, links, files), auto-classify with LLMs (PARA method), auto-link related knowledge via dense vector embeddings, visualize your brain as an interactive force-directed graph, and ask natural language questions synthesized directly from your accumulated notes.

---

## 🏅 Weekly Badges & Progress

- [x] 🏅 **The Archivist** (Week 1 / Phase 0 & 1): Capture text, URLs, and files into `raw/` with unique IDs, timestamps, and metadata.
- [x] 🏅 **The Librarian** (Week 2 / Phase 2 & 3): Autonomous PARA LLM classification (`classify.py`) & dense vector auto-linking (`link.py`) into `wiki/`.
- [x] 🏅 **The Cartographer** (Week 3 / Phase 4): Dynamic interactive 2D PyVis & 3D WebGL force-directed graph visualizer (`build_graph.py`, `graph.html`, `graph_3d.html`).
- [x] 🏅 **The Oracle** (Week 4 / Phase 5, 6, 7 & 8): Retrieval-Augmented Generation (RAG) Q&A search bar (`ask.py`), Cyber Obsidian Streamlit UI dashboard (`app.py`), and production cloud deployment readiness.

---

## 📂 Comprehensive File & Directory Explanation

Below is the complete file tree of the repository along with a detailed explanation for **every file and directory**:

```
secondself/
├── .agents/
│   └── AGENTS.md                  # Workspace agent guidelines & git author configuration rules
├── .streamlit/
│   ├── config.toml                # Streamlit theme & UI styling configuration
│   └── secrets.toml.example       # Template for Streamlit Cloud Dashboard secrets
├── docs/
│   ├── Problem_statement.md       # Core problem definition, specifications, and scope
│   ├── architecture.md            # Technical architecture breakdown, data pipelines & schema designs
│   ├── Implementation-plan.md     # 10-Phase step-by-step development roadmap
│   ├── edge-case.md               # Edge-case handling rules (rate limits, fallback classifiers, bad input)
│   └── deployment-guide.md        # Step-by-step production cloud deployment guide
├── raw/                           # Raw ingested payloads (Phase 1)
│   └── <timestamp_id>/
│       ├── content.md             # Extracted raw text or web page body content
│       └── metadata.json          # Ingestion metadata (ID, source, URL, title, tags, timestamp)
├── wiki/                          # Processed PARA knowledge vault (Phase 2 & 3)
│   ├── Projects/                  # Notes with active deadlines and short-term goals
│   ├── Areas/                     # Long-term standards and ongoing responsibilities
│   ├── Resources/                 # Reference topics, interests, and guides
│   └── Archives/                  # Inactive, completed, or archived knowledge items
├── scratch/                       # Verification scripts and sample data utilities
│   ├── verify_phases.py           # Unified automated test suite for all implemented phases (Phases 0-8)
│   └── clean_and_populate_samples.py # Utility to populate clean random test samples (10-25 notes) into raw/ and wiki/
├── app.py                         # Phase 6: Unified Streamlit Web Application Dashboard (Cyber Obsidian theme)
├── capture.py                     # Phase 1: Ingestion pipeline for text inputs, web URLs, and local files
├── classify.py                    # Phase 2: Autonomous PARA classifier using Groq LLM (Llama 3.3 70B)
├── link.py                        # Phase 3: Dense vector embedding & automatic `[[wikilink]]` linker
├── build_graph.py                 # Phase 4: Graph data model, 2D PyVis & 3D WebGL visualizers
├── ask.py                         # Phase 5: RAG Q&A Search Engine using Groq LLM & vector similarity
├── view_embeddings.py             # Vector Inspector: View & inspect dense embeddings in embeddings.npy
├── graph.html                     # 2D Interactive Force-Directed Graph (PyVis/Vis.js)
├── graph_3d.html                  # 3D Interactive Force-Directed Graph (3D-Force-Graph WebGL)
├── graph.json                     # Serialized graph schema (nodes and weighted edges)
├── embeddings.npy                 # Cached dense vector matrix for all wiki notes
├── requirements.txt               # Production dependencies (streamlit, groq, numpy, scikit-learn, requests, pyvis)

├── .env.example                   # Environment variable template (`GROQ_API_KEY`)
├── .gitignore                     # Git ignore rules for virtual environments, secrets, and caches
└── README.md                      # Complete system documentation & usage guide
```

---

## 📄 Detailed File Descriptions

### ⚙️ Core Pipeline Scripts

* **[`app.py`](file:///g:/My%20Drive/AI/app.py)**  
  The main Streamlit web application. Integrates multi-modal capture sidebar, interactive 2D/3D matrix graph visualization tab, RAG search tab, and PARA wiki vault browser tab.

* **[`capture.py`](file:///g:/My%20Drive/AI/capture.py)**  
  Handles Phase 1 ingestion. Accepts raw text strings, web URLs (scrapes HTML title & body text), or local text/markdown/PDF files. Assigns a unique ID (`YYYYMMDD_HHMMSS_<hash>`) and saves both `content.md` and `metadata.json` under `raw/<id>/`.

* **[`classify.py`](file:///g:/My%20Drive/AI/classify.py)**  
  Handles Phase 2 PARA classification. Reads raw payloads from `raw/`, prompts the Groq LLM (`llama-3.3-70b-versatile` with `llama3-8b-8192` fallback) to categorize notes into **Projects**, **Areas**, **Resources**, or **Archives**, generates tags and a clean title, and writes formatted markdown notes into `wiki/<Category>/`. Supports `st.secrets["GROQ_API_KEY"]` for cloud deployment.

* **[`link.py`](file:///g:/My%20Drive/AI/link.py)**  
  Handles Phase 3 vector auto-linking. Extracts content from all notes in `wiki/`, builds dense embeddings / TF-IDF fallback vectors (persisted in `embeddings.npy`), computes cosine similarity between notes, and injects a `## Related Notes` section with double-bracket `[[wikilinks]]` into matching files.

* **[`build_graph.py`](file:///g:/My%20Drive/AI/build_graph.py)**  
  Handles Phase 4 graph generation. Parses `wiki/` notes and frontmatter metadata, constructs node-edge graph schemas exported to `graph.json`, and generates both 2D PyVis (`graph.html`) and 3D WebGL (`graph_3d.html`) force-directed graph visualizers.

* **[`ask.py`](file:///g:/My%20Drive/AI/ask.py)**  
  Handles Phase 5 RAG search engine. Encodes user search query, retrieves top-$k$ relevant context notes via vector similarity or TF-IDF, and synthesizes cited answers using Groq LLM. Supports `st.secrets["GROQ_API_KEY"]` for cloud deployment.

---

### 🧪 Verification & Utility Scripts (`scratch/`)

* **[`scratch/verify_phases.py`](file:///g:/My%20Drive/AI/scratch/verify_phases.py)**  
  The primary unified test runner for the project. Verifies directory structures (Phase 0), raw ingestion (Phase 1), LLM classification (Phase 2), vector auto-linking (Phase 3), graph visualization (Phase 4), RAG search (Phase 5), Streamlit UI (Phase 6), E2E local testing (Phase 7), and cloud readiness (Phase 8) end-to-end.

* **[`scratch/clean_and_populate_samples.py`](file:///g:/My%20Drive/AI/scratch/clean_and_populate_samples.py)**  
  A utility script that resets existing test notes and populates `raw/` and `wiki/` with clean, diverse example notes (10-25 random notes) spanning all four PARA categories.

---

### 📚 Documentation (`docs/`)

* **[`docs/Problem_statement.md`](file:///g:/My%20Drive/AI/docs/Problem_statement.md)**  
  Outlines the core mission of SecondSelf: solving personal information overload by transforming scattered notes into an organized, queryable second brain.

* **[`docs/architecture.md`](file:///g:/My%20Drive/AI/docs/architecture.md)**  
  Detailed system design specification covering data schemas, directory layout, LLM prompt templates, embedding strategies, and graph visualization plans.

* **[`docs/Implementation-plan.md`](file:///g:/My%20Drive/AI/docs/Implementation-plan.md)**  
  Phase-by-phase implementation blueprint tracking progress across Ingestion (P1), Classification (P2), Auto-linking (P3), Graphing (P4), RAG Q&A (P5), App UI (P6), E2E Testing (P7), Cloud Deployment (P8), and Final Deliverables (P9).

* **[`docs/deployment-guide.md`](file:///g:/My%20Drive/AI/docs/deployment-guide.md)**  
  Step-by-step production cloud deployment guide for Streamlit Community Cloud and Hugging Face Spaces.

* **[`docs/edge-case.md`](file:///g:/My%20Drive/AI/docs/edge-case.md)**  
  Documents edge-case strategies: handling empty files, missing API keys, LLM rate limits, network timeouts, duplicate URL ingestions, and vector indexing cold-starts.

---

### 🔧 Configurations & Setup Files

* **[`requirements.txt`](file:///g:/My%20Drive/AI/requirements.txt)**  
  Defines all required Python libraries: `groq`, `numpy`, `scikit-learn`, `requests`, `beautifulsoup4`, and `python-dotenv`.

* **[`.env.example`](file:///g:/My%20Drive/AI/.env.example)**  
  Template for environment variables. Rename to `.env` and configure `GROQ_API_KEY`.

* **[`.gitignore`](file:///g:/My%20Drive/AI/.gitignore)**  
  Prevents check-in of temporary files, `.env` API keys, `.venv` virtual environments, python bytecode caches, and vector index artifacts (`embeddings.npy`).

* **[`.agents/AGENTS.md`](file:///g:/My%20Drive/AI/.agents/AGENTS.md)**  
  Custom workspace configuration defining project rules, including git author settings (`jyeshtapshetty@gmail.com`).

---

## 🚀 Quickstart & Usage

### 1. Installation Setup
```bash
# Clone the repository
git clone https://github.com/NTRslayer123/second-brain.git
cd second-brain

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Groq API Key
Copy `.env.example` to `.env` and set your API key:
```bash
cp .env.example .env
```
Edit `.env`:
```env
GROQ_API_KEY=your_groq_api_key_here
```

### 3. Run Verification Suite
Run the unified test suite to verify Phases 0–3:
```bash
python scratch/verify_phases.py
```

---

## 📄 License
[MIT License](LICENSE)
