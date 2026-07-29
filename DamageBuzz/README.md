# DamageBuzz — Minecraft 1.12.2 mod

A client-side Forge mod that fires a **Bluetooth LE vibration whenever you take
damage** in Minecraft. Strength can be fixed or scale with how hard you were hit.

It works in single-player and on any server (vanilla or modded), because it
watches your own health on the client rather than relying on server-side events.

## How it works

```
you take damage  →  ClientDamageHandler (health drop)  →  StrengthCalculator
                 →  VibrationClient (HTTP)  →  lovespouse-ble transmitter  →  BLE  →  toy
```

Minecraft cannot emit Bluetooth advertisements from the JVM, so the actual BLE
transmission is done by a tiny **sidecar** — the same proven Windows BLE code
from the parent project, packaged as `lovespouse-ble.exe`. The mod launches it
automatically (see `TransmitterLauncher`), so from the player's side it's just
"install the mod." The mod jar itself stays tiny and dependency-free.

## Requirements

- Minecraft 1.12.2 + Forge 14.23.5.x
- Windows with Bluetooth (the transmitter turns the radio on for you)
- `lovespouse-ble.exe` — bundled in the jar, set via config, or built from the
  parent project (`tools/build_transmitter.ps1`)

## Install

1. Build the mod (see below) or grab `damagebuzz-1.0.0.jar`.
2. Drop it in `.minecraft/mods/`.
3. Make sure the transmitter is available (one of):
   - bundled in the jar (see *Bundling the transmitter*),
   - or set `transmitter.path` in `config/damagebuzz.cfg` to your `lovespouse-ble.exe`,
   - or run it yourself: `lovespouse-ble.exe --headless`.
4. Launch Minecraft, take a hit.

## Configuration — `config/damagebuzz.cfg`

| Category | Key | Default | Meaning |
| --- | --- | --- | --- |
| general | `enabled` | `true` | Master switch |
| general | `backendUrl` | `http://127.0.0.1:4545/API/` | Transmitter API base URL |
| strength | `mode` | `SCALED` | `FIXED` or `SCALED` (scale with damage) |
| strength | `fixedStrength` | `6` | Strength in FIXED mode (0–9) |
| strength | `minStrength` | `2` | Lowest strength in SCALED mode |
| strength | `maxStrength` | `9` | Highest strength in SCALED mode |
| strength | `damageForMax` | `20.0` | Damage (health pts; 2 = 1 heart) that hits max |
| output | `pulseSeconds` | `0.6` | Vibration length per hit |
| output | `cooldownMs` | `250` | Minimum gap between vibrations |
| transmitter | `autoStart` | `true` | Auto-launch the transmitter |
| transmitter | `path` | *(blank)* | Explicit path to `lovespouse-ble.exe` |
| transmitter | `port` | `4545` | Transmitter port (match `backendUrl`) |

SCALED mapping with the defaults: a half-heart hit ≈ strength 2, ~3 hearts ≈ 4,
~5 hearts ≈ 6, a 10-heart hit ≈ 9.

## Build

Needs a **JDK 8** (not just a JRE, and not JDK 9+ — ForgeGradle 2.3 requires 8).
The bundled Gradle wrapper pins Gradle 4.10.3, so you don't need Gradle installed.

```bash
cd DamageBuzz
# point JAVA_HOME at a JDK 8, then:
./gradlew setupDecompWorkspace build      # first run downloads Forge + decompiles MC (~4 min)
```

Output: **`build/libs/damagebuzz-1.0.0.jar`** — drop it in `.minecraft/mods/`.
It builds against Forge 1.12.2-14.23.5.2847 and runs on any 1.12.2 Forge
14.23.5.x. This has been built and verified: the jar contains the FML `@Mod`
annotation cache and its Minecraft references are reobfuscated to SRG names, so
it loads in a normal (production) client.

### Bundling the transmitter (optional, for a single-file distribution)

To ship a jar that carries the transmitter so players need nothing else:

```powershell
# from the repo root — produces dist/lovespouse-ble.exe
./tools/build_transmitter.ps1
# place it where the mod build will pick it up:
copy dist\lovespouse-ble.exe DamageBuzz\src\main\resources\assets\damagebuzz\lovespouse-ble.exe
cd DamageBuzz ; ./gradlew build
```

The exe is deliberately **not** committed to the repo (it's ~19 MB). Without it
bundled, the mod falls back to `transmitter.path` or a manually started backend.

## Source layout

```
DamageBuzz.java            @Mod entry — wires everything up on the client
ModConfig.java             config/damagebuzz.cfg loading
ClientDamageHandler.java   watches health each tick, detects hits
StrengthCalculator.java    damage → 0–9 strength (FIXED / SCALED)
VibrationClient.java       async HTTP to the transmitter
TransmitterLauncher.java   finds & auto-launches lovespouse-ble.exe
```
