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
<title>Factory OS · Somos El Encuadre</title>
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
<style>
body{font-family:Inter,system-ui,sans-serif;background:#09090b;color:#f4f4f5;margin:0}
.mono{font-family:'JetBrains Mono',monospace}
.glass{background:rgba(24,24,27,.7);backdrop-filter:blur(12px);border:1px solid rgba(63,63,70,.5)}
.tab-active{border-bottom:2px solid #e63946;color:#e63946}
.video-container{aspect-ratio:16/9;background:#000;border-radius:12px;overflow:hidden;display:flex;justify-content:center}
.video-container.vertical{aspect-ratio:9/16;max-height:60vh;margin:0 auto}
.video-container video{width:100%;height:100%;object-fit:contain}
.field-box{background:#09090b;border:1px solid #3f3f46;border-radius:6px;padding:8px;font-size:12px;width:100%;margin-bottom:8px;font-family:'JetBrains Mono',monospace;color:#fff}
.hidden{display:none!important}
.grid{display:grid}
</style>
</head>
<body>
<header style="position:sticky;top:0;z-index:50;background:rgba(9,9,11,.95);backdrop-filter:blur;border-bottom:1px solid #27272a;padding:10px 12px">
<div style="max-width:1280px;margin:0 auto;display:flex;align-items:center;gap:10px;flex-wrap:wrap">
<div style="display:flex;align-items:center;gap:8px">
<div style="width:32px;height:32px;border-radius:8px;background:linear-gradient(135deg,#dc2626,#ea580c);display:flex;align-items:center;justify-content:center;font-size:14px">🎬</div>
<div><div style="font-weight:800;font-size:13px;color:#fafafa">FACTORY OS</div><div style="font-size:10px;color:#71717a">Somos El Encuadre</div></div>
</div>
<select id="dateSelector" style="background:#18181b;border:1px solid #3f3f46;border-radius:6px;padding:6px 10px;font-size:11px;color:#fff;margin-left:auto"></select>
<div id="initStatus" style="font-size:10px;color:#71717a;font-family:'JetBrains Mono',monospace">init: pendiente</div>
</div>
</header>
<nav style="position:sticky;top:53px;z-index:40;background:rgba(9,9,11,.95);backdrop-filter:blur;border-bottom:1px solid #27272a;overflow-x:auto">
<div style="max-width:1280px;margin:0 auto;display:flex;gap:2px;padding:0 12px">
<button onclick="cambiarVista('preview')" id="tab-preview" class="tab-active" style="font-size:11px;font-weight:600;padding:8px 12px;white-space:nowrap;background:none;border:none;cursor:pointer;color:#e63946">👁 Preview</button>
<button onclick="cambiarVista('publicar')" id="tab-publicar" style="font-size:11px;font-weight:600;padding:8px 12px;white-space:nowrap;background:none;border:none;cursor:pointer;color:#a1a1aa">🚀 Publicar</button>
<button onclick="cambiarVista('crear')" id="tab-crear" style="font-size:11px;font-weight:600;padding:8px 12px;white-space:nowrap;background:none;border:none;cursor:pointer;color:#a1a1aa">✨ Crear</button>
<button onclick="cambiarVista('live')" id="tab-live" style="font-size:11px;font-weight:600;padding:8px 12px;white-space:nowrap;background:none;border:none;cursor:pointer;color:#a1a1aa">🖥 Live</button>
<button onclick="cambiarVista('analytics')" id="tab-analytics" style="font-size:11px;font-weight:600;padding:8px 12px;white-space:nowrap;background:none;border:none;cursor:pointer;color:#a1a1aa">📈 Analytics</button>
<button onclick="cambiarVista('ab')" id="tab-ab" style="font-size:11px;font-weight:600;padding:8px 12px;white-space:nowrap;background:none;border:none;cursor:pointer;color:#a1a1aa">🧪 A/B</button>
<button onclick="cambiarVista('calendario')" id="tab-calendario" style="font-size:11px;font-weight:600;padding:8px 12px;white-space:nowrap;background:none;border:none;cursor:pointer;color:#a1a1aa">📅 Calendario</button>
<button onclick="cambiarVista('agentes')" id="tab-agentes" style="font-size:11px;font-weight:600;padding:8px 12px;white-space:nowrap;background:none;border:none;cursor:pointer;color:#a1a1aa">🤖 Agentes</button>
<button onclick="cambiarVista('cms')" id="tab-cms" style="font-size:11px;font-weight:600;padding:8px 12px;white-space:nowrap;background:none;border:none;cursor:pointer;color:#a1a1aa">✏ CMS</button>
<button onclick="cambiarVista('monetizacion')" id="tab-monetizacion" style="font-size:11px;font-weight:600;padding:8px 12px;white-space:nowrap;background:none;border:none;cursor:pointer;color:#a1a1aa">💰 Monetización</button>
</div>
</nav>
<main style="max-width:1280px;margin:0 auto;padding:12px;padding-bottom:80px">

<div id="view-preview" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:12px">
<div style="display:flex;flex-direction:column;gap:12px">
<div class="glass" style="border-radius:12px;padding:12px">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px"><h3 style="font-size:12px;font-weight:700;color:#f87171;margin:0">🎬 Vídeo Largo</h3><button onclick="cambiarVideo('largo')" style="font-size:10px;background:#27272a;padding:4px 8px;border-radius:4px;color:#fff;border:none;cursor:pointer">Largo</button></div>
<div id="videoWrapper" class="video-container" style="position:relative"><iframe id="ytFrame" style="width:100%;height:100%;border:0;border-radius:12px" allow="accelerometer;autoplay;clipboard-write;encrypted-media;gyroscope;picture-in-picture" allowfullscreen></iframe><div id="videoPlaceholder" style="position:absolute;inset:0;display:none;align-items:center;justify-content:center;color:#71717a;font-size:12px;background:#000;border-radius:12px">🎬 Vídeo no disponible</div></div>
<div id="ytLinkWrapper" style="margin-top:8px;display:none"><a id="ytLink" target="_blank" style="display:block;text-align:center;background:#dc2626;padding:8px;border-radius:6px;font-size:11px;font-weight:700;text-decoration:none;color:#fff">▶ Ver en YouTube</a></div>
</div>
<div class="glass" style="border-radius:12px;padding:12px"><h3 style="font-size:12px;font-weight:700;color:#fb923c;margin:0 0 8px 0">📱 Shorts</h3><div id="shorts-gallery" style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px"><div style="font-size:11px;color:#71717a">Cargando...</div></div></div>
<div class="glass" style="border-radius:12px;padding:12px"><h3 style="font-size:12px;font-weight:700;color:#c084fc;margin:0 0 8px 0">🎧 Podcast</h3><div id="podcast-player" style="font-size:11px;color:#71717a">Cargando...</div></div>
</div>
<div style="display:flex;flex-direction:column;gap:12px">
<div class="glass" style="border-radius:12px;padding:12px"><h3 style="font-size:12px;font-weight:700;color:#f87171;margin:0 0 8px 0">📋 Dossier</h3><div id="dossierResumen" style="font-size:11px;color:#d4d4d8"></div></div>
<div class="glass" style="border-radius:12px;padding:12px"><h3 style="font-size:12px;font-weight:700;color:#fb923c;margin:0 0 8px 0">🌐 Enlaces</h3><div id="enlaces-web" style="font-size:11px"></div></div>
</div>
</div>


<div id="view-publicar" class="hidden">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px"><h2 style="font-size:16px;font-weight:700;color:#ef4444;margin:0">🚀 Publicar Todo</h2><button onclick="cargarPublicar()" style="font-size:10px;background:#27272a;padding:4px 8px;border-radius:4px;color:#fff;border:none;cursor:pointer">🔄</button></div>
<div id="publicar-content" style="display:flex;flex-direction:column;gap:8px"><div style="font-size:11px;color:#71717a">Cargando...</div></div>
</div>

<div id="view-crear" class="hidden" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px">
<div class="glass" style="border-radius:12px;padding:12px">
<h3 style="font-size:12px;font-weight:700;color:#ef4444;margin:0 0 8px 0">✨ Crear Custom</h3>
<label style="font-size:10px;color:#a1a1aa;text-transform:uppercase">Nicho</label>
<select id="crear-nicho" class="field-box"></select>
<label style="font-size:10px;color:#a1a1aa;text-transform:uppercase">Formatos</label>
<div id="crear-formatos" style="display:flex;gap:4px;flex-wrap:wrap;margin-bottom:8px"></div>
<label style="font-size:10px;color:#a1a1aa;text-transform:uppercase">Tema</label>
<select id="crear-tema-tipo" class="field-box" onchange="crearToggleTema()"><option value="auto">Auto (dossier)</option><option value="manual">Manual</option></select>
<input id="crear-manual" type="text" class="field-box hidden" placeholder="Ej: La manipulación del caso Urda">
<button onclick="crearLanzar()" style="width:100%;background:linear-gradient(90deg,#dc2626,#ea580c);padding:8px;border-radius:6px;font-size:11px;font-weight:700;border:none;color:#fff;cursor:pointer">🚀 Lanzar</button>
</div>
<div class="glass" style="border-radius:12px;padding:12px">
<h3 style="font-size:12px;font-weight:700;color:#fb923c;margin:0 0 8px 0">📊 SEO Optimizer</h3>
<div id="crear-seo" style="font-size:11px;color:#71717a">Cargando...</div>
</div>
</div>

<div id="view-live" class="hidden">
<div class="glass" style="border-radius:12px;padding:12px">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;flex-wrap:wrap;gap:6px">
<h3 style="font-size:12px;font-weight:700;color:#f87171;margin:0">🔴 Pipeline Live</h3>
<div style="display:flex;gap:4px">
<select id="live-log-select" onchange="liveCambiarLog()" style="background:#18181b;border:1px solid #3f3f46;border-radius:4px;padding:4px 8px;font-size:10px;color:#fff;max-width:160px"></select>
<button onclick="liveRefrescar()" style="font-size:10px;background:#27272a;padding:4px 8px;border-radius:4px;color:#fff;border:none;cursor:pointer">🔄</button>
<label style="font-size:10px;color:#a1a1aa;display:flex;align-items:center;gap:2px"><input type="checkbox" id="live-auto" checked onchange="liveToggleAuto()">Auto</label>
</div>
</div>
<div style="display:flex;gap:4px;margin-bottom:8px;flex-wrap:wrap">
<button onclick="liveLanzarPipeline()" style="font-size:10px;background:#16a34a;padding:4px 8px;border-radius:4px;color:#fff;border:none;cursor:pointer">▶ Lanzar</button>
<button onclick="liveMatar()" style="font-size:10px;background:#b91c1c;padding:4px 8px;border-radius:4px;color:#fff;border:none;cursor:pointer">⏹ Matar</button>
</div>
<div id="live-activos" style="font-size:10px;margin-bottom:4px"></div>
<pre id="live-terminal" class="mono" style="font-size:10px;color:#4ade80;background:#000;border-radius:6px;padding:8px;overflow-y:auto;height:55vh;white-space:pre-wrap;margin:0">Esperando logs...</pre>
</div>
</div>

<div id="view-analytics" class="hidden" style="display:flex;flex-direction:column;gap:12px">
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px">
<div class="glass" style="border-radius:12px;padding:10px"><div style="font-size:10px;color:#71717a;text-transform:uppercase">Page Views</div><div id="cf-pv" style="font-size:22px;font-weight:800;color:#f87171">—</div></div>
<div class="glass" style="border-radius:12px;padding:10px"><div style="font-size:10px;color:#71717a;text-transform:uppercase">Visitas</div><div id="cf-vt" style="font-size:22px;font-weight:800;color:#fb923c">—</div></div>
<div class="glass" style="border-radius:12px;padding:10px"><div style="font-size:10px;color:#71717a;text-transform:uppercase">Top País</div><div id="cf-pais" style="font-size:14px;font-weight:700">—</div></div>
<div class="glass" style="border-radius:12px;padding:10px"><div style="font-size:10px;color:#71717a;text-transform:uppercase">Top Página</div><div id="cf-pag" style="font-size:14px;font-weight:700">—</div></div>
</div>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px">
<div class="glass" style="border-radius:12px;padding:12px"><h3 style="font-size:12px;font-weight:700;color:#f87171;margin:0 0 8px 0">🔥 Top Páginas</h3><div id="cf-top-paginas" style="font-size:11px">Cargando...</div></div>
<div class="glass" style="border-radius:12px;padding:12px"><h3 style="font-size:12px;font-weight:700;color:#fb923c;margin:0 0 8px 0">🌐 Top Países</h3><div id="cf-top-paises" style="font-size:11px">Cargando...</div></div>
</div>
</div>

<div id="view-ab" class="hidden">
<div style="margin-bottom:8px;display:flex;gap:4px;flex-wrap:wrap">
<button onclick="cargarAB('largo')" id="ab-tab-largo" style="font-size:10px;background:#dc2626;color:#fff;padding:4px 10px;border-radius:4px;border:none;cursor:pointer;font-weight:700">Largo</button>
<button onclick="cargarAB('short_1')" id="ab-tab-short_1" style="font-size:10px;background:#27272a;color:#fff;padding:4px 10px;border-radius:4px;border:none;cursor:pointer">Short 1</button>
<button onclick="cargarAB('short_2')" id="ab-tab-short_2" style="font-size:10px;background:#27272a;color:#fff;padding:4px 10px;border-radius:4px;border:none;cursor:pointer">Short 2</button>
<button onclick="cargarAB('short_3')" id="ab-tab-short_3" style="font-size:10px;background:#27272a;color:#fff;padding:4px 10px;border-radius:4px;border:none;cursor:pointer">Short 3</button>
<button onclick="cargarAB('short_4')" id="ab-tab-short_4" style="font-size:10px;background:#27272a;color:#fff;padding:4px 10px;border-radius:4px;border:none;cursor:pointer">Short 4</button>
</div>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px">
<div class="glass" style="border-radius:12px;padding:12px"><h3 style="font-size:12px;font-weight:700;color:#f87171;margin:0 0 8px 0">🎯 Actual</h3><div id="ab-actual" style="font-size:11px">Cargando...</div></div>
<div class="glass" style="border-radius:12px;padding:12px"><h3 style="font-size:12px;font-weight:700;color:#fb923c;margin:0 0 8px 0">🅰️ Alt A</h3><div id="ab-alt0" style="font-size:11px">—</div></div>
<div class="glass" style="border-radius:12px;padding:12px"><h3 style="font-size:12px;font-weight:700;color:#facc15;margin:0 0 8px 0">🅱️ Alt B</h3><div id="ab-alt1" style="font-size:11px">—</div></div>
</div>
</div>

<div id="view-calendario" class="hidden">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px"><h3 style="font-size:12px;font-weight:700;color:#f87171;margin:0">📅 Calendario</h3><div style="display:flex;gap:4px"><button onclick="cargarCalendario()" style="font-size:10px;background:#27272a;padding:4px 8px;border-radius:4px;color:#fff;border:none;cursor:pointer">🔄</button><button onclick="calendarioProgramarHoy()" style="font-size:10px;background:#dc2626;padding:4px 8px;border-radius:4px;color:#fff;border:none;cursor:pointer">➕ Hoy</button></div></div>
<div id="cal-lista" style="display:flex;flex-direction:column;gap:4px;font-size:11px">Cargando...</div>
</div>

<div id="view-agentes" class="hidden">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px"><h3 style="font-size:12px;font-weight:700;color:#f87171;margin:0">🤖 Agentes IA</h3><button onclick="cargarAgentes()" style="font-size:10px;background:#27272a;padding:4px 8px;border-radius:4px;color:#fff;border:none;cursor:pointer">🔄</button></div>
<div id="agentes-grid" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:8px;font-size:11px">Cargando...</div>
</div>

<div id="view-cms" class="hidden" style="display:grid;grid-template-columns:1fr 3fr;gap:12px">
<div class="glass" style="border-radius:12px;padding:12px"><h3 style="font-size:12px;font-weight:700;color:#f87171;margin:0 0 8px 0">📁 Archivos</h3><div id="cms-tree" style="font-size:11px;overflow-y:auto;max-height:70vh">Cargando...</div></div>
<div class="glass" style="border-radius:12px;padding:12px">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px"><h3 id="cms-filename" class="mono" style="font-size:12px;font-weight:700;color:#d4d4d8;margin:0">Selecciona archivo</h3><div style="display:flex;gap:4px"><button onclick="cmsGuardar()" style="font-size:10px;background:#16a34a;padding:4px 8px;border-radius:4px;color:#fff;border:none;cursor:pointer">💾</button><button onclick="cmsBuild()" style="font-size:10px;background:#2563eb;padding:4px 8px;border-radius:4px;color:#fff;border:none;cursor:pointer">🚀</button></div></div>
<textarea id="cms-editor" class="mono" style="width:100%;height:70vh;background:#09090b;color:#d4d4d8;font-size:11px;padding:8px;border-radius:6px;border:1px solid #3f3f46;outline:none;resize:vertical" disabled></textarea>
</div>
</div>

<div id="view-monetizacion" class="hidden" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px">
<div class="glass" style="border-radius:12px;padding:12px"><h3 style="font-size:12px;font-weight:700;color:#4ade80;margin:0 0 8px 0">💸 Afiliados</h3><p style="font-size:11px;color:#a1a1aa;margin:0 0 8px 0">Amazon + libros</p><button onclick="aplicarAfiliados()" style="width:100%;background:#16a34a;padding:8px;border-radius:6px;font-size:11px;font-weight:700;border:none;color:#fff;cursor:pointer">Inyectar</button></div>
<div class="glass" style="border-radius:12px;padding:12px"><h3 style="font-size:12px;font-weight:700;color:#c084fc;margin:0 0 8px 0">👕 Printify</h3><p style="font-size:11px;color:#a1a1aa;margin:0 0 8px 0">Merch SDXL</p><button onclick="subirPrintify()" style="width:100%;background:#9333ea;padding:8px;border-radius:6px;font-size:11px;font-weight:700;border:none;color:#fff;cursor:pointer">Subir</button></div>
<div class="glass" style="border-radius:12px;padding:12px"><h3 style="font-size:12px;font-weight:700;color:#facc15;margin:0 0 8px 0">📚 KDP</h3><p style="font-size:11px;color:#a1a1aa;margin:0 0 8px 0">Libro análisis</p><button onclick="generarKDP()" style="width:100%;background:#ca8a04;padding:8px;border-radius:6px;font-size:11px;font-weight:700;border:none;color:#fff;cursor:pointer">Generar</button></div>
</div>

</main>

<div id="drawer" style="position:fixed;top:0;right:-100%;width:100%;max-width:640px;height:100%;background:#18181b;transition:right .3s;z-index:50;overflow-y:auto;padding:16px;border-left:1px solid #3f3f46">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px"><h2 id="drawerTitle" style="font-size:16px;font-weight:700;color:#ef4444;margin:0"></h2><button onclick="cerrarDrawer()" style="color:#a1a1aa;font-size:22px;background:none;border:none;cursor:pointer">×</button></div>
<div id="drawerContent" style="font-size:11px;color:#d4d4d8"></div>
</div>

<button onclick="diosToggle()" style="position:fixed;bottom:16px;right:16px;width:52px;height:52px;border-radius:50%;background:linear-gradient(135deg,#e63946,#f77f00);color:#fff;border:none;font-size:1.4em;z-index:100;cursor:pointer;box-shadow:0 8px 32px rgba(230,57,70,.5)">🤖</button>
<div id="dios-panel" style="display:none;position:fixed;bottom:76px;right:16px;width:min(360px,90vw);max-height:60vh;background:#18181b;border:1px solid #e63946;border-radius:12px;z-index:101;box-shadow:0 20px 60px rgba(0,0,0,.6);flex-direction:column;overflow:hidden">
<div style="padding:10px;border-bottom:1px solid #3f3f46;display:flex;justify-content:space-between;align-items:center"><strong style="color:#f77f00;font-size:.9em">🤖 Dios</strong><button onclick="diosToggle()" style="background:none;border:none;color:#a1a1aa;font-size:1.2em;cursor:pointer">×</button></div>
<div id="dios-chat" style="flex:1;overflow-y:auto;padding:10px;font-size:11px;color:#d4d4d8;min-height:100px;max-height:45vh"></div>
<div style="padding:8px;border-top:1px solid #3f3f46;display:flex;gap:4px"><input id="dios-input" placeholder="Pregunta..." style="flex:1;background:#09090b;border:1px solid #3f3f46;color:#fff;border-radius:4px;padding:6px;font-size:11px;outline:none" onkeypress="if(event.key==='Enter')diosEnviar()"><button onclick="diosEnviar()" style="background:#e63946;border:none;color:#fff;padding:6px 10px;border-radius:4px;cursor:pointer;font-size:11px">→</button></div>
</div>

<div id="toastContainer" style="position:fixed;top:16px;right:16px;z-index:200"></div>

<script src="/encuadre/factory.js?v=2"></script>

<!-- Modal universal (agentes/guion/lightbox) -->
<div id="bigModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.85);z-index:300;align-items:center;justify-content:center;padding:16px" onclick="if(event.target.id==='bigModal')cerrarModal()">
<div style="background:#18181b;border:1px solid #e63946;border-radius:12px;max-width:720px;width:100%;max-height:85vh;display:flex;flex-direction:column;overflow:hidden">
<div style="padding:12px 16px;border-bottom:1px solid #3f3f46;display:flex;justify-content:space-between;align-items:center"><strong id="bigModalTitle" style="color:#f87171;font-size:14px">Info</strong><button onclick="cerrarModal()" style="background:none;border:none;color:#a1a1aa;font-size:22px;cursor:pointer;line-height:1">×</button></div>
<div id="bigModalContent" style="flex:1;overflow-y:auto;padding:16px;font-size:12px;color:#d4d4d8;line-height:1.6"></div>
</div>
</div>

</body>
</html>
"""

FACTORY_JS = r"""/* Factory OS JS - 2026-11-09 v2 */
var fechaActual = '';
var datosGlobales = null;
var _liveTimer = null;
var _liveLogActual = 'pipeline.log';
var _publicarData = null;
var _crearSeo = null;
var _cmsCurrentPath = '';
var _abTipo = 'largo';

function $safe(id, prop, val) { var el = document.getElementById(id); if (el) { try { el[prop] = val; } catch(e){} } }
function $safeHTML(id, html) { var el = document.getElementById(id); if (el) { try { el.innerHTML = html; } catch(e){} } }
function $safeText(id, txt) { var el = document.getElementById(id); if (el) { try { el.textContent = txt; } catch(e){} } }
function $esc(s) { return (s||'').toString().replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }

function mostrarToast(msg, color) {
  var c = document.getElementById('toastContainer'); if (!c) return;
  var t = document.createElement('div');
  t.style.cssText = 'background:#18181b;color:#fff;padding:8px 12px;border-radius:6px;font-size:11px;margin-bottom:6px;border-left:3px solid #e63946';
  t.textContent = msg; c.appendChild(t);
  setTimeout(function(){ t.remove(); }, 3000);
}

function abrirModal(titulo, contenidoHTML) {
  var m = document.getElementById('bigModal');
  var t = document.getElementById('bigModalTitle');
  var c = document.getElementById('bigModalContent');
  if (!m) return;
  if (t) t.textContent = titulo || '';
  if (c) c.innerHTML = contenidoHTML || '';
  m.style.display = 'flex';
}
function cerrarModal() {
  var m = document.getElementById('bigModal'); if (m) m.style.display = 'none';
}

function cambiarVista(v) {
  var vistas = ['preview','publicar','crear','live','analytics','ab','calendario','agentes','cms','monetizacion'];
  vistas.forEach(function(t){
    try {
      var vel = document.getElementById('view-' + t);
      if (vel) { if (t === v) { vel.classList.remove('hidden'); vel.style.display = ''; } else { vel.classList.add('hidden'); vel.style.display = 'none'; } }
      var tab = document.getElementById('tab-' + t);
      if (tab) tab.style.color = (t === v) ? '#e63946' : '#a1a1aa';
    } catch(e) {}
  });
  try {
    if (v === 'publicar') cargarPublicar();
    if (v === 'crear') cargarCrear();
    if (v === 'live') liveInit();
    if (v === 'analytics') cargarCloudflareStats();
    if (v === 'ab') cargarAB('largo');
    if (v === 'calendario') cargarCalendario();
    if (v === 'agentes') cargarAgentes();
    if (v === 'cms') cmsCargarArbol();
  } catch(e) { console.warn('hook', v, e); }
}

function cargarDatos(fecha) {
  if (!fecha) return;
  fechaActual = fecha;

  // YouTube
  fetch('/api/encuadre/youtube/' + fecha).then(function(r){ return r.json(); }).then(function(yt){
    window._ytData = yt;
    actualizarVideoYT('largo');
  }).catch(function(e){ console.warn('yt', e); });

  // Producción (dossier, shorts)
  fetch('/api/encuadre/datos/' + fecha).then(function(r){ return r.json(); }).then(function(data){
    datosGlobales = data;
    var d = data.dossier || {};
    var html = '';
    if (d.titular_brutal) html += '<p style="margin:0 0 6px 0"><strong style="color:#f87171">Titular:</strong> ' + $esc(d.titular_brutal) + '</p>';
    if (d.resumen_ejecutivo) html += '<p style="margin:0 0 6px 0;font-size:10px"><strong style="color:#f87171">Resumen:</strong> ' + $esc(d.resumen_ejecutivo) + '</p>';
    if (d.citas_bomba && d.citas_bomba.length) html += '<p style="margin:0 0 6px 0"><strong style="color:#f87171">Cita:</strong> <em>' + $esc(d.citas_bomba[0]) + '</em></p>';
    if (d.metricas) html += '<p style="margin:0;font-size:10px;color:#71717a">' + JSON.stringify(d.metricas).slice(0,80) + '</p>';
    if (!html) html = '<p style="color:#71717a;font-size:11px">Dossier sin datos</p>';
    $safeHTML('dossierResumen', html);

    var shorts = data.shorts_finales || [];
    var sg = document.getElementById('shorts-gallery');
    if (sg) {
      if (shorts.length) {
        sg.innerHTML = shorts.map(function(s, i){
          return '<div onclick="actualizarVideoYT(\'short_' + (i+1) + '\')" style="cursor:pointer;background:#18181b;border-radius:6px;padding:6px;text-align:center">' +
                 '<div style="font-size:18px">📱</div><div style="font-size:10px;color:#fb923c;font-weight:700">S' + (i+1) + '</div>' +
                 '<div style="font-size:9px;color:#71717a;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + $esc(s.tipo || '') + '</div></div>';
        }).join('');
      } else sg.innerHTML = '<div style="font-size:11px;color:#71717a">Sin shorts</div>';
    }
  }).catch(function(e){ console.warn('datos', e); });

  // Podcast
  fetch('/api/encuadre/podcast/' + fecha).then(function(r){ return r.json(); }).then(function(d){
    var el = document.getElementById('podcast-player');
    if (!el) return;
    if (d.url) el.innerHTML = '<audio controls preload="none" style="width:100%" src="' + d.url + '"></audio><div style="font-size:9px;color:#71717a;margin-top:4px">' + (Math.round(d.size/1024/1024*10)/10) + 'MB</div>';
    else el.innerHTML = '<div style="font-size:11px;color:#71717a">Sin podcast disponible</div>';
  }).catch(function(e){ console.warn('podcast', e); });

  // Enlaces web
  var linkEl = document.getElementById('enlaces-web');
  if (linkEl) {
    linkEl.innerHTML = '<a href="https://elencuadre.pages.dev/analisis/' + fecha + '-largo/" target="_blank" style="color:#60a5fa;text-decoration:none;display:block;padding:2px 0">📄 Post largo</a>' +
                       '<a href="https://elencuadre.pages.dev/analisis/' + fecha + '-dossier-v2/" target="_blank" style="color:#60a5fa;text-decoration:none;display:block;padding:2px 0">📄 Dossier v2</a>' +
                       '<a href="https://elencuadre.pages.dev/" target="_blank" style="color:#60a5fa;text-decoration:none;display:block;padding:2px 0">🏠 Home</a>';
  }
}

function actualizarVideoYT(tipo) {
  var yt = window._ytData || {};
  var frame = document.getElementById('ytFrame');
  var placeholder = document.getElementById('videoPlaceholder');
  var ytLink = document.getElementById('ytLinkWrapper');
  var ytLinkAnchor = document.getElementById('ytLink');
  if (!frame) return;
  var videoId = null, url = null, titulo = '';
  if (tipo === 'largo' && yt.largo && yt.largo.video_id) { videoId = yt.largo.video_id; url = 'https://youtu.be/' + videoId; titulo = yt.largo.titulo || 'Vídeo largo'; }
  else if (tipo.indexOf('short_') === 0) {
    var idx = parseInt(tipo.replace('short_', '')) - 1;
    var s = (yt.shorts || [])[idx];
    if (s && s.video_id) { videoId = s.video_id; url = 'https://youtu.be/' + videoId; titulo = s.titulo || 'Short'; }
  }
  if (videoId) {
    frame.src = 'https://www.youtube.com/embed/' + videoId + '?rel=0';
    frame.style.display = 'block';
    if (placeholder) placeholder.style.display = 'none';
    if (ytLink) ytLink.style.display = 'block';
    if (ytLinkAnchor) { ytLinkAnchor.href = url; ytLinkAnchor.textContent = '▶ Ver en YouTube: ' + titulo.slice(0, 40); }
  } else {
    frame.src = '';
    frame.style.display = 'none';
    if (placeholder) placeholder.style.display = 'flex';
    if (ytLink) ytLink.style.display = 'none';
  }
}

function cambiarVideo(tipo) { actualizarVideoYT(tipo); }
function reproducirShort(n) { actualizarVideoYT('short_' + n); }

/* PUBLICAR */
function cargarPublicar() {
  var root = document.getElementById('publicar-content');
  if (!root) return;
  root.innerHTML = '<div style="font-size:11px;color:#71717a">Cargando...</div>';
  fetch('/api/encuadre/publicar/' + fechaActual).then(function(r){ return r.json(); }).then(function(d){
    _publicarData = d;
    var html = '';
    var largo = d.largo || {};
    html += '<div class="glass" style="border-radius:10px;padding:10px;border-left:3px solid #dc2626">' +
            '<div style="display:flex;justify-content:space-between;align-items:center"><div style="font-size:12px;font-weight:700;color:#f87171">🎬 Vídeo Largo</div><button onclick="verGuion(\'largo\')" style="font-size:10px;background:#27272a;padding:3px 6px;border-radius:4px;color:#fff;border:none;cursor:pointer">Ver guion</button></div>' +
            '<div style="font-size:10px;color:#a1a1aa;margin-top:4px">' + (largo.palabras || 0) + ' palabras · Viralidad ' + (largo.viralidad || 0) + '/10</div>' +
            '<div style="font-size:10px;color:#d4d4d8;margin-top:4px"><strong>SEO:</strong> ' + $esc((largo.seo && largo.seo.titulo) || '—') + '</div></div>';
    (d.shorts || []).forEach(function(s){
      html += '<div class="glass" style="border-radius:10px;padding:10px;border-left:3px solid #ea580c">' +
              '<div style="display:flex;justify-content:space-between;align-items:center"><div style="font-size:12px;font-weight:700;color:#fb923c">📱 Short ' + s.num + ' · ' + $esc(s.tipo || '') + '</div><button onclick="verGuion(' + s.num + ')" style="font-size:10px;background:#27272a;padding:3px 6px;border-radius:4px;color:#fff;border:none;cursor:pointer">Ver guion</button></div>' +
              '<div style="font-size:10px;color:#a1a1aa;margin-top:4px">' + $esc((s.hook || '').slice(0, 100)) + '</div>' +
              '<div style="font-size:10px;color:#d4d4d8;margin-top:4px"><strong>SEO:</strong> ' + $esc((s.seo && s.seo.titulo) || '—') + '</div></div>';
    });
    root.innerHTML = html;
  }).catch(function(e){ root.innerHTML = '<div style="color:#ef4444;font-size:11px">Error: ' + e.message + '</div>'; });
}

function verGuion(id) {
  if (!_publicarData) return;
  var txt = '', titulo = '';
  if (id === 'largo') { txt = (_publicarData.largo && _publicarData.largo.guion) || 'Sin guion'; titulo = '🎬 Guion Vídeo Largo'; }
  else { var s = (_publicarData.shorts || [])[id-1]; txt = (s && s.guion) || 'Sin guion'; titulo = '📱 Guion Short ' + id + ' · ' + ((s && s.tipo) || ''); }
  abrirModal(titulo, '<pre style="white-space:pre-wrap;font-family:inherit;font-size:12px;line-height:1.6;margin:0">' + $esc(txt) + '</pre>');
}

/* CREAR */
function cargarCrear() {
  fetch('/api/encuadre/pipeline_options').then(function(r){ return r.json(); }).then(function(opt){
    var sel = document.getElementById('crear-nicho');
    if (sel) sel.innerHTML = (opt.nichos || []).map(function(n){ return '<option value="' + n + '">' + n + '</option>'; }).join('');
    var fmt = document.getElementById('crear-formatos');
    if (fmt) fmt.innerHTML = (opt.formatos || []).map(function(f){
      return '<label style="font-size:10px;background:#27272a;padding:4px 8px;border-radius:4px;cursor:pointer;display:flex;align-items:center;gap:4px"><input type="checkbox" value="' + f.id + '"> ' + f.icon + ' ' + f.label + '</label>';
    }).join('');
  });
  fetch('/api/encuadre/seo_top').then(function(r){ return r.json(); }).then(function(d){
    _crearSeo = d;
    var html = '<div style="margin-bottom:6px"><div style="font-size:10px;color:#71717a">Keywords:</div><div class="mono" style="font-size:10px;color:#d4d4d8">' + $esc((d.keywords || []).join(' · ') || '—') + '</div></div>';
    html += '<div style="margin-bottom:6px"><div style="font-size:10px;color:#71717a">Mejor hora:</div><div style="font-size:14px;font-weight:700;color:#4ade80">' + $esc(d.mejor_hora || '—') + '</div></div>';
    html += '<div><div style="font-size:10px;color:#71717a">CTR estimado:</div><div style="font-size:12px;font-weight:700;color:#fb923c">' + $esc(d.ctr_estimado || '—') + '</div></div>';
    $safeHTML('crear-seo', html);
  });
}
function crearToggleTema() {
  var v = document.getElementById('crear-tema-tipo'); var m = document.getElementById('crear-manual');
  if (v && m) m.classList.toggle('hidden', v.value !== 'manual');
}
function crearLanzar() {
  var nicho = (document.getElementById('crear-nicho') || {}).value || '';
  var formatos = []; document.querySelectorAll('#crear-formatos input:checked').forEach(function(i){ formatos.push(i.value); });
  var temaTipo = (document.getElementById('crear-tema-tipo') || {}).value || 'auto';
  var tema = temaTipo === 'manual' ? ((document.getElementById('crear-manual') || {}).value || '') : '';
  if (!formatos.length) { mostrarToast('Elige formato', 'bg-red-600'); return; }
  if (temaTipo === 'manual' && !tema) { mostrarToast('Escribe tema', 'bg-red-600'); return; }
  mostrarToast('🚀 Lanzando...', 'bg-orange-600');
  fetch('/api/encuadre/crear_custom', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({nicho: nicho, formatos: formatos, num_shorts: 4, tema_tipo: temaTipo, tema: tema})})
    .then(function(r){ return r.json(); }).then(function(d){ if (d.ok) mostrarToast('✅ Lanzado', 'bg-green-600'); else mostrarToast('❌ ' + (d.error || 'error'), 'bg-red-600'); });
}

/* LIVE */
function liveInit() { liveCargarLista(); liveIniciarAuto(); }
function liveCargarLista() {
  fetch('/api/encuadre/logs/list').then(function(r){ return r.json(); }).then(function(d){
    var sel = document.getElementById('live-log-select');
    if (sel) {
      var cur = _liveLogActual;
      sel.innerHTML = (d.logs || []).slice(0, 20).map(function(l){ return '<option value="' + l.name + '"' + (l.name === cur ? ' selected' : '') + '>' + l.name + '</option>'; }).join('') || '<option value="">(sin logs)</option>';
    }
    var act = document.getElementById('live-activos');
    if (act) act.innerHTML = (d.pipelines_activos && d.pipelines_activos.length) ? '<span style="color:#4ade80">🔴 ' + d.pipelines_activos.length + ' corriendo</span>' : '<span style="color:#71717a">Sin pipelines</span>';
  });
}
function liveCambiarLog() { var s = document.getElementById('live-log-select'); if (s) { _liveLogActual = s.value; liveRefrescar(); } }
function liveRefrescar() {
  if (!_liveLogActual) return;
  fetch('/api/encuadre/logs/tail?name=' + encodeURIComponent(_liveLogActual) + '&n=200').then(function(r){ return r.json(); }).then(function(d){
    var term = document.getElementById('live-terminal');
    if (!term) return;
    if (d.error) { term.textContent = 'Error: ' + d.error; return; }
    term.textContent = d.content || '(vacio)';
    term.scrollTop = term.scrollHeight;
  });
}
function liveToggleAuto() { var a = document.getElementById('live-auto'); if (a && a.checked) liveIniciarAuto(); else if (_liveTimer) { clearInterval(_liveTimer); _liveTimer = null; } }
function liveIniciarAuto() { if (_liveTimer) clearInterval(_liveTimer); liveRefrescar(); _liveTimer = setInterval(function(){ liveRefrescar(); }, 3000); }
function liveLanzarPipeline() {
  if (!confirm('Lanzar pipeline?')) return;
  fetch('/api/encuadre/run_pipeline', {method:'POST'}).then(function(r){ return r.json(); }).then(function(d){
    if (d.status === 'ok' || d.ok) { mostrarToast('✅ Lanzado', 'bg-green-600'); liveIniciarAuto(); }
    else mostrarToast('❌ ' + (d.msg || d.error || 'error'), 'bg-red-600');
  });
}
function liveMatar() {
  if (!confirm('Matar pipelines?')) return;
  fetch('/api/encuadre/kill_pipeline', {method:'POST'}).then(function(r){ return r.json(); }).then(function(d){ mostrarToast(d.ok ? '✅ Matados' : '❌ Error', d.ok ? 'bg-green-600' : 'bg-red-600'); });
}

/* ANALYTICS */
function cargarCloudflareStats() {
  fetch('/api/cloudflare/stats').then(function(r){ return r.json(); }).then(function(d){
    $safeText('cf-pv', (d.page_views || 0).toLocaleString('es-ES'));
    $safeText('cf-vt', (d.visitas || 0).toLocaleString('es-ES'));
    var tp = (d.top_paginas || [])[0]; var tc = (d.top_paises || [])[0];
    $safeText('cf-pais', tc ? tc[0] : '—');
    var pag = tp ? tp[0].replace(/\/$/, '').split('/').pop() : '—';
    $safeText('cf-pag', pag || '—');
    var maxP = tp ? tp[1] : 1;
    var pg = document.getElementById('cf-top-paginas');
    if (pg) pg.innerHTML = (d.top_paginas || []).map(function(p){
      var pct = Math.round((p[1] / maxP) * 100);
      var slug = p[0].replace(/\/$/, '').split('/').pop() || '/';
      return '<div style="margin-bottom:6px"><div style="display:flex;justify-content:space-between;font-size:10px;color:#d4d4d8"><span>' + $esc(slug) + '</span><span>' + p[1] + '</span></div><div style="height:4px;background:#27272a;border-radius:2px;overflow:hidden"><div style="height:100%;width:' + pct + '%;background:linear-gradient(90deg,#ef4444,#f97316)"></div></div></div>';
    }).join('') || '<div style="font-size:11px;color:#71717a">Sin datos aún (beacon <24h)</div>';
    var maxC = tc ? tc[1] : 1;
    var ps = document.getElementById('cf-top-paises');
    if (ps) ps.innerHTML = (d.top_paises || []).map(function(c){
      var pct = Math.round((c[1] / maxC) * 100);
      return '<div style="margin-bottom:6px"><div style="display:flex;justify-content:space-between;font-size:10px;color:#d4d4d8"><span>' + $esc(c[0]) + '</span><span>' + c[1] + '</span></div><div style="height:4px;background:#27272a;border-radius:2px;overflow:hidden"><div style="height:100%;width:' + pct + '%;background:linear-gradient(90deg,#f97316,#facc15)"></div></div></div>';
    }).join('') || '<div style="font-size:11px;color:#71717a">Sin datos aún</div>';
  });
}

/* A/B */
function cargarAB(tipo) {
  _abTipo = tipo || 'largo';
  ['largo','short_1','short_2','short_3','short_4'].forEach(function(t){
    var b = document.getElementById('ab-tab-' + t);
    if (b) b.style.background = (t === _abTipo) ? '#dc2626' : '#27272a';
  });
  fetch('/api/encuadre/ab_titulos/' + fechaActual + '?tipo=' + _abTipo).then(function(r){ return r.json(); }).then(function(d){
    $safeText('ab-actual', d.actual || '—');
    $safeText('ab-alt0', (d.alternativas && d.alternativas[0]) || '—');
    $safeText('ab-alt1', (d.alternativas && d.alternativas[1]) || '—');
  });
}

/* CALENDARIO */
function cargarCalendario() {
  fetch('/api/encuadre/calendario').then(function(r){ return r.json(); }).then(function(d){
    var el = document.getElementById('cal-lista'); if (!el) return;
    if (!d.items || !d.items.length) { el.innerHTML = '<div style="color:#71717a">Sin publicaciones programadas. Pulsa ➕ Hoy para encolar el vídeo de hoy.</div>'; return; }
    el.innerHTML = d.items.map(function(it){
      return '<div style="background:#18181b;border-radius:4px;padding:6px 8px;display:flex;justify-content:space-between;align-items:center"><span>' + $esc(it.titulo || '') + '</span><span style="color:#fbbf24;font-size:10px">' + $esc(it.estado || '') + '</span></div>';
    }).join('');
  });
}
function calendarioProgramarHoy() {
  if (!confirm('Programar vídeo de hoy?')) return;
  fetch('/api/encuadre/programar_hoy', {method:'POST'}).then(function(r){ return r.json(); }).then(function(d){ mostrarToast(d.ok ? '✅ Programado' : '❌ ' + (d.error || ''), d.ok ? 'bg-green-600' : 'bg-red-600'); cargarCalendario(); });
}

/* AGENTES con modal */
function cargarAgentes() {
  fetch('/api/encuadre/agentes').then(function(r){ return r.json(); }).then(function(d){
    var el = document.getElementById('agentes-grid'); if (!el) return;
    if (!d.agentes || !d.agentes.length) { el.innerHTML = '<div style="color:#ef4444">0 agentes</div>'; return; }
    el.innerHTML = d.agentes.map(function(a, i){
      return '<div class="glass" style="border-radius:8px;padding:8px;cursor:pointer" onclick="verAgente(' + i + ')"><div style="font-size:11px;font-weight:700;color:#f87171">' + $esc(a.label) + '</div><div style="font-size:9px;color:#71717a;margin-top:2px;max-height:32px;overflow:hidden;text-overflow:ellipsis">' + $esc((a.desc || '').slice(0, 80)) + '</div></div>';
    }).join('');
    window._agentesData = d.agentes;
  });
}
function verAgente(i) {
  var a = (window._agentesData || [])[i]; if (!a) return;
  abrirModal('🤖 ' + a.label, '<div style="margin-bottom:8px"><strong style="color:#f87171">ID:</strong> <code style="color:#d4d4d8">' + $esc(a.id) + '</code></div><div><strong style="color:#f87171">Descripción completa:</strong><p style="margin-top:6px;font-size:12px;line-height:1.6">' + $esc(a.desc || '(sin descripción)') + '</p></div>');
}

/* CMS con lightbox imagen */
function cmsCargarArbol() {
  fetch('/api/cms/files').then(function(r){ return r.json(); }).then(function(d){
    var root = document.getElementById('cms-tree'); if (!root) return;
    function render(items) {
      return (items || []).map(function(i){
        if (i.type === 'dir') return '<div style="font-size:10px;color:#71717a;margin-top:4px;font-weight:700">📁 ' + $esc(i.name) + '</div>' + render(i.children);
        return '<div onclick="cmsAbrirArchivo(\'' + $esc(i.path).replace(/'/g, "\\'") + '\')" style="font-size:10px;color:#d4d4d8;cursor:pointer;padding:2px 4px;border-radius:2px">📄 ' + $esc(i.name) + '</div>';
      }).join('');
    }
    root.innerHTML = render(d.tree);
  });
}
function cmsAbrirArchivo(path) {
  _cmsCurrentPath = path;
  $safeText('cms-filename', path);
  var ed = document.getElementById('cms-editor');
  if (!ed) return;
  ed.disabled = true; ed.value = 'Cargando...';
  fetch('/api/cms/read', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({path: path})})
    .then(function(r){ return r.json(); }).then(function(d){
      if (d.type === 'binary') {
        ed.value = '';
        var url = d.url || ('/' + path);
        if (/\.(png|jpg|jpeg|gif|webp|svg)$/i.test(path)) {
          abrirModal('🖼 ' + path.split('/').pop(), '<img src="' + url + '" style="max-width:100%;border-radius:8px" onerror="this.style.display=\'none\';this.parentNode.innerHTML+=\'<p style=color:#ef4444>No se pudo cargar</p>\'"><p style="margin-top:8px;font-size:11px;color:#71717a">' + url + '</p>');
        } else if (/\.(mp3|wav|ogg)$/i.test(path)) {
          abrirModal('🎵 ' + path.split('/').pop(), '<audio controls style="width:100%" src="' + url + '"></audio>');
        } else if (/\.(mp4|webm)$/i.test(path)) {
          abrirModal('🎬 ' + path.split('/').pop(), '<video controls style="width:100%" src="' + url + '"></video>');
        } else {
          ed.value = '[archivo binario: ' + url + ']';
        }
      } else { ed.value = d.content || ''; ed.disabled = false; }
    });
}
function cmsGuardar() {
  if (!_cmsCurrentPath) return;
  var ed = document.getElementById('cms-editor'); if (!ed) return;
  fetch('/api/cms/save', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({path: _cmsCurrentPath, content: ed.value})})
    .then(function(r){ return r.json(); }).then(function(d){ mostrarToast(d.ok ? '✅ Guardado' : '❌ ' + (d.error || ''), d.ok ? 'bg-green-600' : 'bg-red-600'); });
}
function cmsBuild() {
  mostrarToast('🚀 Build...', 'bg-blue-600');
  fetch('/api/cms/build', {method:'POST'}).then(function(r){ return r.json(); }).then(function(d){ mostrarToast(d.ok ? '✅ Deploy' : '❌ ' + (d.error || ''), d.ok ? 'bg-green-600' : 'bg-red-600'); });
}

/* MONETIZACIÓN */
function aplicarAfiliados() { mostrarToast('💸 Inyectando afiliados', 'bg-green-600'); }
function subirPrintify() { mostrarToast('👕 Printify', 'bg-purple-600'); }
function generarKDP() { mostrarToast('📚 KDP', 'bg-yellow-600'); }

/* DIOS */
function diosToggle() { var p = document.getElementById('dios-panel'); if (!p) return; p.style.display = (p.style.display === 'none' || !p.style.display) ? 'flex' : 'none'; }
function diosPush(txt, color) { var c = document.getElementById('dios-chat'); if (!c) return; var d = document.createElement('div'); d.style.marginBottom = '6px'; d.style.color = color; d.style.whiteSpace = 'pre-wrap'; d.textContent = txt; c.appendChild(d); c.scrollTop = c.scrollHeight; }
function diosEnviar() {
  var inp = document.getElementById('dios-input'); if (!inp) return;
  var q = inp.value.trim(); if (!q) return;
  inp.value = '';
  diosPush('👤 ' + q, '#a1a1aa'); diosPush('⏳ ...', '#f77f00');
  fetch('/api/encuadre/dios_ask', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({pregunta: q, fecha: fechaActual})})
    .then(function(r){ return r.json(); }).then(function(d){ var c = document.getElementById('dios-chat'); if (c && c.lastChild) c.lastChild.remove(); if (d.ok) diosPush('🤖 ' + d.respuesta, '#d4d4d8'); else diosPush('❌ ' + (d.error || ''), '#ef4444'); });
}

/* INIT */
function __init_factory() {
  var st = document.getElementById('initStatus'); if (st) st.textContent = 'init: ok';
  fetch('/api/encuadre/fechas').then(function(r){ return r.json(); }).then(function(data){
    var sel = document.getElementById('dateSelector'); if (!sel) return;
    if (!data.fechas || !data.fechas.length) { sel.innerHTML = '<option>Sin producciones</option>'; return; }
    sel.innerHTML = data.fechas.map(function(f){ return '<option value="' + f + '">' + f + '</option>'; }).join('');
    sel.onchange = function(){ cargarDatos(this.value); };
    cargarDatos(data.fechas[0]);
  }).catch(function(e){ if (st) st.textContent = 'init ERR: ' + e.message; });
}

if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', __init_factory); } else { __init_factory(); }

['cambiarVista','cargarDatos','actualizarVideoYT','cambiarVideo','reproducirShort','compartir','abrirModal','cerrarModal','cargarPublicar','verGuion','cargarCrear','crearToggleTema','crearLanzar','liveInit','liveCargarLista','liveCambiarLog','liveRefrescar','liveToggleAuto','liveLanzarPipeline','liveMatar','cargarCloudflareStats','cargarAB','cargarCalendario','calendarioProgramarHoy','cargarAgentes','verAgente','cmsCargarArbol','cmsAbrirArchivo','cmsGuardar','cmsBuild','aplicarAfiliados','subirPrintify','generarKDP','diosToggle','diosEnviar','diosPush','mostrarToast'].forEach(function(fn){ try { window[fn] = eval(fn); } catch(e){} });
console.log('[factory] ready');
"""




# === LOGS EN VIVO (2026-11-09) ===
LOGS_DIR = ROOT / "data" / "logs"





@encuadre_bp.route("/api/encuadre/youtube/<fecha>")
def api_youtube(fecha):
    p = ROOT / "data" / "agent" / f"youtube_urls_{fecha}.json"
    if not p.exists(): return jsonify({"largo": None, "shorts": [], "error": "sin_urls"})
    try: return jsonify(json.loads(p.read_text()))
    except Exception as e: return jsonify({"error": str(e)})


@encuadre_bp.route("/api/encuadre/podcast/<fecha>")
def api_podcast(fecha):
    """Devuelve URL del podcast: prefiere /docs/podcast/ (protegido, persiste)."""
    web_pod = ROOT / "web" / "docs" / "podcast" / f"{fecha}.mp3"
    out_pod = ROOT / "output" / "encuadre" / "podcast" / f"{fecha}.mp3"
    out_direct = ROOT / "output" / "encuadre" / f"podcast_{fecha}.mp3"
    for path, url in [
        (web_pod, f"/ui-podcast/{fecha}.mp3"),
        (out_pod, f"/output/encuadre/podcast/{fecha}.mp3"),
        (out_direct, f"/output/encuadre/podcast_{fecha}.mp3"),
    ]:
        if path.exists(): return jsonify({"url": url, "size": path.stat().st_size, "source": path.name})
    return jsonify({"url": None, "error": "sin_podcast"})


@encuadre_bp.route("/ui-podcast/<path:filename>")
def serve_ui_podcast(filename):
    from flask import send_from_directory
    if ".." in filename or "/" in filename:
        return jsonify({"error": "invalido"}), 400
    return send_from_directory(str(ROOT / "web" / "docs" / "podcast"), filename, mimetype="audio/mpeg")


@encuadre_bp.route("/encuadre/factory.js")
def factory_js():
    from flask import Response
    return Response(FACTORY_JS, mimetype="application/javascript", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@encuadre_bp.route("/api/encuadre/buscar")
def api_buscar():
    from flask import request as _rq
    import sqlite3, re as _re
    q = _rq.args.get("q", "").strip()
    if not q or len(q) < 2:
        return jsonify({"q": q, "results": []})
    db = ROOT / "data" / "agent" / "busqueda_fts.db"
    if not db.exists():
        return jsonify({"q": q, "results": [], "error": "indice no construido"})
    try:
        con = sqlite3.connect(str(db))
        con.row_factory = sqlite3.Row
        cur = con.execute(
            "SELECT tipo, fecha, titulo, path, snippet(docs, 3, '<b>', '</b>', '...', 25) as snip "
            "FROM docs WHERE docs MATCH ? ORDER BY rank LIMIT 20",
            (q,))
        results = [dict(r) for r in cur.fetchall()]
        con.close()
        return jsonify({"q": q, "results": results, "total": len(results)})
    except Exception as e:
        return jsonify({"q": q, "results": [], "error": str(e)}), 500


@encuadre_bp.route("/api/encuadre/buscar/reindex", methods=["POST"])
def api_buscar_reindex():
    import subprocess as _sp
    try:
        r = _sp.run(["python3", "scripts/indexar_busqueda.py"], cwd=str(ROOT), capture_output=True, text=True, timeout=120)
        return jsonify({"ok": r.returncode == 0, "output": (r.stdout or r.stderr)[-300:]})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@encuadre_bp.route("/api/encuadre/rollback/list")
def api_rollback_list():
    import subprocess as _sp
    r = _sp.run(["git", "tag", "-l", "snap-*"], cwd=str(ROOT), capture_output=True, text=True, timeout=10)
    tags = sorted(r.stdout.strip().splitlines(), reverse=True)[:20]
    items = []
    for tag in tags:
        info = _sp.run(["git", "log", "-1", "--format=%ci|%s", tag], cwd=str(ROOT), capture_output=True, text=True, timeout=5)
        parts = info.stdout.strip().split("|", 1)
        items.append({"tag": tag, "fecha": parts[0] if parts else "", "motivo": parts[1] if len(parts) > 1 else ""})
    return jsonify({"tags": items})


@encuadre_bp.route("/api/encuadre/rollback/create", methods=["POST"])
def api_rollback_create():
    import subprocess as _sp
    try:
        r = _sp.run(["python3", "scripts/rollback.py", "snapshot", "manual-dashboard"], cwd=str(ROOT), capture_output=True, text=True, timeout=60)
        return jsonify({"ok": True, "output": r.stdout[-300:]})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@encuadre_bp.route("/api/encuadre/rollback/to", methods=["POST"])
def api_rollback_to():
    import subprocess as _sp
    data = request.get_json() or {}
    tag = data.get("tag", "")
    if not tag.startswith("snap-"):
        return jsonify({"ok": False, "error": "Tag invalido"}), 400
    try:
        r = _sp.run(["python3", "scripts/rollback.py", "rollback", tag], cwd=str(ROOT), capture_output=True, text=True, timeout=120)
        return jsonify({"ok": r.returncode == 0, "output": r.stdout[-300:]})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@encuadre_bp.route("/api/encuadre/kill_pipeline", methods=["POST"])
def api_kill_pipeline():
    import subprocess as _sp
    try:
        _sp.run(["pkill", "-9", "-f", "pipeline_encuadre"], capture_output=True, timeout=10)
        _sp.run(["pkill", "-9", "-f", "pipeline_internacional"], capture_output=True, timeout=10)
        return jsonify({"ok": True, "matados": 1})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@encuadre_bp.route("/api/encuadre/logs/list")
def api_logs_list():
    import subprocess as _sp
    items = []
    if LOGS_DIR.exists():
        for f in LOGS_DIR.glob("*.log"):
            try:
                st = f.stat()
                items.append({"name": f.name, "size": st.st_size, "mtime": st.st_mtime})
            except: pass
    items.sort(key=lambda x: -x["mtime"])
    activos = []
    try:
        r = _sp.run(["pgrep", "-af", "pipeline_"], capture_output=True, text=True, timeout=5)
        for line in r.stdout.splitlines():
            if "pgrep" not in line: activos.append(line.strip()[:200])
    except: pass
    return jsonify({"logs": items, "pipelines_activos": activos})


@encuadre_bp.route("/api/encuadre/logs/tail")
def api_logs_tail():
    from flask import request as _req
    name = _req.args.get("name", "")
    n = int(_req.args.get("n", "200"))
    if not name or ".." in name or "/" in name:
        return jsonify({"error": "name invalido"}), 400
    p = LOGS_DIR / name
    if not p.exists():
        return jsonify({"error": "log no existe"}), 404
    try:
        import subprocess as _sp
        r = _sp.run(["tail", "-n", str(min(n, 500)), str(p)], capture_output=True, text=True, timeout=10)
        return jsonify({"name": name, "content": r.stdout, "size": p.stat().st_size, "mtime": p.stat().st_mtime})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
