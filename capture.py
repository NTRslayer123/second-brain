#!/usr/bin/env python3
"""
SecondSelf — Capture Engine (Week 1: The Archivist)
Ingests text notes, URLs, and local files (TXT, MD, PDF), generates a unique ID + ISO timestamp,
and persists raw payloads into raw/{capture_id}/ with separate metadata.json and content.md files.
"""

import os
import sys
import json
import uuid
import datetime
import urllib.parse
from pathlib import Path

# Optional third-party imports with fallback handling
try:
    import trafilatura  # type: ignore # pyrefly: ignore [missing-import]
except ImportError:
    trafilatura = None

try:
    import requests  # type: ignore # pyrefly: ignore [missing-import]
    from bs4 import BeautifulSoup  # type: ignore # pyrefly: ignore [missing-import]
except ImportError:
    requests = None
    BeautifulSoup = None

try:
    from pypdf import PdfReader  # type: ignore # pyrefly: ignore [missing-import]
except ImportError:
    PdfReader = None

# Base directories
BASE_DIR = Path(__file__).parent.resolve()
RAW_DIR = BASE_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)


def generate_capture_id() -> tuple[str, str]:
    """Generates a unique ID in format YYYYMMDD_HHMMSS_{short_uuid} and an ISO timestamp."""
    now = datetime.datetime.now(datetime.timezone.utc)
    timestamp_str = now.strftime("%Y%m%d_%H%M%S")
    iso_timestamp = now.isoformat()
    short_uuid = uuid.uuid4().hex[:6]
    capture_id = f"{timestamp_str}_{short_uuid}"
    return capture_id, iso_timestamp


def is_url(text: str) -> bool:
    """Checks if a string is a valid HTTP/HTTPS URL."""
    text = text.strip()
    if not (text.startswith("http://") or text.startswith("https://")):
        return False
    try:
        result = urllib.parse.urlparse(text)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def is_existing_file(text: str) -> bool:
    """Checks if a string points to an existing file on disk."""
    try:
        p = Path(text.strip())
        return p.exists() and p.is_file()
    except Exception:
        return False


def extract_url_content(url: str) -> tuple[str, str]:
    """
    Scrapes primary body text and title from a web URL using trafilatura or requests/BeautifulSoup.
    Returns (title, body_text).
    """
    url = url.strip()
    title = url
    text_content = ""

    # Strategy 1: Trafilatura
    if trafilatura is not None:
        try:
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                extracted = trafilatura.extract(downloaded, include_links=True, include_images=False)
                if extracted and len(extracted.strip()) > 50:
                    text_content = extracted.strip()
        except Exception as e:
            print(f"[Warning] Trafilatura fetch failed for {url}: {e}", file=sys.stderr)

    # Strategy 2: Fallback to Requests + BeautifulSoup
    if not text_content and requests is not None:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                
                # Extract title
                if soup.title and soup.title.string:
                    title = soup.title.string.strip()
                
                # Remove scripts and styles
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()
                
                paragraphs = [p.get_text().strip() for p in soup.find_all(["p", "h1", "h2", "h3", "li"])]
                text_content = "\n\n".join([p for p in paragraphs if p])
        except Exception as e:
            print(f"[Warning] Requests fetch failed for {url}: {e}", file=sys.stderr)

    # Fallback if scraping yielded nothing
    if not text_content:
        text_content = f"Bookmark capture for URL: {url}\n(Content could not be automatically scraped or requires authentication)."

    return title, text_content


def extract_file_content(filepath_str: str) -> tuple[str, str, str]:
    """
    Extracts text content, filename, and absolute source path from a local file (TXT, MD, PDF).
    Returns (title, body_text, absolute_source_path).
    """
    p = Path(filepath_str.strip()).resolve()
    title = p.name
    source_path = str(p)
    content = ""

    if not p.exists():
        raise FileNotFoundError(f"File not found: {filepath_str}")

    suffix = p.suffix.lower()

    if suffix == ".pdf":
        if PdfReader is None:
            raise ImportError("pypdf package is required to read PDF files.")
        try:
            reader = PdfReader(str(p))
            page_texts = []
            for i, page in enumerate(reader.pages):
                extracted = page.extract_text()
                if extracted:
                    page_texts.append(extracted)
            content = "\n\n".join(page_texts)
        except Exception as e:
            content = f"Error reading PDF file {p.name}: {e}"
    else:
        # Text, Markdown, JSON, Code files
        encodings = ["utf-8", "latin-1", "cp1252"]
        for enc in encodings:
            try:
                content = p.read_text(encoding=enc)
                break
            except Exception:
                continue

    if not content:
        content = f"Empty or unreadable file: {p.name}"

    return title, content, source_path


def capture(input_str: str, source_type: str = "auto") -> dict:
    """
    Core entrypoint for capturing notes, URLs, or files.
    Standardizes payload, assigns unique ID + ISO timestamp, and writes to raw/{capture_id}/
    containing separate metadata.json and content.md.
    """
    cleaned_input = input_str.strip()
    if not cleaned_input:
        raise ValueError("Capture input cannot be empty.")

    # Auto-detect source type if requested
    if source_type == "auto":
        if is_url(cleaned_input):
            source_type = "link"
        elif is_existing_file(cleaned_input):
            source_type = "file"
        else:
            source_type = "note"

    capture_id, iso_timestamp = generate_capture_id()
    title = ""
    raw_content = ""
    source = ""

    if source_type == "link":
        source = cleaned_input
        title, raw_content = extract_url_content(cleaned_input)
    elif source_type == "file":
        title, raw_content, source = extract_file_content(cleaned_input)
    else:
        # Plain note
        source_type = "note"
        source = "CLI / User Note"
        raw_content = cleaned_input
        # Derive title from first line or first 60 chars
        first_line = cleaned_input.split("\n")[0].strip()
        title = first_line[:60] if len(first_line) > 60 else first_line

    # Create dedicated subfolder in raw/{capture_id}/
    capture_dir = RAW_DIR / capture_id
    capture_dir.mkdir(parents=True, exist_ok=True)

    metadata_payload = {
        "id": capture_id,
        "timestamp": iso_timestamp,
        "type": source_type,
        "source": source,
        "title": title,
        "char_count": len(raw_content),
        "content_file": "content.md",
        "captured_via": "capture.py"
    }

    metadata_path = capture_dir / "metadata.json"
    content_path = capture_dir / "content.md"

    # Save metadata.json
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata_payload, f, indent=2, ensure_ascii=False)

    # Save content.md
    with open(content_path, "w", encoding="utf-8") as f:
        f.write(raw_content)

    print(f"[OK] Successfully captured [{source_type.upper()}] ID: {capture_id}")
    print(f"     -> Metadata: raw/{capture_id}/metadata.json")
    print(f"     -> Content:  raw/{capture_id}/content.md")

    return {
        "metadata": metadata_payload,
        "content": raw_content,
        "dir": str(capture_dir)
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python capture.py <text_note | URL | filepath> [source_type]")
        sys.argv.append("https://news.ycombinator.com") # Sample fallback run if executed without args

    input_arg = sys.argv[1]
    stype = sys.argv[2] if len(sys.argv) > 2 else "auto"
    capture(input_arg, stype)


if __name__ == "__main__":
    main()
