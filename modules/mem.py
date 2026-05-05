#!/usr/bin/env python3
"""
mem.py - Memory Metrics Module for snaputil
========================================================================================

This module collects memory usage statistics using psutil, including total, used,
available, free, and percent usage values. Used internally by snaputil.py to provide
system snapshots.

Author: Juan J. Garcia (arpatek)
"""

# ──[ Imports ]─────────────────────────────────────────────────────────────────────────
# from pprint import pprint  # debug artifact — used by main() for raw dict inspection
import psutil


# ──[ Memory Info Collection ]──────────────────────────────────────────────────────────
def get_mem_info():
    """
    Collects memory usage statistics using psutil.

    Returns:
        dict: {
            "Total": int - Total physical memory in bytes,
            "Available": int - Available memory in bytes,
            "Used": int - Memory used in bytes,
            "Free": int - Free memory in bytes,
            "Percent": float - Memory usage as a percentage
        }
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
def main():
    """
    Debug entry point for standalone testing.

    Prints the full dictionary of memory metrics returned by get_mem_info()
    using pprint for readability. Intended for development use only.
    """
    from pprint import pprint
    pprint(get_mem_info())


# ──[ Entry Point ]─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
