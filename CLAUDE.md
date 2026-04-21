# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Application

```bash
pip install -r requirements.txt
python main.py
```

No build step, no test suite. The app is a single-window PyQt6 desktop application launched via `main.py`.

## Architecture

This is a PyQt6 desktop app for browsing and downloading files from OpenList (AList fork) network drives via aria2.

### Three-layer structure

- **`core/`** — Business logic, no Qt dependencies except `file_scanner.py` which uses QThread/signals for async scanning.
  - `api_client.py` / `token_manager.py` — OpenList REST API (login, file listing, file info). Token auto-refresh on 401.
  - `aria2_rpc.py` — aria2 JSON-RPC client (start process, add downloads, verify connection).
  - `file_scanner.py` — Recursive directory scanner with suffix filtering, runs in QThread.
- **`gui/`** — PyQt6 widgets. Each panel is a self-contained QWidget.
  - `main_window.py` — QMainWindow that composes all panels and wires signals.
  - `styles.py` — Global QSS stylesheet (LIGHT_THEME) and default constants.
  - `login_widget.py`, `file_list_widget.py`, `aria2_widget.py` — Individual panels.
- **`utils/`** — Cross-cutting: logging (daily rotating files in `logs/`), format helpers, config persistence (`config/user_config.json`).

### Key data flow

1. User logs in → `TokenManager` stores token → used by `OpenListClient` for all API calls
2. User scans path → `FileScanner` (QThread) recursively calls `list_files` → emits `scan_finished(list[FileInfo])` → `FileListWidget.populate()` displays results
3. User clicks download → each file's `raw_url` fetched via `get_file_info` → pushed to aria2 via `aria2.addUri` JSON-RPC

### Config persistence

`utils/config_manager.py` saves/loads `config/user_config.json`. Triggered on: successful login, successful aria2 start, scan button click. Usernames are saved; passwords are never persisted.

## Conventions

- All `@author` annotations use `awen`
- All UI text and comments in Chinese
- Async operations use QThread workers (see `aria2_widget.py` `Aria2Worker` pattern) to avoid blocking the UI
- Button styles controlled via QSS object names: `browseBtn` (light secondary), `toolBtn` (light with border), `primaryBtn` (blue primary)
