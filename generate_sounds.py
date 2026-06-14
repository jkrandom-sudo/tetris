"""Generate retro game sound effects for Tetris using Python's wave module."""
import wave
import struct
import math
import os

SAMPLE_RATE = 22050
AMPLITUDE = 0.5
MAX_16BIT = 32767

SOUND_DIR = os.path.join(os.path.dirname(__file__), "sounds")
os.makedirs(SOUND_DIR, exist_ok=True)

def make_sine(freq, duration_sec, volume=AMPLITUDE):
    """Generate a sine wave."""
    n_samples = int(SAMPLE_RATE * duration_sec)
    return [
        int(volume * MAX_16BIT * math.sin(2 * math.pi * freq * t / SAMPLE_RATE))
        for t in range(n_samples)
    ]

def make_square(freq, duration_sec, volume=AMPLITUDE):
    """Generate a square wave (retro feel)."""
    n_samples = int(SAMPLE_RATE * duration_sec)
    return [
        int(volume * MAX_16BIT * (1 if math.sin(2 * math.pi * freq * t / SAMPLE_RATE) >= 0 else -1))
        for t in range(n_samples)
    ]

def make_sawtooth(freq, duration_sec, volume=AMPLITUDE):
    """Generate a sawtooth wave."""
    n_samples = int(SAMPLE_RATE * duration_sec)
    return [
        int(volume * MAX_16BIT * 2 * (freq * t / SAMPLE_RATE - math.floor(freq * t / SAMPLE_RATE + 0.5)))
        for t in range(n_samples)
    ]

def apply_envelope(samples, attack=0.01, decay=0.05):
    """Apply AD envelope to avoid clicks."""
    n = len(samples)
    attack_n = int(attack * SAMPLE_RATE)
    decay_n = int(decay * SAMPLE_RATE)
    result = list(samples)
    for i in range(min(attack_n, n)):
        result[i] = int(result[i] * (i / attack_n))
    for i in range(max(0, n - decay_n), n):
        result[i] = int(result[i] * ((n - i) / decay_n))
    return result

def mix(*signals):
    """Mix multiple signals together."""
    max_len = max(len(s) for s in signals)
    result = [0] * max_len
    for s in signals:
        for i in range(len(s)):
            result[i] += s[i]
    # Clamp
    max_val = max(abs(s) for s in result)
    if max_val > MAX_16BIT:
        scale = MAX_16BIT / max_val
        result = [int(s * scale) for s in result]
    return result

def write_wav(filename, samples):
    """Write samples to a WAV file."""
    path = os.path.join(SOUND_DIR, filename)
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        for s in samples:
            wf.writeframes(struct.pack("<h", max(-32768, min(32767, s))))
    print(f"  Created: {path}")

print("Generating sound effects...")

# 1. Move sound - short blip
move = make_square(300, 0.05, 0.3)
move = apply_envelope(move)
write_wav("move.wav", move)

# 2. Rotate sound - higher blip
rotate = make_square(500, 0.08, 0.3)
rotate = apply_envelope(rotate)
write_wav("rotate.wav", rotate)

# 3. Soft drop sound
soft_drop = make_square(200, 0.04, 0.2)
soft_drop = apply_envelope(soft_drop)
write_wav("soft_drop.wav", soft_drop)

# 4. Hard drop sound - thump
thump1 = make_sine(100, 0.08, 0.5)
thump2 = make_sine(60, 0.12, 0.4)
hard_drop = mix(thump1, thump2)
hard_drop = apply_envelope(hard_drop, attack=0.001, decay=0.1)
write_wav("hard_drop.wav", hard_drop)

# 5. Line clear - ascending arpeggio
clear_note1 = make_square(400, 0.08, 0.4)
clear_note2 = make_square(500, 0.08, 0.4)
clear_note3 = make_square(600, 0.08, 0.4)
clear_note4 = make_square(800, 0.12, 0.4)
line_clear = mix(
    clear_note1 + [0] * (SAMPLE_RATE // 10),
    [0] * (SAMPLE_RATE // 20) + clear_note2 + [0] * (SAMPLE_RATE // 10),
    [0] * (SAMPLE_RATE // 10) + clear_note3 + [0] * (SAMPLE_RATE // 10),
    [0] * (SAMPLE_RATE // 8) + clear_note4,
)
line_clear = apply_envelope(line_clear, attack=0.005, decay=0.2)
write_wav("line_clear.wav", line_clear)

# 6. Tetris (4-line) clear - triumphant
tetris_clear = make_square(600, 0.15, 0.5) + make_square(800, 0.15, 0.5) + make_square(1000, 0.3, 0.5)
tetris_clear = apply_envelope(tetris_clear, attack=0.005, decay=0.3)
write_wav("tetris_clear.wav", tetris_clear)

# 7. Game over - descending
go1 = make_sawtooth(400, 0.2, 0.4)
go2 = make_sawtooth(300, 0.2, 0.4)
go3 = make_sawtooth(200, 0.2, 0.4)
go4 = make_sawtooth(100, 0.4, 0.4)
game_over = mix(
    go1 + [0] * (SAMPLE_RATE * 1),
    [0] * int(SAMPLE_RATE * 0.2) + go2 + [0] * int(SAMPLE_RATE * 0.8),
    [0] * int(SAMPLE_RATE * 0.4) + go3 + [0] * int(SAMPLE_RATE * 0.6),
    [0] * int(SAMPLE_RATE * 0.6) + go4,
)
game_over = apply_envelope(game_over, attack=0.01, decay=0.3)
write_wav("game_over.wav", game_over)

# 8. Level up sound
lu1 = make_square(500, 0.1, 0.4)
lu2 = make_square(700, 0.1, 0.4)
lu3 = make_square(900, 0.15, 0.4)
level_up = mix(
    lu1 + [0] * int(SAMPLE_RATE * 0.15),
    [0] * int(SAMPLE_RATE * 0.1) + lu2 + [0] * int(SAMPLE_RATE * 0.1),
    [0] * int(SAMPLE_RATE * 0.2) + lu3,
)
level_up = apply_envelope(level_up, attack=0.005, decay=0.2)
write_wav("level_up.wav", level_up)

# 9. Hold sound
hold = make_square(400, 0.06, 0.25) + make_square(600, 0.06, 0.25)
hold = apply_envelope(hold)
write_wav("hold.wav", hold)

print(f"\nDone! {len(os.listdir(SOUND_DIR))} sound files created in {SOUND_DIR}/")
