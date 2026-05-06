# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [v0.4.1] - 2026-05-05
### Removed
- Live refresh mode (`-w` / `--watch`) — `rich.Live` + `rich.layout.Layout` produced
  unavoidable flicker and terminal-height clipping on typical terminal sizes. Removed
  pending a proper curses or textual-based implementation in a future version.
- `build_live_layout()`, `_key_listener()`, and all related threading/termios imports.

---

## [v0.4.0] - 2026-05-05
### Changed
- Replaced flat table layout with color-coded progress bars throughout (green < 60%, yellow < 85%, red ≥ 85%)
- CPU section now shows per-core breakdown with individual bars, load average, and frequency
- Memory section now leads with a usage bar above the stats
- Disk section now shows a per-mountpoint bar, usage percentage, and total size inline
- Snapshot mode (`build_dashboard`) and live mode (`build_live_layout`) share the same panel builders
- `modules/cpu.py` now returns `CPU_PerCore` (list of per-core percentages); `CPU_Percent` is computed as their mean

### Added
- `build_live_layout()` — `rich.layout.Layout`-based full-terminal split-panel dashboard for watch mode
- Keyboard input thread (`q` quit, `p` pause/resume) with POSIX termios; degrades gracefully on non-POSIX
- Pause indicator in footer when dashboard is paused
- Footer with keybind hints (`[q] quit  [p] pause/resume`)

---

## [v0.3.0] - 2026-05-05
### Changed
- Replaced `prettytable` with `rich` for all output rendering
- Snapshot output now uses styled panels and `rich.table.Table` with `SIMPLE_HEAVY` box style
- Main entry function renamed from `basic_snap()` to `build_dashboard()`

### Added
- Live refresh mode via `rich.Live` — `-w` flag with optional interval (default: 2s)
- Dashboard layout using `rich.columns.Columns` — Memory/CPU side by side, Network Interfaces/I/O side by side
- `argparse` CLI with `-w / --watch` flag
- TTY auto-detection — rich dashboard in terminal, plain prettytable output when piped to a file or log

---

## [v0.2.0] - 2026-05-05
### Changed
- Renamed project from **gTOP** to **snaputil** across all files, docstrings, and documentation
- Replaced plain-text ASCII output with `prettytable`-formatted tables for all subsystems
- Disk section now iterates all mountpoints instead of hardcoding `"/"`
- Network I/O now uses named attributes (`.bytes_sent` / `.bytes_recv`) instead of positional index access

### Added
- `modules/__init__.py` to make the modules directory an explicit Python package
- `prettytable` as a declared dependency

### Fixed
- `pprint` top-level imports in all modules moved to inline imports inside `main()` debug functions and commented at module level with an explanatory note

---

## [v0.1.0] - 2025-06-04
### Added
- Initial implementation of `gtop.py` for structured system snapshots
- Modular metric collection: `cpu.py`, `mem.py`, `io.py`, `net.py`
- Human-readable stdout snapshot with CPU, memory, disk, and network data
- MIT License
- Project README with usage, structure, and installation guide
- Module-level and function-level documentation across all components
