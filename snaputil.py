#!/usr/bin/env python3
"""
snaputil.py - Lightweight System Snapshot Tool
========================================================================================

snaputil provides a one-glance summary of system health by aggregating and printing
vital metrics from CPU, memory, disk, and network subsystems using formatted tables.
Designed for terminal use and modular enough to be extended into a full live-dashboard
monitoring suite (btop-style TUI).

Author: Juan J. Garcia (arpatek)

Dependencies:
-------------
- Python 3.6+
- `psutil` for hardware/system metrics
- `prettytable` for formatted table output
- `platform`, `socket`, `time` from stdlib
- `modules/` directory containing:
    - cpu.py with get_cpu_info()
    - mem.py with get_mem_info()
    - io.py  with get_io_info()
    - net.py with get_net_info()

Sample Usage:
-------------
$ ./snaputil.py
"""

__version__ = "0.2.0"

# ──[ Standard Library Imports ]────────────────────────────────────────────────────────
# from pprint import pprint  # debug artifact — useful for inspecting raw dicts
# during TUI development
import socket
import time
import platform
import psutil
from prettytable import PrettyTable

# ──[ Internal Module Imports ]─────────────────────────────────────────────────────────
from modules import cpu, io, mem, net


def basic_snap() -> str:
    """
    Collect and format a real-time system snapshot using prettytable.

    Gathers data from internal modules and standard libraries to display an
    overview of system status across five sections: header metadata, memory,
    CPU, disk (all mountpoints), and network (interfaces + I/O).

    Returns:
        str: A preformatted string ready for printing to console.
    """

    # ──[ Fetch Subsystem Data ]────────────────────────────────────────────────────────
    cpu_data = cpu.get_cpu_info()
    mem_data = mem.get_mem_info()
    disk_data = io.get_io_info()
    net_data = net.get_net_info()

    # ──[ System Metadata ]─────────────────────────────────────────────────────────────
    hostname = socket.gethostname()
    os_name = platform.system()
    kernel = platform.release()
    uptime_seconds = time.time() - psutil.boot_time()
    uptime = (
        f"{int(uptime_seconds // 86400)}d "
        f"{int((uptime_seconds % 86400) // 3600)}h "
        f"{int((uptime_seconds % 3600) // 60)}m"
    )
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    # ──[ Memory Table ]────────────────────────────────────────────────────────────────
    mem_table = PrettyTable(["Metric", "Value"])
    mem_table.align["Metric"] = "l"
    mem_table.align["Value"] = "r"
    mem_table.add_rows(
        [
            ["Total", f"{mem_data['Total'] / (1024**3):.2f} GB"],
            ["Used", f"{mem_data['Used'] / (1024**3):.2f} GB"],
            ["Free", f"{mem_data['Free'] / (1024**3):.2f} GB"],
            ["Available", f"{mem_data['Available'] / (1024**3):.2f} GB"],
            ["Usage", f"{mem_data['Percent']}%"],
        ]
    )

    # ──[ CPU Table ]───────────────────────────────────────────────────────────────────
    cpu_load = ", ".join(f"{x:.2f}" for x in cpu_data["CPU_Load"])
    cpu_table = PrettyTable(["Metric", "Value"])
    cpu_table.align["Metric"] = "l"
    cpu_table.align["Value"] = "r"
    cpu_table.add_rows(
        [
            ["Logical Cores", str(cpu_data["CPU_Count"])],
            ["Physical Cores", str(cpu_data["CPU_Physical"])],
            ["Usage", f"{cpu_data['CPU_Percent']}%"],
            ["Load Avg", cpu_load],
        ]
    )

    # ──[ Disk Table (all mountpoints) ]────────────────────────────────────────────────
    disk_table = PrettyTable(["Mount", "Type", "Total", "Used", "Free", "Usage"])
    disk_table.align["Mount"] = "l"
    disk_table.align["Type"] = "l"
    for col in ["Total", "Used", "Free", "Usage"]:
        disk_table.align[col] = "r"
    for part in disk_data["Disk_Partitions"]:
        mp = part["Mountpoint"]
        if mp in disk_data["Disk_Usage"]:
            u = disk_data["Disk_Usage"][mp]
            disk_table.add_row(
                [
                    mp,
                    part["FSType"],
                    f"{u['Total'] / (1024**3):.2f} GB",
                    f"{u['Used'] / (1024**3):.2f} GB",
                    f"{u['Free'] / (1024**3):.2f} GB",
                    f"{u['Percent']}%",
                ]
            )

    # ──[ Network Interfaces Table ]────────────────────────────────────────────────────
    iface_table = PrettyTable(["Interface", "IP Address"])
    iface_table.align["Interface"] = "l"
    iface_table.align["IP Address"] = "l"
    for iface, ip in net_data["Addresses"].items():
        iface_table.add_row([iface, ip])

    # ──[ Network I/O Table ]───────────────────────────────────────────────────────────
    net_io = net_data["I/O"]
    io_table = PrettyTable(["Direction", "Volume"])
    io_table.align["Direction"] = "l"
    io_table.align["Volume"] = "r"
    io_table.add_rows(
        [
            ["Sent", f"{net_io.bytes_sent / (1024**2):.2f} MB"],
            ["Received", f"{net_io.bytes_recv / (1024**2):.2f} MB"],
        ]
    )

    # ──[ Assemble Output ]─────────────────────────────────────────────────────────────
    sep = "=" * 46
    output = f"""
{sep}
  SNAPUTIL SYSTEM SNAPSHOT
{sep}
  Hostname  : {hostname}
  OS        : {os_name}
  Kernel    : {kernel}
  Uptime    : {uptime}
  Snapshot  : {timestamp}
{sep}

[ Memory ]
{mem_table}

[ CPU ]
{cpu_table}

[ Disk ]
{disk_table}

[ Network Interfaces ]
{iface_table}

[ Network I/O ]
{io_table}
"""
    return output


# ──[ Entry Point ]─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(basic_snap())
