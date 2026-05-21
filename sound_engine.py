"""
Piano sound engine — synthesis modes with adaptive dynamics, ASMR backgrounds, and special keys.
"""

import threading
import numpy as np
import sounddevice as sd

SAMPLE_RATE = 44100
MAX_NOTE_CACHE_SIZE = 256


def midi_to_freq(midi_note: int) -> float:
    return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))


class PianoEngine:
    """Polyphonic synthesizer with backgrounds and special keys."""

    _PROFILES = {
        "piano": {
            "harmonics": [1.0, 0.45, 0.25, 0.12, 0.08, 0.05, 0.03, 0.015],
            "attack": 0.003,
            "decay_rate": 3.0,
            "note_vol": 0.30,
            "master": 0.45,
            "max_poly": 6,
        },
        "gentle": {
            "harmonics": [1.0, 0.12, 0.04],
            "attack": 0.015,
            "decay_rate": 1.2,
            "note_vol": 0.18,
            "master": 0.25,
            "max_poly": 3,
        },
        "rain": {
            "harmonics": [1.0, 0.5, 0.2],  # Pluckle/droplet tone
            "attack": 0.005,
            "decay_rate": 5.0,
            "note_vol": 0.25,
            "master": 0.35,
            "max_poly": 4,
            "bg": "rain_noise"
        }
    }

    def __init__(self, mode: str = "piano"):
        self.mode = mode
        self._profile = self._PROFILES.get(mode, self._PROFILES["piano"])
        self._max_poly = self._profile.get("max_poly", 6) if mode != "typewriter" else 2
        
        self._note_cache: dict[tuple[int, int], np.ndarray] = {}
        self._special_cache: dict[str, np.ndarray] = {}
        self._active: list[list] = []
        
        self._lock = threading.Lock()
        self._timer_lock = threading.Lock()
        self._note_timers: set[threading.Timer] = set()
        self._rng = np.random.default_rng()

        if mode == "typewriter":
            self._click_variants = [self._make_click(i) for i in range(8)]
            
        self._bg_phase = 0
        self._has_bg = self._profile.get("bg") == "rain_noise"

        self._synth = None
        self._sfid = None
        import sys
        import os
        
        # Determine if we are in py2app (RESOURCEPATH) or PyInstaller (_MEIPASS) or default dev environment
        if 'RESOURCEPATH' in os.environ:
            # macOS .app bundle via py2app
            resource_path = os.environ['RESOURCEPATH']
            framework_path = os.path.join(os.path.dirname(resource_path), 'Frameworks')
            is_bundled = True
        elif getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # PyInstaller
            resource_path = sys._MEIPASS
            framework_path = sys._MEIPASS
            is_bundled = True
        else:
            # Dev mode
            resource_path = os.path.dirname(os.path.abspath(__file__))
            framework_path = resource_path
            is_bundled = False
            
        sf2_path = os.path.join(resource_path, "Piano.sf3")
        try:
            if is_bundled:
                # Monkey-patch find_library to return the bundled dylib
                import ctypes.util
                _orig_find = ctypes.util.find_library
                def _find_override(name):
                    if "fluidsynth" in name:
                        bundled = os.path.join(framework_path, "libfluidsynth.dylib")
                        if os.path.exists(bundled):
                            return bundled
                    return _orig_find(name)
                ctypes.util.find_library = _find_override

            import fluidsynth
            
            # Note: Do not load piano soundfont for typewriter mode
            if os.path.exists(sf2_path) and mode != "typewriter":
                self._synth = fluidsynth.Synth()
                self._synth.setting("synth.gain", 0.5) # Reduced slightly from 0.7 to avoid being too noisy
                self._synth.start(driver="coreaudio")
                self._sfid = self._synth.sfload(sf2_path)
                self._synth.program_select(0, self._sfid, 0, 0)
                print(f"✅ 已加载高级音源: {sf2_path}")
        except Exception as e:
            print(f"⚠ 加载高级音色库失败: {e}，将使用基础内置合成器。")


        self._stream = sd.OutputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            callback=self._callback,
            blocksize=512,
        )

    def start(self):
        self._stream.start()

    def stop(self):
        with self._timer_lock:
            timers = list(self._note_timers)
            self._note_timers.clear()
        for timer in timers:
            timer.cancel()

        self._stream.stop()
        self._stream.close()
        if self._synth:
            self._synth.delete()
            self._synth = None

    def play_notes(self, midi_notes: list[int], sustain: float = 1.8, volume: float = 1.0, octaves_to_add: list[int] = None):
        """Play notes with an optional volume scale and extra octaves/harmonies."""
        if self.mode == "typewriter":
            click = self._click_variants[self._rng.integers(0, len(self._click_variants))]
            with self._lock:
                while len(self._active) >= self._max_poly:
                    self._active.pop(0)
                self._active.append([click, 0, volume])
            return

        all_notes = list(midi_notes)
        if octaves_to_add:
            for note in midi_notes:
                for oct_diff in octaves_to_add:
                    all_notes.append(note + oct_diff * 12)

        for note in all_notes:
            synth = self._synth
            if synth:
                # Greatly increased max velocity mapping
                vel = int(min(127, max(30, volume * 115)))
                synth.noteon(0, int(note), vel)
                self._schedule_noteoff(int(note), sustain)
            else:
                samples = self._get_samples(note, sustain)
                with self._lock:
                    while len(self._active) >= self._max_poly:
                        self._active.pop(0)
                    self._active.append([samples, 0, volume])

    def play_special(self, key_type: str, volume: float = 1.0):
        """Play synthesized feedback for special keys."""
        if key_type not in self._special_cache:
            if key_type == "enter":
                self._special_cache[key_type] = self._make_bell()
            elif key_type == "backspace":
                self._special_cache[key_type] = self._make_thud()
            elif key_type == "modifier":
                self._special_cache[key_type] = self._make_woosh()
            elif key_type == "space":
                self._special_cache[key_type] = self._make_space_click()
            else:
                return

        samples = self._special_cache[key_type]
        with self._lock:
            # Special keys can bypass max_poly slightly to ensure they are heard
            self._active.append([samples, 0, volume])

    def _schedule_noteoff(self, note: int, sustain: float):
        timer = threading.Timer(sustain, self._noteoff_timer, args=(note,))
        timer.daemon = True
        with self._timer_lock:
            self._note_timers.add(timer)
        timer.start()

    def _noteoff_timer(self, note: int):
        try:
            synth = self._synth
            if synth:
                synth.noteoff(0, note)
        finally:
            current = threading.current_thread()
            with self._timer_lock:
                self._note_timers.discard(current)

    # ── audio callback ───────────────────────────────────────────

    def _callback(self, outdata: np.ndarray, frames: int, _time, _status):
        buf = np.zeros(frames, dtype=np.float32)
        master = self._profile.get("master", 0.35)

        # 1. Background Generation (Rain ASMR)
        if self._has_bg:
            # Simple filtered noise for rain
            noise = self._rng.standard_normal(frames).astype(np.float32)
            # A very simplistic low-pass by smoothing
            rc = np.convolve(noise, np.ones(5)/5, mode='same') 
            # Modulate amplitude slightly over time for rolling rain effect
            t_buf = (self._bg_phase + np.arange(frames)) / SAMPLE_RATE
            mod = 0.5 + 0.1 * np.sin(2 * np.pi * 0.2 * t_buf) + 0.05 * np.sin(2 * np.pi * 0.7 * t_buf)
            buf += rc * mod * 0.08  # Quiet background
            self._bg_phase += frames

        # 2. Foreground Notes
        with self._lock:
            survivors = []
            for entry in self._active:
                samples, pos, vol = entry
                remaining = len(samples) - pos
                if remaining <= 0:
                    continue
                n = min(frames, remaining)
                buf[:n] += samples[pos : pos + n] * vol
                entry[1] = pos + n
                survivors.append(entry)
            self._active = survivors

        outdata[:, 0] = np.tanh(buf * master)

    # ── synthesis routines ───────────────────────────────────────

    def _get_samples(self, midi_note: int, sustain: float) -> np.ndarray:
        key = (midi_note, int(sustain * 100))
        if key not in self._note_cache:
            self._note_cache[key] = self._synthesize(midi_note, sustain)
            if len(self._note_cache) > MAX_NOTE_CACHE_SIZE:
                self._note_cache.pop(next(iter(self._note_cache)))
        return self._note_cache[key]

    def _synthesize(self, midi_note: int, sustain: float) -> np.ndarray:
        p = self._profile
        freq = midi_to_freq(midi_note)

        # Rain mode produces shorter, raindrop-like sounds
        if self.mode == "rain":
            sustain *= 0.8
        elif self.mode == "gentle":
            sustain *= 1.3

        n_samples = int(SAMPLE_RATE * sustain)
        t = np.linspace(0, sustain, n_samples, endpoint=False, dtype=np.float32)

        signal = np.zeros(n_samples, dtype=np.float32)
        for i, amp in enumerate(p["harmonics"]):
            h = i + 1
            partial_decay = np.exp(-h * 0.8 * t / sustain)
            signal += amp * partial_decay * np.sin(2 * np.pi * freq * h * t)

        envelope = np.ones(n_samples, dtype=np.float32)
        att_len = int(p["attack"] * SAMPLE_RATE)
        if 0 < att_len < n_samples:
            envelope[:att_len] = np.linspace(0, 1, att_len, dtype=np.float32)

        decay_start = att_len
        if decay_start < n_samples:
            decay_rate = p.get("decay_rate", 3.0)
            decay_t = t[decay_start:] - t[decay_start]
            envelope[decay_start:] = np.exp(-decay_rate * decay_t / sustain)

        release_len = int(0.08 * n_samples)
        if release_len > 0:
            envelope[-release_len:] *= np.linspace(1, 0, release_len, dtype=np.float32)

        signal *= envelope

        peak = np.max(np.abs(signal))
        if peak > 0:
            signal /= peak
        signal *= p.get("note_vol", 0.3)
        return signal

    # ── special key / typewriter routines ────────────────────────
    
    def _make_bell(self) -> np.ndarray:
        # High pitched ding for enter
        dur = 0.8
        n = int(SAMPLE_RATE * dur)
        t = np.linspace(0, dur, n, endpoint=False, dtype=np.float32)
        freq = 1800.0
        sig = np.sin(2 * np.pi * freq * t) * np.exp(-5 * t)
        sig += 0.3 * np.sin(2 * np.pi * (freq * 2.1) * t) * np.exp(-10 * t)
        return (sig * 0.25).astype(np.float32)

    def _make_thud(self) -> np.ndarray:
        # Low thud / rewind for backspace
        dur = 0.25
        n = int(SAMPLE_RATE * dur)
        t = np.linspace(0, dur, n, endpoint=False, dtype=np.float32)
        # pitch drop
        freqs = np.linspace(150, 40, n)
        phase = np.cumsum(freqs) * 2 * np.pi / SAMPLE_RATE
        sig = np.sin(phase) * np.exp(-15 * t)
        noise = self._rng.standard_normal(n).astype(np.float32) * 0.1 * np.exp(-25 * t)
        return ((sig + noise) * 0.4).astype(np.float32)

    def _make_woosh(self) -> np.ndarray:
        # Modifier sweep noise
        dur = 0.15
        n = int(SAMPLE_RATE * dur)
        t = np.linspace(0, dur, n, endpoint=False, dtype=np.float32)
        noise = self._rng.standard_normal(n).astype(np.float32)
        env = np.sin(np.pi * t / dur)  # swell and fade
        return (noise * env * 0.05).astype(np.float32)

    def _make_space_click(self) -> np.ndarray:
        # Spacebar dull wood block
        dur = 0.1
        n = int(SAMPLE_RATE * dur)
        t = np.linspace(0, dur, n, endpoint=False, dtype=np.float32)
        sig = np.sin(2 * np.pi * 300 * t) * np.exp(-30 * t)
        return (sig * 0.3).astype(np.float32)

    def _make_click(self, seed: int) -> np.ndarray:
        rng = np.random.default_rng(seed + 42)
        duration = 0.045 + rng.uniform(-0.008, 0.008)
        n_samples = int(SAMPLE_RATE * duration)
        t = np.linspace(0, duration, n_samples, endpoint=False, dtype=np.float32)

        noise = rng.standard_normal(n_samples).astype(np.float32)
        click_freq = 3200 + rng.uniform(-600, 600)
        click = noise * np.sin(2 * np.pi * click_freq * t) * 0.3

        thud = np.sin(2 * np.pi * (120 + rng.uniform(-30, 30)) * t) * 0.2
        ping = np.sin(2 * np.pi * (5500 + rng.uniform(-800, 800)) * t) * 0.06

        signal = (click + thud + ping) * np.exp(-75 * t)

        att = min(int(0.001 * SAMPLE_RATE), n_samples)
        if att > 0:
            signal[:att] *= np.linspace(0, 1, att, dtype=np.float32)

        peak = np.max(np.abs(signal))
        if peak > 0:
            signal /= peak
        signal *= 0.2
        return signal
