import time
import httpx
from strata.base.configs import ConfigService
from strata.modules.corpus.common.models import CorpusPaper
from strata.modules.corpus.common.venues import all_s2_venues
from strata.modules.corpus import create_store

S2_BULK_URL = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"
S2_FIELDS = "paperId,title,authors,abstract,year,venue,externalIds,citationCount,openAccessPdf,publicationDate"
BASE_DELAY = 60
MAX_RETRIES = 5

YEARS = range(2016, 2027)


def s2_request(params, headers, max_retries=MAX_RETRIES):
    for attempt in range(max_retries):
        delay = BASE_DELAY * (2 ** attempt)
        try:
            resp = httpx.get(S2_BULK_URL, params=params, headers=headers, timeout=60.0)
        except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as e:
            print(f"  network error: {e.__class__.__name__}, retry {attempt+1}/{max_retries} after {delay}s...", flush=True)
            time.sleep(delay)
            continue
        if resp.status_code in (429, 500, 502, 503, 504):
            print(f"  {resp.status_code}, retry {attempt+1}/{max_retries} after {delay}s...", flush=True)
            time.sleep(delay)
            continue
        resp.raise_for_status()
        return resp.json()
    return None


def check_existing(conn, venue_s2, year):
    probe = s2_request({"venue": venue_s2, "year": str(year), "fields": "venue"}, {}, max_retries=2)
    if not probe or not probe.get("data"):
        return False, 0
    full_venue = probe["data"][0].get("venue", "")
    if not full_venue:
        return False, 0
    count = conn.execute(
        "SELECT COUNT(*) FROM papers WHERE venue = ? AND year = ?",
        (full_venue, year),
    ).fetchone()[0]
    return count > 0, count


def fetch_venue_year(venue, year, repo, headers):
    token = None
    imported = 0

    while True:
        params = {"venue": venue, "year": str(year), "fields": S2_FIELDS}
        if token:
            params["token"] = token

        print(f"  requesting (imported so far: {imported})...", flush=True)
        data = s2_request(params, headers)
        if not data:
            print(f"  failed, skipping", flush=True)
            break

        raw_papers = data.get("data") or []
        if not raw_papers:
            break

        papers = [CorpusPaper.from_s2_response(d) for d in raw_papers]
        repo.upsert_batch(papers)
        imported += len(papers)

        total = data.get("total", "?")
        print(f"  {imported}/{total}", flush=True)

        token = data.get("token")
        if not token:
            break

        print(f"  waiting {BASE_DELAY}s...", flush=True)
        time.sleep(BASE_DELAY)

    return imported


def main():
    config = ConfigService()
    db, repo = create_store(config)
    api_key = config.get("corpus.s2.api_key", None)
    headers = {}
    if api_key:
        headers["x-api-key"] = api_key

    conn = db.connection()
    existing_count = conn.execute("SELECT COUNT(*) FROM papers").fetchone()[0]

    s2_venues = all_s2_venues()
    jobs = [(v, y) for v in s2_venues for y in YEARS]

    print(f"Existing papers in DB: {existing_count}")
    print(f"Jobs: {len(jobs)} ({len(s2_venues)} venues x {len(list(YEARS))} years)")
    print(f"Delay: {BASE_DELAY}s\n")

    total_imported = 0
    skipped = 0
    for i, (venue, year) in enumerate(jobs):
        exists, count = check_existing(conn, venue, year)
        if exists:
            print(f"[{i+1}/{len(jobs)}] {venue} {year} — skipped ({count} exist)", flush=True)
            skipped += 1
            time.sleep(3)
            continue

        print(f"[{i+1}/{len(jobs)}] {venue} {year}", flush=True)
        imported = fetch_venue_year(venue, year, repo, headers)
        total_imported += imported
        print(f"  done: {imported} papers (total new: {total_imported})\n", flush=True)

        if i < len(jobs) - 1 and imported > 0:
            time.sleep(BASE_DELAY)

    repo.rebuild_fts()
    db.close()
    print(f"\nComplete. Imported: {total_imported}, skipped: {skipped}")


if __name__ == "__main__":
    main()
