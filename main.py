#!/usr/bin/env python3
"""
Keyboard Piano 🎹 — The Virtual Jazz Pianist Update

Turn every keypress into a note of a piano piece or an improvisational jazz session.
Features async arpeggio handling for burst typing, semantic chords for special keys, 
and "Thinking Vamp" backgrounds.

Usage:
    python3 main.py --mode jazz
    python3 main.py --pomodoro 25
"""

import argparse
import sys
import threading
import time
import random
import queue

from sound_engine import PianoEngine
from keyboard_listener import KeyboardListener
from songs import ALL_SONGS

PENTATONIC_SCALE = [48, 51, 53, 55, 58, 60, 63, 65, 67, 70, 72, 75, 77, 79, 82, 84]

class KeyboardPiano:
    """Main application — wires together the song, engine, and listener."""

    MODE_EMOJI = {"piano": "🎹", "gentle": "🌙", "typewriter": "⌨️", "rain": "🌧️", "jazz": "🎷"}
    MODE_LABEL = {"piano": "钢琴", "gentle": "柔和", "typewriter": "打字机", "rain": "雨滴", "jazz": "虚拟钢琴家 (爵士即兴)"}

    def __init__(self, song: dict, mode: str = "piano", pomodoro_minutes: int = 0):
        self.song = song
        self.mode = mode
        self.pomodoro = pomodoro_minutes
        
        self.events = song["events"] if song else []
        self.cursor = 0
        self.total = len(self.events) if self.events else 1
        
        self._engine = PianoEngine(mode="piano" if mode == "jazz" else mode)
        self._stop_event = threading.Event()
        self._last_press = time.monotonic()
        self._start_time = 0.0
        
        self._jazz_idx = len(PENTATONIC_SCALE) // 2
        self._last_note_played = 60 # Default middle C tracks context

        # The phrase queue smooths out burst typing into arpeggios
        self._play_queue = queue.Queue()
        self._player_thread = threading.Thread(target=self._player_loop, daemon=True)
        self._vamp_thread = threading.Thread(target=self._vamp_loop, daemon=True)

    def start(self):
        self._engine.start()
        
        # Start background helper threads
        self._player_thread.start()
        self._vamp_thread.start()

        listener = KeyboardListener(
            on_keypress=self._advance,
            on_quit=self._quit,
        )
        self._start_time = time.monotonic()
        self._last_press = self._start_time
        listener.start()

        emoji = self.MODE_EMOJI.get(self.mode, "🎹")
        label = self.MODE_LABEL.get(self.mode, self.mode)
        
        print("\n==================================")
        if self.mode == "jazz":
            print(f"{emoji} 正在加载: {label}")
            print(f"🎵 这是全动态模式:")
            print(f"   [普通打字] → 单音即兴乐句，打字变快变成竖琴般滑音")
            print(f"   [Backspace] → 发出紧张感的转折和弦")
            print(f"   [Enter] → 大切分完美收尾和弦")
            print(f"   [停顿思考] → 自动为你拉起贝斯与伴奏！")
        else:
            name = self.song["name"]
            composer = self.song["composer"]
            print(f"{emoji} 正在播放: {name} — {composer} [{label}模式]")
            print(f"   共 {self.total} 个音符")
            
        if self.pomodoro > 0:
            print(f"🍅 史诗番茄钟开启 ({self.pomodoro} 分钟后音乐将达到最高潮)")
            
        print("💡 Esc 键退出。现在切到后台随便打两把字试试吧！")
        print("==================================\n")

        self._stop_event.wait()
        listener.stop()
        self._engine.stop()
        print("\n👋 再见！\n")

    def _player_loop(self):
        """Asynchronous worker that drains the note queue.
        If many notes are clumped, it introduces small delays to create arpeggios/glissandos."""
        while not self._stop_event.is_set():
            try:
                item = self._play_queue.get(timeout=0.1)
                midi_notes, sustain, volume, oct_add = item
                self._engine.play_notes(midi_notes, sustain, volume, oct_add)
                
                # Arpeggio logic: if the queue has more notes backing up (burst typing)
                # We sleep just a tiny bit to make them roll out smoothly like an arpeggio run
                if not self._play_queue.empty():
                    time.sleep(0.035) 
                
                self._play_queue.task_done()
            except queue.Empty:
                pass

    def _vamp_loop(self):
        """Background tracker that plays autonomous bebop solos when the user is thinking."""
        while not self._stop_event.is_set():
            idle_time = time.monotonic() - self._last_press
            
            # Start intense vamping if user hasn't typed for 2 seconds
            if idle_time > 2.0:
                # Decide next phrase type
                phrase_type = random.choices(
                    ["bebop", "chords", "burst", "pause"],
                    weights=[50, 30, 15, 5]
                )[0]
                
                if phrase_type == "bebop":
                    # Melodic run, slowed down to a more relaxed jazz groove
                    num_notes = random.randint(3, 8)
                    for _ in range(num_notes):
                        if time.monotonic() - self._last_press < 2.0: break
                        step = random.choice([-2, -1, 1, 2, 3])
                        self._jazz_idx = max(0, min(len(PENTATONIC_SCALE)-1, self._jazz_idx + step))
                        note = PENTATONIC_SCALE[self._jazz_idx]
                        vol = random.uniform(0.6, 1.1)
                        self._play_queue.put(([note], 1.2, vol, []))
                        
                        # Slower, more relaxed rhythm
                        time.sleep(random.choice([0.15, 0.2, 0.25, 0.35]))
                        
                elif phrase_type == "chords":
                    # 1 to 3 syncopated block chords
                    num_chords = random.randint(1, 3)
                    for _ in range(num_chords):
                        if time.monotonic() - self._last_press < 2.0: break
                        root = PENTATONIC_SCALE[self._jazz_idx]
                        if random.random() < 0.5:
                            chord = [root-12, root-5, root-2, root+2, root+5]
                        else:
                            chord = [root-12, root-8, root-2, root+1, root+3]
                        
                        self._play_queue.put((chord, 1.5, random.uniform(1.0, 1.4), []))
                        time.sleep(random.choice([0.4, 0.5, 0.6]))
                    time.sleep(0.4)
                    
                elif phrase_type == "burst":
                    # Quick cascading cascade but less frantic
                    if time.monotonic() - self._last_press < 2.0: continue
                    for i in range(4):
                        idx = max(0, min(len(PENTATONIC_SCALE)-1, self._jazz_idx - i))
                        self._play_queue.put(([PENTATONIC_SCALE[idx]], 1.5, 1.0, []))
                        time.sleep(0.08)
                    time.sleep(0.6)
                    
                elif phrase_type == "pause":
                    # Give the solo some breathing room
                    time.sleep(random.uniform(0.4, 1.0))
            else:
                time.sleep(0.1)

    def _advance(self, key_type="char"):
        # Semantic mapping for special keys
        if key_type != "char":
            if key_type == "modifier":
                # Super strong jazzy "punch" for Shift/Cmd/Alt
                root = self._last_note_played
                shift = random.choice([-12, -24])
                # The classic "Hendrix" / Altered dominant punch
                chord = [root+shift, root+4+shift, root+10+shift, root+15+shift, root+17+shift]
                self._play_queue.put((chord, 1.0, 1.8, [])) # Very loud
                self._last_press = time.monotonic()
                return
            elif key_type == "enter":
                # Big resolution chord (Massive Minor 9 or Major 9/13 inversion)
                root = self._last_note_played
                shift = random.choice([-12, -24]) 
                if random.random() < 0.5:
                    chord = [root+shift, root+4+shift, root+7+shift, root+11+shift, root+14+shift, root+21+shift] # Maj 13
                else:
                    chord = [root+shift, root+3+shift, root+7+shift, root+10+shift, root+14+shift, root+17+shift] # Min 11
                
                self._play_queue.put((chord, 3.5, 2.0, [])) # Deep ringing completion
                self._last_press = time.monotonic()
                return
            elif key_type == "backspace":
                # Aggressive diminished / fully altered cluster
                root = self._last_note_played
                shift = random.choice([-12, -24])
                drop = random.choice([0, 3, 6, 9]) # Diminished cycle offsets
                r = root + shift - drop
                
                chord = [r, r+3, r+6, r+9, r+14] # Pure tension cascade
                self._play_queue.put((chord, 1.5, 1.7, []))
                self._last_press = time.monotonic()
                return
            elif key_type == "space":
                # Broad, loud jazz comping
                root = self._last_note_played
                shift = random.choice([-12, 0])
                if random.random() < 0.5:
                    chord = [root+shift, root+7+shift, root+10+shift, root+14+shift] # Min9
                else:
                    chord = [root+shift, root+7+shift, root+11+shift, root+14+shift] # Maj9
                self._play_queue.put((chord, 1.8, 1.5, []))
                self._last_press = time.monotonic()
                return
            return

        now = time.monotonic()
        dt = now - self._last_press if self._last_press > 0 else 1.0
        self._last_press = now

        # Speed scaling
        speed = max(0.0, min(1.0, 1.0 - (dt - 0.04) / 0.36))
        sustain_scale = 1.0 - speed * 0.4
        volume_scale = 1.0 - speed * 0.3 

        octaves_to_add = []
        
        # Pomodoro logic
        if self.pomodoro > 0:
            elapsed = now - self._start_time
            progress = min(1.0, elapsed / (self.pomodoro * 60.0))
            if progress > 0.4:
                volume_scale *= 1.2
                sustain_scale *= 1.5
                octaves_to_add.append(1)
            if progress > 0.8:
                volume_scale *= 1.4
                sustain_scale *= 2.0
                octaves_to_add.append(-1)
                
        # Main melody determination
        if self.mode == "jazz":
            step = random.choice([-2, -1, 1, 2])
            # High speed typing tends to make larger melodic jumps smoothly 
            if dt < 0.1: step *= 2
            
            self._jazz_idx = max(0, min(len(PENTATONIC_SCALE)-1, self._jazz_idx + step))
            midi_notes = [PENTATONIC_SCALE[self._jazz_idx]]
            base_sustain = 1.5
            
            # Chance to inject standard piano chord if not burst typing
            if dt > 0.3 and random.random() > 0.8 and self._jazz_idx + 2 < len(PENTATONIC_SCALE):
                midi_notes.append(PENTATONIC_SCALE[self._jazz_idx + 2])
            
            self._last_note_played = midi_notes[0]
        else:
            if self.cursor >= self.total:
                self.cursor = 0
            midi_notes, base_sustain = self.events[self.cursor]
            self.cursor += 1
            if len(midi_notes) > 0:
                self._last_note_played = midi_notes[0]

        # Push to the async queue instead of playing immediately
        # This fixes the "burst noise" issue
        self._play_queue.put((midi_notes, base_sustain * sustain_scale, volume_scale, octaves_to_add))

        if self.mode != "jazz":
            bar_len = 30
            progress = self.cursor / self.total
            filled = int(bar_len * progress)
            bar = "█" * filled + "░" * (bar_len - filled)
            
            pomo_info = ""
            if self.pomodoro > 0:
                pomo_prog = (now - self._start_time) / (self.pomodoro * 60.0) * 100
                pomo_info = f" [🍅 {min(100, pomo_prog):.1f}%]"

            sys.stdout.write(f"\r  ♪ [{bar}] {self.cursor}/{self.total}{pomo_info}")
            sys.stdout.flush()
            if self.cursor >= self.total:
                sys.stdout.write("  ↻ 循环中    ")
                sys.stdout.flush()

    def _quit(self):
        self._stop_event.set()


def pick_song_interactive() -> dict:
    print("\n🎵 可选曲目:\n")
    for i, song in enumerate(ALL_SONGS, 1):
        notes = len(song["events"])
        print(f"  [{i}] {song['name']} — {song['composer']}  ({notes} 音符)")
    print()

    while True:
        try:
            choice = input(f"选择曲目编号 (1-{len(ALL_SONGS)}): ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(ALL_SONGS):
                return ALL_SONGS[idx]
        except (ValueError, EOFError):
            pass
        print("  ⚠ 请输入有效编号")


def main():
    parser = argparse.ArgumentParser(
        description="Keyboard Piano 2.0 — The Virtual Jazz Pianist",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--song", "-s", type=int, default=0, help="曲目编号 (从 1 开始)")
    parser.add_argument("--midi", "-m", type=str, default="", help="加载 MIDI 文件路径")
    parser.add_argument("--mode", type=str, default="jazz",
                        choices=["piano", "gentle", "typewriter", "rain", "jazz"],
                        help="音色模式: piano(钢琴), gentle(柔和), typewriter(打机), rain(雨滴), jazz(虚拟爵士钢琴家)")
    parser.add_argument("--pomodoro", "-p", type=int, default=0, help="番茄钟分钟数 (随时间推移音效将变得史诗宏大)")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有可选曲目")
    args = parser.parse_args()

    if args.list:
        print("\n🎵 可选曲目:")
        for i, song in enumerate(ALL_SONGS, 1):
            notes = len(song["events"])
            print(f"  [{i}] {song['name']} — {song['composer']}  ({notes} 音符)")
        print(f"\n💡 也可以用 --midi <文件路径> 加载任意 MIDI 文件\n")
        return

    song = None
    if args.mode != "jazz":
        if args.midi:
            from midi_loader import load_midi
            print(f"\n📂 正在加载 MIDI: {args.midi}")
            song = load_midi(args.midi)
            print(f"   已提取 {len(song['events'])} 个音符事件")
        elif args.song > 0:
            if args.song > len(ALL_SONGS):
                print(f"⚠ 只有 {len(ALL_SONGS)} 首曲目")
                sys.exit(1)
            song = ALL_SONGS[args.song - 1]
        else:
            song = pick_song_interactive()

    app = KeyboardPiano(song, mode=args.mode, pomodoro_minutes=args.pomodoro)
    try:
        app.start()
    except KeyboardInterrupt:
        print("\n👋 再见！")

if __name__ == "__main__":
    main()
