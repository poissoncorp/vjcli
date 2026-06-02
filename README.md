# vjctl

Terminal-native VJ instrument for Ghostty.

`vjctl` turns a terminal into a playable visual surface for DJ/VJ sets: manual
shockwaves, aggressive hold effects, custom text hits, simulated social events,
and automatic music-reactive visuals from live audio input.

It is built for the booth: fast to launch, keyboard-first, dirty in the right
places, and usable without opening a browser or a heavyweight visual stack.

## What It Does

- Runs as a real terminal app.
- Looks best in Ghostty.
- Starts in fully automatic live-audio mode.
- Falls back to free roam with low aggression and density when audio is absent.
- Spawns waves manually from `Tab`.
- Locks manual BPM after four steady taps.
- Reacts to live or simulated audio energy, bass, brightness, density, onsets,
  beat estimates, and beat phase.
- Lets confident audio guide the free clock without taking over manual lock.
- Auto-triggers effects `1-9` from musical features.
- Supports opt-in `--lsd` color profiling from the character of the track.
- Keeps spawned waves alive until they naturally decay.
- Renders text hits with bundled FIGlet fonts and terminal-native ANSI output.

## Install

```bash
git clone https://github.com/poissoncorp/vjcli.git
cd vjcli
python3 -m pip install -e '.[audio]'
```

Run with live audio as the default mode:

```bash
vjctl
```

Run from the repo without installing:

```bash
script/run
```

## Quick Start

Live audio performance mode:

```bash
vjctl
```

Live audio with mood-reactive color profiling:

```bash
vjctl --lsd
```

Manual-only mode:

```bash
vjctl --music none
```

Synthetic music-reactive demo for development:

```bash
vjctl --music demo
```

AutoVJ with on-screen diagnostics:

```bash
vjctl --debug
```

AutoVJ plus LSD diagnostics:

```bash
vjctl --debug --lsd
```

Preview one frame in a non-interactive shell:

```bash
vjctl --preview-frames 1 --width 132 --height 36 --music demo
```

## Audio Routing

Install or refresh audio input support:

```bash
python3 -m pip install -e '.[audio]'
```

List input devices:

```bash
vjctl --list-audio-devices
```

List output devices:

```bash
vjctl --list-audio-outputs
```

Inspect the analyzer and model decisions:

```bash
vjctl --meter
```

Tune AutoVJ triggering:

```bash
vjctl --onset-threshold 0.50 --effect-threshold 0.70 --debug
```

Run with live audio:

```bash
vjctl
```

On macOS, `sounddevice` can open input devices directly. It cannot magically
read speaker output as an input stream. To react to system/DJ output, route that
output into an input with BlackHole, Loopback, or an audio interface, then select
the input with `--audio-device` when needed.

`--list-audio-outputs` is diagnostic: it shows where audio can play, but visual
analysis still needs a capture input or loopback device.

## Music Sync

`vjctl` is audio-first. It does not require Ableton Link, CDJ metadata, or a
prebuilt beat grid to feel alive.

The audio path works like this:

```text
audio input -> analyzer -> MusicFrame -> MusicReactor -> VJModel -> Renderer
                         -> TempoClock audio hint
                         -> LsdDirector when --lsd is enabled
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
  whether to spawn an onset wave or fire an automatic effect from `1-9`.
- `TempoClock` accepts confident audio BPM/phase hints while still respecting
  manual lock.
- `LsdDirector` classifies the musical climate when `--lsd` is enabled and
  chooses the color, speed, line weight, kick impact, haze, and AutoVJ effect
  bias.

That means audio can guide the free clock, but four steady manual taps still win.
Releasing effects or resetting to free roam does not restart the underlying loop
or kill waves that are already travelling.

Automatic effect selection is driven by a tiny scene director. It tracks pressure
over time, classifies the current moment, and uses that scene to choose effects:

- `listen` keeps the app restrained
- `drive` draws current rails and can trigger `3` pressure
- `fault` draws chromatic slips and can trigger `7` chroma
- `weight` draws low-end columns and can trigger `5` tunnel
- `rupture` draws hard cuts and can trigger `2` blackout or `9` collapse
- `chaos` combines rails, slips, cuts, and can trigger `1` overdrive or `8` quake
- clean hits can still fall back to `4` slam

The director tracks scene age and avoids repeating the same automatic effect
back-to-back, so a sustained section can escalate instead of looping one hit.
Entering a strong scene can also spawn its own transition wave, even when the
audio block is not a clean onset.
Scenes hold briefly before demoting, so AutoVJ keeps stage weight instead of
flickering between modes every analyzer frame.
Slower, oldschool-tempo material gets extra restraint: kicks can still create
visible waves, but automatic effects need stronger evidence before escalating
into rupture or chaos.

`0` stays manual. It is the operator's free-roam reset, not an automatic music
decision.

## LSD Mode

`--lsd` keeps the same control model and effect timing, but lets the track choose
the visual climate and bias automatic effect selection:

- `velvet` slows down and softens calm, airy material
- `house` keeps kick response clean and warm, favoring slam and pressure
- `acid` pushes bright, unstable, high-frequency tracks toward chroma and smear
- `spectral` opens up cold, sparse, melodic space
- `industrial` adds grit, heavier line pressure, quake, and blackout bias
- `hard` makes fast, dense, high-drive sections favor overdrive and blackout

The mode is opt-in. Without `--lsd`, `vjctl` stays in the original red/black
warehouse palette.

## Meter

The meter is the best way to tune a room before performing:

```bash
vjctl --meter
vjctl --music demo --meter
```

Columns include scene, scene age, latest automatic effect, audio features,
beat/phase estimates, clock phase, timing confidence, trigger decisions,
pressure, trigger score, transition hit strength, aftershock strength,
beat accent, aggression, density, LSD profile, LSD confidence, LSD margin, and
LSD shift.

For an in-scene readout, run:

```bash
vjctl --debug
```

The debug overlay shows analyzer features, beat hints, clock state, scene, scene
age, pressure, trigger score, model aggression/density, wave count, the latest
beat accent, transition hit, aftershock strength, automatic effect, and active
hold effects. With `--lsd`, it also shows the selected profile, confidence, and
profile margin. Stable profile changes also create a short LSD shift hit.

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
| `4` | Slam | Visible hit |
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
- `lsd.py` turns music frames into opt-in color and motion profiles.
- `clock.py` owns free/manual/audio timing.
- `timing.py` exposes the neutral timing state.
- `model.py` owns scene state: waves, text, effects, music, and socials.
- `renderer.py`, `scene_renderer.py`, `wave_renderer.py`, `effect_renderers.py`,
  and `text_layer.py` turn model state into ANSI frames.

Renderer code reads state. Sources and adapters produce events or music frames.
The model applies decisions. This keeps future inputs such as Link, deck metadata,
OSC, MIDI, or real social adapters from leaking into the renderer.

## Credits

Bundled FIGlet fonts `Delta_Corps_Priest_1.flf` and `Doom.flf` come from
[xero/figlet-fonts](https://github.com/xero/figlet-fonts).
