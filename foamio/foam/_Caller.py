# %%
from __future__ import annotations

import logging
import subprocess
from pathlib import Path


class Caller:
    """Naive OpenFOAM wrapper which uses `foamExec` Python's `subprocess`, e.g.:
    - `Foam().Run(solver='incompressibleFluid')` will call
    `$ foamExec foamRun -solver incompressibleFluid`
    - `Foam().blockMesh()` will call `$ foamExec blockMesh`
    - `Foam().Dictionary(expand=True)` will call 
    `$ foamExec foamDictionary -expand`
    """

    def __init__(
        self,
        wm_project_dir: str | Path = f'{Path.home()}/.local/opt/OpenFOAM-dev',
        **run_kwargs
    ) -> None:
        self.project_dir = wm_project_dir
        self.run_kwargs: dict = run_kwargs

    def __getattr__(self, cmd: str):

        def wrapper(**kwargs):
            # Since OpenFOAM uses lower-camel case capitalised calls
            # are prepended with 'foam'
            self.call(f'foam{cmd}' if cmd.istitle() else cmd, **kwargs)

        return wrapper

    def call(self, cmd: str, **kwargs):
        args = ([f'{self.project_dir}/bin/./foamExec', cmd] +
                self.__kwargs_to_args(**kwargs))
        # logging.debug(f'calling `subprocess.run({args})`')
        print(f'calling `subprocess.run({args})`')
        subprocess.run(args, **self.run_kwargs)

    @staticmethod
    def __kwargs_to_args(**kwargs) -> list[str]:
        args = []
        for key, value in kwargs.items():
            args.append(f"-{key}")
            if isinstance(value, bool) and not value is True:
                args.append(value)
        return args


# %%
