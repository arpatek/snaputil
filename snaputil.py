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
- `prettytable` for plain-text output when stdout is not a TTY
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
$ ./snaputil.py >> sys.log  # plain-text log (auto-detected, no TTY)
"""

__version__ = "0.4.0"

# ──[ Standard Library Imports ]────────────────────────────────────────────────────────
# from pprint import pprint  # debug artifact — useful for inspecting raw dicts during TUI development
import argparse
import sys
import socket
import time
import platform
import threading
import psutil
try:
    import termios
    import tty as _tty
    _POSIX = True
except ImportError:
    _POSIX = False
from prettytable import PrettyTable
from rich.console import Console, Group
from rich.columns import Columns
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# ──[ Internal Module Imports ]─────────────────────────────────────────────────────────
from modules import cpu, io, mem, net


# ──[ Helpers ]─────────────────────────────────────────────────────────────────────────
def _usage_bar(percent: float, width: int = 25) -> str:
    filled = int(percent / 100 * width)
    bar    = "█" * filled + "░" * (width - filled)
    color  = "green" if percent < 60 else "yellow" if percent < 85 else "red"
    return f"[{color}]{bar}[/{color}]"


def _color_pct(percent: float) -> str:
    color = "green" if percent < 60 else "yellow" if percent < 85 else "red"
    return f"[{color}]{percent:.1f}%[/{color}]"


def _sysinfo() -> tuple:
    hostname = socket.gethostname()
    os_name  = platform.system()
    kernel   = platform.release()
    uptime_s = time.time() - psutil.boot_time()
    uptime   = (
        f"{int(uptime_s // 86400)}d "
        f"{int((uptime_s % 86400) // 3600)}h "
        f"{int((uptime_s % 3600) // 60)}m"
    )
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    return hostname, os_name, kernel, uptime, timestamp


# ──[ Panel Builders ]──────────────────────────────────────────────────────────────────
def _cpu_panel(cpu_data, bar_width: int = 25) -> Table:
    t = Table(box=None, show_header=False, padding=(0, 1))
    t.add_column("Core",  style="cyan",    no_wrap=True, width=8)
    t.add_column("Bar",   no_wrap=True)
    t.add_column("Usage", justify="right", no_wrap=True, width=7)
    for i, pct in enumerate(cpu_data["CPU_PerCore"]):
        t.add_row(f"Core {i}", _usage_bar(pct, bar_width), _color_pct(pct))
    t.add_row("", "", "")
    cpu_load = ", ".join(f"{x:.2f}" for x in cpu_data["CPU_Load"])
    t.add_row("[dim]Load Avg[/dim]", f"[dim]{cpu_load}[/dim]", "")
    if cpu_data["CPU_Freq"]:
        t.add_row(
            "[dim]Freq[/dim]",
            f"[dim]{cpu_data['CPU_Freq'].current:.0f} MHz[/dim]",
            "",
        )
    return t


def _mem_panel(mem_data, bar_width: int = 22) -> Table:
    pct = mem_data["Percent"]
    t = Table(box=None, show_header=False, padding=(0, 1))
    t.add_column("Key",   no_wrap=True)
    t.add_column("Value", justify="right", no_wrap=True)
    t.add_row(_usage_bar(pct, bar_width), _color_pct(pct))
    t.add_row("[cyan]Total[/cyan]",     f"{mem_data['Total']     / (1024**3):.2f} GB")
    t.add_row("[cyan]Used[/cyan]",      f"{mem_data['Used']      / (1024**3):.2f} GB")
    t.add_row("[cyan]Free[/cyan]",      f"{mem_data['Free']      / (1024**3):.2f} GB")
    t.add_row("[cyan]Available[/cyan]", f"{mem_data['Available'] / (1024**3):.2f} GB")
    return t


def _disk_panel(disk_data, bar_width: int = 22) -> Table:
    t = Table(box=None, show_header=False, padding=(0, 1))
    t.add_column("Mount",  style="cyan",    no_wrap=True)
    t.add_column("Type",   no_wrap=True,    width=5)
    t.add_column("Bar",    no_wrap=True)
    t.add_column("Usage",  justify="right", no_wrap=True, width=6)
    t.add_column("Total",  justify="right", no_wrap=True)
    for part in disk_data["Disk_Partitions"]:
        mp = part["Mountpoint"]
        if mp in disk_data["Disk_Usage"]:
            u = disk_data["Disk_Usage"][mp]
            t.add_row(
                mp, part["FSType"],
                _usage_bar(u["Percent"], bar_width),
                _color_pct(u["Percent"]),
                f"{u['Total'] / (1024**3):.2f} GB",
            )
    return t


def _iface_panel(net_data) -> Table:
    t = Table(box=None, show_header=False, padding=(0, 1))
    t.add_column("Interface", style="cyan",  no_wrap=True)
    t.add_column("IP",        style="green", no_wrap=True)
    for iface, ip in net_data["Addresses"].items():
        t.add_row(iface, ip)
    return t


def _io_panel(net_data) -> Table:
    net_io = net_data["I/O"]
    t = Table(box=None, show_header=False, padding=(0, 1))
    t.add_column("Direction", style="cyan",  no_wrap=True)
    t.add_column("Volume",    style="green", justify="right", no_wrap=True)
    t.add_row("Sent",     f"{net_io.bytes_sent / (1024**2):.2f} MB")
    t.add_row("Received", f"{net_io.bytes_recv / (1024**2):.2f} MB")
    return t


# ──[ Plain Text Snapshot (non-TTY) ]───────────────────────────────────────────────────
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
    hostname, os_name, kernel, uptime, timestamp = _sysinfo()

    # ──[ Memory Table ]────────────────────────────────────────────────────────────────
    mem_table = PrettyTable(["Metric", "Value"])
    mem_table.align["Metric"] = "l"
    mem_table.align["Value"]  = "r"
    mem_table.add_rows([
        ["Total",     f"{mem_data['Total']     / (1024**3):.2f} GB"],
        ["Used",      f"{mem_data['Used']      / (1024**3):.2f} GB"],
        ["Free",      f"{mem_data['Free']      / (1024**3):.2f} GB"],
        ["Available", f"{mem_data['Available'] / (1024**3):.2f} GB"],
        ["Usage",     f"{mem_data['Percent']}%"],
    ])

    # ──[ CPU Table ]───────────────────────────────────────────────────────────────────
    cpu_load  = ", ".join(f"{x:.2f}" for x in cpu_data["CPU_Load"])
    cpu_table = PrettyTable(["Metric", "Value"])
    cpu_table.align["Metric"] = "l"
    cpu_table.align["Value"]  = "r"
    cpu_table.add_rows([
        ["Logical Cores",  str(cpu_data["CPU_Count"])],
        ["Physical Cores", str(cpu_data["CPU_Physical"])],
        ["Usage",          f"{cpu_data['CPU_Percent']}%"],
        ["Load Avg",       cpu_load],
    ])

    # ──[ Disk Table (all mountpoints) ]────────────────────────────────────────────────
    disk_table = PrettyTable(["Mount", "Type", "Total", "Used", "Free", "Usage"])
    disk_table.align["Mount"] = "l"
    disk_table.align["Type"]  = "l"
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
    iface_table.align["Interface"]  = "l"
    iface_table.align["IP Address"] = "l"
    for iface, ip in net_data["Addresses"].items():
        iface_table.add_row([iface, ip])

    # ──[ Network I/O Table ]───────────────────────────────────────────────────────────
    net_io   = net_data["I/O"]
    io_table = PrettyTable(["Direction", "Volume"])
    io_table.align["Direction"] = "l"
    io_table.align["Volume"]    = "r"
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
    """Snapshot mode: rich panel layout rendered once, adapts to content size."""
    # ──[ Fetch Subsystem Data ]────────────────────────────────────────────────────────
    cpu_data  = cpu.get_cpu_info()
    mem_data  = mem.get_mem_info()
    disk_data = io.get_io_info()
    net_data  = net.get_net_info()

    # ──[ System Metadata ]─────────────────────────────────────────────────────────────
    hostname, os_name, kernel, uptime, timestamp = _sysinfo()
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
            Panel(_cpu_panel(cpu_data),  title="[bold]CPU[/bold]",    expand=True),
            Panel(_mem_panel(mem_data),  title="[bold]Memory[/bold]", expand=True),
        ], expand=True),
        Panel(_disk_panel(disk_data), title="[bold]Disk[/bold]"),
        Columns([
            Panel(_iface_panel(net_data), title="[bold]Network Interfaces[/bold]", expand=True),
            Panel(_io_panel(net_data),    title="[bold]Network I/O[/bold]",        expand=True),
        ], expand=True),
    )


# ──[ Live Layout ]─────────────────────────────────────────────────────────────────────
def build_live_layout(paused: bool = False) -> Layout:
    """Watch mode: full-terminal split-panel layout, refreshed on interval."""
    # ──[ Fetch Subsystem Data ]────────────────────────────────────────────────────────
    cpu_data  = cpu.get_cpu_info()
    mem_data  = mem.get_mem_info()
    disk_data = io.get_io_info()
    net_data  = net.get_net_info()

    # ──[ System Metadata ]─────────────────────────────────────────────────────────────
    hostname, os_name, kernel, uptime, timestamp = _sysinfo()
    header = (
        f"[bold cyan]Hostname:[/bold cyan] {hostname}   "
        f"[bold cyan]OS:[/bold cyan] {os_name}   "
        f"[bold cyan]Kernel:[/bold cyan] {kernel}   "
        f"[bold cyan]Uptime:[/bold cyan] {uptime}   "
        f"[bold cyan]Snapshot:[/bold cyan] {timestamp}"
    )

    pause_tag  = "  [bold yellow][ PAUSED ][/bold yellow]" if paused else ""
    footer_txt = Text.from_markup(
        f" [dim][[/dim][bold]q[/bold][dim]][/dim] quit  "
        f"[dim][[/dim][bold]p[/bold][dim]][/dim] pause/resume{pause_tag}"
    )

    # ──[ Assemble Layout ]─────────────────────────────────────────────────────────────
    layout = Layout()
    layout.split_column(
        Layout(name="header",  size=3),
        Layout(name="top",     ratio=5),
        Layout(name="disk",    ratio=3),
        Layout(name="network", ratio=2),
        Layout(name="footer",  size=1),
    )
    layout["top"].split_row(
        Layout(name="cpu",    ratio=3),
        Layout(name="memory", ratio=2),
    )
    layout["network"].split_row(
        Layout(name="ifaces"),
        Layout(name="net_io"),
    )

    layout["header"].update(Panel(header, title="[bold green]SNAPUTIL[/bold green]"))
    layout["cpu"].update(Panel(_cpu_panel(cpu_data,  bar_width=28), title="[bold]CPU[/bold]"))
    layout["memory"].update(Panel(_mem_panel(mem_data, bar_width=20), title="[bold]Memory[/bold]"))
    layout["disk"].update(Panel(_disk_panel(disk_data, bar_width=24), title="[bold]Disk[/bold]"))
    layout["ifaces"].update(Panel(_iface_panel(net_data), title="[bold]Network Interfaces[/bold]"))
    layout["net_io"].update(Panel(_io_panel(net_data),    title="[bold]Network I/O[/bold]"))
    layout["footer"].update(footer_txt)

    return layout


# ──[ Keyboard Listener ]───────────────────────────────────────────────────────────────
_stop_event  = threading.Event()
_pause_event = threading.Event()


def _key_listener():
    """Background thread: reads single keypresses to drive q/p actions."""
    if not _POSIX:
        return
    fd  = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        _tty.setraw(fd)
        while not _stop_event.is_set():
            ch = sys.stdin.read(1)
            if ch in ("q", "Q", "\x03"):
                _stop_event.set()
            elif ch in ("p", "P"):
                if _pause_event.is_set():
                    _pause_event.clear()
                else:
                    _pause_event.set()
    except Exception:
        pass
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


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

    is_tty  = sys.stdout.isatty()
    console = Console()

    if args.watch:
        if not is_tty:
            print("snaputil: --watch requires a TTY", file=sys.stderr)
            sys.exit(1)
        _stop_event.clear()
        _pause_event.clear()
        key_thread = threading.Thread(target=_key_listener, daemon=True)
        key_thread.start()
        try:
            with Live(
                build_live_layout(),
                console=console,
                screen=True,
                refresh_per_second=4,
            ) as live:
                while not _stop_event.is_set():
                    time.sleep(args.watch)
                    if not _stop_event.is_set():
                        live.update(build_live_layout(paused=_pause_event.is_set()))
        finally:
            _stop_event.set()
    elif is_tty:
        console.print(build_dashboard())
    else:
        print(basic_snap())
