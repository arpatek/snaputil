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
- `rich` for formatted tables and live dashboard rendering
- `platform`, `socket`, `time` from stdlib
- `modules/` directory containing:
    - cpu.py with get_cpu_info()
    - mem.py with get_mem_info()
    - io.py  with get_io_info()
    - net.py with get_net_info()

Sample Usage:
-------------
$ ./snaputil.py             # one-shot snapshot
$ ./snaputil.py -w          # live refresh every 2 seconds
$ ./snaputil.py -w 5        # live refresh every 5 seconds
"""

__version__ = "0.3.0"

# ──[ Standard Library Imports ]────────────────────────────────────────────────────────
# from pprint import pprint  # debug artifact — useful for inspecting raw dicts during TUI development
import argparse
import sys
import socket
import time
import platform
import psutil
from prettytable import PrettyTable
from rich.console import Console, Group
from rich.columns import Columns
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich import box

# ──[ Internal Module Imports ]─────────────────────────────────────────────────────────
from modules import cpu, io, mem, net


# ──[ Table Builders ]──────────────────────────────────────────────────────────────────
def _mem_table(mem_data) -> Table:
    t = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold")
    t.add_column("Metric", style="cyan", no_wrap=True)
    t.add_column("Value", justify="right")
    t.add_row("Total",     f"{mem_data['Total']     / (1024**3):.2f} GB")
    t.add_row("Used",      f"{mem_data['Used']      / (1024**3):.2f} GB")
    t.add_row("Free",      f"{mem_data['Free']      / (1024**3):.2f} GB")
    t.add_row("Available", f"{mem_data['Available'] / (1024**3):.2f} GB")
    t.add_row("Usage",     f"{mem_data['Percent']}%")
    return t


def _cpu_table(cpu_data) -> Table:
    cpu_load = ", ".join(f"{x:.2f}" for x in cpu_data["CPU_Load"])
    t = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold")
    t.add_column("Metric", style="cyan", no_wrap=True)
    t.add_column("Value", justify="right")
    t.add_row("Logical Cores",  str(cpu_data["CPU_Count"]))
    t.add_row("Physical Cores", str(cpu_data["CPU_Physical"]))
    t.add_row("Usage",          f"{cpu_data['CPU_Percent']}%")
    t.add_row("Load Avg",       cpu_load)
    return t


def _disk_table(disk_data) -> Table:
    t = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold")
    t.add_column("Mount",  style="cyan", no_wrap=True)
    t.add_column("Type",   no_wrap=True)
    t.add_column("Total",  justify="right")
    t.add_column("Used",   justify="right")
    t.add_column("Free",   justify="right")
    t.add_column("Usage",  justify="right")
    for part in disk_data["Disk_Partitions"]:
        mp = part["Mountpoint"]
        if mp in disk_data["Disk_Usage"]:
            u = disk_data["Disk_Usage"][mp]
            t.add_row(
                mp,
                part["FSType"],
                f"{u['Total'] / (1024**3):.2f} GB",
                f"{u['Used']  / (1024**3):.2f} GB",
                f"{u['Free']  / (1024**3):.2f} GB",
                f"{u['Percent']}%",
            )
    return t


def _iface_table(net_data) -> Table:
    t = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold")
    t.add_column("Interface", style="cyan", no_wrap=True)
    t.add_column("IP Address")
    for iface, ip in net_data["Addresses"].items():
        t.add_row(iface, ip)
    return t


def _io_table(net_data) -> Table:
    net_io = net_data["I/O"]
    t = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold")
    t.add_column("Direction", style="cyan", no_wrap=True)
    t.add_column("Volume", justify="right")
    t.add_row("Sent",     f"{net_io.bytes_sent / (1024**2):.2f} MB")
    t.add_row("Received", f"{net_io.bytes_recv / (1024**2):.2f} MB")
    return t


# ──[ Plain Text Snapshot ]────────────────────────────────────────────────────────────
def basic_snap() -> str:
    """
    Collect and format a plain-text system snapshot using prettytable.

    Used when stdout is not a TTY (e.g. redirected to a file or log).
    Safe for piping, logging, and automation pipelines.

    Returns:
        str: A preformatted string ready for printing or writing to a file.
    """
    # ──[ Fetch Subsystem Data ]────────────────────────────────────────────────────────
    cpu_data  = cpu.get_cpu_info()
    mem_data  = mem.get_mem_info()
    disk_data = io.get_io_info()
    net_data  = net.get_net_info()

    # ──[ System Metadata ]─────────────────────────────────────────────────────────────
    hostname  = socket.gethostname()
    os_name   = platform.system()
    kernel    = platform.release()
    uptime_s  = time.time() - psutil.boot_time()
    uptime    = (
        f"{int(uptime_s // 86400)}d "
        f"{int((uptime_s % 86400) // 3600)}h "
        f"{int((uptime_s % 3600) // 60)}m"
    )
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    # ──[ Memory Table ]────────────────────────────────────────────────────────────────
    mem_table = PrettyTable(["Metric", "Value"])
    mem_table.align["Metric"] = "l"
    mem_table.align["Value"] = "r"
    mem_table.add_rows([
        ["Total",     f"{mem_data['Total']     / (1024**3):.2f} GB"],
        ["Used",      f"{mem_data['Used']      / (1024**3):.2f} GB"],
        ["Free",      f"{mem_data['Free']      / (1024**3):.2f} GB"],
        ["Available", f"{mem_data['Available'] / (1024**3):.2f} GB"],
        ["Usage",     f"{mem_data['Percent']}%"],
    ])

    # ──[ CPU Table ]───────────────────────────────────────────────────────────────────
    cpu_load = ", ".join(f"{x:.2f}" for x in cpu_data["CPU_Load"])
    cpu_table = PrettyTable(["Metric", "Value"])
    cpu_table.align["Metric"] = "l"
    cpu_table.align["Value"] = "r"
    cpu_table.add_rows([
        ["Logical Cores",  str(cpu_data["CPU_Count"])],
        ["Physical Cores", str(cpu_data["CPU_Physical"])],
        ["Usage",          f"{cpu_data['CPU_Percent']}%"],
        ["Load Avg",       cpu_load],
    ])

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
            disk_table.add_row([
                mp, part["FSType"],
                f"{u['Total'] / (1024**3):.2f} GB",
                f"{u['Used']  / (1024**3):.2f} GB",
                f"{u['Free']  / (1024**3):.2f} GB",
                f"{u['Percent']}%",
            ])

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
    io_table.add_rows([
        ["Sent",     f"{net_io.bytes_sent / (1024**2):.2f} MB"],
        ["Received", f"{net_io.bytes_recv / (1024**2):.2f} MB"],
    ])

    # ──[ Assemble Output ]─────────────────────────────────────────────────────────────
    sep = "=" * 46
    return f"""
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


# ──[ Dashboard Builder ]───────────────────────────────────────────────────────────────
def build_dashboard() -> Group:
    # ──[ Fetch Subsystem Data ]────────────────────────────────────────────────────────
    cpu_data  = cpu.get_cpu_info()
    mem_data  = mem.get_mem_info()
    disk_data = io.get_io_info()
    net_data  = net.get_net_info()

    # ──[ System Metadata ]─────────────────────────────────────────────────────────────
    hostname  = socket.gethostname()
    os_name   = platform.system()
    kernel    = platform.release()
    uptime_s  = time.time() - psutil.boot_time()
    uptime    = (
        f"{int(uptime_s // 86400)}d "
        f"{int((uptime_s % 86400) // 3600)}h "
        f"{int((uptime_s % 3600) // 60)}m"
    )
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    header = (
        f"[bold cyan]Hostname:[/bold cyan] {hostname}   "
        f"[bold cyan]OS:[/bold cyan] {os_name}   "
        f"[bold cyan]Kernel:[/bold cyan] {kernel}   "
        f"[bold cyan]Uptime:[/bold cyan] {uptime}   "
        f"[bold cyan]Snapshot:[/bold cyan] {timestamp}"
    )

    # ──[ Assemble Dashboard ]──────────────────────────────────────────────────────────
    return Group(
        Panel(header, title="[bold green]SNAPUTIL[/bold green]"),
        Columns([
            Panel(_mem_table(mem_data), title="[bold]Memory[/bold]",  expand=True),
            Panel(_cpu_table(cpu_data), title="[bold]CPU[/bold]",     expand=True),
        ], expand=True),
        Panel(_disk_table(disk_data), title="[bold]Disk[/bold]"),
        Columns([
            Panel(_iface_table(net_data), title="[bold]Network Interfaces[/bold]", expand=True),
            Panel(_io_table(net_data),    title="[bold]Network I/O[/bold]",        expand=True),
        ], expand=True),
    )


# ──[ Entry Point ]─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="snaputil",
        description="Lightweight system snapshot tool.",
    )
    parser.add_argument(
        "-w", "--watch",
        metavar="SECONDS",
        type=int,
        nargs="?",
        const=2,
        help="live refresh mode; optionally specify interval in seconds (default: 2)",
    )
    args = parser.parse_args()

    is_tty = sys.stdout.isatty()
    console = Console()

    if args.watch:
        if not is_tty:
            print("snaputil: --watch requires a TTY", file=sys.stderr)
            sys.exit(1)
        try:
            with Live(
                build_dashboard(),
                console=console,
                screen=True,
                refresh_per_second=4,
            ) as live:
                while True:
                    time.sleep(args.watch)
                    live.update(build_dashboard())
        except KeyboardInterrupt:
            pass
    elif is_tty:
        console.print(build_dashboard())
    else:
        print(basic_snap())
