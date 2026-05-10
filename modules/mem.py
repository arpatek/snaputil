#!/usr/bin/env python3
"""
mem.py - Memory Metrics Module for snaputil
========================================================================================

This module collects memory usage statistics using psutil, including total, used,
available, free, and percent usage values. Used internally by snaputil.py to provide
system snapshots.

Author: Juan Garcia (arpatek)
"""

# ──[ Imports ]─────────────────────────────────────────────────────────────────────────
# from pprint import pprint  # debug artifact — used by main() for raw dict inspection
import psutil


# ──[ Memory Info Collection ]──────────────────────────────────────────────────────────
def get_mem_info() -> dict:
    """Collect virtual memory statistics from the current system.

    Returns:
        dict: Contains the following keys (all byte counts are integers):

            - ``Total`` (int): Total installed physical memory in bytes.
            - ``Available`` (int): Memory available without swapping in bytes.
            - ``Used`` (int): Memory currently in active use in bytes.
            - ``Free`` (int): Memory not in use and not cached in bytes.
            - ``Percent`` (float): Percentage of total memory currently in use.

    Example:
        >>> data = get_mem_info()
        >>> total_gb = data["Total"] / (1024 ** 3)
        >>> print(f"{total_gb:.2f} GB")  # doctest: +SKIP
        16.00 GB
        >>> assert 0.0 <= data["Percent"] <= 100.0
    """
    v_mem = psutil.virtual_memory()
    return {
        "Total": v_mem.total,
        "Available": v_mem.available,
        "Used": v_mem.used,
        "Free": v_mem.free,
        "Percent": v_mem.percent,
    }


# ──[ Debug Entry Point ]───────────────────────────────────────────────────────────────
def main() -> None:
    """Run this module as a standalone diagnostic script.

    Pretty-prints the full output of :func:`get_mem_info` to stdout.
    Intended for development and debugging; not called by snaputil at runtime.

    Example:
        .. code-block:: shell

            $ python3 modules/mem.py
    """
    from pprint import pprint
    pprint(get_mem_info())


# ──[ Entry Point ]─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
