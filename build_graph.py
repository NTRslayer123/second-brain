#!/usr/bin/env python3
"""
SecondSelf — Graph Data Model & Interactive Visualizer Engine (Phase 4: The Cartographer)
Parses wiki/ markdown notes and auto-links, builds graph data schema (nodes & edges),
exports graph.json, and renders an interactive force-directed HTML graph using PyVis.
"""

from __future__ import annotations

import os
import sys
import json
import re
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Base directories
BASE_DIR = Path(__file__).parent.resolve()
WIKI_DIR = BASE_DIR / "wiki"
GRAPH_JSON_PATH = BASE_DIR / "graph.json"
GRAPH_HTML_PATH = BASE_DIR / "graph.html"
GRAPH_3D_HTML_PATH = BASE_DIR / "graph_3d.html"

# Try importing pyvis
try:
    # pyrefly: ignore [missing-import]
    from pyvis.network import Network  # type: ignore
except ImportError:
    Network = None

CATEGORY_COLORS = {
    "Projects": "#F59E0B",   # Neon Amber
    "Areas": "#06B6D4",      # Aurora Cyan
    "Resources": "#10B981",  # Electric Emerald
    "Archives": "#64748B"    # Slate Steel
}
CATEGORY_SHAPES = {
    "Projects": "diamond",   # Diamond (Active Goals)
    "Areas": "triangle",     # Triangle (Responsibilities)
    "Resources": "dot",      # Circle (Knowledge Guides)
    "Archives": "square"     # Square Box (Archived)
}
DEFAULT_COLOR = "#94A3B8"    # Neutral Slate


def parse_yaml_frontmatter(content: str) -> tuple[dict, str]:
    """
    Parses frontmatter block (between --- and ---) and body content.
    Returns (frontmatter_dict, body_content_text).
    """
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
    if not match:
        return {}, content

    frontmatter_raw = match.group(1)
    body = match.group(2)
    metadata = {}

    for line in frontmatter_raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()

            # Unquote string values
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1].replace('\\"', '"').replace('\\\\', '\\')
            elif val.startswith("'") and val.endswith("'"):
                val = val[1:-1]

            # Simple list parsing [item1, item2]
            if val.startswith("[") and val.endswith("]"):
                inner = val[1:-1].strip()
                if not inner:
                    val = []
                else:
                    items = [i.strip().strip('"').strip("'") for i in inner.split(",") if i.strip()]
                    val = items

            metadata[key] = val

    return metadata, body


def parse_auto_links_from_frontmatter(content: str) -> list[dict]:
    """Extracts structured auto_links list from YAML frontmatter."""
    match = re.search(r"auto_links:\s*\n((?:\s*-\s*id:.*\n\s*title:.*\n\s*similarity:.*\n?)+)", content)
    if not match:
        return []

    links_raw = match.group(1)
    links = []
    current_link = {}

    for line in links_raw.splitlines():
        line = line.strip()
        if line.startswith("- id:"):
            if current_link and "id" in current_link:
                links.append(current_link)
            val = line.split(":", 1)[1].strip().strip('"').strip("'")
            current_link = {"id": val}
        elif line.startswith("title:") and current_link:
            val = line.split(":", 1)[1].strip().strip('"').strip("'")
            current_link["title"] = val
        elif line.startswith("similarity:") and current_link:
            try:
                val = float(line.split(":", 1)[1].strip())
                current_link["similarity"] = val
            except ValueError:
                pass

    if current_link and "id" in current_link:
        links.append(current_link)

    return links


def parse_wikilinks_from_body(body: str) -> list[str]:
    """Parses [[note_id]] or [[note_id|title]] wikilinks from body content."""
    matches = re.findall(r"\[\[([^\]\|]+)(?:\|[^\]]+)?\]\]", body)
    return list(set(matches))


def load_all_wiki_notes() -> list[dict]:
    """Scans wiki/ directory for all markdown files and extracts structured node/link data."""
    if not WIKI_DIR.exists():
        print(f"[Notice] Wiki directory '{WIKI_DIR}' does not exist.", file=sys.stderr)
        return []

    md_files = list(WIKI_DIR.rglob("*.md"))
    notes = []

    for file_path in sorted(md_files):
        if file_path.name.startswith("."):
            continue
        try:
            raw_text = file_path.read_text(encoding="utf-8")
            meta, body = parse_yaml_frontmatter(raw_text)

            note_id = meta.get("id") or file_path.stem
            title = meta.get("title") or file_path.stem
            category = meta.get("category") or "Resources"
            summary = meta.get("summary") or ""
            tags = meta.get("tags") if isinstance(meta.get("tags"), list) else []

            # Parse frontmatter auto_links and body wikilinks
            fm_links = parse_auto_links_from_frontmatter(raw_text)
            body_wikilinks = parse_wikilinks_from_body(body)

            notes.append({
                "id": note_id,
                "title": title,
                "category": category,
                "summary": summary,
                "tags": tags,
                "auto_links": fm_links,
                "body_links": body_wikilinks,
                "file_path": file_path
            })
        except Exception as e:
            print(f"[Warning] Failed to load note {file_path}: {e}", file=sys.stderr)

    return notes


def generate_graph_data() -> dict:
    """
    Transforms wiki notes into graph JSON schema with nodes and weighted edges.
    Calculates connection degrees for dynamic node sizing.
    """
    notes = load_all_wiki_notes()
    node_ids = {note["id"] for note in notes}
    id_to_title = {note["id"]: note["title"] for note in notes}

    # Track degree counts for node sizing
    degree_map = {note["id"]: 0 for note in notes}
    edges_set = set()
    edges_list = []

    # Calculate edges from frontmatter auto_links and body wikilinks
    for note in notes:
        src_id = note["id"]

        # 1. Frontmatter auto_links
        for link in note["auto_links"]:
            tgt_id = link["id"]
            if tgt_id in node_ids and src_id != tgt_id:
                edge_pair = tuple(sorted([src_id, tgt_id]))
                if edge_pair not in edges_set:
                    edges_set.add(edge_pair)
                    weight = link.get("similarity", 0.7)
                    sim_pct = int(weight * 100)
                    edges_list.append({
                        "from": edge_pair[0],
                        "to": edge_pair[1],
                        "weight": weight,
                        "title": f"Similarity: {sim_pct}%"
                    })
                    degree_map[edge_pair[0]] += 1
                    degree_map[edge_pair[1]] += 1

        # 2. Body wikilinks
        for tgt_id in note["body_links"]:
            if tgt_id in node_ids and src_id != tgt_id:
                edge_pair = tuple(sorted([src_id, tgt_id]))
                if edge_pair not in edges_set:
                    edges_set.add(edge_pair)
                    edges_list.append({
                        "from": edge_pair[0],
                        "to": edge_pair[1],
                        "weight": 0.65,
                        "title": "Wikilink Reference"
                    })
                    degree_map[edge_pair[0]] += 1
                    degree_map[edge_pair[1]] += 1

    # Build node objects
    nodes_list = []
    for note in notes:
        cat = note["category"]
        color = CATEGORY_COLORS.get(cat, DEFAULT_COLOR)
        deg = degree_map.get(note["id"], 0)
        # Node value scales dynamically with degree (base value 10 + 5 per connection)
        node_value = 10 + (deg * 5)

        tags_str = ", ".join(note["tags"]) if note["tags"] else "None"
        tooltip = (
            f"<b>{note['title']}</b><br/>"
            f"<b>Category:</b> {cat}<br/>"
            f"<b>Tags:</b> {tags_str}<br/>"
            f"<b>Summary:</b> {note['summary'] or 'No summary available.'}"
        )

        nodes_list.append({
            "id": note["id"],
            "label": note["title"],
            "category": cat,
            "shape": CATEGORY_SHAPES.get(cat, "dot"),
            "tags": note["tags"],
            "summary": note["summary"],
            "color": color,
            "value": node_value,
            "degree": deg,
            "title": tooltip
        })

    graph_data = {
        "nodes": nodes_list,
        "edges": edges_list
    }

    # Save graph.json
    try:
        GRAPH_JSON_PATH.write_text(json.dumps(graph_data, indent=2), encoding="utf-8")
        print(f"[OK] Graph data saved to '{GRAPH_JSON_PATH}' ({len(nodes_list)} nodes, {len(edges_list)} edges).")
    except Exception as e:
        print(f"[Error] Failed to save graph.json: {e}", file=sys.stderr)

    return graph_data


def render_interactive_graph(graph_data: dict, output_path: Path = GRAPH_HTML_PATH) -> str:
    """
    Renders PyVis force-directed interactive HTML graph visualization.
    Returns generated HTML content string.
    """
    if Network is None:
        print("[Warning] 'pyvis' package is not installed. Skipping HTML graph render.", file=sys.stderr)
        return ""

    # Create PyVis Network instance with dark sleek styling
    net = Network(height="850px", width="100%", bgcolor="#090D16", font_color="#F3F4F6", directed=False)

    # Configure physics engine & interaction options
    net.set_options("""
    {
      "nodes": {
        "borderWidth": 2,
        "borderWidthSelected": 4,
        "font": {
          "size": 14,
          "face": "Inter, system-ui, sans-serif"
        }
      },
      "edges": {
        "color": {
          "color": "rgba(160, 174, 192, 0.4)",
          "highlight": "#4D96FF"
        },
        "smooth": {
          "type": "continuous",
          "roundness": 0.5
        }
      },
      "physics": {
        "barnesHut": {
          "gravitationalConstant": -26000,
          "centralGravity": 0.035,
          "springLength": 260,
          "springConstant": 0.015,
          "damping": 0.09,
          "avoidOverlap": 0.8
        },
        "maxVelocity": 50,
        "minVelocity": 0.75,
        "solver": "barnesHut"
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 200,
        "zoomView": true,
        "dragNodes": true
      }
    }
    """)

    # Add nodes to PyVis
    for node in graph_data["nodes"]:
        net.add_node(
            n_id=node["id"],
            label=node["label"],
            title=node["title"],
            color=node["color"],
            shape=node.get("shape", "dot"),
            value=node["value"]
        )

    # Add edges to PyVis with dynamic opacity and line thickness based on similarity weight
    for edge in graph_data["edges"]:
        weight = edge.get("weight", 0.65)
        # Normalize weight [0.5, 1.0] -> alpha opacity [0.18, 0.95]
        alpha = max(0.18, min(0.95, (weight - 0.45) / 0.55))
        edge_width = max(1, int(weight * 3.5))

        edge_color = {
            "color": f"rgba(160, 174, 192, {alpha:.2f})",
            "highlight": "#4D96FF",
            "hover": "#FF6B6B"
        }

        net.add_edge(
            source=edge["from"],
            to=edge["to"],
            width=edge_width,
            color=edge_color,
            title=edge.get("title", "")
        )

    # Write HTML file and inject floating glassmorphic legend
    try:
        net.save_graph(str(output_path))
        html_content = output_path.read_text(encoding="utf-8")

        # HTML Legend, Search Bar & Focus Control Overlay
        overlay_html = """
        <style>
          .search-item:hover {
            background: rgba(59, 130, 246, 0.25) !important;
          }
        </style>
        
        <!-- Search & Focus Node Widget -->
        <div id="graph-search-container" style="
          position: fixed;
          top: 20px;
          left: 20px;
          z-index: 9999;
          font-family: 'Inter', system-ui, -apple-system, sans-serif;
          min-width: 280px;
          max-width: 380px;
        ">
          <div style="
            background: rgba(26, 32, 44, 0.90);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 12px;
            padding: 8px 12px;
            display: flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
          ">
            <span style="font-size: 16px;">🔍</span>
            <input type="text" id="graph-search-input" placeholder="Search nodes in graph..." style="
              background: transparent;
              border: none;
              outline: none;
              color: #F7FAFC;
              font-size: 13px;
              width: 100%;
              font-family: inherit;
            " autocomplete="off" />
            <button id="clear-search-btn" title="Reset View" style="
              background: rgba(255,255,255,0.08);
              border: none;
              color: #A0AEC0;
              border-radius: 50%;
              width: 22px;
              height: 22px;
              cursor: pointer;
              display: flex;
              align-items: center;
              justify-content: center;
              font-size: 12px;
              transition: background 0.2s, color 0.2s;
            ">✕</button>
          </div>
          <div id="search-dropdown-list" style="
            display: none;
            margin-top: 6px;
            background: rgba(26, 32, 44, 0.95);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 10px;
            max-height: 240px;
            overflow-y: auto;
            box-shadow: 0 10px 25px rgba(0,0,0,0.6);
            color: #F7FAFC;
            font-size: 13px;
          "></div>
        </div>

        <!-- Legend Overlay -->
        <div id="graph-legend" style="
          position: fixed;
          top: 20px;
          right: 20px;
          background: rgba(26, 32, 44, 0.88);
          backdrop-filter: blur(10px);
          -webkit-backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.12);
          border-radius: 12px;
          padding: 14px 18px;
          color: #F7FAFC;
          font-family: 'Inter', system-ui, -apple-system, sans-serif;
          font-size: 13px;
          box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
          z-index: 9999;
          pointer-events: auto;
          min-width: 220px;
        ">
          <div style="font-weight: 700; font-size: 14px; margin-bottom: 10px; color: #10B981; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 6px; display: flex; align-items: center; gap: 6px;">
            <span>🧠</span> SecondSelf Brain Legend
          </div>
          <div style="display: flex; align-items: center; margin-bottom: 6px;">
            <span style="width: 12px; height: 12px; border-radius: 50%; background-color: #F59E0B; display: inline-block; margin-right: 10px; box-shadow: 0 0 8px #F59E0B;"></span>
            <span><b>Projects</b> (Active Goals)</span>
          </div>
          <div style="display: flex; align-items: center; margin-bottom: 6px;">
            <span style="width: 12px; height: 12px; border-radius: 50%; background-color: #06B6D4; display: inline-block; margin-right: 10px; box-shadow: 0 0 8px #06B6D4;"></span>
            <span><b>Areas</b> (Responsibilities)</span>
          </div>
          <div style="display: flex; align-items: center; margin-bottom: 6px;">
            <span style="width: 12px; height: 12px; border-radius: 50%; background-color: #10B981; display: inline-block; margin-right: 10px; box-shadow: 0 0 8px #10B981;"></span>
            <span><b>Resources</b> (Reference & Knowledge)</span>
          </div>
          <div style="display: flex; align-items: center; margin-bottom: 10px;">
            <span style="width: 12px; height: 12px; border-radius: 50%; background-color: #64748B; display: inline-block; margin-right: 10px; box-shadow: 0 0 8px #64748B;"></span>
            <span><b>Archives</b> (Completed / Inactive)</span>
          </div>
          <div style="border-top: 1px solid rgba(255,255,255,0.1); margin-top: 8px; padding-top: 8px;">
            <div style="font-weight: 600; font-size: 11px; color: #94A3B8; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px;">Vector Similarity (Opacity)</div>
            <div style="display: flex; align-items: center; justify-content: space-between; font-size: 11px; color: #CBD5E0;">
              <span style="opacity: 0.4;">Low (0.55)</span>
              <div style="height: 4px; flex-grow: 1; margin: 0 8px; background: linear-gradient(to right, rgba(16,185,129,0.2), rgba(16,185,129,0.95)); border-radius: 2px;"></div>
              <span style="font-weight: 600; color: #10B981;">High (1.00)</span>
            </div>
          </div>
        </div>

        <script>
          function escapeHtml(str) {
            if (!str) return '';
            return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
          }

          function initGraphSearch() {
            const input = document.getElementById("graph-search-input");
            const dropdown = document.getElementById("search-dropdown-list");
            const clearBtn = document.getElementById("clear-search-btn");

            if (!input || typeof nodes === 'undefined' || typeof network === 'undefined') {
              setTimeout(initGraphSearch, 200);
              return;
            }

            input.addEventListener("input", function() {
              const query = input.value.trim().toLowerCase();
              if (!query) {
                dropdown.style.display = "none";
                dropdown.innerHTML = "";
                return;
              }

              const allNodes = nodes.get();
              const matches = allNodes.filter(n => {
                const label = (n.label || "").toLowerCase();
                const title = (n.title || "").toLowerCase();
                return label.includes(query) || title.includes(query);
              }).slice(0, 8);

              if (matches.length === 0) {
                dropdown.innerHTML = '<div style="padding: 10px 12px; color: #A0AEC0; font-size:12px;">No matching nodes found</div>';
                dropdown.style.display = "block";
                return;
              }

              dropdown.innerHTML = matches.map(n => {
                const bgColor = (typeof n.color === 'object' ? n.color.background : n.color) || '#38BDF8';
                return `
                  <div class="search-item" data-id="${n.id}" style="padding: 9px 12px; cursor: pointer; border-bottom: 1px solid rgba(255,255,255,0.06); display: flex; align-items: center; gap: 8px;">
                    <span style="width: 10px; height: 10px; border-radius: 50%; background-color: ${bgColor}; display: inline-block; flex-shrink: 0;"></span>
                    <span style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-weight: 500;">${escapeHtml(n.label || n.id)}</span>
                  </div>
                `;
              }).join('');

              dropdown.style.display = "block";

              dropdown.querySelectorAll('.search-item').forEach(item => {
                item.addEventListener('click', function() {
                  const nodeId = this.getAttribute('data-id');
                  focusNode(nodeId);
                  input.value = this.innerText.trim();
                  dropdown.style.display = 'none';
                });
              });
            });

            function focusNode(nodeId) {
              if (!network) return;
              network.focus(nodeId, {
                scale: 1.8,
                animation: {
                  duration: 1000,
                  easingFunction: "easeInOutQuad"
                }
              });
              network.selectNodes([nodeId]);
            }

            clearBtn.addEventListener("click", function() {
              input.value = "";
              dropdown.style.display = "none";
              if (network) {
                network.unselectNodes();
                network.fit({ animation: { duration: 800, easingFunction: "easeInOutQuad" } });
              }
            });

            document.addEventListener("click", function(e) {
              if (!e.target.closest("#graph-search-container")) {
                dropdown.style.display = "none";
              }
            });
          }

          if (document.readyState === "loading") {
            document.addEventListener("DOMContentLoaded", initGraphSearch);
          } else {
            initGraphSearch();
          }
        </script>
        """

        # Inject overlay before closing </body> tag
        if "</body>" in html_content:
            html_content = html_content.replace("</body>", f"{overlay_html}\n</body>")
        else:
            html_content += overlay_html

        output_path.write_text(html_content, encoding="utf-8")
        print(f"[OK] Interactive PyVis 2D graph exported to '{output_path}'.")
        return html_content
    except Exception as e:
        print(f"[Error] Failed to render PyVis graph HTML: {e}", file=sys.stderr)
        return ""


def render_interactive_graph_3d(graph_data: dict, output_path: Path = GRAPH_3D_HTML_PATH) -> str:
    """
    Renders 3D WebGL force-directed interactive HTML graph visualization using 3d-force-graph.
    Returns generated HTML content string.
    """
    nodes_json = json.dumps(graph_data["nodes"])
    edges_json = json.dumps(graph_data["edges"])

    html_template = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>SecondSelf 3D Neural Matrix</title>
  <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/3d-force-graph@1.73.0/dist/3d-force-graph.min.js"></script>
  <style>
    html, body {{
      margin: 0;
      padding: 0;
      width: 100%;
      height: 100%;
      background: #090D16;
      color: #F3F4F6;
      font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
      overflow: hidden;
    }}
    #graph-3d {{
      width: 100%;
      height: 100%;
      min-height: 850px;
    }}
    .search-item:hover {{
      background: rgba(16, 185, 129, 0.25) !important;
    }}
  </style>
</head>
<body>
  <div id="graph-3d"></div>

  <!-- Search & Focus Node Widget -->
  <div id="graph-search-container" style="
    position: fixed;
    top: 20px;
    left: 20px;
    z-index: 9999;
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    min-width: 280px;
    max-width: 380px;
  ">
    <div style="
      background: rgba(14, 21, 36, 0.90);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid rgba(16, 185, 129, 0.25);
      border-radius: 12px;
      padding: 8px 12px;
      display: flex;
      align-items: center;
      gap: 8px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);
    ">
      <span style="font-size: 16px;">🔍</span>
      <input type="text" id="graph-search-input" placeholder="Search 3D nodes..." style="
        background: transparent;
        border: none;
        outline: none;
        color: #F7FAFC;
        font-size: 13px;
        width: 100%;
        font-family: inherit;
      " autocomplete="off" />
      <button id="clear-search-btn" title="Reset View" style="
        background: rgba(255,255,255,0.08);
        border: none;
        color: #A0AEC0;
        border-radius: 50%;
        width: 22px;
        height: 22px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
      ">✕</button>
    </div>
    <div id="search-dropdown-list" style="
      display: none;
      margin-top: 6px;
      background: rgba(14, 21, 36, 0.95);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(16, 185, 129, 0.25);
      border-radius: 10px;
      max-height: 240px;
      overflow-y: auto;
      box-shadow: 0 10px 25px rgba(0,0,0,0.6);
      color: #F7FAFC;
      font-size: 13px;
    "></div>
  </div>

  <!-- Legend Overlay -->
  <div id="graph-legend" style="
    position: fixed;
    top: 20px;
    right: 20px;
    background: rgba(14, 21, 36, 0.88);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(16, 185, 129, 0.2);
    border-radius: 12px;
    padding: 14px 18px;
    color: #F7FAFC;
    font-size: 13px;
    z-index: 9999;
    min-width: 220px;
  ">
    <div style="font-weight: 700; font-size: 14px; margin-bottom: 10px; color: #10B981; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 6px;">
      🌐 3D Neural Matrix (Category Shapes)
    </div>
    <div style="display: flex; align-items: center; margin-bottom: 6px;">
      <span style="width: 12px; height: 12px; background-color: #F59E0B; display: inline-block; margin-right: 10px; clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%);"></span>
      <span><b>Projects</b> (Amber Diamond)</span>
    </div>
    <div style="display: flex; align-items: center; margin-bottom: 6px;">
      <span style="width: 12px; height: 12px; background-color: #06B6D4; display: inline-block; margin-right: 10px; clip-path: polygon(50% 0%, 0% 100%, 100% 100%);"></span>
      <span><b>Areas</b> (Cyan Triangle)</span>
    </div>
    <div style="display: flex; align-items: center; margin-bottom: 6px;">
      <span style="width: 12px; height: 12px; border-radius: 50%; background-color: #10B981; display: inline-block; margin-right: 10px;"></span>
      <span><b>Resources</b> (Emerald Sphere)</span>
    </div>
    <div style="display: flex; align-items: center; margin-bottom: 10px;">
      <span style="width: 12px; height: 12px; background-color: #64748B; display: inline-block; margin-right: 10px;"></span>
      <span><b>Archives</b> (Slate Box)</span>
    </div>
    <div style="font-size: 11px; color: #94A3B8; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 6px;">
      🖱️ Drag to rotate 3D view<br/>🖱️ Right-click to pan<br/>📜 Scroll to zoom
    </div>
  </div>

  <script>
    const gData = {{
      nodes: {nodes_json},
      links: {edges_json}.map(e => ({{ source: e.from, target: e.to, weight: e.weight }}))
    }};

    let Graph = null;

    function init3DGraph() {{
      const elem = document.getElementById('graph-3d');
      if (!elem || typeof ForceGraph3D === 'undefined') {{
        setTimeout(init3DGraph, 100);
        return;
      }}

      const width = elem.clientWidth || window.innerWidth || 1000;
      const height = elem.clientHeight || 850;

      Graph = ForceGraph3D()(elem)
        .width(width)
        .height(height)
        .graphData(gData)
        .backgroundColor('#090D16')
        .nodeId('id')
        .nodeLabel(node => `<b>${{node.label}}</b><br/>Category: ${{node.category}}<br/>${{node.summary || ''}}`)
        .nodeThreeObject(node => {{
          const group = new THREE.Group();
          const val = Math.max(2.0, (node.value || 10) / 4.5);

          try {{
            if (typeof THREE !== 'undefined') {{
              let geometry;
              if (node.shape === 'diamond' || node.category === 'Projects') {{
                geometry = new THREE.OctahedronGeometry(val * 1.1);
              }} else if (node.shape === 'triangle' || node.category === 'Areas') {{
                geometry = new THREE.ConeGeometry(val * 0.9, val * 1.4, 3);
              }} else if (node.shape === 'square' || node.category === 'Archives') {{
                geometry = new THREE.BoxGeometry(val * 1.2, val * 1.2, val * 1.2);
              }} else {{
                geometry = new THREE.SphereGeometry(val, 16, 16);
              }}
              const material = new THREE.MeshLambertMaterial({{
                color: node.color || '#10B981',
                transparent: true,
                opacity: 0.90
              }});
              const mesh = new THREE.Mesh(geometry, material);
              group.add(mesh);

              // Floating 2D Sprite Text Label
              const labelText = node.label || node.id;
              const canvas = document.createElement('canvas');
              const ctx = canvas.getContext('2d');
              canvas.width = 256;
              canvas.height = 64;
              ctx.font = 'Bold 22px Plus Jakarta Sans, Inter, sans-serif';
              ctx.fillStyle = 'rgba(14, 21, 36, 0.85)';
              ctx.strokeStyle = node.color || '#10B981';
              ctx.lineWidth = 2;

              const txtWidth = Math.min(240, ctx.measureText(labelText).width + 16);
              ctx.beginPath();
              if (ctx.roundRect) {{
                ctx.roundRect(4, 4, txtWidth, 36, 6);
              }} else {{
                ctx.rect(4, 4, txtWidth, 36);
              }}
              ctx.fill();
              ctx.stroke();

              ctx.fillStyle = '#F3F4F6';
              ctx.fillText(labelText.length > 18 ? labelText.substring(0, 16) + '...' : labelText, 12, 28);

              const texture = new THREE.CanvasTexture(canvas);
              const spriteMat = new THREE.SpriteMaterial({{ map: texture, transparent: true, depthWrite: false }});
              const sprite = new THREE.Sprite(spriteMat);
              sprite.position.set(0, val + 6, 0);
              sprite.scale.set(24, 6, 1);
              group.add(sprite);

              return group;
            }}
          }} catch(e) {{
            console.warn("Fallback 3D node:", e);
          }}
          return false;
        }})
        .linkColor(link => {{
          const w = link.weight || 0.6;
          const alpha = Math.max(0.2, Math.min(0.9, (w - 0.4) / 0.6));
          return `rgba(16, 185, 129, ${{alpha.toFixed(2)}})`;
        }})
        .linkWidth(link => Math.max(1, (link.weight || 0.6) * 2.5))
        .linkOpacity(0.5)
        .linkDirectionalParticles(2)
        .linkDirectionalParticleWidth(1.5)
        .linkDirectionalParticleSpeed(0.005)
        .onNodeClick(node => {{
          const distance = 140;
          const distRatio = 1 + distance / Math.hypot(node.x || 1, node.y || 1, node.z || 1);
          Graph.cameraPosition(
            {{ x: (node.x || 0) * distRatio, y: (node.y || 0) * distRatio, z: (node.z || 0) * distRatio }},
            node,
            1200
          );
        }});

      // Configure 3D force physics for clear node separation & zero overlaps
      if (Graph.d3Force('charge')) {{
        Graph.d3Force('charge').strength(-180);
      }}
      if (Graph.d3Force('link')) {{
        Graph.d3Force('link')
          .distance(link => Math.max(65, (1 - (link.weight || 0.6)) * 120))
          .strength(link => Math.min(0.8, (link.weight || 0.5) * 1.2));
      }}
      if (typeof d3 !== 'undefined' && d3.forceCollide) {{
        Graph.d3Force('collide', d3.forceCollide(node => Math.max(22, (node.value || 10) * 1.2)));
      }}

      window.Graph3D = Graph;
    }}

    if (document.readyState === "loading") {{
      document.addEventListener("DOMContentLoaded", init3DGraph);
    }} else {{
      init3DGraph();
    }}

    // 3D Search & Focus logic
    function escapeHtml(str) {{
      if (!str) return '';
      return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }}

    const input = document.getElementById("graph-search-input");
    const dropdown = document.getElementById("search-dropdown-list");
    const clearBtn = document.getElementById("clear-search-btn");

    input.addEventListener("input", function() {{
      const query = input.value.trim().toLowerCase();
      if (!query) {{
        dropdown.style.display = "none";
        dropdown.innerHTML = "";
        return;
      }}

      const matches = gData.nodes.filter(n => {{
        const label = (n.label || "").toLowerCase();
        const title = (n.title || "").toLowerCase();
        return label.includes(query) || title.includes(query);
      }}).slice(0, 8);

      if (matches.length === 0) {{
        dropdown.innerHTML = '<div style="padding: 10px 12px; color: #A0AEC0; font-size:12px;">No matching nodes</div>';
        dropdown.style.display = "block";
        return;
      }}

      dropdown.innerHTML = matches.map(n => `
        <div class="search-item" data-id="${{n.id}}" style="padding: 9px 12px; cursor: pointer; border-bottom: 1px solid rgba(255,255,255,0.06); display: flex; align-items: center; gap: 8px;">
          <span style="width: 10px; height: 10px; border-radius: 50%; background-color: ${{n.color || '#10B981'}}; display: inline-block;"></span>
          <span style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-weight: 500;">${{escapeHtml(n.label || n.id)}}</span>
        </div>
      `).join('');

      dropdown.style.display = "block";

      dropdown.querySelectorAll('.search-item').forEach(item => {{
        item.addEventListener('click', function() {{
          const nodeId = this.getAttribute('data-id');
          const targetNode = gData.nodes.find(n => n.id === nodeId);
          if (targetNode && targetNode.x !== undefined) {{
            const distance = 140;
            const distRatio = 1 + distance / Math.hypot(targetNode.x || 1, targetNode.y || 1, targetNode.z || 1);
            Graph.cameraPosition(
              {{ x: (targetNode.x || 0) * distRatio, y: (targetNode.y || 0) * distRatio, z: (targetNode.z || 0) * distRatio }},
              targetNode,
              1200
            );
          }}
          input.value = this.innerText.trim();
          dropdown.style.display = 'none';
        }});
      }});
    }});

    clearBtn.addEventListener("click", function() {{
      input.value = "";
      dropdown.style.display = "none";
      Graph.zoomToFit(1000);
    }});
  </script>
</body>
</html>"""

    try:
        output_path.write_text(html_template, encoding="utf-8")
        print(f"[OK] 3D WebGL Graph exported to '{output_path}'.")
        return html_template
    except Exception as e:
        print(f"[Error] Failed to render 3D WebGL graph HTML: {e}", file=sys.stderr)
        return ""


def main():
    print("\n==========================================")
    print("  PHASE 4: Graph Data Model & Visualizer")
    print("==========================================")

    graph_data = generate_graph_data()
    render_interactive_graph(graph_data)
    render_interactive_graph_3d(graph_data)

    print(f"\n--- Graph Engine Summary ---")
    print(f"Total Nodes Processed : {len(graph_data['nodes'])}")
    print(f"Total Connections     : {len(graph_data['edges'])}")
    print("==========================================\n")


if __name__ == "__main__":
    main()
