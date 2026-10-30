from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Service(str, Enum):
    DEEZER = "deezer"
    TIDAL = "tidal"


class Kind(str, Enum):
    TRACK = "track"
    ALBUM = "album"
    PLAYLIST = "playlist"


@dataclass(frozen=True)
class Link:
    """A parsed music link: which service, what kind of item and its id."""

    service: Service
    kind: Kind
    id: str


@dataclass(frozen=True)
class Song:
    """Everything needed to find a song somewhere else."""

    title: str
    artist: str = ""
    isrc: str | None = None
    duration_ms: int | None = None

    @property
    def query(self) -> str:
        """A plain "artist - title" search string."""
        return f"{self.artist} - {self.title}" if self.artist else self.title


@dataclass(frozen=True)
class Collection:
    """The result of resolving a link: one song, or an album/playlist of them."""

    name: str
    link: Link
    songs: list[Song] = field(default_factory=list)

    @property
    def is_single(self) -> bool:
        return self.link.kind is Kind.TRACK
