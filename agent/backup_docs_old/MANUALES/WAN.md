# 🎬 MANUAL WAN 2.2 — Reglas para no alucinar

> El modelo Wan 2.2 TI2V-5B no "entiende" el guion. Solo sigue instrucciones visuales precisas. Si envías frases coloquiales, el resultado será borroso o estático.

## 1. FÓRMULA OBLIGATORIA DE PROMPT

**Orden estricto: Sujeto → Movimiento → Cámara → Escena/Iluminación**

- **Inicio (sujeto + movimiento)**: "Un zorro rojo se mueve sigilosamente por la nieve" (NO "zorro, nieve, caminando").
- **Movimiento específico**: Usa verbos, no adjetivos. "Las olas rompen", "Ella gira lentamente" (estable). "Escena hermosa" (inestable).
- **Cámara**: Especifica claramente. "Toma de seguimiento", "primer plano", "paneo lento". Si no escribes cámara, el modelo tiende a quedarse estático.
- **Final (iluminación/clima)**: "Hora dorada", "niebla matutina", "lluvia intensa".

## 2. REGLAS DE ORO (ANTI-ALUCINACIÓN)

- **Un clip = una acción simple**. Si quieres "abre la puerta y luego se gira para hablar", el modelo se confundirá. Divide el guion en escenas de 2-5 segundos.
- **NO usar "tag soup"** (listas de palabras). Usar frases completas cinematográficas.
- **El inicio del prompt pesa más** que el final.

## 3. CONFIGURACIÓN EN KAGGLE T4

- **Reinicio de kernel**: Después de instalar dependencias, reiniciar. Si no, conflictos de importación.
- **Pasos (steps)**: 5-8 pasos (con Turbo LoRA). NO 20-30 (genera OOM o lentitud).
- **CFG**: 1.0. Omite rama negativa, acelera, reduce alucinaciones.
- **Resolución**: 1280x704 (o 704x1280 vertical). NO 1280x720 (distorsiona por compresión VAE).

## 4. EJEMPLO DE PROMPT BIEN ESCRITO

**❌ Malo**: "Héroe, lluvia, corriendo, ciudad, cinematográfico"
→ Resultado: estático, borroso.

**✅ Bueno**: "Un hombre con chaqueta de cuero corre rápidamente por un callejón lluvioso, cámara en mano siguiéndolo de cerca, luces de neón reflejándose en los charcos, noche lluviosa."
→ Resultado: cinematográfico, movimiento real.

## 5. ESTRATEGIA DEL ORQUESTADOR

Cuando el orquestador recibe un guion:
1. Divide el guion en escenas de 2-5 segundos (una acción por escena).
2. Genera 3 candidatos de prompt por escena.
3. Elige el que mejor cumpla la fórmula (Sujeto → Movimiento → Cámara → Iluminación).
4. Envía ese prompt a Kaggle con la config (CFG=1.0, steps=6, res=1280x704).

## 6. CONFIGURACIÓN DEL NOTEBOOK (worker_definitivo)

- **model_type**: "ti2v_2_2"
- **resolution**: "1280x704" (o "704x1280" vertical)
- **video_length**: 81 frames (≈3.4s)
- **num_inference_steps**: 6
- **guidance_scale**: 1.0
- **flow_shift**: 3.0
