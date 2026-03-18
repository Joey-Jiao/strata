VENUE_SHORT = {
    "Neural Information Processing Systems": "NeurIPS",
    "International Conference on Machine Learning": "ICML",
    "International Conference on Learning Representations": "ICLR",
    "AAAI Conference on Artificial Intelligence": "AAAI",
    "Computer Vision and Pattern Recognition": "CVPR",
    "Annual Meeting of the Association for Computational Linguistics": "ACL",
    "Knowledge Discovery and Data Mining": "KDD",
    "Annual International ACM SIGIR Conference on Research and Development in Information Retrieval": "SIGIR",
    "Proceedings of the VLDB Endowment": "VLDB",
    "The Web Conference": "WWW",
    "IEEE International Conference on Data Engineering": "ICDE",
}


def short_venue(venue: str | None) -> str:
    if not venue:
        return ""
    return VENUE_SHORT.get(venue, venue[:15])
