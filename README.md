# tunebridge

[![tests](https://github.com/qizox/tunebridge/actions/workflows/tests.yml/badge.svg)](https://github.com/qizox/tunebridge/actions/workflows/tests.yml)
![python](https://img.shields.io/badge/python-3.10%2B-c1aee7?style=flat-square&labelColor=1a1821)
![license](https://img.shields.io/badge/license-MIT-c1aee7?style=flat-square&labelColor=1a1821)

Turn **Deezer** and **TIDAL** links into songs your bot can actually play.

Lavalink can't stream Deezer or TIDAL without paid accounts or extra plugins. tunebridge reads the link instead: it gets each song's title, artist and **ISRC** (the code that identifies one exact recording), then gives you the searches that find that same recording on YouTube or SoundCloud.

I built this for the music system in [spite](https://spite.rest), a Discord bot, and pulled it out into its own library.

## What it handles

| Link | Supported |
| --- | --- |
| Deezer track, album, playlist | yes, with pagination up to your limit |
| Deezer short links (`link.deezer.com`, `deezer.page.link`) | yes, expanded first |
| TIDAL track | yes, including the ISRC |
| TIDAL album, playlist, mix | no, needs TIDAL API credentials |

No API keys needed. Deezer has a public API, and TIDAL track pages carry the song's details.

## Install

```bash
pip install git+https://github.com/qizox/tunebridge
```

Python 3.10+, with aiohttp as the only dependency.

## Usage

```python
import asyncio
import tunebridge

async def main():
    playlist = await tunebridge.resolve("https://www.deezer.com/en/album/302127")
    print(playlist.name, len(playlist.songs))
    for song in playlist.songs:
        print(song.artist, "-", song.title, song.isrc)

asyncio.run(main())
```

Resolving many links? Reuse one `Resolver`, or hand it the aiohttp session your bot already has:

```python
async with tunebridge.Resolver(session=bot.http_session, limit=100) as resolver:
    result = await resolver.resolve(url)
```

### Playing the result with Lavalink

`search_queries()` gives you Lavalink identifiers, best first: the exact ISRC search, then text searches on YouTube Music and SoundCloud. ISRC searches are very accurate, but sometimes return an unrelated upload, so check results with `title_matches()`:

```python
from tunebridge import search_queries, title_matches

async def find_track(node, song):
    for query in search_queries(song):
        result = await node.get_tracks(query)
        tracks = result.tracks if result else []
        if query.startswith("ytsearch:"):
            tracks = [t for t in tracks if title_matches(t.title, song)]
        if tracks:
            return tracks[0]
    return None
```

This works with any Lavalink client (lavalink.py, wavelink, mafic...). Only the `get_tracks` call differs.

### Errors

Every error subclasses `tunebridge.TunebridgeError`, and its message is written so you can show it to users as-is.

| Error | When |
| --- | --- |
| `UnsupportedLink` | not a Deezer/TIDAL link, or a TIDAL album/playlist |
| `NotFound` | the item doesn't exist, is private, or has nothing playable |
| `ServiceUnavailable` | the service errored or timed out |

```python
try:
    result = await resolver.resolve(url)
except tunebridge.TunebridgeError as exc:
    await ctx.reply(str(exc))
```

## Testing

```bash
pip install -e ".[test]"
pytest
```

The tests run offline with a fake fetcher, so they never touch Deezer or TIDAL.

## License

MIT
