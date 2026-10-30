from __future__ import annotations

import re

from .models import Song

_SPLIT_EXTRAS = re.compile(r"\s[-(\[]|\s(?:feat|ft)\.?\s", re.IGNORECASE)
_WORDS = re.compile(r"[a-z0-9]+")


def _words(text: str) -> set[str]:
    return set(_WORDS.findall(text.lower()))


def main_title(title: str) -> str:
    """'Song (Remastered 2011) - Live' -> 'Song'. Drops featured artists too."""
    return _SPLIT_EXTRAS.split(title, maxsplit=1)[0].strip()


def title_matches(candidate: str, song: Song) -> bool:
    """True when every word of the song's main title appears in a search result.

    ISRC searches on YouTube are usually spot on, but now and then they return
    an unrelated upload that happens to mention the code. This filters those out.
    """
    wanted = _words(main_title(song.title))
    return bool(wanted) and wanted <= _words(candidate)


def search_queries(song: Song, *, sources: tuple[str, ...] = ("ytsearch", "ytmsearch", "scsearch")) -> list[str]:
    """Lavalink identifiers to try, best first.

    An exact ISRC search comes first when the song has one, then plain text
    searches on each source. Feed them to your node one by one and stop at the
    first that returns something title_matches accepts.
    """
    queries: list[str] = []
    if song.isrc and "ytsearch" in sources:
        queries.append(f'ytsearch:"{song.isrc}"')
    queries.extend(f"{source}:{song.query}" for source in sources if source != "ytsearch" or not song.isrc)
    return queries
