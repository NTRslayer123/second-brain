#!/usr/bin/env python3
"""
SecondSelf — Unified Streamlit Interface (app.py) — Milestone: The Oracle
Polished interactive web interface combining multi-modal capture, living graph visualizer,
RAG Q&A search engine, and PARA wiki note explorer.
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import streamlit as st
import streamlit.components.v1 as components

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).parent.resolve()
RAW_DIR = BASE_DIR / "raw"
WIKI_DIR = BASE_DIR / "wiki"
GRAPH_HTML_PATH = BASE_DIR / "graph.html"
GRAPH_JSON_PATH = BASE_DIR / "graph.json"

# Import system modules
import capture
import classify
import link
import build_graph
import ask
import scratch.clean_and_populate_samples as clean_samples


# ==========================================
# STREAMLIT PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="SecondSelf — Personal AI Second Brain",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Glassmorphic CSS Styling
CUSTOM_CSS = """
<style>
    /* Dark Theme Customizations */
    .stApp {
        background-color: #0F172A;
        color: #F8FAFC;
    }
    .css-1d37w0e {
        background-color: #1E293B;
    }
    /* Metric Cards */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #38BDF8 !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #94A3B8 !important;
    }
    /* Cards Container */
    .glass-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .oracle-badge {
        background: linear-gradient(135deg, #3B82F6, #8B5CF6);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .citation-box {
        border-left: 3px solid #3B82F6;
        background-color: #1E293B;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 12px;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ==========================================
# HELPER FUNCTIONS
# ==========================================
def get_vault_metrics() -> dict:
    """Computes real-time note and connection counts across vault."""
    notes = link.load_wiki_notes()
    counts = {"Total": len(notes), "Projects": 0, "Areas": 0, "Resources": 0, "Archives": 0}
    for n in notes:
        cat = n.get("category", "Resources")
        if cat in counts:
            counts[cat] += 1

    edges_count = 0
    if GRAPH_JSON_PATH.exists():
        try:
            gdata = json.loads(GRAPH_JSON_PATH.read_text(encoding="utf-8"))
            edges_count = len(gdata.get("edges", []))
        except Exception:
            pass

    counts["Edges"] = edges_count
    return counts


# ==========================================
# SIDEBAR INGESTION & PIPELINE CONTROL
# ==========================================
with st.sidebar:
    st.markdown("## 🧠 SecondSelf AI")
    st.markdown("<span class='oracle-badge'>Phase 6 • Milestone: The Oracle</span>", unsafe_allow_html=True)
    st.caption("Autonomous Personal Knowledge Management System")
    st.divider()

    st.markdown("### 📥 Quick Capture Engine")
    ingest_type = st.radio("Capture Type", ["Text Note", "Web URL / Link", "Local File"], index=0)

    if ingest_type == "Text Note":
        input_text = st.text_area("Note Content", placeholder="Enter notes, ideas, code snippets...", height=120)
        source_val = "Streamlit UI Note"
        cap_type = "note"
    elif ingest_type == "Web URL / Link":
        input_text = st.text_input("URL Link", placeholder="https://example.com/article")
        source_val = input_text
        cap_type = "link"
    else:
        uploaded_file = st.file_uploader("Upload Document", type=["txt", "md", "pdf"])
        input_text = ""
        source_val = uploaded_file.name if uploaded_file else ""
        cap_type = "file"
        if uploaded_file:
            # Save temporary file to temp location
            temp_path = BASE_DIR / f"scratch/temp_{uploaded_file.name}"
            temp_path.write_bytes(uploaded_file.getbuffer())
            input_text = str(temp_path)

    if st.button("🚀 Ingest Note", use_container_width=True, type="primary"):
        if not input_text:
            st.warning("Please provide note content, URL, or upload a file.")
        else:
            with st.spinner("Ingesting, classifying, and auto-linking note..."):
                # 1. Capture
                cap_res = capture.capture(input_text, cap_type, source_val)
                raw_path = RAW_DIR / cap_res["id"]
                # 2. Classify
                classify.process_raw_to_wiki(raw_path)
                # 3. Auto-link
                link.auto_link_wiki()
                # 4. Update Graph
                build_graph.generate_graph_data()
                st.success(f"Captured & Classified ID: `{cap_res['id']}`!")
                st.rerun()

    st.divider()

    # Vault Metrics
    metrics = get_vault_metrics()
    st.markdown("### 📊 Vault Status")
    col_m1, col_m2 = st.columns(2)
    col_m1.metric("Total Notes", metrics["Total"])
    col_m2.metric("Connections", metrics["Edges"])

    st.markdown(f"• **Projects**: {metrics['Projects']} | **Areas**: {metrics['Areas']}")
    st.markdown(f"• **Resources**: {metrics['Resources']} | **Archives**: {metrics['Archives']}")

    st.divider()

    st.markdown("### ⚡ Vault Actions")
    if st.button("🔄 Re-link & Update Graph", use_container_width=True):
        with st.spinner("Re-computing vector similarity auto-links..."):
            link.auto_link_wiki()
            build_graph.generate_graph_data()
            st.success("Vault auto-links and graph visualizer refreshed!")
            st.rerun()

    if st.button("🎲 Populate Sample Vault (25-100 Notes)", use_container_width=True):
        with st.spinner("Populating local sample notes..."):
            clean_samples.main()
            link.auto_link_wiki()
            build_graph.generate_graph_data()
            st.success("Sample vault populated & graph rendered!")
            st.rerun()


# ==========================================
# MAIN DASHBOARD TABS
# ==========================================
st.title("🧠 SecondSelf — Personal Knowledge System")
st.caption("Interactive Force-Directed Graph • RAG Q&A Engine • PARA Knowledge Vault")

tab1, tab2, tab3 = st.tabs(["🌐 Living Brain (Graph)", "💬 Ask Your Brain (RAG)", "📁 Wiki Vault Explorer"])


# ------------------------------------------
# TAB 1: LIVING BRAIN (GRAPH VISUALIZER)
# ------------------------------------------
with tab1:
    st.markdown("### 🌐 Living Knowledge Graph")
    st.caption("Interactive force-directed graph color-coded by PARA categories. Drag nodes or scroll to zoom.")

    if GRAPH_HTML_PATH.exists():
        html_content = GRAPH_HTML_PATH.read_text(encoding="utf-8")
        components.html(html_content, height=720, scrolling=True)
    else:
        st.info("Graph visualizer not built yet. Click 'Re-link & Update Graph' in sidebar to build!")


# ------------------------------------------
# TAB 2: ASK YOUR BRAIN (RAG Q&A ENGINE)
# ------------------------------------------
with tab2:
    st.markdown("### 💬 Ask Your Brain (RAG Search Engine)")
    st.caption("Ask natural language questions across your captured notes, links, and documents.")

    query_input = st.text_input("Ask a question:", placeholder="e.g. What notes do I have about Python microservices and vector embeddings?", key="rag_search_input")

    col_q1, col_q2, col_q3 = st.columns([1, 1, 4])
    with col_q1:
        search_clicked = st.button("🔍 Ask Oracle", type="primary")

    # Quick question chips
    st.markdown("**Suggested Queries:**")
    chip1, chip2, chip3 = st.columns(3)
    if chip1.button("📌 Python Microservices & Embeddings"):
        st.session_state["rag_search_input"] = "What notes do I have about Python microservices and vector embeddings?"
        st.rerun()
    if chip2.button("📌 System Architecture & RAG"):
        st.session_state["rag_search_input"] = "What architecture notes do I have about RAG pipelines?"
        st.rerun()
    if chip3.button("📌 Finance & Investment Strategy"):
        st.session_state["rag_search_input"] = "What notes do I have on financial index fund portfolio strategy?"
        st.rerun()

    if search_clicked and query_input:
        with st.spinner("Retrieving relevant notes & synthesizing response..."):
            rag_res = ask.ask(query_input)

            st.markdown("#### 🤖 AI Synthesized Answer")
            confidence_pct = int(rag_res["confidence"] * 100)
            st.info(f"**Confidence**: {confidence_pct}% | **Notes Retrieved**: {rag_res['retrieved_count']}")

            st.markdown(f"> {rag_res['answer']}")

            st.markdown("#### 📚 Source Note Citations")
            if rag_res["sources"]:
                for src in rag_res["sources"]:
                    sim_pct = int(src["similarity"] * 100)
                    with st.expander(f"• [{src['category']}] {src['title']} (Similarity: {sim_pct}%)"):
                        st.markdown(f"**Category**: `{src['category']}` | **Note ID**: `{src['id']}`")
                        st.markdown(f"**File Path**: `{src['file_path']}`")
            else:
                st.caption("No matching source notes retrieved for this query.")


# ------------------------------------------
# TAB 3: WIKI VAULT EXPLORER
# ------------------------------------------
with tab3:
    st.markdown("### 📁 Wiki Vault Explorer")
    st.caption("Browse organized Markdown notes across PARA categories.")

    notes_pool = link.load_wiki_notes()

    if not notes_pool:
        st.info("No wiki notes found in vault. Capture notes or click 'Populate Sample Vault' in sidebar!")
    else:
        cat_filter = st.radio("Filter by Category", ["All", "Projects", "Areas", "Resources", "Archives"], horizontal=True)

        if cat_filter != "All":
            filtered_notes = [n for n in notes_pool if n.get("category") == cat_filter]
        else:
            filtered_notes = notes_pool

        st.caption(f"Showing {len(filtered_notes)} notes")

        if filtered_notes:
            note_options = {f"[{n['category']}] {n['title']} ({n['id']})": n for n in filtered_notes}
            selected_title = st.selectbox("Select Note to Inspect", list(note_options.keys()))

            selected_note = note_options[selected_title]

            col_n1, col_n2 = st.columns([2, 1])
            with col_n1:
                st.markdown(f"### {selected_note['title']}")
                st.markdown(f"**Category**: `{selected_note['category']}` | **ID**: `{selected_note['id']}`")
                tags_formatted = " ".join([f"`#{t}`" for t in selected_note['tags']]) if selected_note['tags'] else "None"
                st.markdown(f"**Tags**: {tags_formatted}")
                st.markdown(f"**Created**: `{selected_note.get('created_at', 'N/A')}`")
                st.divider()
                st.markdown("#### Content Body")
                st.markdown(selected_note['body'])

            with col_n2:
                st.markdown("#### 🔗 Dense Auto-Links")
                auto_links = selected_note.get("auto_links", [])
                if auto_links:
                    for al in auto_links:
                        sim_pct = int(al.get("similarity", 0) * 100)
                        st.markdown(f"• **[[{al.get('title')}]]** ({sim_pct}% similarity)")
                else:
                    st.caption("No auto-links discovered for this note.")

                st.divider()
                st.markdown("#### 📌 Summary")
                st.info(selected_note.get("summary", "No summary available."))
