#!/usr/bin/env python3
"""srt_desde_voz.py - Genera SRT desde edge_tts usando SentenceBoundary.
Sintetiza voz + captura frases con timestamps exactos → SRT para quemar con ffmpeg.
"""
import asyncio, sys
from pathlib import Path
import edge_tts

def _srt_time(seg):
    h = int(seg // 3600)
    m = int((seg % 3600) // 60)
    s = int(seg % 60)
    ms = int((seg - int(seg)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

async def generar_srt(texto, voz_path, srt_path):
    communicate = edge_tts.Communicate(texto, "es-ES-AlvaroNeural", rate="-5%")
    subs = []
    with open(voz_path, "wb") as audio_f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_f.write(chunk["data"])
            elif chunk["type"] == "SentenceBoundary":
                # offset y duration en unidades de 100 nanosegundos
                start = chunk["offset"] / 10_000_000
                dur = chunk["duration"] / 10_000_000
                subs.append((start, start + dur, chunk["text"]))
    # Escribir SRT
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, (start, end, text) in enumerate(subs, 1):
            f.write(f"{i}\n")
            f.write(f"{_srt_time(start)} --> {_srt_time(end)}\n")
            f.write(f"{text}\n\n")
    return len(subs)

if __name__ == "__main__":
    texto = sys.argv[1] if len(sys.argv) > 1 else "Test de subtítulos"
    voz = sys.argv[2] if len(sys.argv) > 2 else "/tmp/test_voz.mp3"
    srt = voz.replace(".mp3", ".srt")
    n = asyncio.run(generar_srt(texto, voz, srt))
    print(f"✅ {n} bloques SRT en {srt}")
    if n > 0:
        print("\n=== CONTENIDO ===")
        print(Path(srt).read_text()[:500])
