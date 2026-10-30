class TunebridgeError(Exception):
    """Base class. The message is written so it can be shown to an end user."""


class UnsupportedLink(TunebridgeError):
    """The URL isn't a link tunebridge knows how to read."""


class NotFound(TunebridgeError):
    """The link is valid but the item doesn't exist, is private, or is empty."""


class ServiceUnavailable(TunebridgeError):
    """The service answered with an error or didn't answer in time."""
