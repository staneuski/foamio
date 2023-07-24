#!/usr/bin/env python3
from pathlib import Path

from foamio.foam import Caller as Foam

WM_PROJECT_DIR = f'{Path.home()}/.local/opt/OpenFOAM-dev'

Foam(WM_PROJECT_DIR).blockMesh()
Foam(WM_PROJECT_DIR).snappyHexMesh(overwrite=True)
