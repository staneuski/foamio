# foam-addons
## `libaddons.so`
OpenFOAM extension library with utilities:
```sh
wmake -all ~/Developer/Projects/foamio/addons
```

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
- Clean up a case (including `postProcessing/`) from a particular time-step
    ```sh
    foam_case=<path>
    foamio --debug clean $foam_case --interval '<time>:' --exclude-first && \
    foamio clean $foam_case/postProcessing/ -i "$(foamListTimes -case $foam_case -latestTime):"
    ```
- Clean up a case (including `postProcessing/`) from a particular time-step but using `foamListTimes -rm`
    ```sh
    foam_case=<path>
    foamListTimes -case $foam_case -time '<time>:' -rm && \
    foamio clean $foam_case/postProcessing/ -i "$(foamListTimes -case $foam_case -latestTime):"
    ```
