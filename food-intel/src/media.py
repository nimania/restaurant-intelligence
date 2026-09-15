from __future__ import annotations

import re
from urllib.parse import urlparse


def _https_url(value: str | None) -> str | None:
    if not value:
        return None
    value = str(value).strip()
    if value.startswith("//"):
        value = "https:" + value
    try:
        parsed = urlparse(value)
    except ValueError:
        return None
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return value


def _from_mapping_list(value, keys=("url", "href")) -> str | None:
    if not value:
        return None
    if isinstance(value, dict):
        value = [value]
    for row in value:
        if not hasattr(row, "get"):
            continue
        media_type = str(row.get("type") or row.get("medium") or "").lower()
        if media_type and "image" not in media_type and media_type not in {"photo"}:
            continue
        for key in keys:
            url = _https_url(row.get(key))
            if url:
                return url
    return None


def entry_image_url(entry) -> str | None:
    """Return a publisher-provided article image when the feed exposes one.

    No crawling is performed here. We only use media metadata already present in
    RSS/Atom (media:content, media:thumbnail, enclosure) or an <img> explicitly
    embedded in the feed summary/content.
    """
    for attr in ("media_content", "media_thumbnail"):
        url = _from_mapping_list(getattr(entry, attr, None))
        if url:
            return url

    url = _from_mapping_list(getattr(entry, "enclosures", None))
    if url:
        return url

    links = getattr(entry, "links", None) or []
    if isinstance(links, dict):
        links = [links]
    for link in links:
        if not hasattr(link, "get"):
            continue
        rel = str(link.get("rel") or "").lower()
        typ = str(link.get("type") or "").lower()
        if rel == "enclosure" and (not typ or "image" in typ):
            url = _https_url(link.get("href"))
            if url:
                return url

    html_candidates = [
        getattr(entry, "summary", ""),
        getattr(entry, "description", ""),
    ]
    for block in getattr(entry, "content", None) or []:
        if hasattr(block, "get"):
            html_candidates.append(block.get("value") or "")

    pattern = re.compile(r"<img[^>]+src=[\"']([^\"']+)[\"']", re.I)
    for raw in html_candidates:
        match = pattern.search(str(raw or ""))
        if match:
            url = _https_url(match.group(1))
            if url:
                return url
    return None
