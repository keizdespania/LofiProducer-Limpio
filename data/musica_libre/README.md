# Biblioteca de Música CC — Somos El Encuadre

## Regla de oro
Cada short usa UNA pista diferente. Cada pista se corta en SU propio peak.
4 moods distintos = 4 experiencias distintas = canal top 1.

## Mapping ángulo → mood
- Controversia → dramatic
- Urgencia     → intriga
- Justicia     → cinematic
- Curiosidad   → ambient

## Cómo llenar (manual, 1 vez)

### Mixkit (recomendado, 0 fricción)
https://mixkit.co/free-stock-music/tag/dramatic/
https://mixkit.co/free-stock-music/tag/ambient/
https://mixkit.co/free-stock-music/tag/cinematic/
https://mixkit.co/free-stock-music/tag/suspense/

Descarga 1-3 MP3 por mood. Sin registro, sin atribución.

### YouTube Audio Library (cero riesgo absoluto)
https://studio.youtube.com/channel/UC/music
Filtro: "Atribución no obligatoria"

## Nombre de fichero (importante)
{autor}_{titulo}_{mood}.mp3
Ejemplo: mixkit_dark_tension_dramatic.mp3

## Metadatos obligatorios
Cada .mp3 tiene su .json hermano con el mismo nombre base:
{
  "titulo": "Dark Tension",
  "autor": "Mixkit",
  "fuente": "mixkit",
  "licencia": "sin_atribucion",
  "mood": "dramatic",
  "duracion_seg": 90,
  "descargado": "2026-10-31"
}

## Qué NO usar para shorts
- YouTube con yt-dlp (riesgo Content ID)
- Jamendo con licencia BY-NC (no comercial)
