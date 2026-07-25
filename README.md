# LoveSpouse Vibration Controller

A Windows desktop controller for LoveSpouse-style Bluetooth LE toys. It ships a
polished tkinter GUI, a local HTTP API for automation, a `.vibepattern` playback
engine, a headless sidecar mode, and Minecraft integrations — a **Forge 1.12.2
mod** ([`DamageBuzz/`](DamageBuzz/README.md)) that vibrates when you take damage,
plus an older Paper server plugin ([`DamageCurl/`](DamageCurl)).

The device is driven purely through **BLE advertising** — no pairing, no GATT
connection. Commands are serialized through a dedicated worker thread so the UI
and the API can never step on each other.

<p align="center">
  <em>Light and dark themes, a live intensity meter, and a pattern library — all
  from a single design-token file.</em>
</p>

## Highlights

- **Professional UI** — light/dark themes, a segmented intensity meter, live
  status indicator, and keyboard shortcuts. Every color, font, and spacing value
  lives in one file (`theme.py`), so reskinning is a five-minute job.
- **Robust BLE backend** — the radio is checked (and turned on) at startup, and
  advertising never hangs: a failed publish reports a clear reason instead of
  blocking forever.
- **Clean architecture** — playback, transport, HTTP, GUI, config, and parsing
  are separate modules with single responsibilities. Easy to read, easy to fork.
- **Automation-friendly** — a tiny HTTP API any script, stream deck, or game can
  hit.

## Requirements

- Windows 10 or newer (BLE advertising uses the Windows Runtime)
- Python 3.9+
- [`winsdk`](https://pypi.org/project/winsdk/) for real Bluetooth control
- Java 17 + Maven — only if you build the Paper plugin

```bash
pip install winsdk
```

> **Bluetooth must be on.** The app tries to enable the radio automatically at
> startup; if it can't, it tells you instead of failing silently. See
> [Troubleshooting](#troubleshooting).

## Quick start

```bash
python main.py                 # normal hardware mode
python main.py --dry-run       # develop without any Bluetooth hardware
python main.py --theme dark    # start in dark mode
```

All options:

| Flag | Default | Description |
| --- | --- | --- |
| `--host` | `127.0.0.1` | HTTP API bind host |
| `--port` | `4545` | HTTP API port |
| `--pattern-dir` | `pattern/` | Directory of `.vibepattern` files |
| `--dry-run` | off | Log commands instead of advertising them |
| `--log-level` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` / `CRITICAL` |
| `--theme` | `light` | `light` or `dark` |
| `--headless` | off | Run the API + BLE backend with no GUI (sidecar mode) |

**Keyboard shortcuts:** `Esc` = emergency stop · `Ctrl+D` = toggle theme ·
`Enter` / double-click a pattern to play it.

## HTTP API

```text
GET /API/{strength}-{duration}{unit}
```

`strength` is `0`–`9`; `unit` is `ms`, `s`, `m` (minutes), or `h` (hours).

```bash
curl http://localhost:4545/API/5-1000ms
curl http://localhost:4545/API/3-1.5s
curl http://localhost:4545/API/0-100ms      # 0 = stop
```

```json
{ "status": "ok", "strength": 5, "duration": "1000ms" }
```

Any request to a path that isn't a valid command returns a small usage hint, so
`GET /` is a handy health check.

## Pattern files

Patterns live in `pattern/` and use the `.vibepattern` extension. The first line
is an optional JSON header; every following line is a step
`{strength}-{duration}{unit}` (`unit` = `ms`, `s`, `m`, `h`):

```text
{"name": "Pulse Wave", "author": "Developer"}
3-500ms
0-250ms
5-750ms
7-1s
0-2m
```

Drop a new file in `pattern/` and hit **Reload** in the UI — no restart needed.
Invalid lines are skipped with a warning; a pattern with zero valid steps is
ignored.

## Architecture

```text
main.py ── src/lovespouse_controller/
   __main__.py     CLI entry point
   config.py       AppConfig + argument parsing
   models.py       VibrationCommand / Pattern (parsing, validation)
   patterns.py     PatternRepository — loads .vibepattern files
   bluetooth.py    BLE advertising driver (+ dry-run driver)
   worker.py       CommandWorker — serializes all device I/O on one thread
   playback.py     PlaybackService — continuous + pattern playback
   api.py          ApiServer — the local HTTP API
   theme.py        Design tokens + ttk styling (all visuals live here)
   gui.py          ControllerWindow — the desktop UI
```

Data flows one way: **UI / API → PlaybackService → CommandWorker → ToyDriver →
BLE**. The worker is the single choke point that talks to hardware, which is why
nothing races and why swapping the driver (e.g. for tests) is trivial.

## Extending it

Common changes and where they go:

- **Restyle the whole app** — edit a `Palette` in `theme.py`, or add a new
  `Theme` and register it in `THEMES`; run with `--theme <name>`.
- **Add a UI control** — write a `_build_<name>` method in `gui.py` and call it
  from `ControllerWindow._build`. It never touches raw colors — ask the theme.
- **Add an API endpoint** — extend `RequestHandler.do_GET` in `api.py`.
- **Support a new command unit** — add it to `COMMAND_PATTERN` and
  `_UNIT_SECONDS` in `models.py` (and the API regex in `api.py`).
- **Swap the transport** — implement the `ToyDriver` protocol in `bluetooth.py`
  and hand it to `CommandWorker`.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow.

## Tests

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests
```

## Minecraft 1.12.2 mod (DamageBuzz)

[`DamageBuzz/`](DamageBuzz/README.md) is a client-side Forge mod that fires a
vibration whenever you take damage, with strength either fixed or scaled to the
hit. Because Minecraft/Java can't emit BLE advertisements itself, the mod drives
this controller running as a **headless sidecar** and launches it automatically:

```bash
python main.py --headless        # or the packaged lovespouse-ble.exe --headless
```

Build a self-contained transmitter exe for the mod to bundle/launch:

```powershell
pip install pyinstaller winsdk
./tools/build_transmitter.ps1     # -> dist/lovespouse-ble.exe
```

See [DamageBuzz/README.md](DamageBuzz/README.md) for mod install, config
(`FIXED`/`SCALED` strength, cooldown, etc.), and build steps.

## Paper plugin (Minecraft)

```bash
cd DamageCurl
mvn package
```

```yaml
server:
  url: "http://localhost:4545/API/"
  power: 9
  time: 0.4
players: {}
```

```text
/damagecurl player <player> <true|false>
/damagecurl url <url>
/damagecurl power <1-9>
/damagecurl time <seconds>
/damagecurl status
```

## Troubleshooting

**The GUI runs but nothing vibrates.** Almost always the Bluetooth radio. On
startup the controller checks the radio and turns it on when it can; if it
can't, it logs a clear warning and each pulse reports `RADIO_NOT_AVAILABLE`
instead of hanging. Turn Bluetooth on in Windows settings and try again. Run with
`--log-level DEBUG` to see each command as it is sent.

**`winsdk is required…` on startup.** Install it (`pip install winsdk`) or use
`--dry-run` to develop without hardware.

## Safety

Use the **Emergency Stop** button, press `Esc`, or send strength `0` to stop
output immediately. The app also sends a stop command on shutdown and whenever
the playback mode changes.
