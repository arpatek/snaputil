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
- `rich` for formatted tables and styled dashboard output
- `prettytable` for plain-text output when stdout is not a TTY
- `platform`, `socket`, `time` from stdlib
- `modules/` directory containing:
    - cpu.py with get_cpu_info()
    - mem.py with get_mem_info()
    - io.py  with get_io_info()
    - net.py with get_net_info()

Sample Usage:
-------------
$ ./snaputil.py             # styled snapshot (TTY auto-detected)
$ ./snaputil.py >> sys.log  # plain-text log (auto-detected, no TTY)
"""

__version__ = "0.4.1"

# ──[ Standard Library Imports ]────────────────────────────────────────────────────────
# from pprint import pprint  # debug artifact — useful for inspecting raw dicts during TUI development
import sys
import socket
import time
import platform
import psutil
from prettytable import PrettyTable
from rich.console import Console, Group
from rich.columns import Columns
from rich.panel import Panel
from rich.table import Table

# ──[ Internal Module Imports ]─────────────────────────────────────────────────────────
from modules import cpu, io, mem, net


# ──[ Helpers ]─────────────────────────────────────────────────────────────────────────
def _usage_bar(percent: float, width: int = 25) -> str:
    """Generate a color-coded Unicode block progress bar as a Rich markup string.

    Color thresholds: green below 60 %, yellow from 60 % to 84 %, red at 85 %
    and above.

    Args:
        percent (float): Usage level between 0.0 and 100.0.
        width (int): Total number of bar characters. Defaults to 25.

    Returns:
        str: Rich markup string containing the colored bar, e.g.
            ``'[green]████████░░░░░░░░░[/green]'``.

    Example:
        >>> _usage_bar(40.0, width=10)
        '[green]████░░░░░░[/green]'
        >>> _usage_bar(70.0, width=10)
        '[yellow]███████░░░[/yellow]'
        >>> _usage_bar(90.0, width=10)
        '[red]█████████░[/red]'
    """
    filled = int(percent / 100 * width)
    bar    = "█" * filled + "░" * (width - filled)
    color  = "green" if percent < 60 else "yellow" if percent < 85 else "red"
    return f"[{color}]{bar}[/{color}]"


def _color_pct(percent: float) -> str:
    """Format a percentage as a color-coded Rich markup string.

    Applies the same thresholds as :func:`_usage_bar`: green below 60 %,
    yellow 60–84 %, red 85 % and above.

    Args:
        percent (float): Usage level between 0.0 and 100.0.

    Returns:
        str: Rich markup string, e.g. ``'[green]45.0%[/green]'``.

    Example:
        >>> _color_pct(45.0)
        '[green]45.0%[/green]'
        >>> _color_pct(75.0)
        '[yellow]75.0%[/yellow]'
        >>> _color_pct(92.0)
        '[red]92.0%[/red]'
    """
    color = "green" if percent < 60 else "yellow" if percent < 85 else "red"
    return f"[{color}]{percent:.1f}%[/{color}]"


def _sysinfo() -> tuple:
    """Collect static system metadata for the dashboard header.

    Gathers hostname, OS name, kernel version, formatted uptime, and a
    human-readable timestamp at the moment of the call.

    Returns:
        tuple: A five-element tuple of pre-formatted strings:
            ``(hostname, os_name, kernel, uptime, timestamp)``

            - ``hostname`` (str): Machine hostname.
            - ``os_name`` (str): OS name from ``platform.system()``
              (e.g. ``'Linux'``).
            - ``kernel`` (str): Kernel release from ``platform.release()``.
            - ``uptime`` (str): Human-readable uptime (e.g. ``'1d 3h 42m'``).
            - ``timestamp`` (str): Current local time as ``'YYYY-MM-DD HH:MM:SS'``.

    Example:
        >>> hostname, os_name, kernel, uptime, ts = _sysinfo()
        >>> assert os_name in ("Linux", "Darwin", "Windows")
    """
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
def _cpu_panel(cpu_data: dict, bar_width: int = 25) -> Table:
    """Build a Rich Table showing per-core CPU usage bars.

    Displays one row per logical core with a color-coded progress bar and
    percentage. A blank separator row is followed by load average and, if
    available, current CPU frequency.

    Args:
        cpu_data (dict): Output of :func:`modules.cpu.get_cpu_info`. Must
            contain ``CPU_PerCore`` (list[float]), ``CPU_Load`` (tuple), and
            ``CPU_Freq`` (psutil.scpufreq | None).
        bar_width (int): Width of each progress bar in characters. Defaults
            to 25. Use a larger value in the live layout where the CPU panel
            is wider.

    Returns:
        rich.table.Table: Three-column table (Core, Bar, Usage) with no box
            borders, intended to be wrapped in a :class:`rich.panel.Panel`.
    """
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


def _mem_panel(mem_data: dict, bar_width: int = 22) -> Table:
    """Build a Rich Table showing a memory usage bar followed by stats.

    The first row contains the overall usage bar and color-coded percentage.
    Subsequent rows show Total, Used, Free, and Available in GB.

    Args:
        mem_data (dict): Output of :func:`modules.mem.get_mem_info`. Must
            contain ``Percent``, ``Total``, ``Used``, ``Free``, and
            ``Available`` keys.
        bar_width (int): Width of the progress bar in characters.
            Defaults to 22.

    Returns:
        rich.table.Table: Two-column table (Key, Value) with no box borders,
            intended to be wrapped in a :class:`rich.panel.Panel`.
    """
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


def _disk_panel(disk_data: dict, bar_width: int = 22) -> Table:
    """Build a Rich Table showing per-mountpoint disk usage bars.

    Each row represents a mounted partition with its filesystem type, a
    color-coded usage bar, usage percentage, and total partition size.
    Mountpoints absent from ``Disk_Usage`` (e.g. due to ``PermissionError``)
    are silently skipped.

    Args:
        disk_data (dict): Output of :func:`modules.io.get_io_info`. Must
            contain ``Disk_Partitions`` (list) and ``Disk_Usage`` (dict).
        bar_width (int): Width of each progress bar in characters.
            Defaults to 22.

    Returns:
        rich.table.Table: Five-column table (Mount, Type, Bar, Usage, Total)
            with no box borders, intended to be wrapped in a
            :class:`rich.panel.Panel`.
    """
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


def _iface_panel(net_data: dict) -> Table:
    """Build a Rich Table listing active network interfaces and their IPv4 addresses.

    Only interfaces present in ``net_data["Addresses"]`` are shown (non-loopback
    IPv4 only, as filtered by :func:`modules.net.get_net_info`).

    Args:
        net_data (dict): Output of :func:`modules.net.get_net_info`. Must
            contain an ``Addresses`` key mapping interface names to IP strings.

    Returns:
        rich.table.Table: Two-column table (Interface, IP) with no box borders,
            intended to be wrapped in a :class:`rich.panel.Panel`.
    """
    t = Table(box=None, show_header=False, padding=(0, 1))
    t.add_column("Interface", style="cyan",  no_wrap=True)
    t.add_column("IP",        style="green", no_wrap=True)
    for iface, ip in net_data["Addresses"].items():
        t.add_row(iface, ip)
    return t


def _io_panel(net_data: dict) -> Table:
    """Build a Rich Table showing cumulative system-wide network I/O totals.

    Values reflect bytes transferred since system boot, not per-interval rates.

    Args:
        net_data (dict): Output of :func:`modules.net.get_net_info`. Must
            contain an ``I/O`` key holding a ``psutil.snetio`` named tuple
            with ``bytes_sent`` and ``bytes_recv`` attributes.

    Returns:
        rich.table.Table: Two-column table (Direction, Volume) with no box
            borders, intended to be wrapped in a :class:`rich.panel.Panel`.
    """
    net_io = net_data["I/O"]
    t = Table(box=None, show_header=False, padding=(0, 1))
    t.add_column("Direction", style="cyan",  no_wrap=True)
    t.add_column("Volume",    style="green", justify="right", no_wrap=True)
    t.add_row("Sent",     f"{net_io.bytes_sent / (1024**2):.2f} MB")
    t.add_row("Received", f"{net_io.bytes_recv / (1024**2):.2f} MB")
    return t


# ──[ Plain Text Snapshot (non-TTY) ]───────────────────────────────────────────────────
def basic_snap() -> str:
    """Collect and format a plain-text system snapshot using prettytable.

    Intended for non-TTY contexts such as piped output, log files, and
    automation pipelines. Produces no ANSI color codes or Unicode box
    characters — safe for any plain-text consumer.

    The call blocks for approximately 1 second while the CPU interval
    measurement completes inside :func:`modules.cpu.get_cpu_info`.

    Returns:
        str: A multi-section preformatted string containing a header block
            followed by Memory, CPU, Disk, Network Interfaces, and Network I/O
            tables. Suitable for ``print()`` or direct ``file.write()``.

    Example:
        >>> output = basic_snap()
        >>> assert "SNAPUTIL SYSTEM SNAPSHOT" in output

        Append to a log file::

            with open("system.log", "a") as f:
                f.write(basic_snap())
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
    """Build a rich panel-based snapshot dashboard for TTY one-shot output.

    Collects all subsystem data and assembles a ``rich.console.Group``
    containing:

    - A full-width header panel (hostname, OS, kernel, uptime, timestamp).
    - A two-column row: CPU (per-core bars) | Memory (usage bar + stats).
    - A full-width Disk panel (per-mountpoint bars).
    - A two-column row: Network Interfaces | Network I/O.

    Layout adapts to terminal width via ``rich.columns.Columns``. The call
    blocks for ~1 second during CPU measurement.

    Returns:
        rich.console.Group: A renderable group suitable for
            ``Console().print(build_dashboard())``.

    Example:
        >>> from rich.console import Console
        >>> Console().print(build_dashboard())  # doctest: +SKIP
    """
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


# ──[ Entry Point ]─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    console = Console()
    if sys.stdout.isatty():
        console.print(build_dashboard())
    else:
        print(basic_snap())
