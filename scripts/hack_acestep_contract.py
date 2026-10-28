#!/usr/bin/env python3
"""hack_acestep_contract.py — Clasifica los 81 params en 5 bloques accionables."""
import json
from pathlib import Path

SRC = Path.home() / "LofiProducer/data/agent/acestep_params.json"
OUT = Path.home() / "LofiProducer/data/agent/acestep_contract.json"

BLOCK = {
    # A: metadatos (agente rellena desde guion)
    "task_type":"A","caption":"A","lyrics":"A","instrumental":"A",
    "vocal_language":"A","bpm":"A","keyscale":"A","timesignature":"A",
    "duration":"A","global_caption":"A",
    # B: difusion DiT
    "inference_steps":"B","guidance_scale":"B","shift":"B","infer_method":"B",
    "sampler_mode":"B","use_adg":"B","cfg_interval_start":"B","cfg_interval_end":"B",
    "latent_shift":"B","latent_rescale":"B","seed":"B",
    "velocity_norm_threshold":"B","velocity_ema_factor":"B","timesteps":"B",
    "dcw_enabled":"B","dcw_mode":"B","dcw_scaler":"B","dcw_high_scaler":"B","dcw_wavelet":"B",
    # C: LM 5Hz
    "thinking":"C","lm_temperature":"C","lm_cfg_scale":"C","lm_top_k":"C","lm_top_p":"C",
    "lm_negative_prompt":"C","use_cot_metas":"C","use_cot_caption":"C","use_cot_lyrics":"C",
    "use_cot_language":"C","use_constrained_decoding":"C",
    "cot_bpm":"C","cot_keyscale":"C","cot_timesignature":"C","cot_duration":"C",
    "cot_vocal_language":"C","cot_caption":"C","cot_lyrics":"C",
    # D: repaint/cover/flow (ignorar para text2music)
    "repainting_start":"D","repainting_end":"D","chunk_mask_mode":"D",
    "repaint_latent_crossfade_frames":"D","repaint_wav_crossfade_sec":"D",
    "repaint_mode":"D","repaint_strength":"D","retake_seed":"D","retake_variance":"D",
    "flow_edit_morph":"D","flow_edit_source_caption":"D","flow_edit_source_lyrics":"D",
    "flow_edit_n_min":"D","flow_edit_n_max":"D","flow_edit_n_avg":"D",
    "audio_cover_strength":"D","cover_noise_strength":"D",
    "reference_audio":"D","src_audio":"D","audio_codes":"D",
    # E: config del job y post-proceso
    "instruction":"E","enable_normalization":"E","normalization_db":"E",
    "fade_in_duration":"E","fade_out_duration":"E",
    "batch_size":"E","allow_lm_batch":"E","use_random_seed":"E","seeds":"E",
    "lm_batch_chunk_size":"E","constrained_decoding_debug":"E",
    "audio_format":"E","mp3_bitrate":"E","mp3_sample_rate":"E",
}

META = {
    "caption":{"rol":"rellenar","obligatorio":True,"nota":"Prompt descriptivo del estilo musical"},
    "lyrics":{"rol":"rellenar","nota":"Opcional. Solo si instrumental=False"},
    "instrumental":{"rol":"rellenar","nota":"True=música sin voz (lyrics='')"},
    "vocal_language":{"rol":"rellenar","nota":"'es','en' o 'unknown' para instrumental"},
    "bpm":{"rol":"rellenar","rango":[30,300],"nota":"None=LM lo estima. Indicar género ayuda"},
    "keyscale":{"rol":"rellenar","nota":"Ej 'C Major','Am'. Vacío=auto"},
    "timesignature":{"rol":"rellenar","nota":"'4/4','3/4'. Vacío=auto"},
    "duration":{"rol":"rellenar","rango":[10,600],"nota":"-1=auto. Para 1h: 10x360s + FFmpeg concat"},
    "task_type":{"rol":"fijo","nota":"NUNCA cambiar para generar desde cero"},
    "inference_steps":{"rol":"ajustar_por_modelo","rango":{"turbo":[4,8],"base":[32,100]},
                       "nota":"Turbo no mejora con más pasos"},
    "guidance_scale":{"rol":"fijo","rango":[1,15],"nota":"Solo aplica a Base. Turbo lo ignora"},
    "shift":{"rol":"ajustar_por_modelo","rango":[1,5],"nota":"Turbo: usar 3.0"},
    "lm_temperature":{"rol":"fijo","rango":[0,2],"nota":"Más alto=más creativo y arriesgado"},
    "lm_cfg_scale":{"rol":"fijo","rango":[1,10],"nota":">1 fuerza al LM a seguir el prompt"},
    "lm_top_p":{"rol":"fijo","rango":[0,1],"nota":"1.0=desactivado"},
    "seed":{"rol":"fijo","nota":"-1=aleatorio. Entero fijo para reproducibilidad"},
    "batch_size":{"rol":"fijo","nota":"T4 14GB: mantener 1-2 para no OOM"},
    "audio_format":{"rol":"ajustar_por_modelo","nota":"Kaggle: flac. Redes: mp3"},
}

BLOCK_INFO = {
    "A":{"nombre":"Metadatos","rol_global":"agente rellena desde guion"},
    "B":{"nombre":"Difusion_DiT","rol_global":"NO tocar salvo experto"},
    "C":{"nombre":"LM_5Hz","rol_global":"control del pensamiento del LM"},
    "D":{"nombre":"Repaint_Cover_Edit","rol_global":"ignorar para text2music"},
    "E":{"nombre":"Batch_Config_Post","rol_global":"config del job y post-proceso"},
}

REGLAS = [
    "Turbo: inference_steps 4-8, shift 3.0, NO tocar guidance_scale",
    "Base: inference_steps 32-100, guidance_scale 7.0, shift 1.0",
    "NO pedir duration > 600s en una sola llamada",
    "caption SIEMPRE obligatorio en text2music",
    "instrumental=True -> lyrics='' y vocal_language='unknown'",
    "Para 1h loop: 10x360s o 60x60s y concatenar con FFmpeg",
    "batch_size max 2 en T4 (14GB VRAM)",
    "seed=-1 aleatorio; entero fijo para A/B testing",
    "Termux: audio_format=mp3 para redes; flac para archivo",
    "NUNCA cambiar task_type si no se domina (cover/repaint/lego/extract/complete)",
    "Para 'lofi': bpm 70-85, keyscale minor, instrumental=True, duration 60-180s",
    "Para 'ambient': bpm 60-80, sin percusión en caption, instrumental=True",
    "Para 'piano': caption con 'solo piano', instrumental=True, bpm 70-100",
]

def main():
    data = json.loads(SRC.read_text())
    bloques = {k:{"nombre":v["nombre"],"rol_global":v["rol_global"],"params":{}}
               for k,v in BLOCK_INFO.items()}
    for cls in ("GenerationParams","GenerationConfig"):
        for field, info in data[cls]["fields"].items():
            b = BLOCK.get(field,"E")
            meta = META.get(field,{"rol":"fijo"})
            bloques[b]["params"][field] = {"type":info["type"],"default":info["default"],**meta}
    contract = {"motor":"ACE-Step v11 (acestep.cpp + GGUF)","version":"1.5",
                "source_file":str(SRC),"total_params":data["_total_params"],
                "task_principal":"text2music","bloques":bloques,
                "reglas_anti_alucinacion":REGLAS}
    OUT.write_text(json.dumps(contract,indent=2,ensure_ascii=False))
    for k,v in bloques.items():
        print(f"  Bloque {k} ({v['nombre']:22}): {len(v['params'])} params")
    print(f"OK {OUT} | total: {data['_total_params']}")

if __name__ == "__main__":
    main()
