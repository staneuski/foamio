from foamio import _cli, dat, foam
from foamio.__about__ import __version__

__all__ = [
    "__version__",
    "_cli",
    "dat",
    "foam",
]

try:
    import gp_utilities

    from foamio import gridpro

    __all__.append("gridpro")
except ImportError:
    pass
