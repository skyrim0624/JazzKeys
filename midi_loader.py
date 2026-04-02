"""
MIDI file loader — extract playable note sequences from any .mid file.

This lets you load complete, perfectly accurate piano pieces
from the thousands of free MIDI files available online.
"""

import mido


def load_midi(filepath: str, track_index: int | None = None) -> dict:
    """Load a MIDI file and extract note events.

    Automatically selects the track with the most notes (usually melody).
    Groups simultaneous notes as chords.
    Preserves relative note durations as sustain values.
    """
    mid = mido.MidiFile(filepath)

    # Auto-detect best track (most note events)
    if track_index is None:
        best, max_n = 0, 0
        for i, track in enumerate(mid.tracks):
            count = sum(1 for m in track if m.type == "note_on" and m.velocity > 0)
            if count > max_n:
                max_n = count
                best = i
        track_index = best

    track = mid.tracks[track_index]
    tpb = mid.ticks_per_beat
    tempo = 500_000  # default 120 BPM (microseconds per beat)

    # Collect raw note events with absolute timing
    abs_time = 0
    active: dict[int, int] = {}
    raw = []

    for msg in track:
        abs_time += msg.time
        if msg.type == "set_tempo":
            tempo = msg.tempo
        elif msg.type == "note_on" and msg.velocity > 0:
            active[msg.note] = abs_time
        elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
            if msg.note in active:
                start = active.pop(msg.note)
                raw.append((start, msg.note, abs_time - start))

    if not raw:
        raise ValueError(f"No notes found in track {track_index}")

    def ticks_to_sec(t):
        return (t / tpb) * (tempo / 1_000_000)

    # Group simultaneous notes into chords
    raw.sort(key=lambda x: x[0])
    events = []
    i = 0
    threshold = max(tpb // 8, 10)

    while i < len(raw):
        start, note, dur = raw[i]
        chord = [note]
        max_dur = dur
        j = i + 1
        while j < len(raw) and raw[j][0] - start < threshold:
            chord.append(raw[j][1])
            max_dur = max(max_dur, raw[j][2])
            j += 1
        sus = max(0.15, min(ticks_to_sec(max_dur), 3.0))
        events.append((chord, round(sus, 2)))
        i = j

    # Derive name from filename
    name = filepath.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    name = name.replace("_", " ").replace("-", " ").title()

    return {
        "id": f"midi_{name.lower().replace(' ', '_')}",
        "name": name,
        "composer": "MIDI Import",
        "events": events,
    }
