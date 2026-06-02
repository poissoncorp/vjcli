# vjctl

Live terminal VJ instrument for Ghostty.

vjctl turns a terminal into a playable visual surface: tap tempo, shockwaves, text hits,
blackout gates, glitch pressure, and warehouse-red ANSI chaos.

It is built for DJ/VJ sets where you want something fast, dirty, keyboard-driven, and alive without
opening a browser or a heavyweight visual stack.

## Why It Rules

- Runs in the terminal.
- Looks best in Ghostty.
- Responds instantly to keyboard performance.
- Starts in free roam, then locks to BPM after four steady taps.
- Keeps spawned waves travelling even after you reset back to free roam.
- Uses real ANSI/text rendering instead of a web canvas.
- Ships with simulated social events so the stage can feel alive before real adapters exist.

## Install

```bash
git clone https://github.com/poissoncorp/vjcli.git
cd vjcli
python3 -m pip install -e .
```

Then run it from anywhere:

```bash
vjctl
```

Or run with a synthetic music-reactive feed:

```bash
vjctl --music demo
```

For live audio input:

```bash
python3 -m pip install -e '.[audio]'
vjctl --music audio
```

On macOS, route system/DJ audio into an input device with BlackHole or a real audio interface,
then select it with `--audio-device` if needed.

Or run from the repo without installing:

```bash
script/run
```

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

Digits trigger effects only while the prompt is empty. After you type any non-digit character,
digits become normal text.

## Effects

| Key | Effect |
| --- | --- |
| `1` | Overdrive |
| `2` | Blackout |
| `3` | Pressure |
| `4` | Impact |
| `5` | Tunnel |
| `6` | Smear |
| `7` | Chroma |
| `8` | Quake |
| `9` | Collapse |
| `0` | Free roam reset |

`0` clears active effects and returns to free roam, but it does not kill waves that already spawned.

## Commands

```text
/aggr <0-1|up|down>
/dens <0-1|up|down>
/density <0-1|up|down>
/cooldown
```

`aggr` makes waves travel faster. `dens` makes waves thicker. Defaults start low at `0.10 / 0.10`,
so the room starts controlled and gets ugly only when you push it.

## Credits

Bundled FIGlet fonts `Delta_Corps_Priest_1.flf` and `Doom.flf` come from
[xero/figlet-fonts](https://github.com/xero/figlet-fonts).
