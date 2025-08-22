from __future__ import annotations

import argparse
import concurrent.futures
import logging
import os
from dataclasses import dataclass
from pathlib import Path

import CoolProp.CoolProp as cp
import numpy as np

from foamio._helpers import require_range
from foamio.dat import write


@dataclass(unsafe_hash=True)
class Quantities:
    p: int | float | np.ndarray = None
    T: int | float | np.ndarray = None


def add_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "fluid",
        metavar="COOLPROP_FLUID",
        type=str,
        help="CoolProp.PropsSI fluid name",
    )
    parser.add_argument(
        "outdir",
        metavar="DIR",
        type=Path,
        help="directory to which output lists",
    )
    parser.add_argument(
        "--pressure",
        "-p",
        type=float,
        nargs="+",
        default=[1e05, 5e05, 100],
        action=require_range(3, 3),
        help="pressure args to np.linspace",
    )
    parser.add_argument(
        "--temperature",
        "-t",
        type=float,
        nargs="+",
        default=[293.15, 393.15, 25],
        action=require_range(3, 3),
        help="temperature args to np.linspace",
    )
    parser.add_argument(
        "--entries",
        "-e",
        type=str,
        nargs="+",
        help="CoolProp.PropsSI quantity name, e.g. 'CPMASS'",
    )
    parser.add_argument(
        "--phase",
        metavar="COOLPROP_PHASE",
        type=str,
        help="CoolProp.PropsSI phase name ('gas' or 'liquid')",
    )
    parser.add_argument(
        "--clamp",
        "-c",
        action="store_true",
        help="Clamp -inf, +inf to min, max",
    )


def __fill(
    qs: Quantities, fluid: str, entry: str, phase: str = None, clamp: str = True
) -> np.ndarray:
    """Fill array (pressure and temperature) for selected CoolProp quantity.

    Args:
        qs (Quantities): pressure(s) and temperature(s)
        fluid (str): CoolProp fluid name
        entry (str): CoolProp quantity name, e.g. 'CPMASS'
        phase (str, optional): CoolProp phase name ('gas' or 'liquid').
        Defaults to None.
        clamp (bool, optional): Replace -inf, +inf with min, max finite values.
        Defaults to False.

    Returns:
        np.ndarray: filled-in quantity
    """

    values = np.zeros((len(qs.T), len(qs.p)))
    with concurrent.futures.ThreadPoolExecutor() as e:
        future_to_indrow = {
            e.submit(
                cp.PropsSI,
                entry,
                "P" if phase is None else f"P|{phase}",
                qs.p,
                "T",
                T_row,
                fluid,
            ): i
            for i, T_row in enumerate(qs.T)
        }

        for future in concurrent.futures.as_completed(future_to_indrow):
            i = future_to_indrow[future]
            try:
                values[i] = future.result()
                logging.debug(f"{entry=} at {i=} ({qs.T[i]=}) filled")
            except Exception as exception:
                logging.warning(
                    f"filling {entry=} at {i=} ({qs.T[i]=}) raised an {exception=}"
                )
    if clamp:
        is_finite = np.isfinite(values)
        values[np.isneginf(values)], values[np.isposinf(values)] = (
            np.min(values[is_finite]),
            np.max(values[is_finite]),
        )
    return values


def __validate(args: argparse.Namespace) -> None:
    args.outdir = args.outdir.resolve()

    args.entries = ["DMASS"] if args.entries is None else args.entries

    args.pressure[2] = int(args.pressure[2])
    args.temperature[2] = int(args.temperature[2])


def tabulate(args: argparse.Namespace) -> None:
    __validate(args)

    cp.set_config_string(
        cp.ALTERNATIVE_REFPROP_HMX_BNC_PATH, os.getenv("REFPROP_HMX_BNC_PATH", "")
    )
    cp.set_config_string(cp.ALTERNATIVE_REFPROP_PATH, os.getenv("REFPROP_PATH", ""))
    cp.set_config_string(
        cp.ALTERNATIVE_REFPROP_LIBRARY_PATH, os.getenv("REFPROP_LIBRARY_PATH", "")
    )

    logging.info(
        f"generating tabulated {args.entries=} at "
        f"p=np.linspace(*{args.pressure}) [Pa], "
        f"T=np.linspace(*{args.temperature}) [K]"
    )

    qs = Quantities(p=np.linspace(*args.pressure), T=np.linspace(*args.temperature))
    header = f"low ({qs.p[0]} {qs.T[0]}); " f"high ({qs.p[-1]} {qs.T[-1]}); " "values "
    with concurrent.futures.ProcessPoolExecutor() as e:
        future_to_outfile = {
            e.submit(
                write,
                Path(args.outdir, f"{args.fluid}.{entry}.gz"),
                __fill(qs, args.fluid, entry, args.phase, args.clamp).T,
                header=f'/* cp.PropsSI("{entry}", … "T|{args.phase}", … "{args.fluid}") */ '
                f"{header}",
                compression=True,
                dims=True,
                footer=";",
            ): Path(args.outdir, f"{args.fluid}.{entry}.gz")
            for entry in args.entries
        }

        for future in concurrent.futures.as_completed(future_to_outfile):
            outfile = future_to_outfile[future]
            try:
                future.result()
                logging.info(f"{outfile.name=} tabulation created")
            except Exception as exception:
                logging.warning(f"writing to {outfile.name=} raised an {exception=}")
