#!/data/data/com.termux/files/usr/bin/bash
cd /data/data/com.termux/files/home/LofiProducer
echo "⬇️  Trayendo cambios desde GitHub..."
git pull origin main
echo "📦 Moviendo archivos nuevos de output/ a una copia de seguridad local..."
mkdir -p data/output_local
mv output/*.mp3 output/*.mp4 output/*.wav data/output_local/ 2>/dev/null
echo "🧹 Limpiando el repo de archivos binarios pesados..."
git rm --cached output/* 2>/dev/null
git commit -m "chore: limpiar output/ tras sincronizar a móvil" --no-verify 2>/dev/null
echo "🚀 Subiendo limpieza a GitHub..."
git push origin main 2>/dev/null
echo "✅ Sincronización completa. Los archivos están en data/output_local/"
ls -lh data/output_local/
