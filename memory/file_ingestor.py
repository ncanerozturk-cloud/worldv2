import os
import logging
import tempfile
from datetime import datetime
from typing import Optional

import requests

from memory.qdrant_client import QdrantMemory

log = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".csv"}


class FileIngestor:
    def __init__(self, memory: QdrantMemory):
        self.memory = memory

    def ingest_text(self, text: str, metadata: Optional[dict] = None) -> str:
        """Save raw text directly to Qdrant. Returns the point UUID."""
        base_metadata = {
            "type": "ingested_text",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "agent": "health_sport",
        }
        if metadata:
            base_metadata.update(metadata)

        point_id = self.memory.save(text=text, metadata=base_metadata)
        log.info(f"[INGEST] Saved text chunk ({len(text)} chars) → {point_id}")
        return point_id

    def ingest_pdf(self, file_path: str, metadata: Optional[dict] = None) -> int:
        """Extract text page-by-page from a PDF and save each page to Qdrant."""
        try:
            import pdfplumber
        except ImportError:
            raise RuntimeError("pdfplumber not installed. Run: pip install pdfplumber")

        base_metadata = {
            "type": "ingested_pdf",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "agent": "health_sport",
            "source_file": os.path.basename(file_path),
        }
        if metadata:
            base_metadata.update(metadata)

        saved = 0
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if not text or not text.strip():
                    continue
                page_metadata = {**base_metadata, "page": page_num}
                self.memory.save(text=text.strip(), metadata=page_metadata)
                saved += 1

        log.info(f"[INGEST] PDF '{os.path.basename(file_path)}' — {saved} pages saved to Qdrant")
        return saved

    def ingest_plain_file(self, file_path: str, metadata: Optional[dict] = None) -> int:
        """Read a plain text file and save it chunked by paragraph to Qdrant."""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        base_metadata = {
            "type": "ingested_file",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "agent": "health_sport",
            "source_file": os.path.basename(file_path),
        }
        if metadata:
            base_metadata.update(metadata)

        # Split on double newlines (paragraphs), filter empty chunks
        chunks = [c.strip() for c in content.split("\n\n") if c.strip()]
        for chunk in chunks:
            self.memory.save(text=chunk, metadata=base_metadata)

        log.info(f"[INGEST] File '{os.path.basename(file_path)}' — {len(chunks)} chunks saved")
        return len(chunks)

    def ingest_file(self, file_path: str, metadata: Optional[dict] = None) -> int:
        """Auto-detect file type and ingest accordingly."""
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            return self.ingest_pdf(file_path, metadata)
        elif ext in SUPPORTED_EXTENSIONS:
            return self.ingest_plain_file(file_path, metadata)
        else:
            raise ValueError(f"Unsupported file type: {ext}. Supported: {SUPPORTED_EXTENSIONS}")

    def ingest_from_slack(self, file_info: dict, bot_token: str) -> int:
        """
        Download a file from Slack and ingest it into Qdrant.

        Args:
            file_info: The 'file' dict from Slack's files.info API response.
            bot_token: Slack bot token for authenticated download.

        Returns:
            Number of chunks saved.
        """
        name = file_info.get("name", "unknown")
        mimetype = file_info.get("mimetype", "")
        url = file_info.get("url_private_download") or file_info.get("url_private")

        if not url:
            log.warning(f"[INGEST] No download URL for file '{name}'")
            return 0

        log.info(f"[INGEST] Downloading '{name}' from Slack...")
        response = requests.get(url, headers={"Authorization": f"Bearer {bot_token}"})
        response.raise_for_status()

        ext = os.path.splitext(name)[1].lower() or (
            ".pdf" if "pdf" in mimetype else ".txt"
        )

        metadata = {
            "source": "slack_upload",
            "file_name": name,
            "mimetype": mimetype,
        }

        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name

        try:
            count = self.ingest_file(tmp_path, metadata=metadata)
        finally:
            os.unlink(tmp_path)

        return count
