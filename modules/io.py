#!/usr/bin/env python3
"""
io.py - Disk I/O Metrics Module for snaputil
========================================================================================

This module collects various disk-related statistics including mounted partitions, disk
usage per mountpoint, and raw disk I/O counters. Used internally by snaputil.py to
provide system snapshots.

Author: Juan Garcia (arpatek)
"""

# ──[ Imports ]─────────────────────────────────────────────────────────────────────────
# from pprint import pprint  # debug artifact — used by main() for raw dict inspection
import psutil


# ──[ Disk I/O Info Collection ]────────────────────────────────────────────────────────
def get_io_info() -> dict:
    """Collect disk partition layout, usage statistics, and I/O counters.

    Iterates physical mounted partitions via ``psutil.disk_partitions(all=False)``.
    Partitions that raise ``PermissionError`` on ``disk_usage()`` are silently
    skipped and will be absent from the ``Disk_Usage`` mapping.

    Returns:
        dict: Contains the following keys:

            - ``Disk_Partitions`` (list[dict]): One entry per mounted partition.
              Each dict contains:

                  - ``Device`` (str): Device path (e.g. ``'/dev/sda1'``).
                  - ``Mountpoint`` (str): Mount location (e.g. ``'/'``).
                  - ``FSType`` (str): Filesystem type (e.g. ``'ext4'``).
                  - ``Opts`` (str): Mount options string.

            - ``Disk_Usage`` (dict[str, dict]): Maps mountpoint to a usage dict
              with ``Total``, ``Used``, ``Free`` (int, bytes) and
              ``Percent`` (float). Mountpoints with ``PermissionError`` are
              excluded.
            - ``Disk_Counter`` (dict[str, psutil.sdiskio]): Per-device I/O
              counters from ``psutil.disk_io_counters(perdisk=True)``.

    Example:
        >>> data = get_io_info()
        >>> root = data["Disk_Usage"].get("/", {})
        >>> if root:
        ...     print(f"Root: {root['Percent']}% used")  # doctest: +SKIP
        Root: 42.0% used
        >>> assert all("Mountpoint" in p for p in data["Disk_Partitions"])
    """
    disk_partitions_raw = psutil.disk_partitions()
    disk_partitions = []
    disk_usage = {}

    for part in disk_partitions_raw:
        partition_info = {
            "Device": part.device,
            "Mountpoint": part.mountpoint,
            "FSType": part.fstype,
            "Opts": part.opts,
        }
        disk_partitions.append(partition_info)
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disk_usage[part.mountpoint] = {
                "Total": usage.total,
                "Used": usage.used,
                "Free": usage.free,
                "Percent": usage.percent,
            }
        except PermissionError:
            continue

    disk_counter = psutil.disk_io_counters(perdisk=True)
    return {
        "Disk_Partitions": disk_partitions,
        "Disk_Usage": disk_usage,
        "Disk_Counter": disk_counter,
    }


# ──[ Debug Entry Point ]───────────────────────────────────────────────────────────────
def main() -> None:
    """Run this module as a standalone diagnostic script.

    Pretty-prints the full output of :func:`get_io_info` to stdout.
    Intended for development and debugging; not called by snaputil at runtime.

    Example:
        .. code-block:: shell

            $ python3 modules/io.py
    """
    from pprint import pprint
    pprint(get_io_info())


# ──[ Entry Point ]─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
