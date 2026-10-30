import pytest

from tunebridge import Kind, Service, is_supported, parse_link


@pytest.mark.parametrize(
    ("url", "service", "kind", "item_id"),
    [
        ("https://www.deezer.com/track/3135556", Service.DEEZER, Kind.TRACK, "3135556"),
        ("https://www.deezer.com/en/album/302127", Service.DEEZER, Kind.ALBUM, "302127"),
        ("https://deezer.com/fr-fr/playlist/908622995?utm=x", Service.DEEZER, Kind.PLAYLIST, "908622995"),
        ("https://tidal.com/browse/track/77646169", Service.TIDAL, Kind.TRACK, "77646169"),
        ("https://listen.tidal.com/album/77646168", Service.TIDAL, Kind.ALBUM, "77646168"),
        ("https://tidal.com/browse/playlist/0f1a2b3c-aaaa-bbbb", Service.TIDAL, Kind.PLAYLIST, "0f1a2b3c-aaaa-bbbb"),
        ("  https://tidal.com/track/1  ", Service.TIDAL, Kind.TRACK, "1"),
    ],
)
def test_parse_link(url, service, kind, item_id):
    link = parse_link(url)
    assert link is not None
    assert (link.service, link.kind, link.id) == (service, kind, item_id)


@pytest.mark.parametrize(
    "url",
    [
        "https://open.spotify.com/track/abc",
        "https://music.amazon.com/albums/B0",
        "https://www.deezer.com/artist/27",
        "not a url",
    ],
)
def test_unsupported(url):
    assert parse_link(url) is None
    assert not is_supported(url)


def test_short_links_are_supported_but_need_expanding():
    url = "https://link.deezer.com/s/30abcDEF"
    assert is_supported(url)
    assert parse_link(url) is None
