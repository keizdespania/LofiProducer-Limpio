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
            <button onclick="cambiarVista('crear')" id="tab-crear" class="text-zinc-400 hover:text-white text-sm font-semibold pb-2 px-2 whitespace-nowrap"><i class="fa-solid fa-wand-magic-sparkles mr-2"></i>Crear Custom</button>
            <button onclick="cambiarVista('cms')" id="tab-cms" class="text-zinc-400 hover:text-white text-sm font-semibold pb-2 px-2 whitespace-nowrap"><i class="fa-solid fa-pen-ruler mr-2"></i>Diseño Web (CMS)</button>
        </div>

        <!-- VISTA PREVIEW -->
        <div id="view-preview" class="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <!-- COLUMNA IZQ: VÍDEO + SHORTS + PODCAST -->
            <div class="lg:col-span-8 space-y-4">
                <!-- Vídeo largo -->
                <div class="glass rounded-2xl p-4">
                    <div class="flex justify-between items-center mb-3">
                        <h3 class="font-bold text-sm text-red-400">🎬 Vídeo Largo</h3>
                        <div class="flex gap-2">
                            <button onclick="cambiarVideo('largo')" id="btn-largo" class="tab-active text-sm font-semibold pb-1 px-1">Largo</button>
                        </div>
                    </div>
                    <div id="videoWrapper" class="video-container">
                        <video id="mainPlayer" controls></video>
                    </div>
                    <div class="mt-3 flex gap-2">
                        <button onclick="compartir('youtube')" class="flex-1 bg-red-600 py-2 rounded-lg font-semibold text-sm"><i class="fa-brands fa-youtube mr-2"></i>Subir a YouTube</button>
                        <button onclick="abrirDrawer('articulo')" class="flex-1 bg-zinc-800 py-2 rounded-lg font-semibold text-sm"><i class="fa-solid fa-newspaper mr-2"></i>Artículo Web</button>
                    </div>
                </div>

                <!-- Shorts (galería) -->
                <div class="glass rounded-2xl p-4">
                    <h3 class="font-bold text-sm text-orange-400 mb-3">📱 Shorts (4)</h3>
                    <div id="shorts-gallery" class="grid grid-cols-2 md:grid-cols-4 gap-3">
                        <div class="text-xs text-zinc-500 italic">Cargando...</div>
                    </div>
                </div>

                <!-- Podcast -->
                <div class="glass rounded-2xl p-4">
                    <h3 class="font-bold text-sm text-purple-400 mb-3">🎧 Podcast del día</h3>
                    <div id="podcast-player" class="text-xs text-zinc-500 italic">Cargando...</div>
                </div>
            </div>

            <!-- COLUMNA DER: DOSSIER -->
            <div class="lg:col-span-4 space-y-4">
                <div class="glass rounded-2xl p-4">
                    <h3 class="font-bold text-sm mb-2 text-red-400">📋 Dossier de Hoy</h3>
                    <div id="dossierResumen" class="text-xs text-zinc-300 space-y-2"></div>
                </div>
                <div class="glass rounded-2xl p-4">
                    <h3 class="font-bold text-sm mb-2 text-orange-400">🌐 Enlaces públicos</h3>
                    <div id="enlaces-web" class="space-y-1 text-xs"></div>
                </div>
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
        
        <!-- VISTA CREAR CUSTOM -->
        <div id="view-crear" class="hidden grid-cols-1 lg:grid-cols-2 gap-6">
            <div class="glass rounded-2xl p-6">
                <h2 class="text-xl font-bold text-red-500 mb-4"><i class="fa-solid fa-wand-magic-sparkles mr-2"></i>Crear Contenido a la Carta</h2>
                
                <label class="text-xs text-zinc-400 uppercase tracking-wide">Nicho</label>
                <select id="crear-nicho" class="field-box mb-3"></select>

                <label class="text-xs text-zinc-400 uppercase tracking-wide">Formato (uno o varios)</label>
                <div class="flex gap-2 mb-3 flex-wrap" id="crear-formatos"></div>

                <label class="text-xs text-zinc-400 uppercase tracking-wide">Nº Shorts</label>
                <select id="crear-num" class="field-box mb-3"><option value="1">1</option><option value="2">2</option><option value="3">3</option><option value="4" selected>4</option></select>

                <label class="text-xs text-zinc-400 uppercase tracking-wide">Tema</label>
                <select id="crear-tema-tipo" class="field-box mb-2" onchange="crearToggleTema()">
                    <option value="auto">🤖 Automático (dossier del día)</option>
                    <option value="topico">📰 Elegir del top de hoy</option>
                    <option value="manual">✍️ Escribir mi tema</option>
                </select>
                <select id="crear-topico" class="field-box mb-2 hidden"></select>
                <input id="crear-manual" type="text" class="field-box mb-3 hidden" placeholder="Ej: La manipulación del caso Urda">

                <button onclick="crearLanzar()" class="w-full bg-gradient-to-r from-red-600 to-orange-500 py-3 rounded-lg font-bold text-sm hover:opacity-90 transition"><i class="fa-solid fa-rocket mr-2"></i>Lanzar Pipeline Custom</button>
            </div>

            <div class="glass rounded-2xl p-6">
                <h3 class="font-bold text-sm text-orange-400 mb-3"><i class="fa-solid fa-chart-line mr-2"></i>SEO Optimizer · Top 1</h3>
                <div id="crear-seo" class="space-y-3 text-sm"><div class="text-zinc-500 italic">Cargando análisis...</div></div>
            </div>

            <div class="lg:col-span-2 glass rounded-2xl p-6">
                <h3 class="font-bold text-sm text-zinc-400 mb-3"><i class="fa-solid fa-terminal mr-2"></i>Logs del pipeline custom</h3>
                <pre id="crear-logs" class="mono text-xs text-zinc-400 bg-black/50 rounded p-3 overflow-y-auto" style="max-height:300px">Esperando...</pre>
            </div>
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
            ['preview', 'distribucion', 'monetizacion', 'live', 'analytics', 'ab', 'calendario', 'agentes', 'crear', 'cms'].forEach(t => {
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
            if (v === 'crear') { document.getElementById('view-crear').classList.add('grid'); cargarCrear(); }
            if (v === 'ab') { document.getElementById('view-ab').classList.add('grid'); cargarAB(); }
            if (v === 'calendario') { document.getElementById('view-calendario').classList.add('grid'); calendarioCargar(); }
            if (v === 'agentes') { document.getElementById('view-agentes').classList.add('grid'); agentesCargar(); }
            if (v === 'cms') { document.getElementById('view-cms').classList.add('grid'); cmsCargarArbol(); }
        }

        function cambiarVideo(tipo) {
            const w = document.getElementById('videoWrapper');
            const p = document.getElementById('mainPlayer');
            if (tipo === 'largo') { w.classList.remove('vertical'); p.src = `/output/encuadre/video_largo_${fechaActual}.mp4`; }
            else { w.classList.add('vertical'); p.src = `/output/encuadre/short_1_${fechaActual}.mp4`; }
        }
        function reproducirShort(n) {
            const p = document.getElementById('mainPlayer');
            const w = document.getElementById('videoWrapper');
            w.classList.add('vertical');
            p.src = `/output/encuadre/short_${n}_${fechaActual}.mp4`;
            p.play();
            w.scrollIntoView({behavior:'smooth', block:'center'});
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


        // ═══ CREAR CUSTOM ═══
        let _crearSeo = null;
        function cargarCrear() {
            // Cargar nichos, topicos y SEO en paralelo
            Promise.all([
                fetch('/api/encuadre/pipeline_options').then(r=>r.json()),
                fetch('/api/encuadre/topicos').then(r=>r.json()),
                fetch('/api/encuadre/seo_top').then(r=>r.json()).catch(()=>({}))
            ]).then(([opt, top, seo]) => {
                // Nichos
                const sel = document.getElementById('crear-nicho');
                sel.innerHTML = (opt.nichos || []).map(n => `<option value="${n}">${n}</option>`).join('');
                // Formatos
                const fmt = document.getElementById('crear-formatos');
                fmt.innerHTML = (opt.formatos || []).map(f => `
                    <label class="flex items-center gap-1 bg-zinc-800 px-3 py-2 rounded text-xs cursor-pointer">
                        <input type="checkbox" value="${f.id}" ${f.id==='largo'?'checked':''}> ${f.icon} ${f.label}
                    </label>`).join('');
                // Tópicos
                const ts = document.getElementById('crear-topico');
                ts.innerHTML = (top.topicos || []).map((tp,i) => `<option value="${tp.titulo}">${tp.titulo.substring(0,60)}</option>`).join('');
                if (!top.topicos || top.topicos.length === 0) ts.innerHTML = '<option value="">(sin tópicos hoy)</option>';
                // SEO
                _crearSeo = seo;
                renderSeo();
            });
        }

        function crearToggleTema() {
            const v = document.getElementById('crear-tema-tipo').value;
            document.getElementById('crear-topico').classList.toggle('hidden', v !== 'topico');
            document.getElementById('crear-manual').classList.toggle('hidden', v !== 'manual');
        }

        function renderSeo() {
            const el = document.getElementById('crear-seo');
            if (!_crearSeo || !_crearSeo.keywords) {
                el.innerHTML = '<div class="text-xs text-zinc-500 italic">Sin datos SEO aún</div>';
                return;
            }
            el.innerHTML = `
                <div><span class="text-zinc-400 text-xs">Keywords top:</span><div class="text-zinc-200 font-mono text-xs mt-1">${(_crearSeo.keywords||[]).join(' · ')}</div></div>
                <div><span class="text-zinc-400 text-xs">Mejor hora publicar:</span><div class="text-green-400 font-bold text-lg">${_crearSeo.mejor_hora||'20:00'}</div></div>
                <div><span class="text-zinc-400 text-xs">CTR estimado:</span><div class="text-orange-400 font-bold">${_crearSeo.ctr_estimado||'—'}</div></div>
                <div class="text-xs text-zinc-500 italic border-t border-zinc-800 pt-2 mt-2">${_crearSeo.nota||''}</div>
            `;
        }

        function crearLanzar() {
            const nicho = document.getElementById('crear-nicho').value;
            const formatos = Array.from(document.querySelectorAll('#crear-formatos input:checked')).map(i=>i.value);
            const num_shorts = parseInt(document.getElementById('crear-num').value);
            const temaTipo = document.getElementById('crear-tema-tipo').value;
            let tema = '';
            if (temaTipo === 'topico') tema = document.getElementById('crear-topico').value;
            else if (temaTipo === 'manual') tema = document.getElementById('crear-manual').value;
            if (!formatos.length) return mostrarToast('Elige al menos un formato', 'bg-red-600');
            if (temaTipo === 'manual' && !tema) return mostrarToast('Escribe tu tema', 'bg-red-600');
            
            mostrarToast('🚀 Lanzando pipeline custom...', 'bg-orange-600');
            document.getElementById('crear-logs').textContent = '>>> Iniciando...';
            fetch('/api/encuadre/crear_custom', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({nicho, formatos, num_shorts, tema_tipo: temaTipo, tema})})
                .then(r=>r.json()).then(d => {
                    if (d.ok) {
                        mostrarToast('✅ Pipeline lanzado', 'bg-green-600');
                        iniciarPollingCrear();
                    } else mostrarToast('❌ ' + (d.error||d.msg), 'bg-red-600');
                });
        }

        let _crearPolling = null;
        function iniciarPollingCrear() {
            if (_crearPolling) clearInterval(_crearPolling);
            _crearPolling = setInterval(() => {
                fetch('/api/encuadre/pipeline_status').then(r=>r.json()).then(d => {
                    document.getElementById('crear-logs').textContent = d.logs || 'Sin salida';
                    if (!d.running) { clearInterval(_crearPolling); _crearPolling = null; mostrarToast('✅ Pipeline custom terminado', 'bg-green-600'); }
                });
            }, 3000);
        }


        // ═══ A/B TITULOS ═══
        function cargarAB() {
            fetch('/api/encuadre/ab_titulos/' + fechaActual).then(r=>r.json()).then(d => {
                document.getElementById('ab-actual').innerHTML = '<div class="mono">' + (d.actual||'—') + '</div>';
                document.getElementById('ab-alt0').textContent = (d.alternativas && d.alternativas[0]) || '—';
                document.getElementById('ab-alt1').textContent = (d.alternativas && d.alternativas[1]) || '—';
                document.getElementById('ab-nota').textContent = d.nota || '';
            });
        }

        // ═══ CALENDARIO ═══
        function calendarioCargar() {
            fetch('/api/encuadre/calendario').then(r=>r.json()).then(d => {
                const el = document.getElementById('cal-lista');
                if (!d.items || !d.items.length) { el.innerHTML = '<div class="text-xs text-zinc-500 italic">No hay publicaciones programadas. Pulsa "Programar HOY" para encolar el vídeo del día.</div>'; return; }
                el.innerHTML = d.items.map(it => {
                    const estado = it.estado || 'pendiente';
                    const color = estado === 'publicado' ? 'green' : estado === 'pendiente' ? 'yellow' : 'zinc';
                    return `<div class="flex justify-between items-center bg-zinc-900/50 rounded p-2 text-xs">
                        <div class="flex-1 min-w-0">
                            <div class="font-semibold truncate">${it.titulo || '(sin titulo)'}</div>
                            <div class="text-zinc-500 text-[10px]">${it.publish_at || ''} · ${it.video_path ? it.video_path.split('/').pop() : ''}</div>
                        </div>
                        <span class="badge bg-${color}-600/20 text-${color}-400 px-2 py-0.5 rounded text-[10px]">${estado}</span>
                    </div>`;
                }).join('');
            });
        }
        function calendarioProgramarHoy() {
            if (!confirm('¿Programar el vídeo largo de hoy para publicar en +4h?')) return;
            fetch('/api/encuadre/programar_hoy', {method:'POST'}).then(r=>r.json()).then(d => {
                if (d.ok) { mostrarToast('✅ Programado: ' + d.titulo, 'bg-green-600'); calendarioCargar(); }
                else mostrarToast('❌ ' + (d.error||'error'), 'bg-red-600');
            });
        }

        // ═══ AGENTES ═══
        function agentesCargar() {
            fetch('/api/encuadre/agentes').then(r=>r.json()).then(d => {
                const el = document.getElementById('agentes-grid');
                if (!d.agentes || !d.agentes.length) { el.innerHTML = '<div class="text-xs text-zinc-500 italic">No hay agentes definidos</div>'; return; }
                el.innerHTML = d.agentes.map(a => `
                    <div class="glass rounded-xl p-3">
                        <div class="text-sm font-bold text-red-400 mb-1">${a.label}</div>
                        <div class="text-[10px] text-zinc-500 line-clamp-2">${a.desc || '(sin descripcion)'}</div>
                    </div>
                `).join('');
            });
        }


        // ═══ DIOS FAB ═══
        function diosToggle() {
            const p = document.getElementById('dios-panel');
            p.style.display = p.style.display === 'none' ? 'flex' : 'none';
        }
        function diosEnviar() {
            const inp = document.getElementById('dios-input');
            const q = inp.value.trim();
            if (!q) return;
            inp.value = '';
            diosPush('👤 ' + q, '#a1a1aa');
            diosPush('⏳ Pensando...', '#f77f00');
            fetch('/api/encuadre/dios_ask', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({pregunta:q, fecha: fechaActual})})
                .then(r=>r.json()).then(d => {
                    // Quitar el "Pensando..."
                    const chat = document.getElementById('dios-chat');
                    chat.lastChild.remove();
                    if (d.ok) diosPush('🤖 ' + d.respuesta, '#d4d4d8');
                    else diosPush('❌ ' + (d.error || 'Error'), '#ef4444');
                }).catch(e => diosPush('❌ ' + e.message, '#ef4444'));
        }
        function diosPush(txt, color) {
            const chat = document.getElementById('dios-chat');
            const div = document.createElement('div');
            div.style.marginBottom = '8px';
            div.style.color = color;
            div.style.whiteSpace = 'pre-wrap';
            div.textContent = txt;
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }

    </script>

    <!-- DIOS FAB + PANEL -->
    <button id="dios-fab" onclick="diosToggle()" title="Hablar con Dios" style="position:fixed;bottom:24px;right:24px;width:60px;height:60px;border-radius:50%;background:linear-gradient(135deg,#e63946,#f77f00);color:#fff;border:none;font-size:1.6em;z-index:100;cursor:pointer;box-shadow:0 8px 32px rgba(230,57,70,0.5);display:flex;align-items:center;justify-content:center;animation:diosPulse 2.5s ease-in-out infinite;">🤖</button>
    <style>@keyframes diosPulse{0%,100%{box-shadow:0 8px 32px rgba(230,57,70,0.5)}50%{box-shadow:0 8px 32px rgba(230,57,70,0.5),0 0 0 12px rgba(230,57,70,0)}}</style>
    <div id="dios-panel" style="display:none;position:fixed;bottom:96px;right:24px;width:min(420px,90vw);max-height:70vh;background:#18181b;border:1px solid #e63946;border-radius:16px;z-index:101;box-shadow:0 20px 60px rgba(0,0,0,0.6);flex-direction:column;overflow:hidden;">
        <div style="padding:12px 16px;border-bottom:1px solid #3f3f46;display:flex;justify-content:space-between;align-items:center;">
            <strong style="color:#f77f00;">🤖 Dios del Encuadre</strong>
            <button onclick="diosToggle()" style="background:none;border:none;color:#a1a1aa;font-size:1.3em;cursor:pointer;">×</button>
        </div>
        <div id="dios-chat" style="flex:1;overflow-y:auto;padding:12px;font-size:12px;color:#d4d4d8;min-height:120px;max-height:50vh;"></div>
        <div style="padding:10px;border-top:1px solid #3f3f46;display:flex;gap:6px;">
            <input id="dios-input" placeholder="Pregúntale a Dios..." style="flex:1;background:#09090b;border:1px solid #3f3f46;color:#fff;border-radius:6px;padding:8px;font-size:12px;outline:none;" onkeypress="if(event.key==='Enter')diosEnviar()">
            <button onclick="diosEnviar()" style="background:#e63946;border:none;color:#fff;padding:8px 12px;border-radius:6px;cursor:pointer;font-size:12px;font-weight:600;">Enviar</button>
        </div>
    </div>
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


@encuadre_bp.route("/api/encuadre/seo_top")
def api_seo_top():
    import json as _j
    result = {"keywords": [], "mejor_hora": "20:00 UTC", "ctr_estimado": "—", "nota": ""}
    nichos = {}
    p = ROOT / "config" / "nichos.json"
    if p.exists():
        try: nichos = _j.loads(p.read_text())
        except: pass
    for n, v in nichos.items():
        if isinstance(v, dict):
            kws = v.get("keywords_trends") or v.get("queries_youtube") or []
            if isinstance(kws, list): result["keywords"].extend(kws[:5])
    result["keywords"] = list(dict.fromkeys(result["keywords"]))[:10]
    OUT = ROOT / "output" / "encuadre"
    seos = sorted(OUT.glob("seo_*.json"), reverse=True)[:5]
    hrs = []
    for sp in seos:
        try:
            d = _j.loads(sp.read_text())
            largo = d.get("largo", {})
            if largo.get("hora_recomendada"): hrs.append(largo["hora_recomendada"])
        except: pass
    if hrs:
        from collections import Counter
        result["mejor_hora"] = Counter(hrs).most_common(1)[0][0]
    result["ctr_estimado"] = "3.8% (media histórica)"
    result["nota"] = "Basado en keywords del nicho + histórico de publicaciones"
    return jsonify(result)


@encuadre_bp.route("/api/encuadre/crear_custom", methods=["POST"])
def api_crear_custom():
    global _pipeline_process
    import json as _j, datetime
    data = request.get_json() or {}
    nicho = data.get("nicho", "")
    formatos = data.get("formatos", [])
    num_shorts = data.get("num_shorts", 4)
    tema_tipo = data.get("tema_tipo", "auto")
    tema = data.get("tema", "")
    fecha = datetime.date.today().isoformat()
    if not formatos:
        return jsonify({"ok": False, "error": "Sin formatos seleccionados"}), 400
    if _pipeline_process is not None and _pipeline_process.poll() is None:
        return jsonify({"ok": False, "error": "Pipeline ya en ejecución"}), 409
    OUT = ROOT / "output" / "encuadre"
    OUT.mkdir(parents=True, exist_ok=True)
    req = {
        "fecha": fecha, "nicho": nicho, "formatos": formatos,
        "num_shorts": num_shorts, "tema_tipo": tema_tipo, "tema": tema,
        "timestamp": datetime.datetime.now().isoformat()
    }
    (OUT / f"custom_request_{fecha}.json").write_text(_j.dumps(req, indent=2, ensure_ascii=False))
    LOG_FILE_local = ROOT / "data" / "logs" / "pipeline_web.log"
    LOG_FILE_local.parent.mkdir(parents=True, exist_ok=True)
    log_f = open(LOG_FILE_local, "w")
    _pipeline_process = subprocess.Popen(
        ["python3", "scripts/pipeline_encuadre.py"],
        cwd=str(ROOT), stdout=log_f, stderr=subprocess.STDOUT, text=True
    )
    return jsonify({"ok": True, "msg": "Pipeline custom lanzado", "request": req})



@encuadre_bp.route("/api/encuadre/calendario")
def api_calendario():
    import sqlite3
    db = ROOT / "data" / "agent" / "cola_publicacion.db"
    if not db.exists(): return jsonify({"items": [], "hoy_programado": False})
    try:
        con = sqlite3.connect(str(db)); con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT id, video_path, titulo, publish_at, estado, youtube_id, creada FROM publicaciones ORDER BY publish_at ASC")
        items = [dict(r) for r in cur.fetchall()]
        import datetime
        hoy = datetime.date.today().isoformat()
        hoy_prog = any((it.get("publish_at") or "").startswith(hoy) for it in items)
        con.close()
        return jsonify({"items": items, "hoy_programado": hoy_prog, "total": len(items)})
    except Exception as e:
        return jsonify({"error": str(e), "items": []})


@encuadre_bp.route("/api/encuadre/programar_hoy", methods=["POST"])
def api_programar_hoy():
    import sqlite3, datetime, json as _j
    OUT = ROOT / "output" / "encuadre"
    hoy = datetime.date.today().isoformat()
    prod_p = OUT / f"produccion_{hoy}.json"
    seo_p = OUT / f"seo_{hoy}.json"
    if not prod_p.exists(): return jsonify({"error": "No hay produccion de hoy"}), 404
    try: prod = _j.loads(prod_p.read_text())
    except: prod = {}
    try: seo = _j.loads(seo_p.read_text()) if seo_p.exists() else {}
    except: seo = {}
    video = str(OUT / f"video_largo_{hoy}.mp4")
    seo_largo = seo.get("largo", {})
    titulo = seo_largo.get("titulo") or (prod.get("dossier") or {}).get("titular_brutal", "Video largo")
    desc = seo_largo.get("descripcion", "")
    tags = seo_largo.get("tags", [])
    publish_at = (datetime.datetime.now() + datetime.timedelta(hours=4)).isoformat()
    db = ROOT / "data" / "agent" / "cola_publicacion.db"
    db.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db))
    cur = con.cursor()
    cur.execute("""INSERT INTO publicaciones (video_path, titulo, descripcion, tags, publish_at, estado, creada)
                   VALUES (?, ?, ?, ?, ?, 'pendiente', ?)""",
                (video, titulo, desc, _j.dumps(tags, ensure_ascii=False), publish_at, datetime.datetime.now().isoformat()))
    con.commit(); con.close()
    return jsonify({"ok": True, "titulo": titulo, "publish_at": publish_at})


@encuadre_bp.route("/api/encuadre/agentes")
def api_agentes():
    import importlib, sys as _sys, re as _re
    roles = {}
    err = None
    try:
        brain_dir = str(ROOT / "brain")
        if brain_dir not in _sys.path:
            _sys.path.insert(0, brain_dir)
        if "especialistas" in _sys.modules:
            _esp = importlib.reload(_sys.modules["especialistas"])
        else:
            import especialistas as _esp
        roles = getattr(_esp, "ROLES", {}) or {}
    except Exception as e:
        err = "import: " + type(e).__name__ + ": " + str(e)
    if not roles:
        try:
            txt = (ROOT / "brain" / "especialistas.py").read_text()
            m = _re.search(r'^ROLES\s*=\s*\{(.+?)^\}', txt, _re.DOTALL | _re.MULTILINE)
            if m:
                for km in _re.finditer(r'^\s{4,}["\']?([a-z0-9_]+)["\']?\s*:', m.group(1), _re.MULTILINE):
                    roles[km.group(1)] = {}
                err = (err or "") + " | fallback_parse_ok:" + str(len(roles))
        except Exception as e:
            err = (err or "") + " | parse: " + str(e)
    agentes = []
    for nombre, cfg in roles.items():
        desc = ""
        if isinstance(cfg, dict):
            desc = (cfg.get("descripcion") or cfg.get("desc") or (cfg.get("system", "") or "")[:140])
        elif isinstance(cfg, str):
            desc = cfg[:140]
        agentes.append({"id": nombre, "label": nombre.replace("_", " ").title(), "desc": desc})
    out = {"agentes": agentes, "total": len(agentes)}
    if err:
        out["error"] = err
    return jsonify(out)

@encuadre_bp.route("/api/encuadre/ab_titulos/<fecha>")
def api_ab_titulos(fecha):
    import json as _j, random
    OUT = ROOT / "output" / "encuadre"
    seo_p = OUT / f"seo_{fecha}.json"
    actual = ""
    if seo_p.exists():
        try: actual = _j.loads(seo_p.read_text()).get("largo", {}).get("titulo", "")
        except: pass
    # Generar 2 alternativas simples basadas en el actual
    alt = []
    if actual:
        base = actual.replace("—", "-")
        if "|" in base:
            parts = base.split("|")
            alt.append(" | ".join(reversed([p.strip() for p in parts])))
        else:
            alt.append(base.replace(": ", " — "))
        alt.append("🔴 " + base[:150])
        if "?" not in base and "!" not in base:
            alt.append(base[:140] + " ¿Por qué?")
    else:
        alt = ["Titulo A/B pendiente (sin seo del dia)", "Titulo A/B pendiente 2"]
    return jsonify({
        "fecha": fecha,
        "actual": actual or "(no generado)",
        "alternativas": alt[:2],
        "nota": "A/B real: cuando publiques, YouTube Analytics mostrara CTR por titulo en 48h",
    })



@encuadre_bp.route("/api/encuadre/dios_ask", methods=["POST"])
def api_dios_ask():
    import requests as _rq, json as _j, datetime, pathlib as _pl
    data = request.get_json() or {}
    pregunta = (data.get("pregunta") or "").strip()
    fecha = data.get("fecha") or datetime.date.today().isoformat()
    if not pregunta:
        return jsonify({"ok": False, "error": "Falta pregunta"}), 400

    # Construir contexto del día
    OUT = ROOT / "output" / "encuadre"
    prod = {}
    p = OUT / f"produccion_{fecha}.json"
    if p.exists():
        try: prod = _j.loads(p.read_text())
        except: pass
    seo = {}
    p = OUT / f"seo_{fecha}.json"
    if p.exists():
        try: seo = _j.loads(p.read_text())
        except: pass
    dossier = prod.get("dossier", {})
    seo_largo = seo.get("largo", {})
    shorts_lines = []
    for i, s in enumerate((prod.get("shorts_finales") or [])[:4]):
        ss = (seo.get("shorts") or [])
        tit = ss[i].get("titulo", "") if i < len(ss) else ""
        shorts_lines.append(f"  - Short {i+1} ({s.get('tipo','?')}): hook='{(s.get('hook') or '')[:50]}' | seo='{tit[:50]}'")
    ctx = (
        f"Eres el director técnico de El Encuadre. Fecha {fecha}.\n"
        f"Titulo largo: {seo_largo.get('titulo', '(no)')[:150]}\n"
        f"Score viralidad: {(prod.get('viralidad') or {}).get('score', 0)}/10\n"
        f"Titular dossier: {dossier.get('titular_brutal', '(no)')[:150]}\n"
        f"Shorts:\n" + "\n".join(shorts_lines) + "\n\n"
        f"Pregunta del operador (responde breve, accionable, 1-3 frases max): {pregunta}"
    )

    # CAPA 1: llamar a /api/jarvis/chat (dios.py completo)
    try:
        r = _rq.post("http://127.0.0.1:8001/api/jarvis/chat",
                     json={"texto": ctx}, timeout=180)
        if r.status_code == 200:
            j = r.json()
            resp = j.get("respuesta", "").strip()
            if resp and "Fallo Groq" not in resp and "HTTP 401" not in resp and "Sin respuesta" not in resp:
                return jsonify({"ok": True, "respuesta": resp, "capa": 1, "fecha": fecha})
    except Exception as e:
        pass

    # CAPA 2: fallback directo a Groq con cascada
    try:
        env_path = ROOT / ".env"
        keys = []
        models = []
        for line in env_path.read_text().splitlines():
            if line.startswith("GROQ_API_KEY"):
                keys.append(line.split("=", 1)[1].strip().strip('"').strip("'"))
            if line.startswith("GROQ_MODEL"):
                models.append(line.split("=", 1)[1].strip().strip('"').strip("'"))
        if not keys:
            return jsonify({"ok": False, "error": "Sin GROQ_API_KEY en .env"}), 500
        if not models:
            models = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b", "openai/gpt-oss-20b"]
        CHROME = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        last_err = ""
        for idx, k in enumerate(keys):
            modelo = models[idx] if idx < len(models) else "openai/gpt-oss-120b"
            try:
                rr = _rq.post("https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {k}", "Content-Type": "application/json", "User-Agent": CHROME},
                    json={"model": modelo, "messages": [{"role": "user", "content": ctx}], "max_tokens": 800, "temperature": 0.5},
                    timeout=60)
                if rr.status_code == 200:
                    jj = rr.json()
                    msg = jj.get("choices", [{}])[0].get("message", {})
                    content = (msg.get("content") or "").strip()
                    if not content and msg.get("reasoning"):
                        content = "(razonamiento) " + msg["reasoning"][:400]
                    return jsonify({"ok": True, "respuesta": content or "(respuesta vacia)", "capa": 2, "modelo": modelo, "fecha": fecha})
                last_err = f"HTTP {rr.status_code}: {rr.text[:200]}"
            except Exception as e:
                last_err = str(e)
        return jsonify({"ok": False, "error": "Groq fallo en cascada: " + last_err}), 500
    except Exception as e:
        return jsonify({"ok": False, "error": "Fallback: " + str(e)}), 500


def video_encuadre(filename):
    return send_from_directory(ROOT / "output" / "encuadre", filename)
