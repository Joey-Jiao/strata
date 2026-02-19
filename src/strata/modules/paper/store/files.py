import os
import shutil
import tempfile
from pathlib import Path


class PaperFiles:
    def __init__(self, files_dir: Path | str):
        self._files_dir = Path(files_dir).expanduser()
        self._files_dir.mkdir(parents=True, exist_ok=True)

    def _paper_dir(self, citation_key: str) -> Path:
        return self._files_dir / citation_key

    def get_path(self, citation_key: str) -> Path:
        return self._paper_dir(citation_key) / "paper.pdf"

    def exists(self, citation_key: str) -> bool:
        return self.get_path(citation_key).exists()

    def store(self, source_path: Path | str, citation_key: str) -> str:
        source_path = Path(source_path)
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
        paper_dir = self._paper_dir(citation_key)
        paper_dir.mkdir(parents=True, exist_ok=True)
        dest_path = paper_dir / "paper.pdf"
        fd, tmp_path = tempfile.mkstemp(dir=paper_dir, suffix=".tmp")
        try:
            os.close(fd)
            shutil.copy2(source_path, tmp_path)
            os.rename(tmp_path, dest_path)
        except:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise
        return f"{citation_key}/paper.pdf"

    def rename(self, old_key: str, new_key: str) -> str | None:
        old_dir = self._paper_dir(old_key)
        if not old_dir.exists():
            return None
        new_dir = self._paper_dir(new_key)
        os.rename(old_dir, new_dir)
        return f"{new_key}/paper.pdf"

    def delete(self, citation_key: str) -> bool:
        paper_dir = self._paper_dir(citation_key)
        if paper_dir.exists():
            shutil.rmtree(paper_dir)
            return True
        return False

    def list_folders(self) -> list[str]:
        return [
            d.name for d in self._files_dir.iterdir()
            if d.is_dir() and (d / "paper.pdf").exists()
        ]

    def delete_all(self) -> int:
        count = 0
        for d in self._files_dir.iterdir():
            if d.is_dir():
                shutil.rmtree(d)
                count += 1
        return count
