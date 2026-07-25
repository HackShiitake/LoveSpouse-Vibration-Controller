# Contributing

Thanks for hacking on this project! It's built to be forked and modified. This
guide covers the layout, the conventions, and the most common changes.

## Getting set up

```bash
pip install winsdk          # real hardware; skip if you only use --dry-run
python main.py --dry-run --log-level DEBUG
```

`--dry-run` swaps the BLE driver for one that just logs, so you can develop the
UI, API, and playback engine without any hardware or even Bluetooth.

Run the tests before and after your change:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests
```

## How the pieces fit

Data flows in one direction:

```
UI / HTTP API  →  PlaybackService  →  CommandWorker  →  ToyDriver  →  BLE
```

- **`models.py`** — `VibrationCommand` and `Pattern`. All parsing/validation.
- **`patterns.py`** — reads `.vibepattern` files into `Pattern` objects.
- **`playback.py`** — turns a slider level or a pattern into a stream of
  commands. Owns the playback threads and the stop logic.
- **`worker.py`** — the *only* thread that touches the device. Everything is
  queued here, which is what keeps the app race-free.
- **`bluetooth.py`** — the BLE advertising driver plus a `DryRunToyDriver`. Both
  satisfy the `ToyDriver` protocol.
- **`api.py`** — the local HTTP server.
- **`theme.py`** — every color, font, and spacing value. No visuals live
  anywhere else.
- **`gui.py`** — the tkinter window, built from small `_build_*` methods.

## Recipes

### Add or restyle a theme
Edit a `Palette` in `theme.py`, or copy `LIGHT_THEME`, rename it, tweak the hex
values, and add it to the `THEMES` dict. It's immediately available via
`--theme <name>` and the in-app toggle. No widget code changes.

### Add a UI control
Write a `_build_<name>(self, parent)` method in `ControllerWindow` and call it
from `_build`. Use `self._theme` for spacing (`space_sm`, `space_md`, …) and a
named ttk style for colors — never a literal hex value.

### Add an HTTP endpoint
Extend `RequestHandler.do_GET` in `api.py`. Keep responses JSON and set the CORS
header via the existing `_json_response` helper.

### Add a command time unit
Add the suffix to `COMMAND_PATTERN` and `_UNIT_SECONDS` in `models.py`, and to
`API_PATH_PATTERN` in `api.py`. Add a parser test in `tests/test_models.py`.

### Swap the transport (different protocol/hardware)
Implement the `ToyDriver` protocol (a single `send(strength, duration_seconds)`
method) and construct `CommandWorker` with it in `app.py`.

## Conventions

- No new runtime dependencies unless there's a strong reason — the app is
  deliberately just `winsdk` + the standard library.
- Keep hardware I/O on the worker thread. UI callbacks and API handlers should
  enqueue work, never advertise directly.
- Type hints and short docstrings on public methods; match the surrounding style.
- Add a test when you touch parsing or pattern loading.
