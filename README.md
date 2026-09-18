
# snaputil

[![built by arpatek](.assets/badge.svg)](https://arpatek.dev)
[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.6%2B-blue.svg)](https://www.python.org/downloads/)
[![Status](https://img.shields.io/badge/status-alpha-lightgrey.svg)]()

**snaputil** is a modular Python tool that provides a real-time snapshot of system metrics in clean, formatted tables. It reports information on:

- Hostname, OS, and kernel
- CPU load, frequency, and utilization
- Memory usage and availability
- Disk partitions and usage (all mountpoints)
- Network interface data and I/O

> Long-term goal: evolve into a lightweight live-dashboard monitoring tool (btop-style TUI).

---

### Features

`[POSIX-friendly]` Designed to work seamlessly in Unix-like environments, including headless servers.  
`[Modular Design]` Each subsystem is decoupled into a module (CPU, Mem, I/O, Net) for easy extension.  
`[Rich Output]` Uses `rich` for styled, columnar tables and panel-based dashboard layout.  
`[Log Friendly]` Auto-detects TTY — falls back to plain prettytable output when piped to a file.  
`[Automation Ready]` Clean stdout output for chaining, logging, or integration.  
`[Extensible]` Modular design makes it straightforward to add JSON output, extra subsystems, or a future TUI layer.

---

### Usage

```bash
./snaputil.py            # styled snapshot (auto-detected TTY)
./snaputil.py >> sys.log # plain-text log (auto-detected, no TTY)
```

When stdout is not a TTY (piped to a file or log), snaputil automatically falls back
to plain-text prettytable output — safe for logging and automation pipelines.

---

### Project Structure

```text
snaputil/
├── snaputil.py       # Main entry script
├── modules/
│   ├── __init__.py   # Package marker
│   ├── cpu.py        # CPU metrics
│   ├── mem.py        # Memory metrics
│   ├── io.py         # Disk I/O and partition info
│   └── net.py        # Network stats
└── README.md
```

Each module exposes a `get_<subsystem>_info()` function that returns a dictionary of structured metrics.

---

### Example Output

**Terminal (TTY)**

```text
╭──────────────────────────────────────── SNAPUTIL ────────────────────────────────────────╮
│ Hostname: dev-vm   OS: Linux   Kernel: 6.6.12-arch1-1   Uptime: 1d 3h 42m               │
│ Snapshot: 2025-06-04 18:14:32                                                            │
╰──────────────────────────────────────────────────────────────────────────────────────────╯
╭────────────────────── CPU ───────────────────────╮ ╭────────────── Memory ───────────────╮
│  Core 0    ████████░░░░░░░░░░░░░░░░░    33.3%    │ │  █████████████░░░░░░░░     53.7%    │
│  Core 1    ████████████░░░░░░░░░░░░░    50.2%    │ │  Total                   7.67 GB    │
│  Core 2    ████░░░░░░░░░░░░░░░░░░░░░    17.6%    │ │  Used                    4.12 GB    │
│  Core 3    █░░░░░░░░░░░░░░░░░░░░░░░░     4.0%    │ │  Free                    2.21 GB    │
│                                                  │ │  Available               3.45 GB    │
│  Load Avg  0.57, 0.89, 1.22                      │ ╰─────────────────────────────────────╯
│  Freq      2400 MHz                              │
╰──────────────────────────────────────────────────╯
╭────────────────────────────────────────── Disk ──────────────────────────────────────────╮
│  /    ext4   ████████░░░░░░░░░░░░░░   42.0%   50.00 GB                                   │
╰──────────────────────────────────────────────────────────────────────────────────────────╯
╭─────────── Network Interfaces ────────────╮ ╭─────────────── Network I/O ────────────────╮
│  eth0  192.168.0.100                      │ │  Sent        85.23 MB                      │
╰───────────────────────────────────────────╯ │  Received   124.67 MB                      │
                                              ╰────────────────────────────────────────────╯
```

**Piped / log output** (`./snaputil.py >> system.log`)

```text
==============================================
  SNAPUTIL SYSTEM SNAPSHOT
==============================================
  Hostname  : dev-vm
  OS        : Linux
  Kernel    : 6.6.12-arch1-1
  Uptime    : 1d 3h 42m
  Snapshot  : 2025-06-04 18:14:32
==============================================

[ Memory ]
+-----------+-----------+
| Metric    |     Value |
+-----------+-----------+
| Total     |  7.67 GB  |
| Used      |  4.12 GB  |
| Free      |  2.21 GB  |
| Available |  3.45 GB  |
| Usage     |    53.7%  |
+-----------+-----------+

[ CPU ]
+----------------+------------------+
| Metric         |            Value |
+----------------+------------------+
| Logical Cores  |                4 |
| Physical Cores |                2 |
| Usage          |            12.8% |
| Load Avg       | 0.57, 0.89, 1.22 |
+----------------+------------------+

[ Disk ]
+-------+------+----------+----------+-----------+-------+
| Mount | Type |    Total |     Used |      Free | Usage |
+-------+------+----------+----------+-----------+-------+
| /     | ext4 | 50.00 GB | 20.42 GB |  27.89 GB | 42.0% |
+-------+------+----------+----------+-----------+-------+

[ Network Interfaces ]
+-----------+---------------+
| Interface | IP Address    |
+-----------+---------------+
| eth0      | 192.168.0.100 |
+-----------+---------------+

[ Network I/O ]
+-----------+-----------+
| Direction |    Volume |
+-----------+-----------+
| Sent      |  85.23 MB |
| Received  | 124.67 MB |
+-----------+-----------+
```

---

### Installation

1. Clone the repository:

   ```bash
   git clone https://codeberg.org/arpatek/snaputil.git
   cd snaputil
   ```

2. Install dependencies:

   ```bash
   pip install psutil rich prettytable
   ```

3. Run the snapshot tool:

   ```bash
   ./snaputil.py
   ```
