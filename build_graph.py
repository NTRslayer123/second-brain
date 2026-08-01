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

# Try importing pyvis
try:
    # pyrefly: ignore [missing-import]
    from pyvis.network import Network  # type: ignore
except ImportError:
    Network = None

# PARA Category Color Palette
CATEGORY_COLORS = {
    "Projects": "#FF6B6B",   # Coral Red
    "Areas": "#4D96FF",      # Vibrant Blue
    "Resources": "#6BCB77",  # Emerald Green
    "Archives": "#9D9D9D"    # Slate Gray
}
DEFAULT_COLOR = "#A0AEC0"    # Muted Slate Neutral


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
    net = Network(height="750px", width="100%", bgcolor="#1A202C", font_color="#F7FAFC", directed=False)

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
          "gravitationalConstant": -22000,
          "centralGravity": 0.08,
          "springLength": 260,
          "springConstant": 0.02,
          "damping": 0.09,
          "avoidOverlap": 0.9
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

        # HTML Legend & Opacity Scale Overlay
        legend_html = """
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
          <div style="font-weight: 700; font-size: 14px; margin-bottom: 10px; color: #ED8936; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 6px; display: flex; align-items: center; gap: 6px;">
            <span>🧠</span> SecondSelf Brain Legend
          </div>
          <div style="display: flex; align-items: center; margin-bottom: 6px;">
            <span style="width: 12px; height: 12px; border-radius: 50%; background-color: #FF6B6B; display: inline-block; margin-right: 10px; box-shadow: 0 0 6px #FF6B6B;"></span>
            <span><b>Projects</b> (Deadlines)</span>
          </div>
          <div style="display: flex; align-items: center; margin-bottom: 6px;">
            <span style="width: 12px; height: 12px; border-radius: 50%; background-color: #4D96FF; display: inline-block; margin-right: 10px; box-shadow: 0 0 6px #4D96FF;"></span>
            <span><b>Areas</b> (Standards)</span>
          </div>
          <div style="display: flex; align-items: center; margin-bottom: 6px;">
            <span style="width: 12px; height: 12px; border-radius: 50%; background-color: #6BCB77; display: inline-block; margin-right: 10px; box-shadow: 0 0 6px #6BCB77;"></span>
            <span><b>Resources</b> (Guides)</span>
          </div>
          <div style="display: flex; align-items: center; margin-bottom: 10px;">
            <span style="width: 12px; height: 12px; border-radius: 50%; background-color: #9D9D9D; display: inline-block; margin-right: 10px; box-shadow: 0 0 6px #9D9D9D;"></span>
            <span><b>Archives</b> (Inactive)</span>
          </div>
          <div style="border-top: 1px solid rgba(255,255,255,0.1); margin-top: 8px; padding-top: 8px;">
            <div style="font-weight: 600; font-size: 11px; color: #A0AEC0; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px;">Link Similarity (Opacity)</div>
            <div style="display: flex; align-items: center; justify-content: space-between; font-size: 11px; color: #CBD5E0;">
              <span style="opacity: 0.4;">Low (0.50)</span>
              <div style="height: 4px; flex-grow: 1; margin: 0 8px; background: linear-gradient(to right, rgba(160,174,192,0.2), rgba(77,150,255,0.95)); border-radius: 2px;"></div>
              <span style="font-weight: 600; color: #4D96FF;">High (1.00)</span>
            </div>
          </div>
        </div>
        """

        # Inject legend before closing </body> tag
        if "</body>" in html_content:
            html_content = html_content.replace("</body>", f"{legend_html}\n</body>")
        else:
            html_content += legend_html

        output_path.write_text(html_content, encoding="utf-8")
        print(f"[OK] Interactive PyVis graph exported to '{output_path}'.")
        return html_content
    except Exception as e:
        print(f"[Error] Failed to render PyVis graph HTML: {e}", file=sys.stderr)
        return ""


def main():
    print("\n==========================================")
    print("  PHASE 4: Graph Data Model & Visualizer")
    print("==========================================")

    graph_data = generate_graph_data()
    render_interactive_graph(graph_data)

    print(f"\n--- Graph Engine Summary ---")
    print(f"Total Nodes Processed : {len(graph_data['nodes'])}")
    print(f"Total Connections     : {len(graph_data['edges'])}")
    print("==========================================\n")


if __name__ == "__main__":
    main()
