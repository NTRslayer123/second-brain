# SecondSelf — Your Personal AI Second Brain

> Capture anything (notes, links, files), auto-classify with LLMs (PARA method), auto-link related knowledge via dense vector embeddings, visualize your brain as an interactive force-directed graph, and ask natural language questions synthesized directly from your accumulated notes.

---

## 🏅 Weekly Badges & Progress

- [ ] 🏅 **The Archivist** (Week 1): Capture notes, URLs, and files into `raw/` with unique IDs & timestamps.
- [ ] 🏅 **The Librarian** (Week 2): Autonomous PARA LLM classification & dense vector auto-linking into `wiki/`.
- [ ] 🏅 **The Cartographer** (Week 3): Dynamic interactive force-directed graph visualizer.
- [ ] 🏅 **The Oracle** (Week 4): Retrieval-Augmented Generation (RAG) Q&A search bar & public cloud deployment.

---

## 🛠️ Repository Architecture

```
secondself/
├── raw/                      # Raw ingested payloads (Week 1)
├── wiki/                     # Auto-classified & linked Markdown notes (Week 2)
├── docs/                     # Project specifications & plans
│   ├── Problem_statement.md
│   ├── architecture.md
│   ├── Implementation-plan.md
│   └── edge-case.md
├── capture.py                # Ingestion pipeline script (Phase 1)
├── classify.py               # PARA LLM classification pipeline (Phase 2)
├── link.py                   # Vector embedding & auto-linking engine (Phase 3)
├── build_graph.py            # Graph JSON & PyVis visualizer (Phase 4)
├── ask.py                    # RAG retrieval & QA synthesis (Phase 5)
├── app.py                    # Streamlit unified application (Phase 6)
├── requirements.txt          # Production dependencies
├── .env.example              # Environment variables template
└── README.md                 # System setup & guide
```

---

## 🚀 Quickstart & Installation Setup

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/your-username/secondself.git
cd secondself
python -m venv .venv
# Activate virtual environment:
# On Windows: .venv\Scripts\activate
# On macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and add your free Groq API key:
```bash
cp .env.example .env
```
Edit `.env`:
```env
GROQ_API_KEY=your_actual_groq_api_key
```

---

## 📄 License
MIT License
