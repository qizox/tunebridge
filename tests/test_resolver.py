import asyncio

import pytest

from tunebridge import Kind, NotFound, Resolver, UnsupportedLink


class FakeFetcher:
    def __init__(self, routes, redirects=None):
        self.routes = routes
        self.redirects = redirects or {}
        self.calls = []

    async def get(self, url, *, json):
        self.calls.append(url)
        return self.routes.get(url)

    async def expand(self, url):
        return self.redirects[url]


def run(fetcher, url, **kwargs):
    async def go():
        async with Resolver(fetcher=fetcher, **kwargs) as resolver:
            return await resolver.resolve(url)

    return asyncio.run(go())


def deezer_track(n, artist="Artist", isrc=True):
    return {
        "title": f"Song {n}",
        "artist": {"name": artist} if artist else None,
        "isrc": f"USAAA{n:07d}" if isrc else None,
        "duration": 200 + n,
    }


def test_deezer_track():
    fetcher = FakeFetcher({"https://api.deezer.com/track/1": deezer_track(1)})
    result = run(fetcher, "https://www.deezer.com/track/1")
    assert result.is_single
    assert result.name == "Artist - Song 1"
    [song] = result.songs
    assert (song.isrc, song.duration_ms) == ("USAAA0000001", 201_000)


def test_deezer_album_fills_missing_artist_and_paginates():
    base = "https://api.deezer.com/album/9"
    fetcher = FakeFetcher(
        {
            base: {"title": "The Album", "artist": {"name": "Band"}},
            f"{base}/tracks?limit=50": {"data": [deezer_track(1, artist=None), deezer_track(2)], "next": f"{base}/tracks?index=2"},
            f"{base}/tracks?index=2": {"data": [deezer_track(3), {**deezer_track(4), "readable": False}]},
        }
    )
    result = run(fetcher, "https://www.deezer.com/album/9")
    assert result.link.kind is Kind.ALBUM
    assert result.name == "The Album"
    assert [s.title for s in result.songs] == ["Song 1", "Song 2", "Song 3"]
    assert result.songs[0].artist == "Band"


def test_limit_caps_long_playlists():
    base = "https://api.deezer.com/playlist/5"
    fetcher = FakeFetcher(
        {
            base: {"title": "Big"},
            f"{base}/tracks?limit=2": {"data": [deezer_track(i) for i in range(5)], "next": f"{base}/tracks?index=5"},
        }
    )
    result = run(fetcher, "https://www.deezer.com/playlist/5", limit=2)
    assert len(result.songs) == 2
    assert f"{base}/tracks?index=5" not in fetcher.calls


def test_deezer_errors():
    fetcher = FakeFetcher({"https://api.deezer.com/track/2": {"error": {"code": 800}}})
    with pytest.raises(NotFound):
        run(fetcher, "https://www.deezer.com/track/2")
    with pytest.raises(NotFound):
        run(FakeFetcher({}), "https://www.deezer.com/track/3")


def test_short_link_is_expanded():
    fetcher = FakeFetcher(
        {"https://api.deezer.com/track/7": deezer_track(7)},
        redirects={"https://link.deezer.com/s/abc": "https://www.deezer.com/en/track/7?host=1"},
    )
    assert run(fetcher, "https://link.deezer.com/s/abc").songs[0].title == "Song 7"


def test_tidal_track_reads_title_and_isrc():
    page = '<meta property="og:title" content="Lieu - cant get out &amp; more" /> {"isrcCode":"QZAAA2400001"}'
    fetcher = FakeFetcher({"https://tidal.com/browse/track/42": page})
    [song] = run(fetcher, "https://tidal.com/browse/track/42").songs
    assert (song.artist, song.title) == ("Lieu", "cant get out & more")
    assert song.isrc == "QZAAA2400001"


def test_tidal_title_without_artist():
    page = '<meta property="og:title" content="Untitled" />'
    fetcher = FakeFetcher({"https://tidal.com/browse/track/43": page})
    [song] = run(fetcher, "https://tidal.com/browse/track/43").songs
    assert (song.artist, song.title, song.isrc) == ("", "Untitled", None)


def test_tidal_missing_and_collections():
    with pytest.raises(NotFound):
        run(FakeFetcher({}), "https://tidal.com/browse/track/1")
    with pytest.raises(UnsupportedLink):
        run(FakeFetcher({}), "https://tidal.com/browse/album/1")


def test_unsupported_link():
    with pytest.raises(UnsupportedLink):
        run(FakeFetcher({}), "https://open.spotify.com/track/1")
