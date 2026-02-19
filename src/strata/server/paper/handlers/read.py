import base64

from mcp.types import TextContent, ImageContent

from strata.base.configs import ConfigService
from strata.modules.paper.export import BibTeXExporter
from strata.server.common import text, not_found
from ..helpers import get_components


def parse_page_range(pages_str: str, max_pages: int) -> list[int]:
    if not pages_str:
        return list(range(max_pages))

    result = []
    for part in pages_str.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            start = int(start.strip()) - 1
            end = int(end.strip())
            result.extend(range(start, min(end, max_pages)))
        else:
            page = int(part.strip()) - 1
            if 0 <= page < max_pages:
                result.append(page)
    return sorted(set(result))


def handle_read(config: ConfigService, arguments: dict) -> list[TextContent | ImageContent]:
    db, files, repo = get_components(config)
    try:
        key = arguments.get("key", "")
        mode = arguments.get("mode", "visual")
        pages_str = arguments.get("pages", "")

        paper = repo.get(key)
        if not paper:
            return not_found("Paper", key)
        if not paper.pdf_path:
            return text(f"No PDF available for: {key}")

        pdf_path = files.get_path(paper.citation_key)
        if not pdf_path.exists():
            return text(f"PDF file missing: {paper.pdf_path}")

        if mode == "path":
            return text(str(pdf_path))

        try:
            import fitz
        except ImportError:
            return text("PDF rendering requires pymupdf. Install with: pip install pymupdf")

        doc = fitz.open(str(pdf_path))
        page_indices = parse_page_range(pages_str, len(doc))

        if not page_indices:
            doc.close()
            return text("No valid pages specified.")

        result: list[TextContent | ImageContent] = []
        result.append(TextContent(
            type="text",
            text=f"Rendering {len(page_indices)} page(s) from: {paper.title}"
        ))

        for idx in page_indices:
            page = doc[idx]
            pix = page.get_pixmap(dpi=150)
            img_data = pix.tobytes("png")
            b64_data = base64.b64encode(img_data).decode("utf-8")
            result.append(ImageContent(
                type="image",
                data=b64_data,
                mimeType="image/png",
            ))

        doc.close()
        return result
    finally:
        db.close()


def handle_export(config: ConfigService, arguments: dict) -> list[TextContent]:
    db, files, repo = get_components(config)
    try:
        keys = arguments.get("keys", [])
        tag = arguments.get("tag")

        if tag:
            papers, _ = repo.find(tag=tag, limit=1000)
        elif keys:
            papers = [repo.get(k) for k in keys]
            papers = [p for p in papers if p]
        else:
            return text("Provide either keys or tag.")

        if not papers:
            return text("No papers found.")

        exporter = BibTeXExporter()
        bib = exporter.export_papers(papers)
        return text(bib)
    finally:
        db.close()


READ_HANDLERS = {
    "paper_read": handle_read,
    "paper_read_export": handle_export,
}
