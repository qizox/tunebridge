"""Turn Deezer and TIDAL links into songs you can play from YouTube or SoundCloud."""

from .errors import NotFound, ServiceUnavailable, TunebridgeError, UnsupportedLink
from .links import is_supported, parse_link
from .matching import main_title, search_queries, title_matches
from .models import Collection, Kind, Link, Service, Song
from .resolver import AiohttpFetcher, Fetcher, Resolver, resolve

__all__ = [
    "AiohttpFetcher",
    "Collection",
    "Fetcher",
    "Kind",
    "Link",
    "NotFound",
    "Resolver",
    "Service",
    "ServiceUnavailable",
    "Song",
    "TunebridgeError",
    "UnsupportedLink",
    "is_supported",
    "main_title",
    "parse_link",
    "resolve",
    "search_queries",
    "title_matches",
]

__version__ = "0.1.0"
