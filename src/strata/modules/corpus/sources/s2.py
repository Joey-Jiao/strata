import time

import httpx
from tqdm import tqdm

from ..common.models import CorpusPaper
from ..store.repository import CorpusRepository

S2_BULK_URL = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"
S2_FIELDS = "paperId,title,authors,abstract,year,venue,externalIds,citationCount,openAccessPdf,publicationDate"


class S2Importer:
    def __init__(self, repo: CorpusRepository, api_key: str | None = None, timeout: int = 60):
        self._repo = repo
        self._timeout = timeout
        self._headers = {}
        if api_key:
            self._headers["x-api-key"] = api_key

    def import_venue_year(self, venue: str, year: int) -> int:
        imported = 0
        token = None
        pbar = None

        while True:
            params = {"venue": venue, "year": str(year), "fields": S2_FIELDS}
            if token:
                params["token"] = token

            for attempt in range(5):
                delay = 60 * (2 ** attempt)
                try:
                    resp = httpx.get(S2_BULK_URL, params=params, headers=self._headers, timeout=self._timeout)
                except httpx.TimeoutException:
                    time.sleep(delay)
                    continue
                if resp.status_code in (429, 500, 502, 503, 504):
                    time.sleep(delay)
                    continue
                resp.raise_for_status()
                break
            else:
                break

            data = resp.json()
            raw_papers = data.get("data") or []
            if not raw_papers:
                break

            if pbar is None:
                total = data.get("total", len(raw_papers))
                pbar = tqdm(total=total, desc=f"{venue} {year}")

            papers = [CorpusPaper.from_s2_response(d) for d in raw_papers]
            self._repo.upsert_batch(papers)
            imported += len(papers)
            pbar.update(len(papers))

            token = data.get("token")
            if not token:
                break

        if pbar:
            pbar.close()

        self._repo.rebuild_fts()
        return imported
