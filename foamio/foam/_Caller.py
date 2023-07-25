from __future__ import annotations

import logging
import subprocess
from pathlib import Path


class Caller:
    """Naive OpenFOAM wrapper which uses `foamExec` Python's `subprocess`, e.g.:
    - `Caller().Run(solver='incompressibleFluid')` will call
    `$ foamExec foamRun -solver incompressibleFluid`
    - `Caller().blockMesh()` will call `$ foamExec blockMesh`
    - `Caller().Dictionary('system/controlDict', expand=True)` will call 
    `$ foamExec foamDictionary -expand system/controlDict`
    """

    def __init__(self,
                 wm_project_dir: str
                 | Path = f'{Path.home()}/.local/opt/OpenFOAM-dev',
                 invert_args: bool = True,
                 **kwargs) -> None:
        """
        Forwards each keyword argument to `subprocess.run` besides specified
        below.

        Args:
            wm_project_dir (str | Path, optional): OpenFOAM project directory.
            Defaults to '~/.local/opt/OpenFOAM-dev'.
            invert_args (bool, optional): are key-word arguments followed by
            word arguments, e.g.
            `Caller(invert_args=True).Dictionary('system/controlDict', expand=True)`
            is calling `$ foamDictionary -expand system/controlDict`
            or `Caller(invert_args=False).Dictionary('constant/polyMesh/boundary', set='entry0/front/type=wedge')`
            is calling `$ foamDictionary constant/polyMesh/boundary -set "entry0/front/type=wedge"`.
            Defaults to True.
        """
        self.project_dir = wm_project_dir
        self.invert_args = invert_args
        self.__kwargs = kwargs

    def __getattr__(self, cmd: str):

        def wrapper(*args, **kwargs):
            # Since OpenFOAM uses lower-camel case capitalised calls
            # are prepended with 'foam'
            return self._call(
                f'foam{cmd}' if cmd.istitle() else cmd,
                *args,
                **kwargs,
            )

        return wrapper

    @staticmethod
    def __convert_kwargs(**kwargs) -> list[str]:
        args = []
        for key, value in kwargs.items():
            if (isinstance(value, bool) and value is False) or value is None:
                continue
            elif isinstance(value, bool) and value is True:
                args.append(f'-{key}')
                continue
            args.append(f'-{key}')
            args.append(str(value))

        return args

    def _call(self, cmd: str, *args,
              **kwargs) -> subprocess.CompletedProcess[int]:
        str_args = [f'{self.project_dir}/bin/./foamExec', cmd]
        if not self.invert_args:
            str_args += ([str(arg)
                          for arg in args] + self.__convert_kwargs(**kwargs))
        else:
            str_args += (self.__convert_kwargs(**kwargs) +
                         [str(arg) for arg in args])

        # print(*str_args, sep=' ')
        logging.debug(f'calling `subprocess.run({str_args})`')
        return subprocess.run(str_args, **self.__kwargs)
