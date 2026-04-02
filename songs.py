"""
Song library — complete piano pieces as note event sequences.

Uses a compact notation parser for readable, maintainable song data.
Each event: (midi_notes: list[int], sustain_seconds: float)
"""

import re

_NOTE = {
    "C": 0, "C#": 1, "Db": 1,
    "D": 2, "D#": 3, "Eb": 3,
    "E": 4,
    "F": 5, "F#": 6, "Gb": 6,
    "G": 7, "G#": 8, "Ab": 8,
    "A": 9, "A#": 10, "Bb": 10,
    "B": 11,
}


def n(name: str, octave: int) -> int:
    """Shorthand: n('C', 4) → 60 (middle C)."""
    return 12 * (octave + 1) + _NOTE[name]


def _melody(notation: str, default_sus: float = 0.4) -> list:
    """Parse compact notation into events.

    Tokens:
        E5       → single note, default sustain
        E5:0.8   → single note, explicit sustain
        C4+E4+G4 → chord (simultaneous notes)
        |        → bar separator (ignored, for readability)
    """
    events = []
    for token in notation.split():
        if token == "|":
            continue
        parts = token.split(":")
        notes_str = parts[0]
        sus = float(parts[1]) if len(parts) > 1 else default_sus

        midi_notes = []
        for ns in notes_str.split("+"):
            m = re.match(r"([A-G][b#]?)(\d)", ns)
            if m:
                midi_notes.append(n(m.group(1), int(m.group(2))))

        if midi_notes:
            events.append((midi_notes, sus))
    return events


# ══════════════════════════════════════════════════════════════════════
# Für Elise — Beethoven (WoO 59)  ·  Complete A-B-A-C-A structure
# ══════════════════════════════════════════════════════════════════════

_FE_A = """
    E5 Eb5 | E5 Eb5 E5 B4 D5 C5 |
    A3+A4:0.7 C4 E4 A4 |
    E3+B4:0.7 E4 Ab4 B4 |
    A3+C5:0.6 E4 |
    E5 Eb5 | E5 Eb5 E5 B4 D5 C5 |
    A3+A4:0.7 C4 E4 A4 |
    E3+B4:0.7 E4 C5 B4 |
    A3+A4:1.0
"""

_FE_B = """
    B4 C5 D5 |
    C4+E5:0.7 G4 F5 E5 |
    G3+D5:0.7 F4 E5 D5 |
    A3+C5:0.7 E4 D5 C5 |
    E3+B4:0.5 E4 E5:0.7 E6:0.5 |
    Eb5 E5 | Eb5 E5 Eb5 | E5 B4 D5 C5
"""

_FE_C = """
    A3+A4:0.6 C5 E5 |
    A5:0.8 Ab5 A5 Ab5 G5 |
    F5+D4:0.7 E5 D5 F5 E5 D5 |
    C5+A3:0.7 B4 D5 C5 B4 |
    A4:0.6 Ab4 A4 B4 C5 |
    D5+F4:0.7 E5:0.8 F5 E5 D5 |
    C5+E4:0.7 B4 A4 B4 C5 D5:0.7 |
    E5 D5 C5 B4 |
    A4 Ab4 A4 B4 |
    C5:0.7 D5 C5 B4 |
    Bb4 A4 Ab4:0.5
"""

FUR_ELISE = {
    "id": "fur_elise",
    "name": "Für Elise",
    "composer": "Beethoven",
    "events": (
        _melody(_FE_A)
        + _melody(_FE_B)
        + _melody(_FE_A)
        + _melody(_FE_C)
        + _melody(_FE_A)
    ),
}


# ══════════════════════════════════════════════════════════════════════
# Canon in D — Pachelbel  ·  4 variations of increasing complexity
# ══════════════════════════════════════════════════════════════════════

_CANON_V1 = """
    F#5:0.8 E5:0.8 | D5:0.8 C#5:0.8 |
    B4:0.8 A4:0.8 | B4:0.8 C#5:0.8 |
    D5:0.8 C#5:0.8 | B4:0.8 A4:0.8 |
    G4:0.8 F#4:0.8 | G4:0.8 A4:0.8
"""

_CANON_V2 = """
    D5 F#5 A5 F#5 | E5 C#5 E5 G5 |
    F#5 D5 F#5 A5 | G5 B4 D5 G5 |
    B4 D5 F#5 D5 | A4 D5 F#5 A5 |
    G4 B4 D5 B4 | A4 C#5 E5 A5
"""

_CANON_V3 = """
    A5 F#5 D5 F#5 | A5 G5 E5 C#5 |
    D5 B4 G4 B4 | D5 C#5 A4 C#5 |
    B4 G4 E4 G4 | A4 F#4 D4 F#4 |
    G4 B4 D5 B4 | A4 E5 C#5 A4
"""

_CANON_V4 = """
    D5 E5 F#5 G5 | A5 B5 A5 G5 |
    F#5 G5 A5 F#5 | D5 E5 F#5 D5 |
    B4 C#5 D5 B4 | A4 B4 C#5 A4 |
    G4 A4 B4 C#5 | D5 E5 F#5:0.8 E5:0.8 |
    D5 C#5 B4 A4 | G4 F#4 E4 D4 |
    E4 F#4 G4 A4 | B4 C#5 D5 E5 |
    F#5 E5 D5 C#5 | B4 A4 G4 F#4 |
    G4 A4 B4 C#5 | D5:1.2
"""

CANON_IN_D = {
    "id": "canon_in_d",
    "name": "Canon in D",
    "composer": "Pachelbel",
    "events": (
        _melody(_CANON_V1, 0.6)
        + _melody(_CANON_V2, 0.45)
        + _melody(_CANON_V3, 0.45)
        + _melody(_CANON_V4, 0.4)
    ),
}


# ══════════════════════════════════════════════════════════════════════
# River Flows in You — Yiruma  ·  Full main theme + bridge + reprise
# ══════════════════════════════════════════════════════════════════════

_RFY_A = """
    A4 B4 C#5:0.6 B4 C#5 | E5:0.6 B4:0.6 |
    A4 B4 C#5:0.6 B4 A4 | Ab4:0.6 A4:0.6 |
    F#4 Ab4 A4:0.6 Ab4 A4 | C#5:0.6 Ab4:0.6 |
    F#4 Ab4 A4:0.6 Ab4 F#4 | E4:0.9
"""

_RFY_B = """
    A4 B4 C#5 D5 | E5:0.6 D5 C#5 B4:0.6 |
    A4 B4 C#5:0.6 B4 A4 | Ab4 A4 B4:0.9 |
    F#4 Ab4 A4:0.6 Ab4 A4 | C#5 E5:0.6 C#5 |
    B4 A4 Ab4:0.6 F#4 Ab4 | A4:0.9
"""

_RFY_BRIDGE = """
    E5 F#5 E5 C#5 | B4:0.6 A4 B4 |
    C#5 E5:0.6 F#5 E5 | C#5 B4:0.6 |
    A4 B4 C#5:0.6 D5 | E5 F#5 E5:0.6 |
    D5 C#5 B4 A4 | Ab4 A4 B4:0.9
"""

_RFY_CODA = """
    A4 B4 C#5:0.6 B4 C#5 | E5 F#5:0.6 E5 |
    C#5 B4 A4:0.6 B4 C#5 | E5:0.6 D5 C#5 |
    B4 A4 Ab4:0.6 A4 B4 | C#5:0.6 B4 A4 |
    Ab4 F#4 E4:0.6 F#4 Ab4 | A4:1.2
"""

RIVER_FLOWS = {
    "id": "river_flows",
    "name": "River Flows in You",
    "composer": "Yiruma",
    "events": (
        _melody(_RFY_A, 0.35)
        + _melody(_RFY_B, 0.35)
        + _melody(_RFY_A, 0.35)
        + _melody(_RFY_BRIDGE, 0.35)
        + _melody(_RFY_CODA, 0.35)
    ),
}


# ══════════════════════════════════════════════════════════════════════
# 茉莉花 (Jasmine Flower) — 中国民歌  ·  完整三段
# ══════════════════════════════════════════════════════════════════════

_JAS_1 = """
    E5:0.6 E5 F5 | G5:0.8 A5:0.6 A5 G5 |
    G5:0.6 E5 F5 | G5:0.6 G5 F5 E5 D5 |
    C5:0.6 D5 E5 | D5:0.6 C5 A4 | C5:1.0
"""

_JAS_2 = """
    E5:0.6 E5 F5 | G5:0.8 A5:0.6 A5 G5 |
    G5:0.6 E5 F5 | G5:0.6 G5 F5 E5 D5 |
    C5:0.6 D5 E5 | D5:0.6 C5 A4 | C5:1.0
"""

_JAS_3 = """
    E5:0.6 D5 C5 | D5:0.8 E5:0.6 G5 E5 |
    D5:0.6 C5 A4 | C5 D5 C5:1.0 |
    G4:0.6 A4 C5 | D5:0.6 E5:0.8 D5 C5 |
    A4:0.6 C5 D5 | C5:1.0 |
    E5:0.6 D5 C5 | D5:0.8 E5:0.6 G5 E5 |
    D5:0.6 C5 A4 | C5 D5 C5:1.2
"""

JASMINE = {
    "id": "jasmine",
    "name": "茉莉花 (Jasmine Flower)",
    "composer": "中国民歌",
    "events": (
        _melody(_JAS_1, 0.45)
        + _melody(_JAS_2, 0.45)
        + _melody(_JAS_3, 0.45)
    ),
}


# ══════════════════════════════════════════════════════════════════════
# Twinkle Twinkle Little Star — 完整 AABBAA 结构
# ══════════════════════════════════════════════════════════════════════

TWINKLE = {
    "id": "twinkle",
    "name": "Twinkle Twinkle Little Star",
    "composer": "Mozart (arr.)",
    "events": _melody("""
        C5 C5 G5 G5 | A5 A5 G5:1.0 |
        F5 F5 E5 E5 | D5 D5 C5:1.0 |
        G5 G5 F5 F5 | E5 E5 D5:1.0 |
        G5 G5 F5 F5 | E5 E5 D5:1.0 |
        C5 C5 G5 G5 | A5 A5 G5:1.0 |
        F5 F5 E5 E5 | D5 D5 C5:1.2
    """, 0.5),
}


# ══════════════════════════════════════════════════════════════════════
# Clair de Lune — Debussy  ·  Opening section (simplified)
# ══════════════════════════════════════════════════════════════════════

CLAIR_DE_LUNE = {
    "id": "clair_de_lune",
    "name": "Clair de Lune",
    "composer": "Debussy",
    "events": _melody("""
        Db5:1.2 Eb5:0.6 F5:0.6 |
        Gb5:1.2 F5:0.6 Eb5:0.6 |
        Db5:1.4 Ab4:0.6 Bb4:0.6 |
        Db5:1.0 Eb5:0.6 Db5:0.6 |
        Bb4:1.0 Ab4:0.6 Gb4:0.6 |
        Ab4:1.4 |
        Db5:0.8 Eb5:0.8 F5:1.2 |
        Ab5:0.6 Gb5:0.6 F5:0.6 Eb5:0.6 |
        Db5:1.6 |
        F5:0.6 Gb5:0.6 Ab5:1.2 |
        Gb5:0.6 F5:0.6 Eb5:0.6 Db5:0.6 |
        Eb5:1.4 Db5:0.6 |
        Bb4:1.0 Ab4:0.6 Gb4:0.6 |
        Ab4:0.8 Bb4:0.8 Db5:1.4 |
        Eb5:0.6 F5:0.6 Gb5:0.6 F5:0.6 |
        Eb5:0.6 Db5:0.6 Bb4:0.6 Ab4:0.6 |
        Db5:2.0
    """, 0.6),
}


# ── Song catalog ──────────────────────────────────────────────────────

ALL_SONGS = [
    FUR_ELISE,
    CANON_IN_D,
    RIVER_FLOWS,
    JASMINE,
    TWINKLE,
    CLAIR_DE_LUNE,
]
