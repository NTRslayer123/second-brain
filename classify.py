#!/usr/bin/env python3
"""
SecondSelf — Autonomous Classifier (Phase 2)
Leverages Groq API (llama-3.1-8b-instant) to auto-classify raw captures into PARA categories
(Projects, Areas, Resources, Archives), extract relevant tags, generate a concise summary,
and write structured Markdown files to wiki/ with standard YAML frontmatter.
"""

import os
import sys
import json
import re
import tempfile
from pathlib import Path

# Load environment variables from .env if python-dotenv is installed
try:
    # pyrefly: ignore [missing-import]
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except ImportError:
    pass

# Try importing groq client
try:
    # pyrefly: ignore [missing-import]
    import groq  # type: ignore
except ImportError:
    groq = None

# Base directories
BASE_DIR = Path(__file__).parent.resolve()
RAW_DIR = BASE_DIR / "raw"
WIKI_DIR = BASE_DIR / "wiki"

# Ensure target wiki directory exists
WIKI_DIR.mkdir(parents=True, exist_ok=True)

# Valid PARA Categories
VALID_PARA_CATEGORIES = {"Projects", "Areas", "Resources", "Archives"}
DEFAULT_CATEGORY = "Resources"
MODEL_NAME = "llama-3.1-8b-instant"


def get_groq_client():
    """Initializes and returns Groq client using GROQ_API_KEY from environment."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("[Warning] GROQ_API_KEY is not set in environment or .env file.", file=sys.stderr)
        return None

    if groq is None:
        print("[Warning] 'groq' python package is not installed.", file=sys.stderr)
        return None

    try:
        return groq.Groq(api_key=api_key)
    except Exception as e:
        print(f"[Warning] Failed to initialize Groq client: {e}", file=sys.stderr)
        return None


def clean_json_response(response_text: str) -> str:
    """Strips markdown block wrappers ```json ... ``` from LLM response text."""
    text = response_text.strip()
    # Pattern to extract inside ```json ... ``` or ``` ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text


def classify_raw_content(raw_text: str, raw_title: str = "") -> dict:
    """
    Sends raw text content to Groq API (llama-3.1-8b-instant) for autonomous PARA classification,
    tag extraction, and summary generation. Returns structured metadata dictionary.
    """
    # Defensive check for empty content
    cleaned_text = raw_text.strip() if raw_text else ""
    if not cleaned_text:
        return {
            "title": raw_title.strip() or "Untitled Empty Note",
            "category": DEFAULT_CATEGORY,
            "tags": ["empty-note"],
            "summary": "Empty note payload ingested.",
        }

    # Truncate content if excessively long (~15k characters max to stay safely within context budget)
    max_chars = 15000
    truncated_text = cleaned_text[:max_chars]
    if len(cleaned_text) > max_chars:
        truncated_text += "\n\n[Content truncated for classification prompt]"

    client = get_groq_client()

    # Fallback response generator
    def build_fallback_dict(reason: str) -> dict:
        fallback_title = raw_title.strip() if raw_title.strip() else truncated_text.split("\n")[0][:60].strip()
        first_snippet = truncated_text.replace("\n", " ").strip()
        summary_snippet = (first_snippet[:150] + "...") if len(first_snippet) > 150 else first_snippet
        print(f"[Notice] Using classification fallback ({reason}).", file=sys.stderr)
        return {
            "title": fallback_title or "Untitled Capture",
            "category": DEFAULT_CATEGORY,
            "tags": ["uncategorized"],
            "summary": summary_snippet or "No summary available.",
        }

    if not client:
        return build_fallback_dict("Groq client unavailable")

    system_prompt = (
        "You are SecondSelf, an AI personal knowledge classifier operating under the PARA framework.\n"
        "Analyze the provided text note, article, or document capture and classify it strictly into one of four PARA categories:\n"
        "- Projects: Goal-oriented tasks or active initiatives with clear outcomes and/or deadlines.\n"
        "- Areas: Ongoing standards, domains, or responsibilities to maintain over time without explicit deadlines (e.g., Health, Finance, Career).\n"
        "- Resources: Topics of general interest, reference materials, guides, tutorials, documentation, code snippets, or articles.\n"
        "- Archives: Inactive, completed, or historic reference material from Projects, Areas, or Resources.\n\n"
        "Return ONLY a single valid JSON object containing exactly these fields:\n"
        "{\n"
        '  "title": "A concise, descriptive title representing the document",\n'
        '  "category": "Projects | Areas | Resources | Archives",\n'
        '  "tags": ["lowercase-tag1", "lowercase-tag2", "lowercase-tag3"],\n'
        '  "summary": "A 1-2 sentence concise summary of the core insight or content."\n'
        "}\n"
        "Do NOT include any commentary, explanations, or text outside the JSON object."
    )

    user_prompt = f"Raw Title (Optional): {raw_title}\n\nContent:\n{truncated_text}"

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=400,
        )

        response_content = completion.choices[0].message.content
        cleaned_json_str = clean_json_response(response_content)
        parsed = json.loads(cleaned_json_str)

        # Validate and normalize category
        cat = str(parsed.get("category", "")).strip().capitalize()
        if cat not in VALID_PARA_CATEGORIES:
            cat = DEFAULT_CATEGORY

        # Validate title
        title = str(parsed.get("title", "")).strip()
        if not title:
            title = raw_title.strip() or "Untitled Document"

        # Validate tags
        raw_tags = parsed.get("tags", [])
        if isinstance(raw_tags, list):
            tags = [str(t).strip().lower().replace(" ", "-") for t in raw_tags if str(t).strip()]
        else:
            tags = ["uncategorized"]
        if not tags:
            tags = ["uncategorized"]

        # Validate summary
        summary = str(parsed.get("summary", "")).strip()
        if not summary:
            first_snippet = truncated_text.replace("\n", " ").strip()
            summary = (first_snippet[:150] + "...") if len(first_snippet) > 150 else first_snippet

        return {
            "title": title,
            "category": cat,
            "tags": tags,
            "summary": summary,
        }

    except Exception as e:
        return build_fallback_dict(f"API call error: {e}")


def load_raw_item(raw_item_path: Path) -> tuple[dict, str]:
    """
    Loads raw metadata and content text from a raw capture path.
    Supports either a directory path raw/{capture_id}/ or a metadata/json file path.
    """
    raw_item_path = Path(raw_item_path).resolve()
    metadata = {}
    content_text = ""

    if raw_item_path.is_dir():
        capture_id = raw_item_path.name
        metadata_file = raw_item_path / "metadata.json"
        content_file = raw_item_path / "content.md"

        if metadata_file.exists():
            try:
                metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        if content_file.exists():
            try:
                content_text = content_file.read_text(encoding="utf-8")
            except Exception:
                pass

        # Fallback if metadata missing
        if not metadata.get("id"):
            metadata["id"] = capture_id
        if not metadata.get("title"):
            metadata["title"] = capture_id
        if not metadata.get("timestamp"):
            metadata["timestamp"] = ""

    elif raw_item_path.is_file():
        if raw_item_path.name == "metadata.json":
            parent_dir = raw_item_path.parent
            return load_raw_item(parent_dir)

        elif raw_item_path.suffix.lower() == ".json":
            try:
                data = json.loads(raw_item_path.read_text(encoding="utf-8"))
                metadata = data.get("metadata", data)
                content_text = data.get("raw_content", data.get("content", ""))
            except Exception:
                pass
            if not metadata.get("id"):
                metadata["id"] = raw_item_path.stem

    return metadata, content_text


def format_yaml_value(val) -> str:
    """Formats values safely for YAML frontmatter block."""
    if isinstance(val, str):
        # Escape quotes inside double-quoted string
        escaped = val.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{escaped}"'
    elif isinstance(val, list):
        if not val:
            return "[]"
        formatted_items = [format_yaml_value(item) for item in val]
        return "[" + ", ".join(formatted_items) + "]"
    return str(val)


def process_raw_to_wiki(raw_path: str | Path) -> str:
    """
    Reads a raw capture from raw_path, invokes LLM classification,
    and writes structured Markdown with YAML frontmatter to wiki/{capture_id}.md.
    Returns the file path of the created wiki Markdown file.
    """
    path_obj = Path(raw_path).resolve()
    metadata, raw_content = load_raw_item(path_obj)

    capture_id = metadata.get("id") or path_obj.name
    timestamp = metadata.get("timestamp", "")
    raw_title = metadata.get("title", "")

    # Perform autonomous LLM classification
    classified = classify_raw_content(raw_content, raw_title=raw_title)

    title = classified["title"]
    category = classified["category"]
    tags = classified["tags"]
    summary = classified["summary"]

    # Construct YAML frontmatter
    frontmatter_lines = [
        "---",
        f"id: {format_yaml_value(capture_id)}",
        f"title: {format_yaml_value(title)}",
        f"category: {format_yaml_value(category)}",
        f"tags: {format_yaml_value(tags)}",
        f"summary: {format_yaml_value(summary)}",
        f"created_at: {format_yaml_value(timestamp)}",
        "auto_links: []",
        "---",
    ]
    frontmatter_str = "\n".join(frontmatter_lines)

    # Construct Markdown Body
    body_parts = [
        f"# {title}",
        "",
        f"> **Summary**: {summary}",
        "",
        "## Content",
        "",
        raw_content.strip() if raw_content else "*No raw content recorded.*",
    ]
    full_markdown = frontmatter_str + "\n\n" + "\n".join(body_parts) + "\n"

    # Target category directory: wiki/{category}/
    category_dir = WIKI_DIR / category
    category_dir.mkdir(parents=True, exist_ok=True)
    target_wiki_path = category_dir / f"{capture_id}.md"

    # Atomic file write to wiki/{category}/{capture_id}.md
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=category_dir, delete=False) as tf:
        tf.write(full_markdown)
        temp_name = tf.name

    os.replace(temp_name, target_wiki_path)

    print(f"[OK] Classified [{category}] '{title}' -> wiki/{category}/{capture_id}.md")
    return str(target_wiki_path)


def is_already_classified(capture_id: str) -> bool:
    """Checks if a markdown file for capture_id already exists in wiki/ or any wiki subfolder."""
    if not WIKI_DIR.exists():
        return False
    matches = list(WIKI_DIR.rglob(f"{capture_id}.md"))
    return len(matches) > 0


def organize_existing_wiki_files():
    """
    Scans root wiki/ directory for un-nested *.md files and moves them into
    their respective wiki/{category}/ subfolder based on their YAML frontmatter.
    """
    if not WIKI_DIR.exists():
        return

    root_md_files = [f for f in WIKI_DIR.iterdir() if f.is_file() and f.suffix.lower() == ".md"]
    if not root_md_files:
        return

    print(f"Organizing {len(root_md_files)} existing wiki notes into PARA category folders...")
    for md_file in root_md_files:
        try:
            content = md_file.read_text(encoding="utf-8")
            category = DEFAULT_CATEGORY
            match = re.search(r'^category:\s*"?( Projects|Areas|Resources|Archives)"?', content, re.MULTILINE | re.IGNORECASE)
            if match:
                found_cat = match.group(1).strip().capitalize()
                if found_cat in VALID_PARA_CATEGORIES:
                    category = found_cat
            
            cat_dir = WIKI_DIR / category
            cat_dir.mkdir(parents=True, exist_ok=True)
            target_path = cat_dir / md_file.name
            os.replace(str(md_file), str(target_path))
            print(f" -> Moved {md_file.name} to wiki/{category}/")
        except Exception as e:
            print(f"[Warning] Failed to move {md_file.name}: {e}", file=sys.stderr)


def batch_classify_all() -> list[str]:
    """
    Scans raw/ for unclassified captures and processes all missing items into wiki/{category}/*.md.
    Returns list of newly created wiki file paths.
    """
    # First, organize any existing un-nested wiki/*.md files
    organize_existing_wiki_files()

    if not RAW_DIR.exists():
        print(f"[Notice] Raw directory '{RAW_DIR}' does not exist.", file=sys.stderr)
        return []

    # Find raw capture folders or json files and group by capture_id
    raw_item_map = {}
    for item in RAW_DIR.iterdir():
        if item.name.startswith("."):
            continue
        if item.is_dir():
            cid = item.name
            if cid not in raw_item_map:
                raw_item_map[cid] = item
        elif item.is_file() and item.suffix.lower() == ".json" and item.name != "metadata.json":
            cid = item.stem
            # Prefer directory if present, otherwise file
            if cid not in raw_item_map or not raw_item_map[cid].is_dir():
                raw_item_map[cid] = item

    sorted_ids = sorted(raw_item_map.keys())
    created_files = []
    already_processed = 0

    print(f"Found {len(sorted_ids)} unique items in raw storage. Checking for unclassified notes...")

    for capture_id in sorted_ids:
        raw_item = raw_item_map[capture_id]

        if is_already_classified(capture_id):
            already_processed += 1
            continue

        try:
            wiki_file = process_raw_to_wiki(raw_item)
            created_files.append(wiki_file)
        except Exception as e:
            print(f"[Error] Failed to process {capture_id} ({raw_item.name}): {e}", file=sys.stderr)

    print(f"\n--- Batch Classification Complete ---")
    print(f"Total items evaluated : {len(sorted_ids)}")
    print(f"Already classified    : {already_processed}")
    print(f"Newly processed       : {len(created_files)}")
    return created_files


def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1].strip()
        # Resolve target capture path
        target_path = Path(arg)
        if not target_path.exists():
            # Try looking inside RAW_DIR
            target_path = RAW_DIR / arg
        if not target_path.exists():
            print(f"[Error] Raw capture path '{arg}' not found.", file=sys.stderr)
            sys.exit(1)
        process_raw_to_wiki(target_path)
    else:
        batch_classify_all()


if __name__ == "__main__":
    main()
