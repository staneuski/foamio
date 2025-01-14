# foamio
OpenFOAM addons, Python routines and helpers.

## CLI
- Clean up a case (including _postProcessing/_) from a particular time-step
    ```sh
    foam_case=<path>
    foamio --debug clean $foam_case --interval '<time>:' --exclude-first && \
    foamio clean $foam_case/postProcessing/ -i "$(foamListTimes -case $foam_case -latestTime):"
    ```
- Clean up a case (including _postProcessing/_) from a particular time-step but using `foamListTimes -rm`
    ```sh
    foam_case=<path>
    foamListTimes -case $foam_case -time '<time>:' -rm && \:
    foamio clean $foam_case/postProcessing/ -i "$(foamListTimes -case $foam_case -latestTime):"
    ```
- Create tabulated entry for _physicalProperties_ using [`CoolProp`](http://coolprop.org/):
    ```sh:
    foamio -v tabulate H2O constant/ --pressure 1e+05 5e+06 2500 --temperature 293.15 393.15 100 --entries DMASS HMASS CPMASS CVMASS VISCOSITY CONDUCTIVITY
    ```
    Generated entry can be imported in `mixture` dictionary as:
    ```cpp
    equationOfState
    {
        rho
        {
            #include "H2O.DMASS"
        }
    }
    ```

## Module
- Read OpenFOAM-dictionary (with `#calc`s, etc.) as cached Python-dict:
    ```python
    from functools import cache
    from pathlib import Path
    import tempfile

    from foamio.foam import Caller as Foam, read
    @cache
    def read_dict(root: Path, orig: Path) -> dict:
        """
        Args:
            root (Path): Absolute path to OpenFOAM-case.
            orig (Path): OpenFOAM-dictionary path relative to FOAM_CASE.
        """

        # foamio.foam.read works only for expanded dictionaries => expand to a temporary file using `foamDictionary` and read from this file
        with tempfile.NamedTemporaryFile(dir=root / orig.parent) as tmp:
            fname = Path(tmp.name).relative_to(root)
            Foam().Dictionary(orig, case=root, expand=True, output=str(fname))
            return read(root, tmp.name)
    ```
