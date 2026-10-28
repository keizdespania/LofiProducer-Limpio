

## ✅ RECETA MAESTRA ACE-STEP (Verificada 2026-10-18)
Esta es la secuencia exacta que consiguió arrancar la interfaz web de ACE-Step 1.5 en Kaggle T4.

**Celda 1 (Entorno):**
%cd /kaggle/working
%cd ACE-Step-1.5

**Celda 2 (Descarga del modelo):**

**Celda 3 (Arrancar Web - OJO a MPLBACKEND):**

**CONFIGURACIÓN EN LA WEB DE GRADIO:**
- Archivo de punto de control: checkpoints/Ace-Step1.5
- Ruta del modelo principal: Seleccionar Ace-Step1.5 (si no aparece, hacer cp -r checkpoints/Ace-Step1.5 checkpoints/acestep-v15-turbo en una celda nueva y refrescar).
- Dispositivo: auto
- VAE: official
- Trayectoria del Modelo LM: Dejar vacío.


## ⚠️ BUG CONOCIDO (Rust en Termux)
- **Librerías afectadas:** `primp`, `rpds-py`, `hf-xet`, `maturin`.
- **Síntoma:** `error: metadata-generation-failed` por `Target triple not supported by rustup`.
- **Solución para `gradio_client`:** Si falla al instalar `gradio_client` en Termux por culpa de `hf-xet`, usar la versión antigua que no lo requiere: `pip install gradio_client==1.3.0`. 

## ⚠️ AVISOS CRÍTICOS DE RUST Y DISCO (Actualizado)
- **El terror de Rust (hf-xet, rpds-py, primp):** Termux no compila estas librerías. Si falla la instalación de gradio_client o huggingface-hub, instalar huggingface-hub==0.29.3 (que no usa hf-xet) y usar pip install --no-deps para saltarse la compilación. Luego instalar a mano tqdm, filelock, pyyaml, fsspec, websockets.
- **El disco de Kaggle (20 GB):** Bajo ningún concepto intentar descargar el modelo completo de ACE-Step con acestep-download. Llena el disco, bloquea la sesión y no deja ni hacer rm. Usar siempre hf download ACE-Step/Ace-Step1.5 que baja solo el Turbo.
- **Comando de arranque verificado:** !MPLBACKEND=Agg uv run acestep --share --config_path checkpoints/Ace-Step1.5

## 🚧 EL MISTERIO DE LA API (En investigación)
- El gradio_client de Termux falla al conectar con ACE-Step porque ACE-Step usa un protocolo de eventos/colas propio, no la API estándar de Gradio.
- Se intentó arrancar la API REST (uv run acestep-api --port 8001) pero la T4 se queda colgada por falta de memoria.
- Próximo paso: Investigar si se puede hacer un curl al endpoint /gradio_api/call/generate con el JSON exacto que usa la web.

## 🚀 HACKEO DE LA API DE GRADIO (Verificado 2026-10-18)
- **Endpoint secreto:** `/gradio_api/call/generation_wrapper`.
- **78 parámetros:** El script `generar_musica.py` usa `/config` para leer los valores por defecto de la web.
- **Error "Model not fully initialized":** Ocurre porque el servidor arranca dormido. SOLUCIÓN: Lanzar Kaggle con `--init_service true` (Ej: `uv run acestep --share --init_service true --config_path ...`).

## 🏆 RECETA DEFINITIVA: ARRANQUE AUTOMÁTICO Y DESCARGA (2026-10-18)
- **El comando mágico:** `!MPLBACKEND=Agg uv run acestep --share --init_service true` 
  - ⚠️ **NUNCA** añadir `--config_path` con una ruta absoluta (ej. `checkpoints/...`), porque el script se vuelve loco, cree que no tiene el modelo y se pone a descargar los 19GB, reventando el disco. Dejar que lo autodetecte.
  - El flag `--init_service true` carga el modelo en la GPU **antes** de abrir la web. Así no hay que pulsar botones a mano.
- **Hackeo de los 78 parámetros:** 
  - El endpoint es `/gradio_api/call/generation_wrapper`.
  - Se obtienen los valores por defecto haciendo un `GET` a `/config` y mapeando los IDs.
- **El bucle de Heartbeats:** Gradio responde con `event: heartbeat` y `data: null` mientras la GPU procesa (puede durar varios minutos). NO es un error, es que sigue trabajando.
- **Descarga automática:** Al recibir `event: complete`, el JSON contiene la ruta del archivo en el servidor (ej. `/kaggle/working/.../cancion.mp3`). Se descarga haciendo un `GET` a `{url_base}/gradio_api/file={ruta_del_json}`.

## 🚨 FIX CRÍTICO: NaN en T4
- Causa: T4 no soporta bfloat16 y float16 se desborda.
- Solución: Parchear init_service_orchestrator.py cambiando torch.float16 por torch.float32.
- Script: Usar Python en Kaggle para hacer el .replace('torch.float16', 'torch.float32') antes de arrancar.

## 🎵 Generación de Música Automática
- El script `scripts/generar_musica.py` se conecta a la API de Gradio, extrae los parámetros, envía la petición y descarga el archivo `.mp3` a `output/cancion_generada.mp3`.
- El Dios ya tiene la tool `generar_cancion_kaggle` para hacerlo conversacionalmente.

## 🎵 Generación de Música Automática
- El script  descarga la canción a .
- El Dios ya tiene la tool  para hacerlo conversacionalmente.

## 🏆 EL GRAN HACKEO COMPLETADO
- **El cliente definitivo:** `scripts/generar_musica.py` extrae los 78 parámetros de la web, envía la petición, gestiona los latidos y descarga el MP3.
- **La herramienta del Dios:** `dios.py` tiene la tool `generar_cancion_kaggle` que permite lanzar todo esto desde el chat de la web.
- **El Fix del NaN:** Parchear `init_service_orchestrator.py` con `.replace("torch.float16", "torch.float32")` en Kaggle. Ya está documentado.

## 🚀 NUEVA RECETA v10: acestep.cpp + GGUF (2026-10-19)
- **El problema anterior:** El modelo oficial de ACE-Step (PyTorch) pesa 9.4 GB. Al descargarlo en Kaggle, sumado a las dependencias, reventaba los 20 GB de disco (`No space left on device`).
- **La solución:** Usar el motor **acestep.cpp** (C++) con modelos **GGUF cuantizados**. El conjunto completo (DiT Q4_K_M + LM 0.6B Q8 + Text Encoder Q8 + VAE) pesa ~3.5 GB. Cabe de sobra.

### Celdas del notebook v10 (`worker_definitivo_v10.ipynb`)
1.  **Clonar y compilar:**
    ```bash
    !git clone --recurse-submodules https://github.com/ServeurpersoCom/acestep.cpp.git
    %cd acestep.cpp
    !chmod +x buildcuda.sh
    !./buildcuda.sh
    ```
2.  **Descargar los GGUF:**
    ```bash
    !mkdir -p models
    %cd models
    !wget -q --content-disposition "https://huggingface.co/Serveurperso/ACE-Step-1.5-GGUF/resolve/main/acestep-v15-turbo-Q4_K_M.gguf?download=true"
    !wget -q --content-disposition "https://huggingface.co/Serveurperso/ACE-Step-1.5-GGUF/resolve/main/acestep-5Hz-lm-0.6B-Q8_0.gguf?download=true"
    !wget -q --content-disposition "https://huggingface.co/Serveurperso/ACE-Step-1.5-GGUF/resolve/main/Qwen3-Embedding-0.6B-Q8_0.gguf?download=true"
    !wget -q --content-disposition "https://huggingface.co/Serveurperso/ACE-Step-1.5-GGUF/resolve/main/vae-BF16.gguf?download=true"
    ```
3.  **Generar música (CLI):**
    ```bash
    %cd /kaggle/working/acestep.cpp
    # (Crear el JSON de la petición)
    !./build/ace-lm --request /tmp/request.json --lm models/acestep-5Hz-lm-0.6B-Q8_0.gguf
    !./build/ace-synth --request /tmp/request0.json --embedding models/Qwen3-Embedding-0.6B-Q8_0.gguf --dit models/acestep-v15-turbo-Q4_K_M.gguf --vae models/vae-BF16.gguf
    ```
4.  **Subir a GitHub:** (La celda ya tiene el token inyectado)

## 🤖 EL DIOS YA PUEDE LANZAR EL PIPELINE
- **Nueva herramienta:** `lanzar_pipeline_kaggle`. El Dios la usa cuando le pides música sin darle una URL.
- **Orquestador:** `scripts/kaggle_orchestrator.py` coge el notebook `worker_definitivo_v10.ipynb` de la raíz del proyecto, lo sube a Kaggle y lo activa.

## 🎬 RECETA PARA VÍDEO (LTX-Video en Kaggle)
- **Notebook:** Usar el de `free-aistudio` (`ltx2-3-video.ipynb`). Descarga los pesos cuantizados y arranca un servidor Gradio.
- **Conexión desde Termux:** Usar el script `scripts/generar_video.py`.
- **Endpoint:** `/gradio_api/call/handle_generation`.
- **Opciones obligatorias:** El parámetro de dimensiones debe ser exactamente `'360p (480x360) - Fastest Testing Baseline'` o `'480p (640x368) - Optimized Safe Balanced Size'`. El scheduler debe ser `'default'`. Si se pone otro valor, el servidor devuelve error 500.

---

# 🚀 ACTUALIZACIÓN KAGGLE (2026-10-20): LA ERA DEL CLÚSTER Y WAN 2.2

El ecosistema ha evolucionado. Kaggle ya no es solo para ACE-Step y LTX.

## ☁️ 1. Estrategia Multi-Cuenta (60h/semana)
Para evitar cuellos de botella, el Dios rotará **2 cuentas de Kaggle** (inicialmente), gestionando los tokens `KGAT_` mediante el futuro script `kaggle_rotator.py`. Cada cuenta da ~30h/semana de T4 (16 GB VRAM).

## 🎬 2. El Nuevo Motor de Vídeo: Wan 2.2 TI2V-5B
- **Adiós a LTX-Video**: LTX es pesado y tiene poco movimiento. Usaremos **Wan 2.2 TI2V-5B** (Apache 2.0).
- **Por qué Wan 2.2**: Modelo denso de 5B parámetros. Cabe perfectamente en la T4 (16GB) generando a 720p con FP8. Movimiento cinematográfico muy superior.
- **Implementación**: 
  - Opción A: Usar el notebook de la comunidad **WanGP-Kaggle** (que ya trae ComfyUI preconfigurado).
  - Opción B: Script Python que llame a la API de ComfyUI.
- **Licencia**: Apache 2.0 (100% comercial).

## 🎙️ 3. Servidor Kokoro TTS en Kaggle (Audio Masivo)
- **Objetivo**: Servir como backend masivo para OmniRoute.
- **Herramienta**: `Kokoro-FastAPI` (o `opencoca/AI-Voice-Kokoro-FastAPI`).
- **Despliegue**: Levantar el servidor en un notebook de Kaggle con Docker SDK o UV.
- **Exposición**: Usar `endpoint-vps` o Cloudflare Tunnel para obtener una URL HTTPS.
- **Integración**: Añadir la URL en OmniRoute como proveedor `openai-compatible` (endpoint `/v1/audio/speech`).
- **Licencia**: Apache 2.0 (Comercial).

## 🌍 4. Plan B (Si Kaggle falla o no hay cuota)
- **Modal**: $30/mes gratis (T4/A100) - Requiere tarjeta.
- **Leafcloud**: 50h/mes gratis (RTX 6000, 24GB VRAM) - Requiere tarjeta (verificación).
- **Lightning AI**: ~22h/mes (T4) - Sin tarjeta.

## ⚠️ 5. Reglas de Oro en Kaggle (Recordatorio)
- **Disco (20 GB)**: Por eso usamos GGUF en ACE-Step. Para Wan 2.2, vigilar los pesos descargados (evitar llenar el disco).
- **RAM (16 GB VRAM)**: No cargar dos modelos a la vez (ej. TTS y Vídeo en la misma sesión).
- **Sesiones (12h)**: Apagar manualmente (`Stop Session`) al terminar para no gastar cuota.

## 📦 USO DE KAGGLE DATASETS COMO INPUT (Optimización de Carga)
Para modelos pesados (Wan 2.2, XTTS, LLMs), es ineficiente descargar los pesos desde HuggingFace en cada ejecución. Se debe usar un Dataset de Kaggle.

### 1. Preparación del Dataset
1. Descargar los pesos una sola vez (en el móvil o en un notebook de Kaggle).
2. Subirlos a Kaggle como un Dataset privado (ej. `tu-usuario/wan22-weights`).

### 2. Modificación del Notebook
En lugar de usar `from_pretrained("Wan-AI/...")`, apuntar a la ruta local del input:
    model_path = "/kaggle/input/wan22-weights"
    pipe = WanPipeline.from_pretrained(model_path, ...)

### 3. Modificación del Push (`kaggle_bearer.py`)
Al lanzar el kernel, añadir la fuente del dataset en el payload:
    "datasetDataSources": ["tu-usuario/wan22-weights"]
