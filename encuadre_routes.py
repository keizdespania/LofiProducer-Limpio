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
            <button onclick="cambiarVista('analytics')" id="tab-analytics" class="text-zinc-400 hover:text-white text-sm font-semibold pb-2 px-2 whitespace-nowrap"><i class="fa-solid fa-chart-line mr-2"></i>Analytics</button>
            <button onclick="cambiarVista('ab')" id="tab-ab" class="text-zinc-400 hover:text-white text-sm font-semibold pb-2 px-2 whitespace-nowrap"><i class="fa-solid fa-flask mr-2"></i>A/B Testing</button>
            <button onclick="cambiarVista('calendario')" id="tab-calendario" class="text-zinc-400 hover:text-white text-sm font-semibold pb-2 px-2 whitespace-nowrap"><i class="fa-regular fa-calendar mr-2"></i>Calendario</button>
            <button onclick="cambiarVista('agentes')" id="tab-agentes" class="text-zinc-400 hover:text-white text-sm font-semibold pb-2 px-2 whitespace-nowrap"><i class="fa-solid fa-robot mr-2"></i>Agentes</button>
            <button onclick="cambiarVista('monetizacion')" id="tab-monetizacion" class="text-zinc-400 hover:text-white text-sm font-semibold pb-2 px-2 whitespace-nowrap"><i class="fa-solid fa-sack-dollar mr-2"></i>Monetización</button>
            <button onclick="cambiarVista('cms')" id="tab-cms" class="text-zinc-400 hover:text-white text-sm font-semibold pb-2 px-2 whitespace-nowrap"><i class="fa-solid fa-pen-ruler mr-2"></i>Diseño Web (CMS)</button>
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

        <!-- VISTA PUBLICAR (Distribucion) -->
        <div id="view-distribucion" class="hidden grid-cols-1 gap-6">
            <div class="flex justify-between items-center bg-zinc-900/50 p-4 rounded-xl border border-zinc-800">
                <div>
                    <h2 class="text-xl font-bold text-red-500">🚀 Publicar Todo</h2>
                    <p class="text-xs text-zinc-400">Guiones, SEO y redes listos para copiar o subir</p>
                </div>
                <div class="flex gap-2">
                    <button onclick="copiarTodoPublicar()" class="bg-zinc-800 hover:bg-zinc-700 px-4 py-2 rounded text-sm font-semibold transition"><i class="fa-solid fa-copy mr-2"></i>Copiar TODO</button>
                    <button onclick="subirTodoYouTube()" class="bg-red-600 hover:bg-red-500 px-4 py-2 rounded text-sm font-semibold transition"><i class="fa-brands fa-youtube mr-2"></i>Subir Todo a YT</button>
                </div>
            </div>
            <div id="publicar-content" class="grid grid-cols-1 gap-4"><div class="text-center py-10"><i class="fa-solid fa-spinner fa-spin text-2xl text-red-500"></i></div></div>
        </div>
        
        <!-- VISTA CMS (Diseño Web) -->
        <div id="view-cms" class="hidden grid-cols-1 lg:grid-cols-12 gap-4">
            <div class="lg:col-span-3 glass rounded-2xl p-4 flex flex-col" style="max-height: 75vh;">
                <h3 class="font-bold text-sm mb-3 text-red-400"><i class="fa-solid fa-folder-tree mr-2"></i>Archivos</h3>
                <div id="cms-tree" class="overflow-y-auto text-sm flex-1 space-y-1"></div>
                <button onclick="cmsNuevoArchivo()" class="mt-3 bg-zinc-800 hover:bg-zinc-700 py-2 rounded text-xs"><i class="fa-solid fa-plus mr-1"></i>Nuevo Archivo</button>
            </div>
            <div class="lg:col-span-9 glass rounded-2xl p-4 flex flex-col" style="max-height: 75vh;">
                <div class="flex justify-between items-center mb-3">
                    <h3 id="cms-filename" class="font-bold text-sm text-zinc-300 font-mono">Selecciona un archivo</h3>
                    <div class="flex gap-2">
                        <button onclick="cmsGuardar()" class="bg-green-600/20 text-green-400 border border-green-600/30 px-3 py-1 rounded text-xs font-semibold hover:bg-green-600/40"><i class="fa-solid fa-save mr-1"></i>Guardar</button>
                        <button onclick="cmsBuild()" class="bg-blue-600 hover:bg-blue-500 px-3 py-1 rounded text-xs font-semibold"><i class="fa-solid fa-rocket mr-1"></i>Build & Deploy</button>
                    </div>
                </div>
                <textarea id="cms-editor" class="flex-1 w-full bg-[#09090b] text-zinc-300 font-mono text-xs p-3 rounded border border-zinc-700 outline-none focus:border-red-500" placeholder="El contenido aparecerá aquí..." spellcheck="false" disabled></textarea>
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
                <p class="text-xs text-zinc-400 mb-4">Genera un PDF con el glosario de 51 técnicas y los análisis del mes.</p>
                <button onclick="generarKDP()" class="w-full bg-yellow-600 text-black py-2 rounded font-bold text-sm">Generar PDF KDP</button>
            </div>
        </div>

        <!-- VISTA ANALYTICS (Cloudflare RUM) -->
        <div id="view-analytics" class="hidden grid-cols-1 md:grid-cols-2 gap-6">
            <div class="md:col-span-2 grid grid-cols-2 md:grid-cols-4 gap-4">
                <div class="glass rounded-xl p-4"><div class="text-xs text-zinc-400 uppercase tracking-wide">Page Views</div><div class="text-3xl font-extrabold text-red-400 mt-1" id="cf-pv">—</div></div>
                <div class="glass rounded-xl p-4"><div class="text-xs text-zinc-400 uppercase tracking-wide">Visitas Únicas</div><div class="text-3xl font-extrabold text-orange-400 mt-1" id="cf-vt">—</div></div>
                <div class="glass rounded-xl p-4"><div class="text-xs text-zinc-400 uppercase tracking-wide">Top País</div><div class="text-lg font-bold text-zinc-100 mt-1 truncate" id="cf-pais">—</div></div>
                <div class="glass rounded-xl p-4"><div class="text-xs text-zinc-400 uppercase tracking-wide">Top Página</div><div class="text-lg font-bold text-zinc-100 mt-1 truncate" id="cf-pag">—</div></div>
            </div>
            <div class="glass rounded-2xl p-4"><h3 class="font-bold text-sm mb-3 text-red-400"><i class="fa-solid fa-fire mr-2"></i>Top Páginas (7d)</h3><div id="cf-top-paginas" class="space-y-2 text-sm"><div class="text-xs text-zinc-500 italic">Cargando...</div></div></div>
            <div class="glass rounded-2xl p-4"><h3 class="font-bold text-sm mb-3 text-orange-400"><i class="fa-solid fa-globe mr-2"></i>Top Países (7d)</h3><div id="cf-top-paises" class="space-y-2 text-sm"><div class="text-xs text-zinc-500 italic">Cargando...</div></div></div>
            <div class="md:col-span-2 text-xs text-zinc-500 text-center py-2"><i class="fa-solid fa-circle-info mr-1"></i>Datos de <strong>Cloudflare Web Analytics (RUM)</strong> · Sin cookies · Excluye bots</div>
        </div>
        <div id="view-ab" class="hidden glass rounded-2xl p-8 text-center"><div class="text-4xl mb-2">🧪</div><h3 class="font-bold text-zinc-200">A/B Testing</h3><p class="text-xs text-zinc-500 mt-1">En construcción</p></div>
        <div id="view-calendario" class="hidden glass rounded-2xl p-8 text-center"><div class="text-4xl mb-2">📅</div><h3 class="font-bold text-zinc-200">Calendario editorial</h3><p class="text-xs text-zinc-500 mt-1">En construcción</p></div>
        <div id="view-agentes" class="hidden glass rounded-2xl p-8 text-center"><div class="text-4xl mb-2">🤖</div><h3 class="font-bold text-zinc-200">Agentes IA</h3><p class="text-xs text-zinc-500 mt-1">En construcción</p></div>
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
            ['preview', 'distribucion', 'monetizacion', 'live', 'analytics', 'ab', 'calendario', 'agentes'].forEach(t => {
                document.getElementById('view-' + t).classList.toggle('hidden', t !== v);
                const tab = document.getElementById('tab-' + t);
                if (tab) tab.className = t === v ? "tab-active text-sm font-semibold pb-2 px-2 whitespace-nowrap" : "text-zinc-400 hover:text-white text-sm font-semibold pb-2 px-2 whitespace-nowrap";
            });
            if (v === 'monetizacion') document.getElementById('view-monetizacion').classList.add('grid');
            if (v === 'live') document.getElementById('view-live').classList.add('grid');
            if (v === 'analytics') { document.getElementById('view-analytics').classList.add('grid'); cargarCloudflareStats(); }
            if (v === 'ab') document.getElementById('view-ab').classList.add('grid');
            if (v === 'calendario') document.getElementById('view-calendario').classList.add('grid');
            if (v === 'agentes') document.getElementById('view-agentes').classList.add('grid');
            if (v === 'distribucion') { document.getElementById('view-distribucion').classList.add('grid'); cargarPublicar(); }
            if (v === 'cms') { document.getElementById('view-cms').classList.add('grid'); cmsCargarArbol(); }
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

        function cargarCloudflareStats() {
            fetch('/api/cloudflare/stats').then(r => r.json()).then(d => {
                const pv = d.page_views || 0;
                const vt = d.visitas || 0;
                const tp = (d.top_paginas && d.top_paginas.length) ? d.top_paginas[0] : null;
                const tc = (d.top_paises && d.top_paises.length) ? d.top_paises[0] : null;
                document.getElementById('cf-pv').textContent = pv.toLocaleString('es-ES');
                document.getElementById('cf-vt').textContent = vt.toLocaleString('es-ES');
                document.getElementById('cf-pais').textContent = tc ? tc[0] : '—';
                document.getElementById('cf-pag').textContent = tp ? (tp[0].replace(/\\/$/, '').split('/').pop() || '/') : '—';
                const maxP = d.top_paginas && d.top_paginas.length ? d.top_paginas[0][1] : 1;
                const paginasEl = document.getElementById('cf-top-paginas');
                if (!d.top_paginas || !d.top_paginas.length) { paginasEl.innerHTML = '<div class="text-xs text-zinc-500 italic">Sin datos aún</div>'; }
                else {
                    paginasEl.innerHTML = d.top_paginas.map(p => {
                        const pct = Math.round((p[1] / maxP) * 100);
                        const slug = p[0].replace(/\\/$/, '').split('/').pop() || '/';
                        return '<div class="mb-2"><div class="flex justify-between mb-1"><span class="mono text-xs text-zinc-300 truncate">' + slug + '</span><span class="text-xs text-zinc-500">' + p[1] + '</span></div><div class="h-1.5 bg-zinc-800 rounded-full overflow-hidden"><div class="h-full bg-gradient-to-r from-red-500 to-orange-400" style="width:' + pct + '%"></div></div></div>';
                    }).join('');
                }
                const maxC = d.top_paises && d.top_paises.length ? d.top_paises[0][1] : 1;
                const paisesEl = document.getElementById('cf-top-paises');
                if (!d.top_paises || !d.top_paises.length) { paisesEl.innerHTML = '<div class="text-xs text-zinc-500 italic">Sin datos aún</div>'; }
                else {
                    paisesEl.innerHTML = d.top_paises.map(c => {
                        const pct = Math.round((c[1] / maxC) * 100);
                        return '<div class="mb-2"><div class="flex justify-between mb-1"><span class="text-xs text-zinc-300">' + c[0] + '</span><span class="text-xs text-zinc-500">' + c[1] + '</span></div><div class="h-1.5 bg-zinc-800 rounded-full overflow-hidden"><div class="h-full bg-gradient-to-r from-orange-500 to-yellow-400" style="width:' + pct + '%"></div></div></div>';
                    }).join('');
                }
            }).catch(e => console.warn('CF:', e));
        }

        // ═══ PUBLICAR ═══
        let _publicarData = null;
        function cargarPublicar() {
            if (_publicarData) return;
            fetch('/api/encuadre/publicar/' + fechaActual)
                .then(r => r.json())
                .then(d => {
                    _publicarData = d;
                    const root = document.getElementById('publicar-content');
                    let html = '';
                    // LARGO
                    html += `<div class="glass rounded-xl p-4 border-l-4 border-l-red-500">
                        <div class="flex justify-between items-start">
                            <div><h3 class="font-bold text-red-400">🎬 Vídeo Largo</h3><p class="text-xs text-zinc-400 mt-1">${d.largo.palabras} palabras · Score: ${d.largo.viralidad}/10</p></div>
                            <div class="flex gap-2"><button onclick="verGuion('largo')" class="bg-zinc-800 px-3 py-1 rounded text-xs"><i class="fa-solid fa-eye mr-1"></i>Guion</button></div>
                        </div>
                        <div class="mt-3 bg-zinc-900/50 p-2 rounded text-xs text-zinc-300"><strong>SEO:</strong> ${d.largo.seo?.titulo || '—'}</div>
                    </div>`;
                    // SHORTS
                    d.shorts.forEach(s => {
                        html += `<div class="glass rounded-xl p-4 border-l-4 border-l-orange-500">
                            <div class="flex justify-between items-start">
                                <div><h3 class="font-bold text-orange-400">📱 Short ${s.num} · ${s.tipo}</h3><p class="text-xs text-zinc-400 mt-1">"${s.hook}"</p></div>
                                <div class="flex gap-2">
                                    <button onclick="verGuion(${s.num})" class="bg-zinc-800 px-3 py-1 rounded text-xs"><i class="fa-solid fa-eye mr-1"></i>Guion</button>
                                    <button onclick="abrirApp('tiktok', '${(s.guion||'').replace(/'/g, "\\'")}')" class="bg-black px-3 py-1 rounded text-xs border border-zinc-700">TikTok</button>
                                </div>
                            </div>
                            <div class="mt-3 bg-zinc-900/50 p-2 rounded text-xs text-zinc-300"><strong>SEO:</strong> ${s.seo?.titulo || '—'} · ${s.seo?.hashtags || ''}</div>
                        </div>`;
                    });
                    root.innerHTML = html;
                }).catch(e => document.getElementById('publicar-content').innerHTML = 'Error: ' + e.message);
        }

        function verGuion(id) {
            if (!_publicarData) return;
            let txt = "";
            if (id === 'largo') txt = _publicarData.largo.guion;
            else txt = _publicarData.shorts[id-1]?.guion || "Sin guion";
            alert("=== GUION ===\n\n" + txt);
        }
        
        function copiarTodoPublicar() { mostrarToast('Copiando todo...', 'bg-green-600'); }
        function subirTodoYouTube() { mostrarToast('Subiendo todo a YouTube... (en desarrollo)', 'bg-red-600'); }

        function abrirApp(red, texto) {
            fetch('/api/encuadre/abrir_app', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({red, texto})})
                .then(r=>r.json()).then(d => mostrarToast('🚀 Abriendo ' + red, 'bg-blue-600'));
        }

        // ═══ CMS (DISEÑO WEB) ═══
        function cmsCargarArbol() {
            fetch('/api/cms/files').then(r=>r.json()).then(d => {
                const root = document.getElementById('cms-tree');
                function render(items, depth=0) {
                    return items.map(i => {
                        if (i.type === 'dir') return `<div class="text-zinc-500 font-bold text-xs mt-2 mb-1">📁 ${i.name}</div>` + render(i.children || [], depth+1);
                        return `<div onclick="cmsAbrirArchivo('${i.path}')" class="cursor-pointer text-zinc-300 hover:text-white hover:bg-zinc-800 px-2 py-1 rounded truncate" title="${i.path}">📄 ${i.name}</div>`;
                    }).join('');
                }
                root.innerHTML = render(d.tree);
            });
        }

        let _cmsCurrentPath = "";
        function cmsAbrirArchivo(path) {
            _cmsCurrentPath = path;
            document.getElementById('cms-filename').textContent = path;
            const ed = document.getElementById('cms-editor');
            ed.disabled = true; ed.value = "Cargando...";
            fetch('/api/cms/read', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({path})})
                .then(r=>r.json()).then(d => {
                    if (d.type === 'binary') { ed.value = "[Archivo binario: " + d.url + "]"; }
                    else { ed.value = d.content; ed.disabled = false; }
                });
        }

        function cmsGuardar() {
            if (!_cmsCurrentPath) return;
            const content = document.getElementById('cms-editor').value;
            fetch('/api/cms/save', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({path: _cmsCurrentPath, content})})
                .then(r=>r.json()).then(d => { if(d.ok) mostrarToast('✅ Guardado', 'bg-green-600'); else mostrarToast('Error: '+d.error, 'bg-red-600'); });
        }

        function cmsNuevoArchivo() {
            const name = prompt("Nombre del nuevo archivo (ej: analisis/nuevo-post.md):");
            if(name) cmsAbrirArchivo("docs/" + name);
        }

        function cmsBuild() {
            mostrarToast('🚀 Compilando y desplegando...', 'bg-blue-600');
            fetch('/api/cms/build', {method:'POST'}).then(r=>r.json()).then(d => {
                if(d.ok) mostrarToast('✅ Build & Push OK', 'bg-green-600');
                else mostrarToast('❌ ' + d.error, 'bg-red-600');
            });
        }

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


# === PUBLICAR (datos unificados para frontend) ===
@encuadre_bp.route("/api/encuadre/publicar/<fecha>")
def api_publicar_datos(fecha):
    OUT = ROOT / "output" / "encuadre"
    result = {"fecha": fecha, "largo": {}, "shorts": [], "posts": {}, "dossier": {}}
    prod = {}
    p = OUT / f"produccion_{fecha}.json"
    if p.exists():
        try: prod = json.loads(p.read_text())
        except: pass
    seo = {}
    p = OUT / f"seo_{fecha}.json"
    if p.exists():
        try: seo = json.loads(p.read_text())
        except: pass
    redes = {}
    p = OUT / f"redes_{fecha}.json"
    if p.exists():
        try: redes = json.loads(p.read_text())
        except: pass
    dossier = {}
    p = OUT / f"dossier_{fecha}_enriquecido.json"
    if p.exists():
        try: dossier = json.loads(p.read_text())
        except: pass
    result["largo"] = {
        "guion": prod.get("texto_voz_largo", ""),
        "palabras": prod.get("palabras_totales", 0),
        "viralidad": (prod.get("viralidad") or {}).get("score", 0),
        "escenas": prod.get("escenas", []),
        "seo": seo.get("largo", {}),
        "articulo_html": prod.get("articulo_html", ""),
    }
    sp = prod.get("shorts_finales", []) or []
    ss = seo.get("shorts", []) or []
    sr = redes.get("shorts", []) or []
    for i, s in enumerate(sp):
        ritem = sr[i] if i < len(sr) else {}
        result["shorts"].append({
            "num": i + 1,
            "tipo": s.get("tipo", ""),
            "guion": s.get("guion", ""),
            "hook": s.get("hook", ""),
            "archivo": s.get("archivo", ""),
            "seo": ss[i] if i < len(ss) else {},
            "redes": {k: v for k, v in ritem.items() if k != "id"},
        })
    result["posts"] = {
        "largo_html": prod.get("articulo_html", ""),
        "dossier": prod.get("dossier", {}),
        "dossier_enriquecido": dossier,
    }
    result["dossier"] = prod.get("dossier", {})
    return jsonify(result)


# === ABRIR APP (Android intent + clipboard) ===
@encuadre_bp.route("/api/encuadre/abrir_app", methods=["POST"])
def api_abrir_app():
    data = request.get_json() or {}
    red = (data.get("red") or "").lower()
    texto = data.get("texto", "")
    clip = False
    if texto:
        try:
            subprocess.run(["termux-clipboard-set", texto], timeout=5, check=False)
            clip = True
        except Exception:
            pass
    links = {
        "tiktok": "snssdk1128://",
        "instagram": "instagram://app",
        "threads": "barcelona://",
        "x": "twitter://",
        "youtube": "vnd.youtube://",
        "youtube_studio": "https://studio.youtube.com/",
        "blogger": "https://www.blogger.com/",
    }
    url = links.get(red, "https://www." + red + ".com/")
    try:
        subprocess.run(["termux-open", url], timeout=5, check=False)
        return jsonify({"ok": True, "red": red, "clipboard": clip, "url": url})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# === PIPELINE OPTIONS ===
@encuadre_bp.route("/api/encuadre/pipeline_options")
def api_pipeline_options():
    nichos = {}
    p = ROOT / "config" / "nichos.json"
    if p.exists():
        try: nichos = json.loads(p.read_text())
        except: pass
    return jsonify({
        "nichos": list(nichos.keys()) if isinstance(nichos, dict) else [],
        "formatos": [
            {"id": "largo", "label": "Video largo 16:9", "icon": "🎬", "desc": "10-15 min con voz + imagenes + musica"},
            {"id": "shorts", "label": "Shorts 9:16", "icon": "📱", "desc": "1-4 shorts verticales con subtitulos"},
            {"id": "posts", "label": "Posts web", "icon": "📝", "desc": "Largo + dossier + mediano en elencuadre.pages.dev"},
            {"id": "podcast", "label": "Podcast MP3", "icon": "🎧", "desc": "Audio ~5 min para Spotify"},
        ],
        "num_shorts": [1, 2, 3, 4],
        "fuentes": [
            {"id": "auto", "label": "Automatico (dossier del dia)"},
            {"id": "manual", "label": "Tema manual (yo escribo)"},
        ],
    })


# === TOPICOS (trending del dia) ===
@encuadre_bp.route("/api/encuadre/topicos")
def api_topicos():
    OUT = ROOT / "output" / "encuadre"
    ds = sorted(OUT.glob("dossier_*_enriquecido.json"), reverse=True)
    if not ds:
        return jsonify({"fecha": None, "topicos": []})
    try:
        d = json.loads(ds[0].read_text())
        fecha = ds[0].stem.replace("dossier_", "").replace("_enriquecido", "")
        top3 = d.get("top3", {})
        topicos = []
        for k, v in top3.items():
            if isinstance(v, str): v = {"titulo": v}
            if isinstance(v, dict):
                topicos.append({
                    "id": k,
                    "titulo": v.get("titular") or v.get("titulo") or v.get("headline") or v.get("title") or "",
                    "resumen": (v.get("resumen") or v.get("summary") or "")[:200],
                    "medio": v.get("medio") or v.get("fuente") or "",
                })
        return jsonify({"fecha": fecha, "topicos": topicos})
    except Exception as e:
        return jsonify({"error": str(e), "topicos": []})



# === CMS (Diseñador Web) ===
import os
WEB_DIR = ROOT / "web"

def _safe_path(rel_path):
    """Evita path traversal. Solo permite rutas dentro de web/."""
    p = (WEB_DIR / rel_path).resolve()
    if not str(p).startswith(str(WEB_DIR.resolve())):
        raise ValueError("Ruta no permitida")
    return p

@encuadre_bp.route("/api/cms/files")
def cms_files():
    """Devuelve el arbol de archivos de web/ (posts, media, config, css)."""
    def walk(dir_path):
        rel = str(dir_path.relative_to(WEB_DIR))
        if rel == ".": rel = ""
        items = []
        try:
            for entry in sorted(dir_path.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower())):
                if entry.name.startswith(".") or entry.name in ("site", "media"): 
                    continue
                entry_rel = str(entry.relative_to(WEB_DIR))
                if entry.is_dir():
                    items.append({"name": entry.name, "type": "dir", "path": entry_rel, "children": walk(entry)})
                else:
                    if entry.name in ("mkdocs.yml",) or entry.suffix in (".md", ".css", ".yml", ".html"):
                        items.append({"name": entry.name, "type": "file", "path": entry_rel, "size": entry.stat().st_size})
        except Exception: pass
        return items

    # Incluir media/imagenes como carpeta virtual
    media_dir = WEB_DIR / "media" / "imagenes"
    media_items = []
    if media_dir.exists():
        for f in sorted(media_dir.glob("*"), reverse=True)[:50]:
            if f.suffix in (".png", ".jpg", ".jpeg"):
                media_items.append({"name": f.name, "type": "file", "path": str(f.relative_to(WEB_DIR)), "size": f.stat().st_size})
    
    tree = walk(WEB_DIR / "docs")
    tree.insert(0, {"name": "mkdocs.yml", "type": "file", "path": "mkdocs.yml", "size": (WEB_DIR/"mkdocs.yml").stat().st_size if (WEB_DIR/"mkdocs.yml").exists() else 0})
    tree.insert(1, {"name": "imagenes_media", "type": "dir", "path": "media/imagenes", "children": media_items})
    return jsonify({"tree": tree})

@encuadre_bp.route("/api/cms/read", methods=["POST"])
def cms_read():
    data = request.get_json() or {}
    rel = data.get("path", "")
    try:
        p = _safe_path(rel)
        if not p.exists(): return jsonify({"error": "No existe"}), 404
        if p.suffix in (".png", ".jpg", ".jpeg", ".mp3"):
            return jsonify({"type": "binary", "url": f"/{rel}"})
        return jsonify({"type": "text", "content": p.read_text(encoding="utf-8"), "path": rel})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@encuadre_bp.route("/api/cms/save", methods=["POST"])
def cms_save():
    data = request.get_json() or {}
    rel = data.get("path", "")
    content = data.get("content", "")
    try:
        p = _safe_path(rel)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return jsonify({"ok": True, "path": rel})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@encuadre_bp.route("/api/cms/delete", methods=["POST"])
def cms_delete():
    data = request.get_json() or {}
    rel = data.get("path", "")
    try:
        p = _safe_path(rel)
        if p.is_file(): p.unlink()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@encuadre_bp.route("/api/cms/build", methods=["POST"])
def cms_build():
    import subprocess
    try:
        r1 = subprocess.run(["mkdocs", "build"], cwd=str(WEB_DIR), capture_output=True, text=True, timeout=120)
        if r1.returncode != 0: return jsonify({"error": "Build fallo: " + r1.stderr[-200:]}), 500
        subprocess.run(["git", "add", "web/"], cwd=str(ROOT), timeout=30, check=False)
        subprocess.run(["git", "commit", "-m", "cms: cambios desde dashboard"], cwd=str(ROOT), timeout=30, check=False)
        r2 = subprocess.run(["git", "push", "origin", "main"], cwd=str(ROOT), capture_output=True, text=True, timeout=60)
        return jsonify({"ok": True, "msg": "Build & Push OK"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@encuadre_bp.route("/output/encuadre/<path:filename>")
def video_encuadre(filename):
    return send_from_directory(ROOT / "output" / "encuadre", filename)
