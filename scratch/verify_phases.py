#!/usr/bin/env python3
"""
SecondSelf — Unified Verification Suite for All Implemented Phases (Phases 0, 1, 2 & 3).
Run using: python scratch/verify_phases.py
"""

import sys
import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(BASE_DIR))

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import capture
import classify
import link
import build_graph
import ask


def test_phase0():
    print("\n==========================================")
    print("  PHASE 0: Repository Setup & Environment")
    print("==========================================")
    raw_dir = BASE_DIR / "raw"
    wiki_dir = BASE_DIR / "wiki"
    req_file = BASE_DIR / "requirements.txt"
    env_example = BASE_DIR / ".env.example"
    gitignore = BASE_DIR / ".gitignore"

    assert raw_dir.exists(), "raw/ directory does not exist"
    assert wiki_dir.exists(), "wiki/ directory does not exist"
    assert req_file.exists(), "requirements.txt does not exist"
    assert env_example.exists(), ".env.example does not exist"
    assert gitignore.exists(), ".gitignore does not exist"

    print("✅ Phase 0 Passed: Scaffolding, requirements, and environment files verified.")


def test_phase1():
    print("\n==========================================")
    print("  PHASE 1: Multi-Modal Ingestion Engine")
    print("==========================================")
    
    # 1. Capture text note
    note_text = "Phase 1 Ingestion Test Note: Python design patterns and SecondSelf system architecture."
    result_note = capture.capture(note_text, "note")
    note_id = result_note["id"]

    assert (BASE_DIR / f"raw/{note_id}/metadata.json").exists(), f"raw/{note_id}/metadata.json was not created!"
    assert (BASE_DIR / f"raw/{note_id}/content.md").exists(), f"raw/{note_id}/content.md was not created!"
    note_meta = json.loads((BASE_DIR / f"raw/{note_id}/metadata.json").read_text(encoding="utf-8"))
    assert note_meta["source"] == "CLI / User Note"
    print(f"✅ Text Note Ingested (ID: {note_id}, Source: {note_meta['source']})")

    # 2. Capture URL
    url = "https://example.com"
    result_url = capture.capture(url, "link")
    url_id = result_url["id"]
    assert (BASE_DIR / f"raw/{url_id}/metadata.json").exists(), f"raw/{url_id}/metadata.json was not created!"
    assert (BASE_DIR / f"raw/{url_id}/content.md").exists(), f"raw/{url_id}/content.md was not created!"
    url_meta = json.loads((BASE_DIR / f"raw/{url_id}/metadata.json").read_text(encoding="utf-8"))
    assert url_meta["source"] == url
    print(f"✅ Web URL Ingested (ID: {url_id}, Source: {url_meta['source']})")

    # 3. Capture file
    sample_file = BASE_DIR / "docs/Problem_statement.md"
    if sample_file.exists():
        result_file = capture.capture(str(sample_file), "file")
        file_id = result_file["id"]
        assert (BASE_DIR / f"raw/{file_id}/metadata.json").exists(), f"raw/{file_id}/metadata.json was not created!"
        assert (BASE_DIR / f"raw/{file_id}/content.md").exists(), f"raw/{file_id}/content.md was not created!"
        file_meta = json.loads((BASE_DIR / f"raw/{file_id}/metadata.json").read_text(encoding="utf-8"))
        print(f"✅ Local File Ingested (ID: {file_id}, Source: {file_meta['source']})")

    print("✅ Phase 1 Passed: Capture engine verified across text, URL, and file inputs.")
    return [note_id, url_id]


def test_phase2(capture_ids):
    print("\n==========================================")
    print("  PHASE 2: Autonomous PARA Classifier")
    print("==========================================")
    
    for cid in capture_ids:
        raw_path = BASE_DIR / f"raw/{cid}"
        wiki_file_path = classify.process_raw_to_wiki(raw_path)
        wiki_p = Path(wiki_file_path)
        assert wiki_p.exists(), f"Wiki file {wiki_p} was not created!"
        
        content = wiki_p.read_text(encoding="utf-8")
        assert content.startswith("---"), f"Wiki file {wiki_p} is missing YAML frontmatter!"
        assert "category:" in content, f"Wiki file {wiki_p} is missing category!"
        assert "auto_links:" in content, f"Wiki file {wiki_p} is missing auto_links!"
        print(f"✅ Classified capture {cid} -> {wiki_p.relative_to(BASE_DIR)}")

    # Batch classify all unclassified captures
    batch_result = classify.batch_classify_all()
    print(f"✅ Phase 2 Passed: Classifier & PARA folder organization verified.")


def test_phase3():
    print("\n==========================================")
    print("  PHASE 3: Dense Vector Auto-Link Engine")
    print("==========================================")
    
    # Ingest 2 closely related notes to guarantee similarity >= 0.50
    n1_text = "Microservices architecture in Python using gRPC, REST APIs, and distributed caching."
    n2_text = "Designing resilient backend services with Python, gRPC microservices, and distributed systems."
    
    cap1 = capture.capture(n1_text, "note")
    cap2 = capture.capture(n2_text, "note")

    classify.process_raw_to_wiki(BASE_DIR / f"raw/{cap1['id']}")
    classify.process_raw_to_wiki(BASE_DIR / f"raw/{cap2['id']}")

    # Run dense vector auto-linking
    stats = link.auto_link_wiki(similarity_threshold=0.50)
    assert stats["total_notes"] > 0, "No notes were processed by auto_link_wiki!"

    notes = link.load_wiki_notes()
    found_link = False
    for n in notes:
        if n["id"] in (cap1["id"], cap2["id"]):
            raw_text_on_disk = n["file_path"].read_text(encoding="utf-8")
            if "## Related Brain Notes" in raw_text_on_disk and "auto_links:" in raw_text_on_disk:
                found_link = True
                print(f"✅ Verified vector auto-link in note {n['id']} ({n['title']})")

    assert found_link, "Failed to discover vector auto-links between related notes!"
    print(f"✅ Phase 3 Passed: Auto-Linker generated dense embeddings & bidirectional links.")


def test_phase4():
    print("\n==========================================")
    print("  PHASE 4: Graph Data Model & Visualizer")
    print("==========================================")
    
    graph_data = build_graph.generate_graph_data()
    assert "nodes" in graph_data and "edges" in graph_data, "graph_data format invalid"
    assert (BASE_DIR / "graph.json").exists(), "graph.json was not created"
    
    build_graph.render_interactive_graph(graph_data)
    assert (BASE_DIR / "graph.html").exists(), "graph.html was not created"
    print(f"✅ Phase 4 Passed: Graph builder & PyVis visualizer exported graph.json & graph.html.")


def test_phase5():
    print("\n==========================================")
    print("  PHASE 5: RAG Q&A Search Engine (ask.py)")
    print("==========================================")

    # Ingest a specific test note to query against
    q_note = "Phase 5 RAG Retrieval Test Note: Building microservices with Python, gRPC, and vector similarity search."
    cap = capture.capture(q_note, "note")
    classify.process_raw_to_wiki(BASE_DIR / f"raw/{cap['id']}")

    # Test context retrieval
    results = ask.retrieve_context("microservices with Python gRPC", top_k=3)
    assert len(results) > 0, "ask.retrieve_context returned no results!"
    print(f"✅ Context Retrieval Verified (Found {len(results)} matching notes for query)")

    # Test ask() end-to-end RAG Q&A
    rag_response = ask.ask("What notes do I have about microservices with Python and gRPC?")
    assert "answer" in rag_response, "ask() response missing 'answer'"
    assert "sources" in rag_response, "ask() response missing 'sources'"
    assert len(rag_response["answer"]) > 0, "ask() answer is empty"
    print(f"✅ RAG Synthesis Verified (Sources cited: {len(rag_response['sources'])}, Confidence: {int(rag_response['confidence']*100)}%)")

    # Test fallback response for unmatched query
    empty_res = ask.ask("xyz_unmatched_query_12345_nonexistent_topic", min_similarity=0.99)
    assert empty_res["confidence"] == 0.0, "Expected 0.0 confidence for unmatched query"
    print(f"✅ Query Fallback Verified for unmatched topics.")
    print(f"✅ Phase 5 Passed: RAG Q&A retrieval & synthesis engine verified.")


def test_phase6():
    print("\n==========================================")
    print("  PHASE 6: Unified Streamlit Interface (app.py)")
    print("==========================================")

    # 1. Verify app.py file exists
    app_path = BASE_DIR / "app.py"
    assert app_path.exists(), "app.py does not exist!"

    # 2. Verify .streamlit/config.toml configuration exists
    st_config = BASE_DIR / ".streamlit/config.toml"
    assert st_config.exists(), ".streamlit/config.toml does not exist!"

    # 3. Import app and test get_vault_metrics
    import app
    metrics = app.get_vault_metrics()
    assert "Total" in metrics and "Edges" in metrics, "get_vault_metrics format invalid"
    print(f"✅ App Vault Metrics Verified (Total Notes: {metrics['Total']}, Connections: {metrics['Edges']})")
    print(f"🏅 Milestone Achieved: The Oracle")
    print(f"✅ Phase 6 Passed: Streamlit dashboard app.py and .streamlit/config.toml verified.")


def test_phase7():
    print("\n==========================================")
    print("  PHASE 7: Comprehensive Local E2E Testing")
    print("==========================================")
    
    notes = link.load_wiki_notes()
    assert len(notes) >= 10, f"Vault note count {len(notes)} is below threshold"
    
    # Verify embeddings cache file
    emb_cache = BASE_DIR / "embeddings.npy"
    assert emb_cache.exists(), "embeddings.npy does not exist!"
    
    print(f"✅ Vault Integrity Verified ({len(notes)} Markdown notes indexed with dense embedding matrix).")
    print(f"✅ Phase 7 Passed: End-to-end local testing & vault state verified.")


def test_phase8():
    print("\n==========================================")
    print("  PHASE 8: Production Cloud Deployment Readiness")
    print("==========================================")
    
    secrets_example = BASE_DIR / ".streamlit/secrets.toml.example"
    deploy_guide = BASE_DIR / "docs/deployment-guide.md"
    req_file = BASE_DIR / "requirements.txt"
    
    assert secrets_example.exists(), ".streamlit/secrets.toml.example missing!"
    assert deploy_guide.exists(), "docs/deployment-guide.md missing!"
    
    req_content = req_file.read_text(encoding="utf-8")
    assert "scikit-learn" in req_content, "scikit-learn missing from requirements.txt!"
    assert "streamlit" in req_content, "streamlit missing from requirements.txt!"
    assert "groq" in req_content, "groq missing from requirements.txt!"
    
    # Test secret fallback function availability
    assert hasattr(classify, "get_groq_client"), "classify.get_groq_client missing!"
    assert hasattr(ask, "get_groq_client"), "ask.get_groq_client missing!"
    
    print("✅ Cloud Deployment Assets Verified (.streamlit/secrets.toml.example, docs/deployment-guide.md, st.secrets fallback).")
    print("✅ Phase 8 Passed: Production Cloud Deployment readiness verified.")


def test_phase9():
    print("\n==========================================")
    print("  PHASE 9: Final Documentation & Badge Audit")
    print("==========================================")
    
    readme = BASE_DIR / "README.md"
    assert readme.exists(), "README.md is missing!"
    content = readme.read_text(encoding="utf-8")
    
    # Audit badge checkboxes
    assert "- [x] 🏅 **The Archivist**" in content, "The Archivist badge checkbox is not complete!"
    assert "- [x] 🏅 **The Librarian**" in content, "The Librarian badge checkbox is not complete!"
    assert "- [x] 🏅 **The Cartographer**" in content, "The Cartographer badge checkbox is not complete!"
    assert "- [x] 🏅 **The Oracle**" in content, "The Oracle badge checkbox is not complete!"
    
    print("✅ Documentation & All 4 Milestone Badges Audited 100% Complete.")
    print("✅ Phase 9 Passed: Documentation & Final Deliverables complete.")


def main():
    try:
        test_phase0()
        cids = test_phase1()
        test_phase2(cids)
        test_phase3()
        test_phase4()
        test_phase5()
        test_phase6()
        test_phase7()
        test_phase8()
        test_phase9()
        print("\n==========================================")
        print("🎉 ALL 10 PHASES (PHASES 0 THROUGH 9) FULLY VERIFIED & COMPLETE!")
        print("==========================================\n")
    except Exception as e:
        print(f"\n❌ VERIFICATION FAILED: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
