import re

_ARXIV_PATTERNS = [
    re.compile(r"arxiv\.org/abs/(\d{4}\.\d{4,5}(?:v\d+)?)"),
    re.compile(r"arxiv\.org/pdf/(\d{4}\.\d{4,5}(?:v\d+)?)"),
    re.compile(r"arxiv\.org/abs/([a-z-]+/\d{7})"),
    re.compile(r"10\.48550/arXiv\.(\d{4}\.\d{4,5}(?:v\d+)?)"),
]

_VENUE_PATTERNS = [
    (re.compile(r"neural\s+information\s+processing|neurips|nips", re.I), "NeurIPS"),
    (re.compile(r"international\s+conference\s+on\s+machine\s+learning|(?<!\w)icml(?!\w)", re.I), "ICML"),
    (re.compile(r"international\s+conference\s+on\s+learning\s+representations|(?<!\w)iclr(?!\w)", re.I), "ICLR"),
    (re.compile(r"computer\s+vision\s+and\s+pattern\s+recognition|(?<!\w)cvpr(?!\w)", re.I), "CVPR"),
    (re.compile(r"international\s+conference\s+on\s+computer\s+vision(?!\s+and)|(?<!\w)iccv(?!\w)", re.I), "ICCV"),
    (re.compile(r"european\s+conference\s+on\s+computer\s+vision|(?<!\w)eccv(?!\w)", re.I), "ECCV"),
    (re.compile(r"association\s+for\s+computational\s+linguistics|(?<!\w)acl(?!\w)", re.I), "ACL"),
    (re.compile(r"empirical\s+methods\s+in\s+natural\s+language\s+processing|(?<!\w)emnlp(?!\w)", re.I), "EMNLP"),
    (re.compile(r"north\s+american.*computational\s+linguistics|(?<!\w)naacl(?!\w)", re.I), "NAACL"),
    (re.compile(r"association\s+for\s+the\s+advancement\s+of\s+artificial|(?<!\w)aaai(?!\w)", re.I), "AAAI"),
    (re.compile(r"knowledge\s+discovery.*data\s+mining|(?<!\w)kdd(?!\w)", re.I), "KDD"),
    (re.compile(r"international\s+conference\s+on\s+robotics\s+and\s+automation|(?<!\w)icra(?!\w)", re.I), "ICRA"),
    (re.compile(r"robotics.*science\s+and\s+systems|(?<!\w)rss(?!\w)", re.I), "RSS"),
    (re.compile(r"conference\s+on\s+robot\s+learning|(?<!\w)corl(?!\w)", re.I), "CoRL"),
    (re.compile(r"(?<!\w)ijcv(?!\w)|international\s+journal\s+of\s+computer\s+vision", re.I), "IJCV"),
    (re.compile(r"transactions\s+on\s+pattern\s+analysis.*machine\s+intelligence|(?<!\w)tpami(?!\w)|ieee\s+trans.*pami", re.I), "TPAMI"),
    (re.compile(r"transactions\s+on\s+neural\s+networks|(?<!\w)tnnls(?!\w)", re.I), "TNNLS"),
    (re.compile(r"journal\s+of\s+machine\s+learning\s+research|(?<!\w)jmlr(?!\w)", re.I), "JMLR"),
    (re.compile(r"(?<!\w)nature(?!\w)", re.I), "Nature"),
    (re.compile(r"(?<!\w)science(?!\w)", re.I), "Science"),
    (re.compile(r"(?<!\w)arxiv(?!\w)", re.I), "arXiv"),
]


def extract_arxiv_id(url: str | None, doi: str | None) -> str | None:
    for source in [url, doi]:
        if not source:
            continue
        for pattern in _ARXIV_PATTERNS:
            match = pattern.search(source)
            if match:
                return match.group(1)
    return None


def normalize_venue(journal: str | None, book_title: str | None) -> str | None:
    for source in [journal, book_title]:
        if not source:
            continue
        for pattern, venue in _VENUE_PATTERNS:
            if pattern.search(source):
                return venue
    return journal or book_title or None
