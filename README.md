# SecondSelf — Your Personal AI Second Brain

> Capture anything (notes, links, files), auto-classify with LLMs (PARA method), auto-link related knowledge via dense vector embeddings, visualize your brain as an interactive force-directed graph, and ask natural language questions synthesized directly from your accumulated notes.

---

## 🏅 Weekly Badges & Progress

- [x] 🏅 **The Archivist** (Week 1 / Phase 0 & 1): Capture text, URLs, and files into `raw/` with unique IDs, timestamps, and metadata.
- [x] 🏅 **The Librarian** (Week 2 / Phase 2 & 3): Autonomous PARA LLM classification (`classify.py`) & dense vector auto-linking (`link.py`) into `wiki/`.
- [ ] 🏅 **The Cartographer** (Week 3 / Phase 4): Dynamic interactive force-directed graph visualizer.
- [ ] 🏅 **The Oracle** (Week 4 / Phase 5 & 6): Retrieval-Augmented Generation (RAG) Q&A search bar & public cloud deployment.

---

## 📂 Comprehensive File & Directory Explanation

Below is the complete file tree of the repository along with a detailed explanation for **every file and directory**:

```
secondself/
├── .agents/
│   └── AGENTS.md                  # Workspace agent guidelines & git author configuration rules
├── docs/
│   ├── Problem_statement.md       # Core problem definition, specifications, and scope
│   ├── architecture.md            # Technical architecture breakdown, data pipelines & schema designs
│   ├── Implementation-plan.md     # 6-Phase step-by-step development roadmap
│   └── edge-case.md               # Edge-case handling rules (rate limits, fallback classifiers, bad input)
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
│   ├── verify_phases.py           # Unified automated test suite for Phases 0, 1, 2, and 3
│   ├── verify_phase3.py           # Focused test suite for vector embedding & wikilink generation
│   └── clean_and_populate_samples.py # Utility to populate clean test samples into raw/ and wiki/
├── capture.py                     # Phase 1: Ingestion pipeline for text inputs, web URLs, and local files
├── classify.py                    # Phase 2: Autonomous PARA classifier using Groq LLM (Llama 3.3 70B)
├── link.py                        # Phase 3: Dense vector embedding & automatic `[[wikilink]]` linker
├── requirements.txt               # Production dependencies (groq, numpy, scikit-learn, requests, bs4)
├── .env.example                   # Environment variable template (`GROQ_API_KEY`)
├── .gitignore                     # Git ignore rules for virtual environments, secrets, and caches
└── README.md                      # Complete system documentation & usage guide
```

---

## 📄 Detailed File Descriptions

### ⚙️ Core Pipeline Scripts

* **[`capture.py`](file:///g:/My%20Drive/AI/capture.py)**  
  Handles Phase 1 ingestion. Accepts raw text strings, web URLs (scrapes HTML title & body text), or local text/markdown files. Assigns a unique ID (`YYYYMMDD_HHMMSS_<hash>`) and saves both `content.md` and `metadata.json` under `raw/<id>/`.

* **[`classify.py`](file:///g:/My%20Drive/AI/classify.py)**  
  Handles Phase 2 PARA classification. Reads raw payloads from `raw/`, prompts the Groq LLM (`llama-3.3-70b-versatile` with `llama3-8b-8192` fallback) to categorize notes into **Projects**, **Areas**, **Resources**, or **Archives**, generates tags and a clean title, and writes formatted markdown notes into `wiki/<Category>/`.

* **[`link.py`](file:///g:/My%20Drive/AI/link.py)**  
  Handles Phase 3 vector auto-linking. Extracts content from all notes in `wiki/`, builds TF-IDF / dense vector embeddings (persisted in `embeddings.npy`), computes cosine similarity between notes, and injects a `## Related Notes` section with double-bracket `[[wikilinks]]` into matching files.

---

### 🧪 Verification & Utility Scripts (`scratch/`)

* **[`scratch/verify_phases.py`](file:///g:/My%20Drive/AI/scratch/verify_phases.py)**  
  The primary test runner for the project. Verifies directory structures (Phase 0), raw ingestion (Phase 1), LLM classification (Phase 2), and vector auto-linking (Phase 3) end-to-end.

* **[`scratch/verify_phase3.py`](file:///g:/My%20Drive/AI/scratch/verify_phase3.py)**  
  Targeted test script focused specifically on validating vector embedding matrix construction, similarity calculations, and `[[wikilink]]` insertion in `link.py`.

* **[`scratch/clean_and_populate_samples.py`](file:///g:/My%20Drive/AI/scratch/clean_and_populate_samples.py)**  
  A utility script that resets existing test notes and populates `raw/` and `wiki/` with clean, diverse example notes spanning all four PARA categories for testing.

---

### 📚 Documentation (`docs/`)

* **[`docs/Problem_statement.md`](file:///g:/My%20Drive/AI/docs/Problem_statement.md)**  
  Outlines the core mission of SecondSelf: solving personal information overload by transforming scattered notes into an organized, queryable second brain.

* **[`docs/architecture.md`](file:///g:/My%20Drive/AI/docs/architecture.md)**  
  Detailed system design specification covering data schemas, directory layout, LLM prompt templates, embedding strategies, and graph visualization plans.

* **[`docs/Implementation-plan.md`](file:///g:/My%20Drive/AI/docs/Implementation-plan.md)**  
  Phase-by-phase implementation blueprint tracking progress across Ingestion (P1), Classification (P2), Auto-linking (P3), Graphing (P4), RAG Q&A (P5), and App UI (P6).

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
