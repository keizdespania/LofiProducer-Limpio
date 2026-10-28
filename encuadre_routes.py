import json, threading, subprocess, glob, os
from pathlib import Path
from flask import Blueprint, jsonify, request, send_from_directory, Response

encuadre_bp = Blueprint('encuadre', __name__)
ROOT = Path(__file__).resolve().parent

HTML_FACTORY = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Factory OS - Somos El Encuadre</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=JetBrains+Mono:wght@400;700&display=swap');
        body { font-family: 'Inter', sans-serif; background: #09090b; color: #f4f4f5; }
        .mono { font-family: 'JetBrains Mono', monospace; }
        .glass { background: rgba(24, 24, 27, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(63, 63, 70, 0.5); }
        .glow-red { box-shadow: 0 0 15px rgba(230, 57, 70, 0.4); }
        .tab-active { border-bottom: 2px solid #e63946; color: #e63946; }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-thumb { background: #3f3f46; border-radius: 3px; }
        .video-container { aspect-ratio: 16/9; background: #000; border-radius: 12px; overflow: hidden; display: flex; justify-content: center; transition: all 0.3s ease; }
        .video-container.vertical { aspect-ratio: 9/16; max-height: 60vh; margin: 0 auto; }
        .video-container video { width: 100%; height: 100%; object-fit: contain; }
        .toast { animation: slideIn 0.3s forwards; }
        @keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
        .field-box { background: #09090b; border: 1px solid #3f3f46; border-radius: 6px; padding: 8px; font-size: 12px; width: 100%; margin-bottom: 8px; font-family: 'JetBrains Mono', monospace; }
    </style>
</head>
<body class="min-h-screen pb-20">
    <div id="toastContainer" class="fixed bottom-5 right-5 z-[200] flex flex-col gap-2"></div>

    <header class="border-b border-zinc-800 bg-zinc-950/80 sticky top-0 z-50 glass">
        <div class="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <a href="/" class="mr-4 text-zinc-400 hover:text-white transition" title="Volver a la Web Principal">
                    <i class="fa-solid fa-arrow-left text-xl"></i>
                </a>
                <div class="w-10 h-10 rounded-lg bg-red-600 flex items-center justify-center glow-red">
                    <i class="fa-solid fa-film text-white text-xl"></i>
                </div>
                <div>
                    <h1 class="text-xl font-bold tracking-tight">FACTORY OS</h1>
                    <p class="text-xs text-zinc-400 mono">SOMOS EL ENCUADRE</p>
                </div>
            </div>
            <div class="flex items-center gap-6">
                <select id="dateSelector" class="bg-zinc-900 border border-zinc-700 text-sm rounded-lg px-3 py-2 outline-none mono cursor-pointer">
                    <option value="">Cargando...</option>
                </select>
                <div class="text-right">
                    <p class="text-[10px] text-zinc-400 uppercase tracking-widest">IMD Global</p>
                    <p id="imdScore" class="text-2xl font-bold text-red-500 mono">--</p>
                </div>
            </div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 mt-6">
        <div class="flex gap-4 border-b border-zinc-800 mb-4 overflow-x-auto">
            <button onclick="cambiarVista('preview')" id="tab-preview" class="tab-active text-sm font-semibold pb-2 px-2 whitespace-nowrap"><i class="fa-solid fa-eye mr-2"></i>Previsualización</button>
            <button onclick="cambiarVista('distribucion')" id="tab-distribucion" class="text-zinc-400 hover:text-white text-sm font-semibold pb-2 px-2 whitespace-nowrap"><i class="fa-solid fa-share-nodes mr-2"></i>Distribución & SEO</button>
            <button onclick="cambiarVista('live')" id="tab-live" class="text-zinc-400 hover:text-white text-sm font-semibold pb-2 px-2 whitespace-nowrap"><i class="fa-solid fa-terminal mr-2"></i>Pipeline Live</button>
            <button onclick="cambiarVista('monetizacion')" id="tab-monetizacion" class="text-zinc-400 hover:text-white text-sm font-semibold pb-2 px-2 whitespace-nowrap"><i class="fa-solid fa-sack-dollar mr-2"></i>Monetización</button>
        </div>

        <!-- VISTA PREVIEW -->
        <div id="view-preview" class="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div class="lg:col-span-8 glass rounded-2xl p-4">
                <div class="flex gap-4 border-b border-zinc-800 mb-3">
                    <button onclick="cambiarVideo('largo')" id="btn-largo" class="tab-active text-sm font-semibold pb-2 px-1">Vídeo Largo</button>
                    <button onclick="cambiarVideo('short')" id="btn-short" class="text-zinc-400 hover:text-white text-sm font-semibold pb-2 px-1">Short</button>
                </div>
                <div id="videoWrapper" class="video-container">
                    <video id="mainPlayer" controls></video>
                </div>
                <div class="mt-3 flex gap-2">
                    <button onclick="compartir('youtube')" class="flex-1 bg-red-600 py-2 rounded-lg font-semibold text-sm"><i class="fa-brands fa-youtube mr-2"></i>Subir a YouTube</button>
                    <button onclick="abrirDrawer('articulo')" class="flex-1 bg-zinc-800 py-2 rounded-lg font-semibold text-sm"><i class="fa-solid fa-newspaper mr-2"></i>Artículo Web</button>
                </div>
            </div>
            <div class="lg:col-span-4 glass rounded-2xl p-4">
                <h3 class="font-bold text-sm mb-2 text-red-400">Dossier de Hoy</h3>
                <div id="dossierResumen" class="text-xs text-zinc-300 space-y-2"></div>
            </div>
        </div>

        <!-- VISTA DISTRIBUCIÓN -->
        <div id="view-distribucion" class="hidden">
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                
                <!-- YouTube -->
                <div class="glass rounded-xl p-4 border-l-4 border-l-red-600">
                    <h3 class="font-bold text-sm mb-2 text-red-500"><i class="fa-brands fa-youtube mr-2"></i> YouTube Shorts</h3>
                    <label class="text-[10px] text-zinc-400">Título</label>
                    <input id="yt-titulo" class="field-box" readonly>
                    <label class="text-[10px] text-zinc-400">Descripción</label>
                    <textarea id="yt-desc" class="field-box h-16 resize-none" readonly></textarea>
                    <label class="text-[10px] text-zinc-400">Primer Comentario</label>
                    <textarea id="yt-comment" class="field-box h-12 resize-none" readonly></textarea>
                    <div class="flex gap-2 mt-2">
                        <button onclick="copiar('yt-titulo')" class="flex-1 bg-zinc-800 py-1.5 rounded text-xs">Copiar Título</button>
                        <button onclick="copiar('yt-desc')" class="flex-1 bg-zinc-800 py-1.5 rounded text-xs">Copiar Desc</button>
                    </div>
                </div>

                <!-- TikTok -->
                <div class="glass rounded-xl p-4 border-l-4 border-l-cyan-400">
                    <h3 class="font-bold text-sm mb-2 text-cyan-400"><i class="fa-brands fa-tiktok mr-2"></i> TikTok</h3>
                    <label class="text-[10px] text-zinc-400">Texto</label>
                    <textarea id="tt-texto" class="field-box h-20 resize-none" readonly></textarea>
                    <label class="text-[10px] text-zinc-400">Hashtags</label>
                    <input id="tt-tags" class="field-box" readonly>
                    <div class="flex gap-2 mt-2">
                        <button onclick="copiar('tt-texto')" class="flex-1 bg-cyan-600 py-1.5 rounded text-xs font-bold text-black">Copiar</button>
                        <button onclick="compartir('tiktok')" class="flex-1 bg-zinc-800 py-1.5 rounded text-xs">Abrir App</button>
                    </div>
                </div>

                <!-- Instagram -->
                <div class="glass rounded-xl p-4 border-l-4 border-l-pink-500">
                    <h3 class="font-bold text-sm mb-2 text-pink-500"><i class="fa-brands fa-instagram mr-2"></i> Instagram</h3>
                    <label class="text-[10px] text-zinc-400">Texto</label>
                    <textarea id="ig-texto" class="field-box h-16 resize-none" readonly></textarea>
                    <label class="text-[10px] text-zinc-400">Hashtags</label>
                    <input id="ig-tags" class="field-box" readonly>
                    <label class="text-[10px] text-zinc-400">Primer Comentario</label>
                    <textarea id="ig-comment" class="field-box h-12 resize-none" readonly></textarea>
                    <div class="flex gap-2 mt-2">
                        <button onclick="copiar('ig-texto')" class="flex-1 bg-pink-600 py-1.5 rounded text-xs font-bold">Copiar</button>
                        <button onclick="compartir('instagram')" class="flex-1 bg-zinc-800 py-1.5 rounded text-xs">Abrir App</button>
                    </div>
                </div>

                <!-- X -->
                <div class="glass rounded-xl p-4 border-l-4 border-l-zinc-400">
                    <h3 class="font-bold text-sm mb-2 text-white"><i class="fa-brands fa-x-twitter mr-2"></i> X (Twitter)</h3>
                    <label class="text-[10px] text-zinc-400">Tuit</label>
                    <textarea id="x-texto" class="field-box h-24 resize-none" readonly></textarea>
                    <div class="flex gap-2 mt-2">
                        <button onclick="copiar('x-texto')" class="flex-1 bg-zinc-700 py-1.5 rounded text-xs font-bold">Copiar</button>
                        <button onclick="compartir('x')" class="flex-1 bg-zinc-800 py-1.5 rounded text-xs">Abrir X</button>
                    </div>
                </div>

                <!-- Threads -->
                <div class="glass rounded-xl p-4 border-l-4 border-l-zinc-600">
                    <h3 class="font-bold text-sm mb-2 text-zinc-300"><i class="fa-brands fa-threads mr-2"></i> Threads</h3>
                    <label class="text-[10px] text-zinc-400">Texto</label>
                    <textarea id="th-texto" class="field-box h-24 resize-none" readonly></textarea>
                    <button onclick="copiar('th-texto')" class="w-full bg-zinc-700 py-1.5 rounded text-xs font-bold mt-2">Copiar</button>
                </div>

                
                <!-- YouTube Comunidad -->
                <div class="glass rounded-xl p-4 border-l-4 border-l-red-500">
                    <h3 class="font-bold text-sm mb-2 text-red-500"><i class="fa-brands fa-youtube mr-2"></i> YouTube Comunidad</h3>
                    <label class="text-[10px] text-zinc-400">Texto para el Post de Comunidad</label>
                    <textarea id="yt-community" class="field-box h-24 resize-none" readonly></textarea>
                    <div class="flex gap-2 mt-2">
                        <button onclick="copiar('yt-community')" class="flex-1 bg-zinc-800 py-1.5 rounded text-xs">Copiar</button>
                        <button onclick="compartir('youtube_comunidad')" class="flex-1 bg-red-600 py-1.5 rounded text-xs font-bold">Abrir Comunidad</button>
                    </div>
                </div>

                <!-- Blogger -->
                <div class="glass rounded-xl p-4 border-l-4 border-l-orange-500">
                    <h3 class="font-bold text-sm mb-2 text-orange-500"><i class="fa-brands fa-blogger mr-2"></i> Blogger</h3>
                    <label class="text-[10px] text-zinc-400">Título</label>
                    <input id="bl-titulo" class="field-box" readonly>
                    <label class="text-[10px] text-zinc-400">Resumen</label>
                    <textarea id="bl-resumen" class="field-box h-20 resize-none" readonly></textarea>
                    <div class="flex gap-2 mt-2">
                        <button onclick="copiar('bl-resumen')" class="flex-1 bg-orange-600 py-1.5 rounded text-xs font-bold">Copiar</button>
                        <button onclick="publicarBlogger()" class="flex-1 bg-zinc-800 py-1.5 rounded text-xs">Publicar</button>
                    </div>
                </div>

            </div>
        </div>

        <!-- VISTA MONETIZACIÓN -->
        <div id="view-monetizacion" class="hidden grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div class="glass rounded-2xl p-5 border-t-4 border-t-green-500">
                <h3 class="font-bold text-lg mb-2 text-green-400"><i class="fa-brands fa-google mr-2"></i>AdSense + Afiliados</h3>
                <p class="text-xs text-zinc-400 mb-4">Inyecta el tag de Amazon y prepara el post para AdSense.</p>
                <input id="amazon-tag" type="text" placeholder="Tag Amazon" class="field-box">
                <button onclick="aplicarAfiliados()" class="w-full bg-green-600 py-2 rounded font-semibold text-sm mt-2">Inyectar en Artículo</button>
            </div>
            <div class="glass rounded-2xl p-5 border-t-4 border-t-purple-500">
                <h3 class="font-bold text-lg mb-2 text-purple-400"><i class="fa-solid fa-shirt mr-2"></i>Printify (Merch)</h3>
                <p class="text-xs text-zinc-400 mb-4">Sube las mejores imágenes generadas para crear camisetas y posters.</p>
                <button onclick="subirPrintify()" class="w-full bg-purple-600 py-2 rounded font-semibold text-sm">Subir a Printify</button>
            </div>
            <div class="glass rounded-2xl p-5 border-t-4 border-t-yellow-500">
                <h3 class="font-bold text-lg mb-2 text-yellow-400"><i class="fa-solid fa-book mr-2"></i>Amazon KDP</h3>
                <p class="text-xs text-zinc-400 mb-4">Genera un PDF con el glosario de 71 técnicas y los análisis del mes.</p>
                <button onclick="generarKDP()" class="w-full bg-yellow-600 text-black py-2 rounded font-bold text-sm">Generar PDF KDP</button>
            </div>
        </div>
    </main>

    
        <!-- VISTA PIPELINE LIVE -->
        <div id="view-live" class="hidden grid-cols-1 gap-4">
            <div class="glass rounded-xl p-4 flex justify-between items-center">
                <div>
                    <h3 class="font-bold text-lg text-green-400"><i class="fa-solid fa-terminal mr-2"></i>Consola del Sistema</h3>
                    <p class="text-xs text-zinc-400">Ejecuta el pipeline y observa a los agentes trabajar.</p>
                </div>
                <button onclick="iniciarPipeline()" id="btn-run-pipeline" class="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-lg font-bold shadow-lg transition">
                    <i class="fa-solid fa-play mr-2"></i>Ejecutar Pipeline
                </button>
            </div>
            <div class="glass rounded-xl p-4 bg-black border border-zinc-800">
                <pre id="terminalLogs" class="text-xs mono text-green-400 whitespace-pre-wrap h-[60vh] overflow-y-auto" style="font-family: 'JetBrains Mono', monospace;">Esperando inicio del pipeline...</pre>
            </div>
        </div>

    <div id="drawer" class="fixed top-0 right-[-100%] w-full max-w-2xl h-full bg-zinc-900 transition-all duration-300 z-[100] overflow-y-auto p-6 border-l border-zinc-800">
        <div class="flex justify-between items-center mb-6">
            <h2 id="drawerTitle" class="text-2xl font-bold text-red-500"></h2>
            <button onclick="cerrarDrawer()" class="text-zinc-400 hover:text-white"><i class="fa-solid fa-xmark text-2xl"></i></button>
        </div>
        <div id="drawerContent" class="text-sm text-zinc-300 space-y-4"></div>
    </div>

    <script>
        let fechaActual = "";
        let datosGlobales = null;

        window.addEventListener('DOMContentLoaded', () => {
            fetch('/api/encuadre/fechas').then(r => r.json()).then(data => {
                const sel = document.getElementById('dateSelector');
                if (!data.fechas || data.fechas.length === 0) { sel.innerHTML = '<option value="">Sin producciones</option>'; return; }
                sel.innerHTML = '';
                data.fechas.forEach(f => sel.innerHTML += `<option value="${f}">${f}</option>`);
                cargarDatos(data.fechas[0]);
            });
            document.getElementById('dateSelector').addEventListener('change', (e) => cargarDatos(e.target.value));
        });

        function cargarDatos(fecha) {
            if (!fecha) return;
            fechaActual = fecha;
            fetch(`/api/encuadre/datos/${fecha}`).then(r => r.json()).then(data => {
                datosGlobales = data;
                document.getElementById('imdScore').innerText = data.dossier?.indice_manipulacion_global || "--";
                document.getElementById('dossierResumen').innerHTML = `
                    <p><strong class="text-red-400">Tema:</strong> ${data.dossier?.tema_del_dia || 'N/A'}</p>
                    <p><strong class="text-red-400">Cita Bomba:</strong> <em>"${data.dossier?.cita_bomba || 'N/A'}"</em></p>
                    <p><strong class="text-red-400">Sarcasmo:</strong> ${data.dossier?.sarcasmo_del_dia || 'N/A'}</p>
                `;

                const s1 = (data.shorts_finales && data.shorts_finales[0]) || {};
                
                // YouTube
                document.getElementById('yt-titulo').value = s1.youtube?.titulo || "Sin título";
                document.getElementById('yt-desc').value = s1.youtube?.descripcion || "Sin descripción";
                document.getElementById('yt-comment').value = s1.youtube?.primer_comentario || "Sin comentario";
                
                // TikTok
                document.getElementById('tt-texto').value = s1.tiktok?.texto || "Sin texto";
                document.getElementById('tt-tags').value = s1.tiktok?.hashtags || "Sin hashtags";
                
                // Instagram
                document.getElementById('ig-texto').value = s1.instagram?.texto || "Sin texto";
                document.getElementById('ig-tags').value = s1.instagram?.hashtags || "Sin hashtags";
                document.getElementById('ig-comment').value = s1.instagram?.primer_comentario || "Sin comentario";

                // X
                document.getElementById('x-texto').value = s1.x?.texto || "Sin tuit";

                // Threads
                document.getElementById('th-texto').value = s1.threads?.texto || "Sin texto";

                
                // YouTube Comunidad
                const ytCom = document.getElementById('yt-community');
                if (ytCom) {
                    ytCom.value = `📢 Nuevo análisis: ${s1.youtube?.titulo || 'Análisis del día'}\n\n${s1.youtube?.descripcion || ''}\n\nLee el análisis completo en: https://elencuadre.pages.dev`;
                }

                // Blogger
                document.getElementById('bl-titulo').value = s1.blogger?.titulo || "Sin título";
                document.getElementById('bl-resumen').value = s1.blogger?.resumen || "Sin resumen";

                cambiarVideo('largo');
            });
        }

        function cambiarVista(v) {
            ['preview', 'distribucion', 'monetizacion', 'live'].forEach(t => {
                document.getElementById('view-' + t).classList.toggle('hidden', t !== v);
                const tab = document.getElementById('tab-' + t);
                if (tab) tab.className = t === v ? "tab-active text-sm font-semibold pb-2 px-2 whitespace-nowrap" : "text-zinc-400 hover:text-white text-sm font-semibold pb-2 px-2 whitespace-nowrap";
            });
            if (v === 'monetizacion') document.getElementById('view-monetizacion').classList.add('grid');
            if (v === 'live') document.getElementById('view-live').classList.add('grid');
            if (v === 'distribucion') document.getElementById('view-distribucion').classList.remove('grid');
        }

        function cambiarVideo(tipo) {
            document.getElementById('btn-largo').className = tipo === 'largo' ? "tab-active text-sm font-semibold pb-2 px-1" : "text-zinc-400 hover:text-white text-sm font-semibold pb-2 px-1";
            document.getElementById('btn-short').className = tipo === 'short' ? "tab-active text-sm font-semibold pb-2 px-1" : "text-zinc-400 hover:text-white text-sm font-semibold pb-2 px-1";
            const w = document.getElementById('videoWrapper');
            const p = document.getElementById('mainPlayer');
            if (tipo === 'largo') { w.classList.remove('vertical'); p.src = `/output/encuadre/video_largo_${fechaActual}.mp4`; }
            else { w.classList.add('vertical'); p.src = `/output/encuadre/short_1_${fechaActual}.mp4`; }
        }

        function copiar(id) {
            const el = document.getElementById(id);
            el.select(); document.execCommand('copy');
            mostrarToast('✅ Copiado al portapapeles', 'bg-green-600');
        }

        function compartir(red) {
            mostrarToast('🚀 Abriendo ' + red + '...', 'bg-blue-600');
            fetch('/api/encuadre/compartir', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({red: red, fecha: fechaActual}) });
        }

        function publicarBlogger() {
            mostrarToast('⏳ Publicando en Blogger...', 'bg-orange-600');
            fetch('/api/encuadre/publicar_blogger', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({fecha: fechaActual}) })
            .then(() => mostrarToast('✅ Publicado en Blogger', 'bg-green-600'));
        }

        function mostrarToast(msg, color) {
            const t = document.createElement('div');
            t.className = `toast ${color} text-white px-4 py-2 rounded shadow-lg text-sm font-bold`;
            t.innerText = msg;
            document.getElementById('toastContainer').appendChild(t);
            setTimeout(() => t.remove(), 3000);
        }

        
        // --- PIPELINE LIVE ---
        let logInterval = null;

        function iniciarPipeline() {
            const btn = document.getElementById('btn-run-pipeline');
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-2"></i>Ejecutando...';
            btn.disabled = true;
            btn.classList.add('opacity-50');

            fetch('/api/encuadre/run_pipeline', { method: 'POST' })
                .then(r => r.json())
                .then(data => {
                    mostrarToast(data.msg, data.status === 'ok' ? 'bg-green-600' : 'bg-red-600');
                    if (data.status === 'ok') {
                        iniciarPollingLogs();
                    } else {
                        btn.innerHTML = '<i class="fa-solid fa-play mr-2"></i>Ejecutar Pipeline';
                        btn.disabled = false;
                        btn.classList.remove('opacity-50');
                    }
                });
        }

        function iniciarPollingLogs() {
            if (logInterval) clearInterval(logInterval);
            const terminal = document.getElementById('terminalLogs');
            const btn = document.getElementById('btn-run-pipeline');

            logInterval = setInterval(() => {
                fetch('/api/encuadre/pipeline_status')
                    .then(r => r.json())
                    .then(data => {
                        terminal.innerText = data.logs || "Esperando salida...";
                        terminal.scrollTop = terminal.scrollHeight;
                        
                        if (!data.running) {
                            clearInterval(logInterval);
                            btn.innerHTML = '<i class="fa-solid fa-check mr-2"></i>Terminado';
                            btn.classList.remove('opacity-50');
                            btn.classList.add('bg-zinc-700');
                            mostrarToast('Pipeline finalizado', 'bg-green-600');
                        }
                    });
            }, 2000); // Actualizar cada 2 segundos
        }

        // --- MONETIZACIÓN ---
        function aplicarAfiliados() { mostrarToast('💸 Inyectando afiliados...', 'bg-green-600'); }
        function subirPrintify() { mostrarToast('👕 Subiendo a Printify...', 'bg-purple-600'); }
        function generarKDP() { mostrarToast('📚 Generando PDF KDP...', 'bg-yellow-600'); }
    </script>
</body>
</html>"""

@encuadre_bp.route("/encuadre")
def vista_encuadre(): return Response(HTML_FACTORY, mimetype='text/html')


# === PIPELINE LIVE ENDPOINTS ===
LOG_FILE = ROOT / "data" / "logs" / "pipeline_web.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
_pipeline_process = None

@encuadre_bp.route("/api/encuadre/run_pipeline", methods=["POST"])
def api_run_pipeline():
    global _pipeline_process
    import subprocess
    # Comprobar si ya está corriendo
    if _pipeline_process is not None and _pipeline_process.poll() is None:
        return jsonify({"status": "error", "msg": "El pipeline ya está en ejecución."})
    
    # Lanzar pipeline en segundo plano redirigiendo salida al log
    log_f = open(LOG_FILE, "w")
    _pipeline_process = subprocess.Popen(
        ["python3", "scripts/pipeline_encuadre.py"],
        cwd=str(ROOT),
        stdout=log_f,
        stderr=subprocess.STDOUT,
        text=True
    )
    return jsonify({"status": "ok", "msg": "Pipeline iniciado."})

@encuadre_bp.route("/api/encuadre/pipeline_status")
def api_pipeline_status():
    global _pipeline_process
    running = _pipeline_process is not None and _pipeline_process.poll() is None
    
    # Leer las últimas 50 líneas del log
    logs = ""
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, "r") as f:
                lines = f.readlines()
                logs = "".join(lines[-50:])
        except: pass
        
    return jsonify({"running": running, "logs": logs})

@encuadre_bp.route("/api/encuadre/fechas")
def api_encuadre_fechas():
    OUT = ROOT / "output" / "encuadre"
    fechas = [Path(a).stem.replace("redes_", "") for a in glob.glob(str(OUT / "redes_*.json"))]
    fechas += [Path(a).stem.replace("produccion_", "") for a in glob.glob(str(OUT / "produccion_*.json"))]
    return jsonify({"fechas": sorted(list(set(fechas)), reverse=True)})

@encuadre_bp.route("/api/encuadre/datos/<fecha>")
def api_encuadre_datos(fecha):
    OUT = ROOT / "output" / "encuadre"
    prod = OUT / f"produccion_{fecha}.json"
    redes = OUT / f"redes_{fecha}.json"
    data = {}
    if prod.exists(): data = json.loads(prod.read_text())
    if redes.exists():
        r = json.loads(redes.read_text())
        data["shorts_finales"] = r.get("shorts", data.get("shorts_finales", []))
    return jsonify(data)

@encuadre_bp.route("/api/encuadre/compartir", methods=["POST"])
def api_encuadre_compartir():
    data = request.json
    script = ROOT / "scripts" / "hack_compartir_redes.py"
    if data.get("red"):
        def run(): subprocess.run(["python3", str(script), data["red"]], cwd=str(ROOT))
        threading.Thread(target=run).start()
        return jsonify({"status": "ok"})
    return jsonify({"status": "error"})

@encuadre_bp.route("/api/encuadre/publicar_blogger", methods=["POST"])
def api_publicar_blogger():
    data = request.json
    def run(): subprocess.run(["python3", "scripts/publicar_blogger_encuadre.py", data['fecha']], cwd=str(ROOT))
    threading.Thread(target=run).start()
    return jsonify({"status": "ok"})

@encuadre_bp.route("/output/encuadre/<path:filename>")
def video_encuadre(filename):
    return send_from_directory(ROOT / "output" / "encuadre", filename)
