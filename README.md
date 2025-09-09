🎮 Vibration Controller

A Windows-only Python application for controlling Bluetooth LE toys.
It provides both a modern GUI (Tkinter + Discord-like theme) and a local HTTP API for programmatic control.

Designed for users who want to integrate custom vibration patterns or trigger devices from games, scripts, or other automation tools.

✨ Features

Intensity Control
Adjustable vibration strength (0–9) via a GUI slider with real-time feedback.

Pattern Playback
Supports .vibepattern files (JSON header + sequence), enabling user-defined vibration scripts.

HTTP API
Local server on http://localhost:4545 for issuing commands from external applications.
Example:

GET /API/{strength}-{duration}{unit}


Modern UI
Custom Tkinter theme inspired by Discord’s dark palette.

Fail-Safe Stop
One-click STOP button and automatic “level 0” command dispatch to safely terminate vibrations.

📂 Repository Structure
.
├── main.py              # Core application
├── pattern/             # User-defined vibration patterns (.vibepattern)
├── icon.ico             # Optional GUI icon
└── README.md            # This file

📦 Requirements

OS: Windows 10+ (required due to winsdk)

Python: 3.9 or newer

Dependencies:

pip install winsdk


Note: winsdk provides access to the Windows Runtime APIs for Bluetooth LE advertising.

▶️ Usage

Run:

python main.py


This will:

Launch the Tkinter GUI window (🎮 Vibration Controller).

Start an HTTP server listening on port 4545.

🎵 Pattern File Format

Pattern files are stored in pattern/ with extension .vibepattern.

First line: JSON header (name, author).

Subsequent lines: <strength>-<duration><unit>.

Example (WAVE.vibepattern):

{"name": "WAVE Vibe", "author": "Miran"}

9-500ms
3-1s
7-200ms


This defines a repeating sequence of strength/duration pairs.

🌐 API Reference

Base URL: http://localhost:4545

Example Requests
Level 3, 1.5 seconds
curl http://localhost:4545/API/3-1.5s

Level 9, 500 milliseconds
curl http://localhost:4545/API/9-500ms

Response
{
  "status": "ok",
  "strength": 3,
  "duration": "1.5s"
}


If no valid API call is provided, the server responds with usage instructions.

🖼️ GUI Preview

(Insert screenshot here, e.g. assets/gui.png)

Left: Intensity slider + STOP button.

Right: Pattern list with double-click or Enter to start playback.

Bottom: Status indicator (Ready, Running, Stopped, Playing Pattern).

⚠️ Disclaimer

This software is provided for educational and experimental purposes only.
The author(s) take no responsibility for any misuse, damages, or consequences arising from its use.

💡 Tip: Combining the HTTP API with a game, MIDI controller, or automation script allows for fully synchronized interactive experiences.
