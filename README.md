# foam-addons
## `libaddons.so`
OpenFOAM extension library.

## foamio
OpenFOAM addons, Python routines and helpers.

CLI examples:
- Convert all Z-cutPlanes from .vtk to .vtp and generate a .pvd-file matching the 
case name
    ```sh
    foam_case=<path>
    foamio convert $foam_case/postProcessing/cutPlanes && \
    foamio -v generate $foam_case/postProcessing/cutPlanes --pattern='*(z).vtp' --outfile=$foam_case/postProcessing/$(basename $foam_case).pvd
    ```
- Clean up the case including `postProcessing/` before restart (`foamListTimes` is not possible to use in `postProcessing/` folder)
    ```sh
    foam_case=<path>
    foamio -v clean $foam_case/postProcessing/ --interval "$(foamDictionary -case $foam_case -processor -latestTime):"
    ```
