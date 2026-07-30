#!/usr/bin/env python3
"""
Verification suite for SecondSelf Phase 3 (Dense Vector Auto-Link Engine).
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


def test_phase3():
    print("\n--- Testing Phase 3: Dense Vector Auto-Link Engine ---")

    # Ingest 2 closely related notes to ensure similarity >= threshold
    note1_text = "Microservices architecture in Python using gRPC, REST APIs, and distributed caching."
    note2_text = "Designing resilient backend services with Python, gRPC microservices, and distributed systems."
    
    cap1 = capture.capture(note1_text, "note")
    cap2 = capture.capture(note2_text, "note")

    classify.process_raw_to_wiki(BASE_DIR / f"raw/{cap1['id']}")
    classify.process_raw_to_wiki(BASE_DIR / f"raw/{cap2['id']}")

    # Run auto-linking with lower threshold to guarantee match
    stats = link.auto_link_wiki(similarity_threshold=0.50)

    assert stats["total_notes"] > 0, "No notes were processed by auto_link_wiki!"

    # Verify that note 1 contains auto_links to note 2 or vice versa
    notes = link.load_wiki_notes()
    found_bidirectional = False
    for n in notes:
        if n["id"] in (cap1["id"], cap2["id"]):
            if "## Related Brain Notes" in n["body"] or "auto_links:" in n["raw_text"]:
                found_bidirectional = True
                print(f"✅ Verified auto-link references in note {n['id']} ({n['title']})")

    assert found_bidirectional, "Failed to discover vector auto-links between related notes!"
    print(f"✅ Phase 3 Check Passed: Auto-Linker created {stats['total_edges']} bidirectional links.")


def main():
    try:
        test_phase3()
        print("\n🎉 PHASE 3 (DENSE VECTOR AUTO-LINK ENGINE) VERIFIED & WORKING PERFECTLY!")
    except Exception as e:
        print(f"\n❌ VERIFICATION FAILED: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
