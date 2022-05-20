from pathlib import Path
from typing import Union
import pandas as pd

from . import readers

class Case():
    """OpenFOAM case handler (mostly for automating data from postProcessing/).
    """

    def __init__(self,
                 case_dir: Union[Path, str] = Path(__file__).parent,
                 suffix: str = None,
                 description: str = None) -> None:

        suffix = '' if suffix is None else suffix

        self.__path = Path(case_dir).resolve()
        self.__post = Path(case_dir, f'postProcessing{suffix}')
        self.__description = description if not description is None else suffix

    def __repr__(self) -> str:
        return str('self.__post')

    def __str__(self) -> str:
        description = str(self.__path.with_suffix('')).replace('/', ' ')
        if not self.__description is None:
            description = f'{description}: {self.__description}'
        return description

    @property
    def path(self):
        return self.__path

    @property
    def post(self):
        return self.__post

    @property
    def description(self):
        return self.__description

    def load_postfn(self,
                    fn_name: str,
                    join_timefolders: bool = True,
                    use_nth: int = None) -> pd.DataFrame:
        """Load results of post-process function."""

        def load(filepath: str) -> pd.DataFrame:
            if filepath.suffix == '.dat':
                return readers.load_dat(filepath, use_nth=use_nth)
            elif filepath.suffix == '.xy':
                return readers.load_xy(filepath, use_nth=use_nth)
            else:
                raise ValueError(
                    'postProcessing file must have .dat, .xy extension.')

        def load_all(fn_path: Path) -> list:
            filepaths = (fn_path.rglob('*.*[dat,xy]')
                         if join_timefolders else fn_path.glob('*.*[dat,xy]'))

            return [load(filepath) for filepath in filepaths]

        post_path = Path(self.__post, fn_name)
        if not post_path.exists():
            raise ValueError(f'{post_path} not exist')

        if join_timefolders:
            return pd.concat(load_all(post_path), axis=0, sort=False)

        dfs = load_all(post_path)
        if not dfs:
            dfs = load_all(sorted(post_path.glob('*'))[-1])

        return pd.concat(dfs, axis=1)
