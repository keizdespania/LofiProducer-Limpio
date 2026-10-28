"""hack_wan_contract.py — Contrato Wan 2.2 TI2V-5B con presets reales para T4."""
import json, pathlib

OUT = pathlib.Path.home() / "LofiProducer/data/agent/video_contract.json"

PRESETS = {
    "cinematic_480p": {
        "desc": "Cine rápido 480p (T4 friendly)",
        "params": {"resolution": "832x480", "num_frames": 49, "num_inference_steps": 25, "guidance_scale": 5.0, "shift": 3.0, "fps": 16}
    },
    "cinematic_720p": {
        "desc": "Cine 720p (más lento, máxima calidad)",
        "params": {"resolution": "1280x704", "num_frames": 49, "num_inference_steps": 30, "guidance_scale": 5.0, "shift": 5.0, "fps": 24}
    },
    "vertical_480p": {
        "desc": "Vertical TikTok/Reels/Shorts",
        "params": {"resolution": "480x832", "num_frames": 49, "num_inference_steps": 25, "guidance_scale": 5.0, "shift": 3.0, "fps": 16}
    },
    "vertical_720p": {
        "desc": "Vertical alta calidad",
        "params": {"resolution": "704x1280", "num_frames": 49, "num_inference_steps": 30, "guidance_scale": 5.0, "shift": 5.0, "fps": 24}
    },
    "turbo_4steps": {
        "desc": "Turbo con Lightning LoRA (4 pasos)",
        "params": {"resolution": "832x480", "num_frames": 49, "num_inference_steps": 4, "guidance_scale": 1.0, "shift": 3.0, "fps": 16}
    },
    "draft_rapido": {
        "desc": "Borrador rápido (calidad baja, velocidad máxima)",
        "params": {"resolution": "640x384", "num_frames": 33, "num_inference_steps": 15, "guidance_scale": 5.0, "shift": 3.0, "fps": 16}
    }
}

RESOLUCIONES = {
    "480p_16:9": {"width": 832, "height": 480},
    "480p_9:16": {"width": 480, "height": 832},
    "720p_16:9": {"width": 1280, "height": 704},
    "720p_9:16": {"width": 704, "height": 1280},
    "square": {"width": 704, "height": 704},
    "custom": {"width": 832, "height": 480}
}

VALIDADOR = {
    "reglas": [
        {"campo": "width", "min": 128, "max": 1280, "default": 832, "multiplo": 32, "nota": "TI2V-5B exige múltiplos de 32"},
        {"campo": "height", "min": 128, "max": 1280, "default": 480, "multiplo": 32},
        {"campo": "num_frames", "min": 8, "max": 121, "default": 49, "formula": "4n+1"},
        {"campo": "num_inference_steps", "min": 4, "max": 50, "default": 25, "rec": "4 (Turbo) o 25-50 (estándar)"},
        {"campo": "guidance_scale", "min": 1.0, "max": 10.0, "default": 5.0, "nota": "Turbo: 1.0; estándar: 5.0"},
        {"campo": "shift", "min": 1.0, "max": 20.0, "default": 3.0, "rec": "3.0 para 480p, 5.0 para 720p"},
        {"campo": "fps", "min": 8, "max": 24, "default": 16}
    ]
}

REGLAS = [
    "TI2V-5B SOLO acepta resoluciones múltiplos de 32 (832x480, 1280x704, 480x832, 704x1280)",
    "NO usar 1280x720 (720 NO es múltiplo de 32). Usar 1280x704",
    "num_frames debe ser 4n+1 (8, 13, 17, 21, 25, 29, 33, 37, 41, 45, 49...)",
    "T4 15GB: 480p (832x480) con 49 frames es seguro. 720p puede hacer OOM",
    "Con Lightning LoRA: num_inference_steps=4 y guidance_scale=1.0 (Turbo)",
    "Sin LoRA: num_inference_steps=25-50 y guidance_scale=5.0",
    "shift=3.0 recomendado para 480p; shift=5.0 para 720p",
    "negative_prompt por defecto: blurry, low quality, distorted, static, watermark, text",
    "Un clip = una acción simple. Dividir guiones largos en escenas de 2-5s",
    "El prompt debe seguir: Sujeto + Movimiento + Cámara + Iluminación",
    "fps=16 para 480p; fps=24 para 720p (evitar >24 en T4)",
    "Duración máx por clip: 121 frames / 24 fps ≈ 5s. Para 15 min: concatenar N clips"
]

EJEMPLOS = [
    {"input": "un gato en bicicleta en un parque", "preset": "cinematic_480p", "prompt": "Un gato atigrado monta una bicicleta roja por un parque soleado, cámara de seguimiento lateral, luz dorada de tarde"},
    {"input": "clip vertical para TikTok de SpaceX", "preset": "vertical_480p", "prompt": "Un cohete SpaceX despega lentamente dejando una estela de humo blanco, cámara fija desde abajo, cielo azul despejado"},
    {"input": "prueba rápida de concepto", "preset": "turbo_4steps", "prompt": "Una ola rompiendo en una playa al atardecer, cámara lenta, tonos cálidos"}
]

NEGATIVE_DEFAULT = "blurry, low quality, distorted, static, watermark, text, jpeg artifacts, oversaturated, deformed"

def main():
    contract = {
        "motor": "Wan 2.2 TI2V-5B",
        "modelo": "Wan-AI/Wan2.2-TI2V-5B-Diffusers",
        "version": "2.2",
        "donde": "Kaggle T4 (15GB VRAM) o VPS con GPU >=16GB",
        "presets": PRESETS,
        "resoluciones": RESOLUCIONES,
        "validador": VALIDADOR,
        "reglas_anti_alucinacion": REGLAS,
        "ejemplos": EJEMPLOS,
        "negative_prompt_default": NEGATIVE_DEFAULT,
        "stats": {
            "presets": len(PRESETS),
            "resoluciones": len(RESOLUCIONES),
            "reglas": len(REGLAS)
        }
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(contract, indent=2, ensure_ascii=False))
    print(f"OK {OUT}")
    print(f"  Presets: {len(PRESETS)} | Resoluciones: {len(RESOLUCIONES)} | Reglas: {len(REGLAS)}")

if __name__ == "__main__":
    main()
