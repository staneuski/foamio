from importlib import metadata

try:
    __version__ = metadata.version("foamio")
except Exception:
    __version__ = "unknown"
