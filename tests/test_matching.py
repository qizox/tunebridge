import pytest

from tunebridge import Song, main_title, search_queries, title_matches


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("Blinding Lights", "Blinding Lights"),
        ("Over My Head (Cable Car)", "Over My Head"),
        ("Song - 2011 Remaster", "Song"),
        ("Beautiful feat. Someone", "Beautiful"),
        ("Track [Live]", "Track"),
    ],
)
def test_main_title(title, expected):
    assert main_title(title) == expected


def test_title_matches_ignores_case_and_punctuation():
    song = Song(title="I Need A Doctor", artist="Dr. Dre")
    assert title_matches("Dr. Dre - I NEED A DOCTOR (Official Video)", song)
    assert not title_matches("Dr. Dre - Still D.R.E.", song)


def test_title_matches_rejects_empty_titles():
    assert not title_matches("anything", Song(title="!!!"))


def test_search_queries_with_isrc():
    song = Song(title="Contraband", artist="Colato", isrc="QZES52300123")
    assert search_queries(song) == [
        'ytsearch:"QZES52300123"',
        "ytmsearch:Colato - Contraband",
        "scsearch:Colato - Contraband",
    ]


def test_search_queries_without_isrc():
    song = Song(title="Beautiful", artist="Eminem")
    assert search_queries(song) == [
        "ytsearch:Eminem - Beautiful",
        "ytmsearch:Eminem - Beautiful",
        "scsearch:Eminem - Beautiful",
    ]


def test_search_queries_custom_sources():
    song = Song(title="x", isrc="AAAAA0000000")
    assert search_queries(song, sources=("scsearch",)) == ["scsearch:x"]
