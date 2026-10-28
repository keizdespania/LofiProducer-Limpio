#!/usr/bin/env python3
"""hack_sherpa_contract.py v2 — Contrato Sherpa-ONNX con presets + validador + ejemplos."""
import json, pathlib, sherpa_onnx

OUT = pathlib.Path.home() / "LofiProducer/data/agent/sherpa_contract.json"

# ═══ TABLA DE VOCES CONOCIDAS ═══
VOCES = {
    "es_ES-davefx-medium": {"nombre": "Davefx", "idioma": "es_ES", "genero": "M", "calidad": "media", "sid": 0, "nota": "Voz oficial del Dios. Clara y rápida."},
    "es_ES-sharvard-medium": {"nombre": "Sharvard", "idioma": "es_ES", "genero": "F", "calidad": "media", "sid": 0, "nota": "Femenina, neutra."},
    "es_MX-claude-high": {"nombre": "Claude", "idioma": "es_MX", "genero": "M", "calidad": "alta", "sid": 0, "nota": "Mexicana, calidad alta."},
    "en_US-lessac-medium": {"nombre": "Lessac", "idioma": "en_US", "genero": "F", "calidad": "media", "sid": 0, "nota": "Inglés, referencia audiobook."},
    "en_US-ryan-high": {"nombre": "Ryan", "idioma": "en_US", "genero": "M", "calidad": "alta", "sid": 0, "nota": "Inglés, calidad alta."},
}

# ═══ PRESETS (parámetros reales, no prosa) ═══
PRESETS = {
    "noticias": {
        "descripcion": "Telediario / IA News. Clara, directa, sin adornos.",
        "params": {"speed": 1.0, "length_scale": 1.0, "noise_scale": 0.667, "noise_scale_w": 0.8, "silence_scale": 0.2, "max_num_sentences": 5}
    },
    "narracion_relajada": {
        "descripcion": "Documental / audiolibro. Pausada, con silencios.",
        "params": {"speed": 0.9, "length_scale": 1.15, "noise_scale": 0.6, "noise_scale_w": 0.8, "silence_scale": 0.3, "max_num_sentences": 5}
    },
    "urgente": {
        "descripcion": "Breaking news / alerta. Rápida, tensa.",
        "params": {"speed": 1.15, "length_scale": 0.87, "noise_scale": 0.7, "noise_scale_w": 0.8, "silence_scale": 0.1, "max_num_sentences": 5}
    },
    "audiobook": {
        "descripcion": "Audiolibro largo. Natural, sin prisa.",
        "params": {"speed": 0.95, "length_scale": 1.05, "noise_scale": 0.6, "noise_scale_w": 0.8, "silence_scale": 0.25, "max_num_sentences": 8}
    },
    "publicidad": {
        "descripcion": "Spot publicitario. Energética, con gancho.",
        "params": {"speed": 1.05, "length_scale": 0.95, "noise_scale": 0.7, "noise_scale_w": 0.9, "silence_scale": 0.15, "max_num_sentences": 3}
    },
    "tutorial": {
        "descripcion": "Tutorial / educativo. Clara, pausada, didáctica.",
        "params": {"speed": 0.95, "length_scale": 1.05, "noise_scale": 0.6, "noise_scale_w": 0.8, "silence_scale": 0.3, "max_num_sentences": 5}
    },
    "sintesis_rapida": {
        "descripcion": "Pruebas / borradores. Rápida, menos natural.",
        "params": {"speed": 1.25, "length_scale": 0.8, "noise_scale": 0.667, "noise_scale_w": 0.8, "silence_scale": 0.1, "max_num_sentences": 8}
    }
}

# ═══ EJEMPLOS FEW-SHOT ═══
EJEMPLOS = [
    {
        "input": "Narra la noticia de SpaceX en 60 segundos",
        "preset": "noticias",
        "params": {"texto": "...", "voz": "es_ES-davefx-medium", "preset": "noticias"}
    },
    {
        "input": "Hazme un audiolibro de 10 minutos de mi novela",
        "preset": "audiobook",
        "params": {"texto": "...", "voz": "es_ES-davefx-medium", "preset": "audiobook", "max_num_sentences": 8}
    },
    {
        "input": "Genera un spot publicitario corto y energético",
        "preset": "publicidad",
        "params": {"texto": "...", "voz": "es_ES-davefx-medium", "preset": "publicidad", "speed": 1.1}
    },
]

# ═══ VALIDADOR (rangos con efecto documentado) ═══
VALIDADOR = {
    "descripcion": "Clampea parámetros de voz antes de generar. NUNCA rechaza, corrige.",
    "reglas": [
        {"campo": "speed", "min": 0.5, "max": 2.0, "default": 1.0, "efecto": "Multiplicador de velocidad"},
        {"campo": "length_scale", "min": 0.5, "max": 2.0, "default": 1.0, "efecto": "<1 más rápido, >1 más lento"},
        {"campo": "noise_scale", "min": 0.1, "max": 1.5, "default": 0.667, "efecto": "Varianza de la voz. >1.0 distorsiona"},
        {"campo": "noise_scale_w", "min": 0.1, "max": 1.5, "default": 0.8, "efecto": "Varianza de duración"},
        {"campo": "silence_scale", "min": 0.0, "max": 1.0, "default": 0.2, "efecto": "Pausas entre frases"},
        {"campo": "max_num_sentences", "min": 1, "max": 10, "default": 5, "efecto": "Frases por batch. >8 puede OOM en Termux"},
        {"campo": "num_threads", "min": 1, "max": 4, "default": 2, "efecto": "Termux: no saturar CPU"},
        {"campo": "sid", "min": 0, "max": 0, "default": 0, "efecto": "Piper/VITS = monovoz. NUNCA cambiar"},
    ]
}

# ═══ REGLAS ANTI-ALUCINACIÓN ═══
REGLAS = [
    "SOLO VITS para las 5 voces (Davefx, Sharvard, Claude, Lessac, Ryan). NO usar matcha/kokoro/zipvoice",
    "provider='cpu' y num_threads=2 en Termux",
    "sid=0 SIEMPRE (Piper es monovoz). MeloTTS es la excepción (sid=1) y NO está en nuestro catálogo",
    "length_scale>1.2 suena arrastrado; <0.8 suena apresurado",
    "noise_scale>1.0 distorsiona la voz; <0.3 suena robótico",
    "max_num_sentences=5-8 para textos largos (>100 palabras). Evita OOM",
    "Las rutas model/lexicon/tokens/data_dir NUNCA se inventan: se leen del FS",
    "output por defecto: WAV 22050Hz. Convertir a MP3 con FFmpeg para redes",
    "Para noticias: speed=1.0, length_scale=1.0 (preset 'noticias')",
    "Para audiolibro: length_scale=1.15, silence_scale=0.3 (preset 'narracion_relajada')",
    "Si el texto es >2000 chars, partir en chunks de ~500 chars y concatenar con FFmpeg",
]

def main():
    contract = {
        "motor": "Sherpa-ONNX",
        "version": getattr(sherpa_onnx, "__version__", "?"),
        "uso": "TTS offline local (5 voces Piper/VITS)",
        "voces_disponibles": VOCES,
        "presets": PRESETS,
        "ejemplos": EJEMPLOS,
        "validador": VALIDADOR,
        "reglas_anti_alucinacion": REGLAS,
        "motores_no_usados": ["matcha", "kokoro", "kitten", "pocket", "supertonic", "zipvoice"],
        "notas_tecnicas": {
            "noise_scale": "0.667 mono-speaker, 0.333 multi-speaker (Piper docs)",
            "length_scale": "1.0 default. <1 faster, >1 slower. Para natural: 1.1-1.25",
            "silence_scale": "0.2 default. Subir a 0.3 para narración pausada",
            "max_num_sentences": "1 default. Subir a 5-8 para textos largos",
            "sid": "0 para todas nuestras voces (Piper monovoz)",
        }
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(contract, indent=2, ensure_ascii=False))
    print(f"OK {OUT}")
    print(f"  Sherpa-ONNX {contract['version']}")
    print(f"  Voces: {len(VOCES)} | Presets: {len(PRESETS)} | Ejemplos: {len(EJEMPLOS)} | Reglas: {len(REGLAS)}")

if __name__ == "__main__":
    main()
