#!/usr/bin/env python3
"""
io.py - Disk I/O Metrics Module for snaputil
========================================================================================

This module collects various disk-related statistics including mounted partitions, disk
usage per mountpoint, and raw disk I/O counters. Used internally by snaputil.py to
provide system snapshots.

Author: Juan J. Garcia (arpatek)
"""

# ──[ Imports ]─────────────────────────────────────────────────────────────────────────
# from pprint import pprint  # debug artifact — used by main() for raw dict inspection
import psutil


# ──[ Disk I/O Info Collection ]────────────────────────────────────────────────────────
def get_io_info():
    """
    Collects disk partition, usage, and I/O statistics using psutil.

    Returns:
        dict: {
            "Disk_Partitions": list - Device, mountpoint, FS type, and options,
            "Disk_Usage": dict - Usage stats per mountpoint (total, used, free, percent),
            "Disk_Counter": dict - Low-level I/O counters by device
        }
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
def main():
    """
    Debug entry point for standalone testing.

    Prints the full dictionary of disk metrics returned by get_io_info()
    using pprint for readability. Intended for development use only.
    """
    from pprint import pprint
    pprint(get_io_info())


# ──[ Entry Point ]─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
