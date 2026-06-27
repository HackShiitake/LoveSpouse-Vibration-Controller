# LoveSpouse Vibration Controller

Windows BLE vibration controller with a desktop GUI, local HTTP API, pattern playback, and an optional Paper plugin that can trigger pulses from Minecraft damage events.

This repository has been reorganized into a production-style project:

- Python application code lives under `src/lovespouse_controller/`.
- Bluetooth commands are serialized through a dedicated worker thread.
- Continuous playback, pattern playback, HTTP serving, GUI, configuration, and parsing are separated by responsibility.
- The Paper plugin is split into command, config, HTTP client, and listener packages.
- Basic parser/repository tests live under `tests/`.

## Repository Layout

```text
.
├── main.py
├── pyproject.toml
├── pattern/
├── src/
│   └── lovespouse_controller/
│       ├── api.py
│       ├── app.py
│       ├── bluetooth.py
│       ├── config.py
│       ├── gui.py
│       ├── models.py
│       ├── patterns.py
│       ├── playback.py
│       └── worker.py
├── tests/
└── DamageCurl/
    └── src/main/java/com/lovespouse/damagecurl/
        ├── command/
        ├── config/
        ├── http/
        └── listener/
```

## Requirements

- Windows 10 or newer
- Python 3.9+
- `winsdk` for real Bluetooth LE advertising
- Java 17 and Maven for building the Paper plugin

Install the Python dependency:

```bash
pip install winsdk
```

## Run The Controller

Normal hardware mode:

```bash
python main.py
```

Dry run mode for development without Bluetooth hardware:

```bash
python main.py --dry-run
```

Useful options:

```bash
python main.py --host 127.0.0.1 --port 4545 --pattern-dir pattern --log-level INFO
```

## HTTP API

The local API keeps the original endpoint format:

```text
GET /API/{strength}-{duration}{unit}
```

Examples:

```bash
curl http://localhost:4545/API/5-1000ms
curl http://localhost:4545/API/3-1.5s
curl http://localhost:4545/API/0-100ms
```

Response:

```json
{
  "status": "ok",
  "strength": 5,
  "duration": "1000ms"
}
```

## Pattern Files

Pattern files live in `pattern/` and use the `.vibepattern` extension.

```text
{"name": "Pulse Wave", "author": "Developer"}
3-500ms
0-250ms
5-750ms
0-500ms
7-1s
```

## Tests

Run Python tests from the repository root:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests
```

## Build The Paper Plugin

```bash
cd DamageCurl
mvn package
```

The plugin configuration is:

```yaml
server:
  url: "http://localhost:4545/API/"
  power: 9
  time: 0.4
players: {}
```

Commands:

```text
/damagecurl player <player> <true|false>
/damagecurl url <url>
/damagecurl power <1-9>
/damagecurl time <seconds>
/damagecurl status
```

## Safety Notes

Use the STOP button or send strength `0` through the API to stop output. The app also sends a stop command during shutdown and when playback modes are changed.
