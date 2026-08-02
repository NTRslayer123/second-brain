#!/usr/bin/env python3
"""
SecondSelf — Personal AI Knowledge Matrix & Neural Vault (app.py)
Polished, cyber-obsidian interactive web interface featuring multi-modal ingestion,
living graph matrix visualizer, RAG Q&A synthesis engine, and PARA vault explorer.
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
GRAPH_3D_HTML_PATH = BASE_DIR / "graph_3d.html"
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
    page_title="SecondSelf • Neural Knowledge Matrix",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# CYBER OBSIDIAN & AURORA DESIGN SYSTEM (CSS)
# ==========================================
CYBER_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, sans-serif !important;
    }

    /* Main App Background Gradient */
    .stApp {
        background: #090D16;
        background-image: 
            radial-gradient(circle at 10% 20%, rgba(16, 185, 129, 0.05) 0%, transparent 40%),
            radial-gradient(circle at 90% 80%, rgba(6, 182, 212, 0.05) 0%, transparent 40%);
        color: #F3F4F6;
    }

    /* Sidebar Background */
    section[data-testid="stSidebar"] {
        background-color: #0E1524 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }

    /* Hero Header Banner */
    .hero-banner {
        background: linear-gradient(135deg, rgba(19, 28, 46, 0.9), rgba(9, 13, 22, 0.95));
        border: 1px solid rgba(16, 185, 129, 0.25);
        border-radius: 16px;
        padding: 24px 30px;
        margin-bottom: 24px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.6);
    }

    .matrix-title {
        font-size: 28px;
        font-weight: 800;
        letter-spacing: -0.5px;
        background: linear-gradient(135deg, #10B981, #06B6D4, #F59E0B);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: inline-block;
    }

    .matrix-badge {
        background: linear-gradient(135deg, #10B981, #06B6D4);
        color: #090D16;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Status Pill */
    .status-pill {
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 12px;
        color: #6EE7B7;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 8px;
    }

    .pulse-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #10B981;
        box-shadow: 0 0 10px #10B981;
        display: inline-block;
    }

    /* Metric Cards Override */
    div[data-testid="stMetric"] {
        background: rgba(19, 28, 46, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 14px 18px;
        backdrop-filter: blur(10px);
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 800 !important;
        color: #10B981 !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #94A3B8 !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
    }

    /* RAG Response Box */
    .rag-box {
        background: rgba(19, 28, 46, 0.85);
        border-left: 4px solid #10B981;
        border-top: 1px solid rgba(255, 255, 255, 0.08);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 0 12px 12px 0;
        padding: 20px;
        margin-top: 16px;
        margin-bottom: 24px;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
    }

    /* Citation Card */
    .citation-card {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 10px;
    }

    /* Tab Button Styles */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: rgba(19, 28, 46, 0.5);
        border-radius: 10px 10px 0 0;
        padding: 10px 20px;
        color: #94A3B8;
        font-weight: 600;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }

    .stTabs [aria-selected="true"] {
        background-color: #131C2E !important;
        color: #10B981 !important;
        border-top: 2px solid #10B981 !important;
    }
</style>
"""
st.markdown(CYBER_CSS, unsafe_allow_html=True)


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
    st.markdown("## 🧠 SecondSelf")
    st.markdown("<span class='matrix-badge'>Phase 6 • Milestone: The Oracle</span>", unsafe_allow_html=True)
    st.caption("Autonomous Knowledge Matrix Engine")
    st.divider()

    st.markdown("### 📥 Ingestion Hub")
    ingest_type = st.radio("Select Ingestion Mode", ["Text Note", "Web Link", "Local Document"], index=0)

    if ingest_type == "Text Note":
        input_text = st.text_area("Content Payload", placeholder="Type ideas, meeting notes, code snippets...", height=120)
        cap_type = "note"
    elif ingest_type == "Web Link":
        input_text = st.text_input("URL Target", placeholder="https://example.com/article")
        cap_type = "link"
    else:
        uploaded_file = st.file_uploader("Upload File (All Formats Allowed)", type=None)
        input_text = ""
        cap_type = "file"
        if uploaded_file:
            temp_path = BASE_DIR / f"scratch/temp_{uploaded_file.name}"
            temp_path.write_bytes(uploaded_file.getbuffer())
            input_text = str(temp_path)

    if st.button("🚀 Ingest & Matrix Link", use_container_width=True, type="primary"):
        if not input_text:
            st.warning("Please provide content, URL, or upload a file.")
        else:
            with st.spinner("Classifying payload & auto-linking vector mesh..."):
                cap_res = capture.capture(input_text, cap_type)
                raw_path = RAW_DIR / cap_res["id"]
                classify.process_raw_to_wiki(raw_path)
                link.auto_link_wiki()
                build_graph.generate_graph_data()
                st.success(f"Ingested & Vector-Linked ID: `{cap_res['id']}`!")
                st.rerun()

    st.divider()

    # Vault Metrics
    metrics = get_vault_metrics()
    st.markdown("### 📊 Vault Intelligence")
    col_m1, col_m2 = st.columns(2)
    col_m1.metric("Total Notes", metrics["Total"])
    col_m2.metric("Connections", metrics["Edges"])

    st.markdown(f"• **Projects**: {metrics['Projects']} 🟠 | **Areas**: {metrics['Areas']} 🔵")
    st.markdown(f"• **Resources**: {metrics['Resources']} 🟢 | **Archives**: {metrics['Archives']} ⚪")

    st.divider()

    st.markdown("### ⚡ Matrix Operations")
    if st.button("🔄 Refresh Graph & Links", use_container_width=True):
        with st.spinner("Re-computing vector similarity matrix..."):
            link.auto_link_wiki()
            build_graph.generate_graph_data()
            st.success("Graph matrix refreshed successfully!")
            st.rerun()

    if st.button("🎲 Seed Sample Knowledge (25+ Notes)", use_container_width=True):
        with st.spinner("Seeding sample knowledge vault..."):
            clean_samples.main()
            link.auto_link_wiki()
            build_graph.generate_graph_data()
            st.success("Sample vault populated & graph rendered!")
            st.rerun()


# ==========================================
# MAIN HERO HEADER
# ==========================================
st.markdown("""
<div class="hero-banner">
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 16px;">
        <div>
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 6px;">
                <span style="font-size: 32px;">🧠</span>
                <span class="matrix-title">SECONDSELF AI</span>
                <span class="matrix-badge">v2.0 • Neural Matrix</span>
            </div>
            <div style="color: #94A3B8; font-size: 14px; font-weight: 500;">
                Autonomous Knowledge Engine • Dense Vector Auto-Linking • RAG Oracle Synthesis
            </div>
        </div>
        <div style="display: flex; gap: 12px;">
            <div class="status-pill">
                <span class="pulse-dot"></span>
                <span>Brain Mesh Active</span>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ==========================================
# MAIN DASHBOARD TABS
# ==========================================
tab1, tab2, tab3 = st.tabs([
    "🌌 Neural Knowledge Matrix",
    "⚡ Oracle RAG Console",
    "🗂️ Knowledge Vault Atlas"
])


# ------------------------------------------
# TAB 1: NEURAL KNOWLEDGE MATRIX (GRAPH)
# ------------------------------------------
with tab1:
    st.markdown("### 🌌 Interactive Knowledge Matrix")
    st.caption("Force-directed vector similarity graph color-coded by PARA categories. Switch between 2D and 3D WebGL render modes.")

    col_g1, col_g2 = st.columns([2, 3])
    with col_g1:
        dimension_mode = st.radio("Graph View Mode", ["2D Force Graph", "3D WebGL Matrix Graph"], horizontal=True, key="graph_dim_mode")

    focused_id = ""
    if GRAPH_JSON_PATH.exists():
        try:
            gdata = json.loads(GRAPH_JSON_PATH.read_text(encoding="utf-8"))
            node_map = {f"[{n.get('category', 'Note')}] {n['label']}": n["id"] for n in gdata.get("nodes", [])}
            selected_label = st.selectbox(
                "🎯 Jump & Focus Node in Graph",
                ["-- Select a note to auto-zoom & focus node --"] + sorted(list(node_map.keys())),
                key="graph_focus_selector"
            )
            focused_id = node_map.get(selected_label, "")
        except Exception:
            focused_id = ""

    target_html_path = GRAPH_3D_HTML_PATH if dimension_mode == "3D WebGL Matrix Graph" else GRAPH_HTML_PATH

    if target_html_path.exists():
        html_content = target_html_path.read_text(encoding="utf-8")
        if focused_id:
            if dimension_mode == "2D Force Graph":
                focus_js = f"""
                <script>
                  window.addEventListener('load', function() {{
                    const checkNet = setInterval(function() {{
                      if (typeof network !== 'undefined' && network) {{
                        clearInterval(checkNet);
                        network.focus("{focused_id}", {{ scale: 1.8, animation: {{ duration: 1000, easingFunction: "easeInOutQuad" }} }});
                        network.selectNodes(["{focused_id}"]);
                      }}
                    }}, 100);
                  }});
                </script>
                """
            else:
                focus_js = f"""
                <script>
                  window.addEventListener('load', function() {{
                    const check3D = setInterval(function() {{
                      if (typeof Graph3D !== 'undefined' && Graph3D) {{
                        clearInterval(check3D);
                        const gData = Graph3D.graphData();
                        const targetNode = gData.nodes.find(n => n.id === "{focused_id}");
                        if (targetNode) {{
                          const distRatio = 1 + 140 / Math.hypot(targetNode.x || 1, targetNode.y || 1, targetNode.z || 1);
                          Graph3D.cameraPosition(
                            {{ x: (targetNode.x || 0) * distRatio, y: (targetNode.y || 0) * distRatio, z: (targetNode.z || 0) * distRatio }},
                            targetNode,
                            1200
                          );
                        }}
                      }}
                    }}, 150);
                  }});
                </script>
                """
            html_content = html_content.replace("</body>", f"{focus_js}\n</body>")
        components.html(html_content, height=900, scrolling=True)
    else:
        st.info("Graph visualizer not built yet. Click 'Refresh Graph & Links' in sidebar to build!")


# ------------------------------------------
# TAB 2: ORACLE RAG CONSOLE
# ------------------------------------------
with tab2:
    st.markdown("### ⚡ Oracle RAG Q&A Engine")
    st.caption("Query your knowledge vault in natural language with dense vector retrieval and AI synthesis.")

    query_input = st.text_input(
        "Ask a question across your Second Brain:",
        placeholder="e.g. What notes do I have about Python microservices and vector embeddings?",
        key="rag_search_input"
    )

    col_q1, col_q2 = st.columns([1, 4])
    with col_q1:
        search_clicked = st.button("⚡ Synthesize Answer", type="primary")

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
        with st.spinner("Retrieving vector embeddings & synthesizing answer via Groq LLM..."):
            rag_res = ask.ask(query_input)

            confidence_pct = int(rag_res["confidence"] * 100)
            
            st.markdown(f"""
            <div class="rag-box">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                    <div style="font-weight: 700; color: #10B981; font-size: 16px; display: flex; align-items: center; gap: 8px;">
                        <span>🤖</span> AI Synthesized Answer
                    </div>
                    <div style="font-size: 12px; color: #94A3B8;">
                        Confidence Score: <strong style="color: #10B981;">{confidence_pct}%</strong> | Notes Retrieved: <strong>{rag_res['retrieved_count']}</strong>
                    </div>
                </div>
                <div style="color: #F3F4F6; line-height: 1.7; font-size: 15px;">
                    {rag_res['answer']}
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("#### 📚 Source Note Citations")
            if rag_res["sources"]:
                for src in rag_res["sources"]:
                    sim_pct = int(src["similarity"] * 100)
                    with st.expander(f"• [{src['category']}] {src['title']} — Match: {sim_pct}%"):
                        st.markdown(f"**Category**: `{src['category']}` | **Note ID**: `{src['id']}`")
                        st.markdown(f"**File Location**: `{src['file_path']}`")
            else:
                st.caption("No matching source notes retrieved for this query topic.")


# ------------------------------------------
# TAB 3: KNOWLEDGE VAULT ATLAS
# ------------------------------------------
with tab3:
    st.markdown("### 🗂️ Knowledge Vault Atlas")
    st.caption("Browse and inspect organized Markdown notes across PARA categories.")

    notes_pool = link.load_wiki_notes()

    if not notes_pool:
        st.info("No wiki notes found in vault. Capture notes or click 'Seed Sample Knowledge' in sidebar!")
    else:
        cat_filter = st.radio("Filter Category", ["All", "Projects", "Areas", "Resources", "Archives"], horizontal=True)

        if cat_filter != "All":
            filtered_notes = [n for n in notes_pool if n.get("category") == cat_filter]
        else:
            filtered_notes = notes_pool

        st.caption(f"Displaying {len(filtered_notes)} notes")

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
                st.divider()
                st.markdown("#### Document Body")
                st.markdown(selected_note['body'])

            with col_n2:
                st.markdown("#### 🔗 Auto-Linked Connections")
                auto_links = selected_note.get("auto_links", [])
                if auto_links:
                    for al in auto_links:
                        sim_pct = int(al.get("similarity", 0) * 100)
                        st.markdown(f"• **[[{al.get('title')}]]** ({sim_pct}% match)")
                else:
                    st.caption("No auto-links discovered for this note.")

                st.divider()
                st.markdown("#### 📌 Summary")
                st.info(selected_note.get("summary", "No summary available."))
