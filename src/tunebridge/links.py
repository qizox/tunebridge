from __future__ import annotations

import re

from .models import Kind, Link, Service

DEEZER = re.compile(
    r"^https?://(?:www\.)?deezer\.com/(?:[a-z]{2}(?:-[a-z]{2})?/)?(track|album|playlist)/(\d+)",
    re.IGNORECASE,
)
DEEZER_SHORT = re.compile(r"^https?://(?:link\.deezer\.com|deezer\.page\.link|dzr\.page\.link)/", re.IGNORECASE)
TIDAL = re.compile(
    r"^https?://(?:www\.|listen\.)?tidal\.com/(?:browse/)?(track|album|playlist|mix|video)/([\w-]+)",
    re.IGNORECASE,
)


def is_short_link(url: str) -> bool:
    """Deezer share links (link.deezer.com/...) redirect to the real URL."""
    return bool(DEEZER_SHORT.match(url.strip()))


def is_supported(url: str) -> bool:
    url = url.strip()
    return bool(DEEZER.match(url) or DEEZER_SHORT.match(url) or TIDAL.match(url))


def parse_link(url: str) -> Link | None:
    """Parse a full Deezer or TIDAL URL. Short links return None until expanded."""
    url = url.strip()
    m = DEEZER.match(url)
    if m:
        return Link(Service.DEEZER, Kind(m.group(1).lower()), m.group(2))
    m = TIDAL.match(url)
    if m:
        kind = m.group(1).lower()
        if kind in ("mix", "video"):
            kind = "playlist" if kind == "mix" else "track"
        return Link(Service.TIDAL, Kind(kind), m.group(2))
    return None
