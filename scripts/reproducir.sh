#!/data/data/com.termux/files/usr/bin/bash
# Reproductor del ecosistema KeiZ
# Uso: reproducir.sh [audio|video|playlist|menu]

MODE="${1:-menu}"

case "$MODE" in
  audio)
    ULTIMO=$(ls -t ~/LofiProducer/assets/*/audio/local/*.wav 2>/dev/null | head -1)
    [ -z "$ULTIMO" ] && echo "Sin audio local" && exit 1
    termux-media-player play "$ULTIMO"
    ;;
  video)
    ULTIMO=$(ls -t ~/LofiProducer/output/*/video_final_*.mp4 2>/dev/null | head -1)
    [ -z "$ULTIMO" ] && echo "Sin vídeos" && exit 1
    termux-open "$ULTIMO"
    ;;
  playlist)
    cd ~/LofiProducer/output/keiz_productions && python -m http.server 8935 &
    sleep 2
    termux-open-url "http://localhost:8935/"
    ;;
  menu)
    echo "🎵 KeiZ Player"
    echo "1) Audio local"
    echo "2) Vídeo final"
    echo "3) Playlist web"
    read -p "Opción: " OP
    case "$OP" in
      1) bash "$0" audio ;;
      2) bash "$0" video ;;
      3) bash "$0" playlist ;;
    esac
    ;;
esac
