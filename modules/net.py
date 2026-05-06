#!/usr/bin/env python3
"""
net.py - Network Metrics Module for snaputil
========================================================================================

This module gathers essential network statistics including interface IP addresses,
interface stats, and total I/O counters. Used internally by snaputil.py for system
snapshots.

Author: Juan J. Garcia (arpatek)
"""

# ──[ Imports ]─────────────────────────────────────────────────────────────────────────
# from pprint import pprint  # debug artifact — used by main() for raw dict inspection
import socket
import psutil


# ──[ Network Info Collection ]─────────────────────────────────────────────────────────
def get_net_info() -> dict:
    """Collect network interface addresses, link stats, and cumulative I/O counters.

    Only interfaces with a non-loopback IPv4 address (``socket.AF_INET``,
    address != ``'127.0.0.1'``) are included in the ``Addresses`` mapping.
    If an interface has multiple IPv4 addresses, the last one wins.

    Returns:
        dict: Contains the following keys:

            - ``Addresses`` (dict[str, str]): Maps interface name to its IPv4
              address string (e.g. ``{'eth0': '192.168.1.100'}``).
            - ``Stats`` (dict[str, psutil.snicstats]): Per-interface link stats
              from ``psutil.net_if_stats()`` — speed, duplex, MTU, and isup.
            - ``I/O`` (psutil.snetio): System-wide cumulative I/O counters.
              Key attributes: ``bytes_sent``, ``bytes_recv``, ``packets_sent``,
              ``packets_recv``, ``errin``, ``errout``, ``dropin``, ``dropout``.

    Example:
        >>> data = get_net_info()
        >>> for iface, ip in data["Addresses"].items():
        ...     print(f"{iface}: {ip}")  # doctest: +SKIP
        eth0: 192.168.1.100
        >>> sent_mb = data["I/O"].bytes_sent / (1024 ** 2)
        >>> assert sent_mb >= 0
    """
    nic_data = {}
    net_addr = psutil.net_if_addrs()
    for nic_name, nic_info in net_addr.items():
        for addr in nic_info:
            if (
                addr.family == socket.AF_INET
                and addr.address
                and addr.address != "127.0.0.1"
            ):
                nic_data[nic_name] = addr.address

    net_stats = psutil.net_if_stats()
    net_io = psutil.net_io_counters()

    return {
        "Addresses": nic_data,
        "Stats": net_stats,
        "I/O": net_io,
    }


# ──[ Debug Entry Point ]───────────────────────────────────────────────────────────────
def main() -> None:
    """Run this module as a standalone diagnostic script.

    Pretty-prints the full output of :func:`get_net_info` to stdout.
    Intended for development and debugging; not called by snaputil at runtime.

    Example:
        .. code-block:: shell

            $ python3 modules/net.py
    """
    from pprint import pprint
    pprint(get_net_info())


# ──[ Entry Point ]─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
