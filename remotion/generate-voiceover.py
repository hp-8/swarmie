#!/usr/bin/env python3
"""Generate voiceover segments for Swarmie Apple-style demo using Kokoro TTS."""

import os
import soundfile as sf
from kokoro import KPipeline

VOICE = "af_bella"  # soft, gentle, bright female voice
LANG = "a"  # American English

SCENES = [
    {
        "id": "scene1-hook",
        "text": "What if five hundred users could roast your startup... before you even launch?",
    },
    {
        "id": "scene2-problem",
        "text": "Founders spend months chasing signal. Ten thousand dollars on interviews. Six months on the wrong positioning. The objections were always there.",
    },
    {
        "id": "scene3-product",
        "text": "Paste your pitch. Set your swarm size. Hit run.",
    },
    {
        "id": "scene4-brain",
        "text": "Five hundred AI personas activate. Skeptics. Founders. VCs. Lurkers. Each with real biases and distinct objections.",
    },
    {
        "id": "scene5-dashboard",
        "text": "In sixty seconds, your top objections surface. Your PMF score lands. Every reaction traceable to a persona you can interrogate.",
    },
    {
        "id": "scene6-close",
        "text": "Swarmie. Roast before you launch.",
    },
]

OUT_DIR = os.path.join(os.path.dirname(__file__), "public", "voiceover")
os.makedirs(OUT_DIR, exist_ok=True)

def main():
    pipeline = KPipeline(lang_code=LANG)

    for scene in SCENES:
        print(f"Generating {scene['id']}...")
        # Collect all audio chunks for this scene
        chunks = []
        for _, _, audio in pipeline(scene["text"], voice=VOICE):
            chunks.append(audio)

        import numpy as np
        full_audio = np.concatenate(chunks)
        out_path = os.path.join(OUT_DIR, f"{scene['id']}.wav")
        sf.write(out_path, full_audio, 24000)
        duration = len(full_audio) / 24000
        print(f"  -> {out_path} ({duration:.1f}s)")

    print("\nDone. All voiceover segments generated.")

if __name__ == "__main__":
    main()
