# SKILL.md — Manual del Dios Orquestador

> **Auto-generado** por `scripts/generate_skill_md.py`.
> **NO editar a mano.** Cambia los contratos y regenera.

---

## ⚡ REGLA DE ORO

> **"Imposible romperlo."** Todos los motores validan backend. Params 'fijo' bloqueados. Si falla 2 veces, PARA y pregunta.

---

## 🎯 1. MAPA DE MOTORES

| Motor | Contrato | Tool de Dios | Presets (nombres) |
|-------|----------|--------------|-------------------|
| **musica** | `acestep_contract.json` | `generar_cancion_kaggle` | lofi, ambient, piano, cinematic, hiphop, electronic... |
| **voz** | `sherpa_contract.json` | `generar_narracion` | noticias, narracion_relajada, urgente, audiobook, publicidad, tutorial... |
| **imagen** | `image_contract.json` | `generar_imagen` | cinematic, anime, realistic, cartoon, product, portrait... |
| **video** | `video_contract.json` | `generar_video` | cinematic_480p, cinematic_720p, vertical_480p, vertical_720p, turbo_4steps, draft_rapido |
| **ffmpeg** | `ffmpeg_contract.json` | `ensamblar_video_final` | youtube_1080p, youtube_720p, tiktok_9x16, shorts_720_9x16, audio_podcast, audio_lofi... |
| **youtube** | `youtube_contract.json` | `subir_youtube` | draft_privado, publicar_ahora, programar, shorts_vertical, lofi_music, podcast |
| **blogger** | `blogger_contract.json` | `—` | blog_rapido, articulo_seo, review_largo, tutorial_paso_a_paso, post_simple, pagina_estatica |
| **pixabay** | `pixabay_contract.json` | `generar_video_rapido` | ia_news, lofi, finanzas, boe, b_roll_generico, cinematic_drone |

**Cómo consultar un contrato completo**: `leer_documentacion("data/agent/<motor>_contract.json")`

---

## 🎬 1.b RECETAS DE MONTAJE (auto-generadas)

Cada receta en `config/montajes/<canal>.json` define cómo se ensambla el vídeo final:

| Nicho | Duración | Resolución | CRF | Fades | Música vol | Loop |
|-------|----------|------------|-----|-------|-----------|------|
| boe | 900s | 1920x1080 | 20 | 2.0/2.0 | 0.15 | ✅ |
| finanzas_barrio | 900s | 1920x1080 | 20 | 2.0/2.0 | 0.15 | ✅ |
| ia_news | 900s | 1920x1080 | 20 | 2.0/2.0 | 0.15 | ✅ |
| lofi | 900s | 1920x1080 | 20 | 2.0/2.0 | 0.15 | ✅ |

**Motor**: `scripts/motor_ensamblado.py` (lee la receta + assets → MP4 final).
**Regenerar**: `python scripts/sincronizar_montajes.py`.

---

## 🏛️ 2. NICHOS Y SU PIPELINE


### 🏛️ ia_news — IA News
**Formato**: video_voz_imagen · **Duración**: 90s · **Tono**: intriga, thriller tecnológico, misterio

**Presets recomendados:**
- musica: `cinematic`
- voz: `noticias`
- imagen: `cinematic`
- video: `cinematic_480p`
- ffmpeg: `youtube_1080p`
- youtube: `draft_privado`
- blogger: `articulo_seo`
- pixabay: `ia_news`

**Pipeline:**
```
Guion (LLM): noticias de las últimas 24h sobre IA
Voz: generar_narracion(guion, preset='noticias')
Música: generar_cancion_kaggle(preset='cinematic', duration=90)
Imágenes: generar_imagen(preset='cinematic', aspect='16:9') × 3-5
Vídeo: generar_video(preset='cinematic_480p') × 2-3
Ensamblar: ensamblar_video_final(preset='youtube_1080p')
Subir: subir_youtube(preset='draft_privado')
```

### 🏛️ finanzas_barrio — Finanzas de Barrio
**Formato**: video_voz_imagen · **Duración**: 90s · **Tono**: cercano, analogías del día a día, sin tecnicismos

**Presets recomendados:**
- musica: `lofi`
- voz: `noticias`
- imagen: `cinematic`
- video: `cinematic_480p`
- ffmpeg: `youtube_1080p`
- youtube: `draft_privado`
- blogger: `articulo_seo`
- pixabay: `finanzas`

**Pipeline:**
```
Guion (LLM): explicar noticia financiera con analogías del barrio
Voz: generar_narracion(guion, preset='noticias')
Música: generar_cancion_kaggle(preset='lofi', duration=90)
Imágenes: generar_imagen(preset='cinematic', aspect='16:9') × 3-5
Vídeo: generar_video(preset='cinematic_480p') × 2-3
Ensamblar: ensamblar_video_final(preset='youtube_1080p')
Subir: subir_youtube(preset='draft_privado')
```

### 🏛️ boe — El BOE
**Formato**: video_voz_imagen · **Duración**: 90s · **Tono**: claro, legal, pausado

**Presets recomendados:**
- musica: `ambient`
- voz: `audiobook`
- imagen: `realistic`
- video: `draft_rapido`
- ffmpeg: `youtube_720p`
- youtube: `draft_privado`
- blogger: `articulo_seo`
- pixabay: `boe`

**Pipeline:**
```
Guion (LLM): resumen de la ley del BOE en lenguaje claro
Voz: generar_narracion(guion, preset='audiobook')
Música: generar_cancion_kaggle(preset='ambient', duration=120)
Imágenes: generar_imagen(preset='realistic', aspect='16:9') × 3
Vídeo: generar_video(preset='draft_rapido') × 2
Ensamblar: ensamblar_video_final(preset='youtube_720p')
Subir: subir_youtube(preset='draft_privado')
```

### 🏛️ lofi — Lofi
**Formato**: musica_loop · **Duración**: 3600s · **Tono**: relax, estudio, concentración

**Presets recomendados:**
- musica: `lofi`
- imagen: `anime`
- video: `draft_rapido`
- ffmpeg: `youtube_1080p`
- youtube: `lofi_music`
- blogger: `post_simple`
- pixabay: `lofi`

**Pipeline:**
```
Música: generar_cancion_kaggle(preset='lofi', duration=590) × N chunks
Imagen: generar_imagen('cozy room rain', preset='anime', aspect='16:9')
Vídeo: generar_video(preset='draft_rapido') × 3 (loop)
Ensamblar: ensamblar_video_final(preset='youtube_1080p')
Subir: subir_youtube(preset='lofi_music')
```

---

## 🔧 3. TOOLS DE DIOS (34 activas)


**🎵 Música**: `generar_cancion_kaggle`

**🎙️ Voz**: `generar_narracion`

**🎨 Imagen**: `generar_imagen`

**🎬 Vídeo**: `generar_video`, `generar_video_rapido`, `ensamblar_video_final`, `producir_video`

**📤 Publicar**: `subir_youtube`, `publicar_en_redes`

**☁️ Kaggle**: `lanzar_notebook_kaggle`, `lanzar_pipeline_kaggle`

**📋 Orquestación**: `producir_nicho`

**🧠 Memoria**: `recordar_hecho`, `consultar_hechos`

**🔍 Búsqueda**: `buscar_en_web`, `buscar_youtube`, `buscar_repositorio`, `leer_rss`

**🛠️ Sistema**: `ejecutar_comando`, `estado_sistema`, `sanar_sistema`, `notificar_movil`, `instalar_dependencia`

**📂 Archivos**: `read_file`, `write_file`, `validate_file`, `promote_file`

**📚 Docs**: `leer_documentacion`, `documentar_aprendizaje`, `consultar_manual_python`

**🤖 Agentes**: `pedir_a_especialista`, `delegar_tareas_paralelas`, `analizar_video_competencia`, `list_canales`

---

## 🚨 4. DICCIONARIO DE ERRORES + FIX

| Error | Motor | Fix |
|-------|-------|-----|
| `403 quotaExceeded` | YouTube | Esperar 24h (reset medianoche PT) o rotar proyecto Google Cloud |
| `403 forbidden (sin auditar)` | YouTube | Sin auditoría Google, TODO sale privado aunque pidas public |
| `400 invalidTitle` | YouTube | Título 1-100 chars, sin < > ni saltos |
| `403 Blogger` | Blogger | Blogger API NO habilitada en Google Cloud Console |
| `429 rate limit` | Pixabay/Groq | Esperar 60s. Si persistente, rotar modelo/proveedor |
| `OOM T4` | Wan 2.2 | Bajar resolution a 832x480, num_frames a 33, o usar turbo_4steps |
| `1280x720 distorsiona` | Wan 2.2 | 720 NO es múltiplo de 32. Usar 1280x704 |
| `num_frames inválido` | Wan 2.2 | Debe ser 4n+1 (8,13,17,21,25,33,41,49,65,81,97,121) |
| `status='public' Blogger` | Blogger | Blogger usa draft/live/scheduled. NO existe public |
| `kernel cuelga >55min` | Kaggle | Timeout interno del template. Reintentar o bajar batch size |

---

## 📏 5. REGLAS GLOBALES

1. **Privacidad por defecto**: siempre `private` / `draft` hasta validar.
2. **Sin auditoría Google**: YouTube = todo privado aunque pidas public.
3. **Batch**: música 5/kernel, vídeo 3/kernel. Ahorro -72% cuota.
4. **Prompt vídeo**: Sujeto + Movimiento + Cámara + Iluminación. Una acción por clip.
5. **Imagen aspect**: 16:9 YouTube, 9:16 TikTok, 1:1 Instagram.
6. **FFmpeg**: `-y` siempre. `-ss` ANTES de `-i`. `pix_fmt yuv420p` para universal.
7. **Blogger**: `status` = draft/live/scheduled (NO public). Cuota 100k/día.
8. **Pixabay**: 100 req/min. B-roll en vídeo transformado OK. Redistribuir as-is NO.
9. **Preset desconocido**: consulta `/api/params/<motor>` o `leer_documentacion`.
10. **Si dudas, pregunta al usuario** (regla 7 del Manual Frodo).

---

## 🚦 6. DECISIÓN RÁPIDA: ¿Qué preset uso?

| Si el nicho es... | Música | Voz | Imagen | Vídeo |
|-------------------|--------|-----|--------|-------|
| IA News | `cinematic` | `noticias` | `cinematic` | `cinematic_480p` |
| Finanzas Barrio | `lofi` | `noticias` | `cinematic` | `cinematic_480p` |
| BOE | `ambient` | `audiobook` | `realistic` | `draft_rapido` |
| Lofi | `lofi` | — | `anime` | `draft_rapido` |

**Si el nicho no está aquí**: usar `cinematic` / `noticias` / `realistic` / `draft_rapido` por defecto.

---

*Auto-generado con 8 motores, 4 nichos, 10 errores.*
