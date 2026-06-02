# vjctl

Terminal-native VJ instrument for Ghostty.

`vjctl` turns a terminal into a playable visual surface for DJ/VJ sets: manual
shockwaves, aggressive hold effects, custom text hits, simulated social events,
and music-reactive timing from live audio input.

It is built for the booth: fast to launch, keyboard-first, dirty in the right
places, and usable without opening a browser or a heavyweight visual stack.

## What It Does

- Runs as a real terminal app.
- Looks best in Ghostty.
- Starts in free roam with low aggression and density.
- Spawns waves manually from `Tab`.
- Locks manual BPM after four steady taps.
- Reacts to live or simulated audio energy, bass, brightness, density, onsets,
  beat estimates, and beat phase.
- Lets confident audio guide the free clock without taking over manual lock.
- Keeps spawned waves alive until they naturally decay.
- Renders text hits with bundled FIGlet fonts and terminal-native ANSI output.

## Install

```bash
git clone https://github.com/poissoncorp/vjcli.git
cd vjcli
python3 -m pip install -e .
```

Run from anywhere:

```bash
vjctl
```

Run from the repo without installing:

```bash
script/run
```

## Quick Start

Manual performance mode:

```bash
vjctl
```

Synthetic music-reactive demo:

```bash
vjctl --music demo
```

Preview one frame in a non-interactive shell:

```bash
vjctl --preview-frames 1 --width 132 --height 36 --music demo
```

## Live Audio

Install optional audio input support:

```bash
python3 -m pip install -e '.[audio]'
```

List input devices:

```bash
vjctl --list-audio-devices
```

Inspect the analyzer and model decisions:

```bash
vjctl --music audio --meter
```

Tune onset triggering:

```bash
vjctl --music audio --meter --onset-threshold 0.50 --onset-debounce 0.16
```

Run with live audio:

```bash
vjctl --music audio
```

On macOS, route system or DJ audio into an input device with BlackHole, Loopback,
or an audio interface. Select a device with `--audio-device` when needed.

## Music Sync

`vjctl` is audio-first. It does not require Ableton Link, CDJ metadata, or a
prebuilt beat grid to feel alive.

The audio path works like this:

```text
audio input -> analyzer -> MusicFrame -> MusicReactor -> VJModel -> Renderer
                         -> TempoClock audio hint
```

The analyzer reads mono audio blocks and extracts:

- energy
- bass
- brightness
- density
- onset
- spectral change
- confidence
- beat BPM estimate
- beat phase estimate

The model uses those values in two ways:

- `MusicReactor` turns music into stage decisions: aggression, density, and
  whether to spawn an onset wave.
- `TempoClock` accepts confident audio BPM/phase hints while still respecting
  manual lock.

That means audio can guide the free clock, but four steady manual taps still win.
Releasing effects or resetting to free roam does not restart the underlying loop
or kill waves that are already travelling.

## Meter

The meter is the best way to tune a room before performing:

```bash
vjctl --music demo --meter
vjctl --music audio --meter
```

Columns include audio features, beat/phase estimates, clock phase, timing
confidence, trigger decisions, aggression, and density.

## Controls

| Input | Action |
| --- | --- |
| `Tab` | Spawn a manual wave |
| 4 steady `Tab` taps | Lock BPM and start beat pulses |
| `Up` / `Down` | Nudge BPM |
| `Left` / `Right` | Jog phase |
| Type text | Build a prompt |
| `Enter` | Fire the prompt as a visual hit |
| `Ctrl-C` | Exit |
| `Esc Esc` | Emergency exit |

Digits trigger effects only while the prompt is empty. After typing any
non-digit character, digits become normal text.

## Effects

| Key | Effect | Role |
| --- | --- | --- |
| `1` | Overdrive | Maximum pressure |
| `2` | Blackout | Hard gate |
| `3` | Pressure | Mid-level field stress |
| `4` | Impact | Visible hit |
| `5` | Tunnel | Spatial pull |
| `6` | Smear | Drag and trail |
| `7` | Chroma | Glitch split |
| `8` | Quake | Heavy impact |
| `9` | Collapse | High-chaos failure |
| `0` | Free roam reset | Clear holds and unlock clock |

`0` clears active hold effects and returns to free roam, but it does not kill
waves that already spawned.

## Commands

```text
/aggr <0-1|up|down>
/dens <0-1|up|down>
/density <0-1|up|down>
/cooldown
```

`aggr` makes waves travel faster. `dens` makes waves thicker. Defaults start at
`0.10 / 0.10`, so the room begins controlled and gets uglier only when pushed.

## Architecture

The project is a small modular monolith:

- `cli.py` parses user-facing commands.
- `app.py` owns terminal runtime, input polling, and the render loop.
- `audio_input.py` reads live audio through `sounddevice`.
- `analyzer.py` turns samples into music features and beat hints.
- `music.py` defines the `MusicFrame` data contract.
- `music_reactor.py` turns music frames into visual decisions.
- `clock.py` owns free/manual/audio timing.
- `timing.py` exposes the neutral timing state.
- `model.py` owns scene state: waves, text, effects, music, and socials.
- `renderer.py`, `wave_renderer.py`, `effect_renderers.py`, and `text_layer.py`
  turn model state into ANSI frames.

Renderer code reads state. Sources and adapters produce events or music frames.
The model applies decisions. This keeps future inputs such as Link, deck metadata,
OSC, MIDI, or real social adapters from leaking into the renderer.

## Credits

Bundled FIGlet fonts `Delta_Corps_Priest_1.flf` and `Doom.flf` come from
[xero/figlet-fonts](https://github.com/xero/figlet-fonts).
