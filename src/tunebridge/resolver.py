from __future__ import annotations

import html
import re
from typing import Any, Protocol

import aiohttp

from .errors import NotFound, ServiceUnavailable, UnsupportedLink
from .links import is_short_link, parse_link
from .models import Collection, Kind, Link, Service, Song

DEFAULT_USER_AGENT = "tunebridge (+https://github.com/qizox/tunebridge)"
_OG_TITLE = re.compile(r'property="og:title" content="([^"]*)"')
_ISRC = re.compile(r'"isrcCode":"([A-Z0-9]{12})"')


class Fetcher(Protocol):
    async def get(self, url: str, *, json: bool) -> Any:
        """Return parsed JSON or text, None on 404, raise ServiceUnavailable otherwise."""

    async def expand(self, url: str) -> str:
        """Follow redirects and return the final URL."""


class AiohttpFetcher:
    def __init__(self, session: aiohttp.ClientSession, *, user_agent: str = DEFAULT_USER_AGENT, timeout: float = 8):
        self._session = session
        self._headers = {"User-Agent": user_agent}
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    async def get(self, url: str, *, json: bool) -> Any:
        try:
            async with self._session.get(url, headers=self._headers, timeout=self._timeout) as resp:
                if resp.status == 404:
                    return None
                if resp.status != 200:
                    raise ServiceUnavailable("That service didn't answer properly, try again in a moment.")
                return await resp.json(content_type=None) if json else await resp.text()
        except (aiohttp.ClientError, TimeoutError) as exc:
            raise ServiceUnavailable("That service didn't answer, try again in a moment.") from exc

    async def expand(self, url: str) -> str:
        try:
            async with self._session.get(url, headers=self._headers, timeout=self._timeout, allow_redirects=True) as resp:
                return str(resp.url)
        except (aiohttp.ClientError, TimeoutError) as exc:
            raise ServiceUnavailable("Couldn't open that short link.") from exc


class Resolver:
    """Turns Deezer and TIDAL links into songs you can search for elsewhere.

    Use it as an async context manager, or pass your own aiohttp session or
    Fetcher if your app already has one.
    """

    def __init__(
        self,
        session: aiohttp.ClientSession | None = None,
        *,
        fetcher: Fetcher | None = None,
        limit: int = 50,
        user_agent: str = DEFAULT_USER_AGENT,
    ):
        self.limit = limit
        self._own_session: aiohttp.ClientSession | None = None
        if fetcher is not None:
            self._fetcher = fetcher
        else:
            if session is None:
                session = self._own_session = aiohttp.ClientSession()
            self._fetcher = AiohttpFetcher(session, user_agent=user_agent)

    async def __aenter__(self) -> Resolver:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    async def close(self) -> None:
        if self._own_session is not None:
            await self._own_session.close()
            self._own_session = None

    async def resolve(self, url: str) -> Collection:
        url = url.strip()
        if is_short_link(url):
            url = await self._fetcher.expand(url)
        link = parse_link(url)
        if link is None:
            raise UnsupportedLink("That link isn't a Deezer or TIDAL link.")
        if link.service is Service.DEEZER:
            return await self._deezer(link)
        return await self._tidal(link)

    async def _deezer(self, link: Link) -> Collection:
        base = f"https://api.deezer.com/{link.kind.value}/{link.id}"
        info = await self._fetcher.get(base, json=True)
        if not info or "error" in info:
            raise NotFound(f"That Deezer {link.kind.value} doesn't exist or isn't public.")
        if link.kind is Kind.TRACK:
            song = _deezer_song(info)
            return Collection(song.query, link, [song])

        fallback_artist = (info.get("artist") or {}).get("name", "") if link.kind is Kind.ALBUM else ""
        songs: list[Song] = []
        page: str | None = f"{base}/tracks?limit={min(self.limit, 100)}"
        while page and len(songs) < self.limit:
            listing = await self._fetcher.get(page, json=True) or {}
            for item in listing.get("data", []):
                if item.get("readable", True):
                    songs.append(_deezer_song(item, fallback_artist))
            page = listing.get("next")
        songs = songs[: self.limit]
        if not songs:
            raise NotFound(f"That Deezer {link.kind.value} has no playable songs.")
        return Collection(info.get("title") or link.kind.value, link, songs)

    async def _tidal(self, link: Link) -> Collection:
        if link.kind is not Kind.TRACK:
            raise UnsupportedLink("Only single TIDAL tracks can be read without a TIDAL API key.")
        page = await self._fetcher.get(f"https://tidal.com/browse/track/{link.id}", json=False)
        title = _OG_TITLE.search(page or "")
        if not page or not title or title.group(1).startswith("Not Found"):
            raise NotFound("That TIDAL track doesn't exist or isn't available.")
        isrc = _ISRC.search(page)
        name = html.unescape(title.group(1))
        artist, _, track = name.partition(" - ")
        if not track:
            artist, track = "", name
        song = Song(title=track, artist=artist, isrc=isrc.group(1) if isrc else None)
        return Collection(name, link, [song])


def _deezer_song(item: dict[str, Any], fallback_artist: str = "") -> Song:
    duration = item.get("duration")
    return Song(
        title=item.get("title") or "",
        artist=(item.get("artist") or {}).get("name") or fallback_artist,
        isrc=item.get("isrc") or None,
        duration_ms=int(duration) * 1000 if duration else None,
    )


async def resolve(url: str, **kwargs: Any) -> Collection:
    """One-off helper: resolve a single link with a temporary session."""
    async with Resolver(**kwargs) as resolver:
        return await resolver.resolve(url)
