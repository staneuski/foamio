#!/usr/bin/env python3
from pathlib import Path

from foamio.foam import Caller as Foam

WM_PROJECT_DIR = f'{Path.home()}/.local/opt/OpenFOAM-dev'

Foam(WM_PROJECT_DIR).blockMesh()
Foam(WM_PROJECT_DIR).wedgeMesh('Z', 'Y', 5)
Foam(WM_PROJECT_DIR, invert_args=False).Dictionary(
    'constant/polyMesh/boundary',
    set='entry0/front/type=wedge, entry0/back/type=wedge',
    expand=False)
