# HANDOFF - SOMOS EL ENCUADRE - 2026-11-05 (LTX VIDEO + CAPIBARAS)

## ESTADO EN 30 SEGUNDOS
Pipeline visual rediseñado (72 fotos SDXL con Groq 4). LTX 2.3 I2V via HF Space funciona (3 capibaras + 1 piramide en GitHub). ZeroGPU limita a 5 min/dia. Se ha creado la via_c (free-aistudio en Kaggle T4) para tener LTX ILIMITADO y GRATIS. Pendiente de probar. Cola separada en pendiente/completados para no tener conflictos git.

## COMMITS RECIENTES
- 6d1e373 fix(ltx): cola separada en pendiente/completados (sin conflictos git)
- 308a24f docs(ltx): contrato v2.0 separa via HF Space y via Kaggle GPU
- 65857e9 test: cola con 5 capibaras (piramide completada)
- cd81f03 chore: pipeline 05/11 + agentes LTX HF/Kaggle + test capibaras

## LO QUE FUNCIONA
- Pipeline diario (SDXL + Groq 4 + voz + podcast + web).
- Shorts con 3 escenas narrativas (9:16).
- LTX I2V via HF Space: 3 capibaras + 1 piramide generados y subidos a GitHub.
- Cola separada (pendiente/completados) sin conflictos git.
- Token GitHub Fine-grained verificado.
- Token HF verificado.

## LO QUE NO FUNCIONA / PENDIENTE
- ZeroGPU: 5 min/dia. 2 videos/dia max. 2 capibaras pendientes esperando reset.
- via_b (Kaggle GPU con dangkhoa2016): bloqueada por libcudart.so.12.
- via_c (free-aistudio en Kaggle T4): EN PRUEBAS. Si funciona, es la definitiva (ilimitada).
- Blogger: pausado hasta 11/11.

## PRIMEROS PASOS PROXIMA IA
1. Comprobar estado del kernel ltx-free-t4 en Kaggle (via_c).
2. Si OK: lanzar los 2 capibaras pendientes.
3. Si falla: leer el log y ajustar el endpoint /generate (mirar src/server.py de free-aistudio).
4. Si via_c funciona: integrar LTX en el pipeline solo para el Hook de la intro.

## REGLAS CRITICAS
- #56: SDXL no entiende metaforas. Describe objetos fisicos.
- #57: SDXL no sabe escribir. Prohibido titulares.
- #58: Groq 4 directo para prompts visuales.
- #59: 3 escenas por short.
- #60: Wan 2.2 Turbo: yetter-ai/Wan2.2-TI2V-5B-Turbo-Diffusers.
- #61: NUNCA usar el mismo fichero de cola como fuente y destino.
- #62: LTX HF Space: usar gradio_client (Python 3.10), NO HTTP manual.
- #63: ZeroGPU = 5 min/dia. Avisar al usuario antes de lanzar.
- #64: LTX ilimitado = free-aistudio en Kaggle T4 (via_c).
- #65: duration_ui maximo = 8.5s.
- #66: Binarios pre-compilados fallan por GLIBC/libcudart. Compilar o usar free-aistudio.

## NO ROMPER
- producir_fase2() (clasico).
- Cron 06:00.
- web/site/ (Cloudflare).
- ltx_cola_pendiente.json (solo lo escribe Termux).
- ltx_cola_completados.json (solo lo escribe Kaggle).
