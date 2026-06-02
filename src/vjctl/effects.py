from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EffectSpec:
    key: str
    name: str
    level: int
    hold_beats: float = 0.42
    release: float = 0.0
    pulses: tuple[float, ...] = ()
    cooldown: float = 0.0
    render: str = ""
    render_order: int = 0

    @property
    def label(self) -> str:
        return self.name.upper()


EFFECTS = (
    EffectSpec(key="0", name="pause", level=0),
    EffectSpec(
        key="1",
        name="overdrive",
        level=10,
        hold_beats=0.55,
        release=1.0,
        pulses=(0.0, -0.25, -0.5),
        render="overdrive",
        render_order=80,
    ),
    EffectSpec(
        key="2",
        name="blackout",
        level=8,
        hold_beats=0.5,
        release=0.62,
        render="blackout",
        render_order=70,
    ),
    EffectSpec(
        key="3",
        name="pressure",
        level=5,
        hold_beats=0.62,
        render="pressure",
        render_order=30,
    ),
    EffectSpec(
        key="4",
        name="slam",
        level=7,
        hold_beats=0.18,
        release=1.0,
        pulses=(0.0,),
        render="slam",
        render_order=90,
    ),
    EffectSpec(
        key="5",
        name="tunnel",
        level=4,
        hold_beats=0.5,
        release=0.42,
        render="tunnel",
        render_order=20,
    ),
    EffectSpec(
        key="6",
        name="smear",
        level=3,
        hold_beats=0.48,
        release=0.28,
        render="smear",
        render_order=40,
    ),
    EffectSpec(
        key="7",
        name="chroma",
        level=6,
        hold_beats=0.52,
        release=0.42,
        render="chroma",
        render_order=60,
    ),
    EffectSpec(
        key="8",
        name="quake",
        level=9,
        hold_beats=0.42,
        release=1.0,
        pulses=(0.0, -0.5),
        render="quake",
        render_order=85,
    ),
    EffectSpec(
        key="9",
        name="collapse",
        level=9,
        hold_beats=0.45,
        release=1.0,
        pulses=(0.0,),
        render="collapse",
        render_order=95,
    ),
)

EFFECT_BY_KEY = {effect.key: effect for effect in EFFECTS}
EFFECT_RENDER_ORDER = tuple(
    sorted(
        (effect for effect in EFFECTS if effect.render),
        key=lambda item: item.render_order,
    )
)
