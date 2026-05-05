# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
