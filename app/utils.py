import hashlib


def make_content_hash(title: str, url: str = "") -> str:
    """
    Hash for news deduplication.
    The news items with the same title and url have the same hash.
    """
    raw = f"{title.lower().strip()}|{url.lower().strip()}"
    return hashlib.md5(raw.encode()).hexdigest()
