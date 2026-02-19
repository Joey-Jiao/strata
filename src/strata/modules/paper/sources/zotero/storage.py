import shutil
from pathlib import Path

from ...models import ZoteroItem, Attachment


class ZoteroStorageManager:
    def __init__(self, storage_dir: Path | str):
        self._storage_dir = Path(storage_dir).expanduser()

    def get_attachment_path(self, attachment: Attachment) -> Path | None:
        if not attachment.key or not attachment.path:
            return None
        full_path = self._storage_dir / attachment.key / attachment.path
        return full_path if full_path.exists() else None

    def get_pdf_path(self, item: ZoteroItem) -> Path | None:
        for att in item.attachments:
            if att.content_type == "application/pdf" or att.path.lower().endswith(".pdf"):
                path = self.get_attachment_path(att)
                if path:
                    return path
        return None

    def get_all_pdfs(self, item: ZoteroItem) -> list[Path]:
        pdfs = []
        for att in item.attachments:
            if att.content_type == "application/pdf" or att.path.lower().endswith(".pdf"):
                path = self.get_attachment_path(att)
                if path:
                    pdfs.append(path)
        return pdfs

    def copy_pdf(self, item: ZoteroItem, dest_dir: Path | str, filename: str | None = None) -> Path | None:
        pdf_path = self.get_pdf_path(item)
        if not pdf_path:
            return None
        dest_dir = Path(dest_dir).expanduser()
        dest_dir.mkdir(parents=True, exist_ok=True)
        if filename:
            if not filename.lower().endswith(".pdf"):
                filename = f"{filename}.pdf"
            dest_path = dest_dir / filename
        else:
            dest_path = dest_dir / pdf_path.name
        shutil.copy2(pdf_path, dest_path)
        return dest_path

    def archive_pdf(self, item: ZoteroItem, dest_dir: Path | str) -> Path | None:
        filename = item.citation_key or item.key
        return self.copy_pdf(item, dest_dir, filename)

    def archive_all_pdfs(
        self,
        items: list[ZoteroItem],
        dest_dir: Path | str,
    ) -> dict[str, Path | None]:
        return {item.key: self.archive_pdf(item, dest_dir) for item in items}
