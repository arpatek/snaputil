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
def get_cpu_info() -> dict:
    """Collect CPU statistics from the current system.

    Measures usage over a 1-second blocking interval via
    ``psutil.cpu_percent(percpu=True)``. The aggregate ``CPU_Percent`` is the
    mean of all per-core values.

    Returns:
        dict: Contains the following keys:

            - ``CPU_Count`` (int): Logical core count (includes hyperthreading).
            - ``CPU_Physical`` (int): Physical core count.
            - ``CPU_Percent`` (float): Mean usage across all cores, 1 d.p.
            - ``CPU_PerCore`` (list[float]): Per-core usage percentages, one
              value per logical core.
            - ``CPU_Stats`` (psutil.scpustats): Low-level counters — context
              switches, interrupts, soft interrupts, syscalls.
            - ``CPU_Freq`` (psutil.scpufreq | None): Current, min, and max
              frequency in MHz. May be ``None`` on some virtual machines.
            - ``CPU_Load`` (tuple[float, float, float]): System load averages
              over the last 1, 5, and 15 minutes.

    Example:
        >>> data = get_cpu_info()
        >>> print(data["CPU_Percent"])
        12.4
        >>> print(len(data["CPU_PerCore"]) == data["CPU_Count"])
        True
    """
    cpu_count    = os.cpu_count()
    cpu_physical = psutil.cpu_count(logical=False)
    cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)
    cpu_percent  = round(sum(cpu_per_core) / len(cpu_per_core), 1)
    cpu_stats    = psutil.cpu_stats()
    cpu_freq     = psutil.cpu_freq()
    cpu_load     = os.getloadavg()

    return {
        "CPU_Count":    cpu_count,
        "CPU_Physical": cpu_physical,
        "CPU_Percent":  cpu_percent,
        "CPU_PerCore":  cpu_per_core,
        "CPU_Stats":    cpu_stats,
        "CPU_Freq":     cpu_freq,
        "CPU_Load":     cpu_load,
    }


# ──[ Debug Entry Point ]───────────────────────────────────────────────────────────────
def main() -> None:
    """Run this module as a standalone diagnostic script.

    Pretty-prints the full output of :func:`get_cpu_info` to stdout.
    Intended for development and debugging; not called by snaputil at runtime.

    Example:
        .. code-block:: shell

            $ python3 modules/cpu.py
    """
    from pprint import pprint
    pprint(get_cpu_info())


# ──[ Entry Point ]─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
