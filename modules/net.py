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
def get_net_info():
    """
    Collects active network interface information including IPv4 addresses,
    link status, and total data transmitted/received.

    Returns:
        dict: {
            "Addresses": dict - {iface_name: ip_address},
            "Stats": dict - Interface statistics (psutil.net_if_stats),
            "I/O": snetio - Total network I/O counters
        }
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
def main():
    """
    Debug entry point for standalone testing.

    Prints the full dictionary of network metrics returned by get_net_info().
    Intended for development use only.
    """
    from pprint import pprint
    pprint(get_net_info())


# ──[ Entry Point ]─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
