#!/usr/bin/env python3
"""
cpu.py - CPU Metrics Module for snaputil
========================================================================================

This module collects various CPU-related statistics including logical and physical core
count, current usage percentage, load averages, CPU frequency, and low-level CPU stats.
Used internally by snaputil.py to provide system snapshots.

Author: Juan J. Garcia (arpatek)
"""

# ──[ Imports ]─────────────────────────────────────────────────────────────────────────
# from pprint import pprint  # debug artifact — used by main() for raw dict inspection
import os
import psutil


# ──[ CPU Info Collection ]─────────────────────────────────────────────────────────────
def get_cpu_info():
    """
    Collects CPU statistics using psutil and os modules.

    Returns:
        dict: {
            "CPU_Count": int - Logical CPU count,
            "CPU_Physical": int - Physical CPU core count,
            "CPU_Percent": float - CPU usage percentage over 1 second,
            "CPU_Stats": scpustats - Context switches, interrupts, etc.,
            "CPU_Freq": scpufreq - Current/max/min frequency (MHz),
            "CPU_Load": tuple - 1, 5, 15-minute load averages
        }
    """
    cpu_count = os.cpu_count()
    cpu_physical = psutil.cpu_count(logical=False)
    cpu_percentage = psutil.cpu_percent(interval=1)
    cpu_stats = psutil.cpu_stats()
    cpu_freq = psutil.cpu_freq()
    cpu_load = os.getloadavg()

    return {
        "CPU_Count": cpu_count,
        "CPU_Physical": cpu_physical,
        "CPU_Percent": cpu_percentage,
        "CPU_Stats": cpu_stats,
        "CPU_Freq": cpu_freq,
        "CPU_Load": cpu_load,
    }


# ──[ Debug Entry Point ]───────────────────────────────────────────────────────────────
def main():
    """
    Debug entry point for standalone testing.

    Prints the full dictionary of CPU metrics returned by get_cpu_info()
    using pprint for readability. Intended for development use only.
    """
    from pprint import pprint
    pprint(get_cpu_info())


# ──[ Entry Point ]─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
