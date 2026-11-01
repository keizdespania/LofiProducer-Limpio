"""generar_informe_pdf.py - Informe PDF completo del pipeline para supervisión."""
import json, pathlib, sys, subprocess, datetime, re
from fpdf import FPDF

# Monkey-patch: multi_cell(0) siempre resetea X al margen izquierdo
_orig_mc = FPDF.multi_cell
def _safe_mc(self, w, h, txt="", *args, **kw):
    if w == 0:
        self.set_x(self.l_margin)
        kw.setdefault("new_x", "LMARGIN")
        kw.setdefault("new_y", "NEXT")
    return _orig_mc(self, w, h, txt, *args, **kw)
FPDF.multi_cell = _safe_mc

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
COLA = ROOT / "output" / "cola_web"
FECHA = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()

def _sanitize(texto, max_len=None):
    """Limpia texto para fpdf (solo latin-1). Reemplaza tipograficos, elimina emojis."""
    if texto is None: return ""
    s = str(texto)
    # Reemplazos tipograficos comunes
    reemplazos = {
        "«": '"', "»": '"', "\u201c": '"', "\u201d": '"',
        "\u2018": "'", "\u2019": "'", "\u2013": "-", "\u2014": "-",
        "\u2026": "...", "\u00a0": " ", "\u00ab": '"', "\u00bb": '"',
        "\u2022": "-", "\u2192": "->", "\u2190": "<-",
    }
    for orig, repl in reemplazos.items():
        s = s.replace(orig, repl)
    # Quitar caracteres fuera de latin-1
    s = "".join(c if (ord(c) < 256 and c not in "\t\r\n") else " " for c in s)
    # Colapsar espacios
    s = re.sub(r"\s+", " ", s).strip()
    if max_len:
        s = s[:max_len]
    return s if s else " "




def _safe_load(path, default=None):
    try:
        return json.loads(path.read_text()) if path.exists() else default
    except:
        return default

class InformePDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, f"Somos El Encuadre - Informe {FECHA}", 0, 0, "L")
        self.cell(0, 5, f"Pag {self.page_no()}", 0, 0, "R")
        self.ln(6)
    
    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 5, "Analisis educativo - Art. 32 LPI - Fuentes citadas y enlazadas", 0, 0, "C")
    
    def titulo_seccion(self, titulo, color=(230, 57, 70)):
        self.ln(4)
        self.set_fill_color(*color)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 13)
        self.cell(0, 8, _sanitize("  " + titulo, 150), 0, 1, "L", True)
        self.set_text_color(0, 0, 0)
        self.ln(2)
    
    def subtitulo(self, texto, color=(40, 40, 50)):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*color)
        self.cell(0, 5, _sanitize(texto, 200), 0, 1)
        self.set_text_color(0, 0, 0)
        self.ln(1)
    
    def parrafo(self, texto, size=9, color=(30, 30, 30)):
        self.set_font("Helvetica", "", size)
        self.set_text_color(*color)
        self.multi_cell(0, 4.5, _sanitize(texto, 5000))
        self.ln(1)
    
    def bullet(self, texto, size=9):
        self.set_font("Helvetica", "", size)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 4.5, _sanitize("  - " + texto, 800))

def _portada(pdf):
    pdf.add_page()
    pdf.ln(40)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(230, 57, 70)
    pdf.cell(0, 15, "SOMOS EL ENCUADRE", 0, 1, "C")
    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, "Informe de supervision - Dossier del creador", 0, 1, "C")
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, _sanitize(f"{FECHA}"), 0, 1, "C")
    pdf.ln(20)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 5, "Analisis educativo bajo el derecho de cita (Art. 32 LPI).\nEste informe contiene material de supervision interna.", 0, "C")
    pdf.ln(30)
    pdf.set_draw_color(230, 57, 70)
    pdf.set_line_width(0.5)
    pdf.line(60, pdf.get_y(), 150, pdf.get_y())

def _resumen_ejecutivo(pdf, data):
    pdf.add_page()
    pdf.titulo_seccion("1. RESUMEN EJECUTIVO")
    
    stats = [
        ("Medios recolectados", data.get("n_medios", "?")),
        ("Noticias crudas", data.get("n_recoleccion", "?")),
        ("Tras filtro seguridad", data.get("n_limpias", "?")),
        ("Top16 final (validas)", len(data.get("top16", []))),
        ("Analisis por medio", data.get("n_analisis", "?")),
        ("Hooks generados", data.get("n_hooks", "?")),
        ("Citas academicas", data.get("n_citas", "?")),
        ("Escenas guion", len(data.get("escenas", []))),
        ("Palabras totales", data.get("palabras", "?")),
        ("Posts web", data.get("n_posts", "?")),
        ("Bloques redes", data.get("n_redes", "?")),
    ]
    pdf.set_font("Helvetica", "", 9)
    for label, val in stats:
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(70, 5.5, _sanitize(label), 1, 0)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 5.5, _sanitize(str(val)), 1, 1)

def _seccion_recoleccion(pdf, data):
    pdf.add_page()
    pdf.titulo_seccion("2. RECOLECCION Y FILTRADO")
    
    pdf.subtitulo("Filtro de seguridad (tragedias, deportes, farandula)")
    rechazadas = data.get("rechazadas", [])
    pdf.parrafo(f"Total rechazadas por filtro_seguridad: {len(rechazadas)}")
    for r in rechazadas[:20]:
        motivo = r.get("razon", r.get("sev", "?"))
        titulo = (r.get("titular") or r.get("titulo") or "")[:80]
        pdf.bullet(f"[{motivo}] {titulo}")
    if len(rechazadas) > 20:
        pdf.parrafo(f"... y {len(rechazadas) - 20} mas")
    
    pdf.ln(3)
    pdf.subtitulo("Aceptadas (pasan al editor jefe)")
    aceptadas = data.get("aceptadas", [])
    pdf.parrafo(f"Total aceptadas: {len(aceptadas)}")
    for i, n in enumerate(aceptadas[:30], 1):
        tit = (n.get("titular") or "")[:100]
        pdf.bullet(f"{i}. {tit}")

def _seccion_analisis(pdf, data):
    pdf.add_page()
    pdf.titulo_seccion("3. TOP16 VALIDAS + ANALISIS POR MEDIO")
    
    top16 = data.get("top16", [])
    pdf.parrafo(f"Total validas seleccionadas: {len(top16)}")
    for i, n in enumerate(top16, 1):
        tit = (n.get("titular") or "")[:110]
        medio = n.get("medio", "?")
        cat = n.get("categoria", "?")
        pdf.set_font("Helvetica", "B", 9)
        pdf.multi_cell(0, 4.5, _sanitize(f"{i}. [{cat}] {medio}", 200))
        pdf.set_font("Helvetica", "", 8)
        pdf.multi_cell(0, 4, _sanitize(f"   {tit}", 200))
        pdf.ln(0.5)
    
    pdf.add_page()
    pdf.subtitulo("Analisis por medio (forense + tecnica)")
    analisis = data.get("analisis", {})
    pdf.parrafo(f"Medios analizados: {len(analisis)}")
    tecnicas = data.get("tecnicas", {})
    for medio, tec in tecnicas.items():
        if not tec: continue
        pdf.set_font("Helvetica", "B", 9)
        pdf.multi_cell(0, 4.5, f"\n{medio}:")
        for k in ("tecnica", "framing", "omite"):
            if tec.get(k):
                pdf.set_font("Helvetica", "", 8)
                pdf.multi_cell(0, 4, _sanitize(f"  {k}: {tec[k][:200]}", 300))

def _seccion_dossier(pdf, data):
    pdf.add_page()
    pdf.titulo_seccion("4. DOSSIER DEL DIA")
    
    dossier = data.get("dossier", {})
    pdf.subtitulo("Top 3 noticias")
    top3 = data.get("top3", {})
    for k, v in top3.items():
        pdf.bullet(f"{k}: {str(v)[:120]}")
    
    pdf.ln(3)
    pdf.subtitulo("Hooks de retencion (top 10)")
    hooks = data.get("hooks", [])
    for h in hooks[:10]:
        tipo = h.get("tipo", "?")
        hook = (h.get("hook") or "")[:120]
        score = h.get("score", "?")
        pdf.bullet(f"[{tipo}] (score {score}) {hook}")
    
    pdf.ln(3)
    pdf.subtitulo("Citas academicas")
    citas = data.get("citas", [])
    for c in citas[:5]:
        pdf.bullet(str(c)[:200])

def _seccion_guion(pdf, data):
    pdf.add_page()
    pdf.titulo_seccion("5. GUION VIDEO LARGO (18 ESCENAS)")
    
    escenas = data.get("escenas", [])
    pdf.parrafo(f"Total escenas: {len(escenas)}")
    for e in escenas:
        eid = e.get("id", "?")
        txt = e.get("texto", "")
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(0, 5, _sanitize(f"ESCENA {eid}"), 0, 1)
        pdf.set_font("Helvetica", "", 8)
        pdf.multi_cell(0, 4, _sanitize(txt, 2000))
        pdf.ln(1)
        if pdf.get_y() > 250:
            pdf.add_page()

def _seccion_texto_alvaro(pdf, data):
    pdf.add_page()
    pdf.titulo_seccion("6. TEXTO LOCUTADO POR ALVARO")
    pdf.parrafo("Este es el texto completo que locuta Alvaro (voz TTS humanizada).")
    
    texto_voz = data.get("texto_voz_largo", "")
    pdf.parrafo(f"Palabras totales: {len(texto_voz.split())}")
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 4.5, _sanitize(texto_voz[:8000], 8000))
    if len(texto_voz) > 8000:
        pdf.parrafo(f"... (truncado, {len(texto_voz) - 8000} caracteres mas)")

def _seccion_posts(pdf, data):
    pdf.add_page()
    pdf.titulo_seccion("7. TEXTOS PUBLICADOS EN WEB")
    
    for post in data.get("posts", []):
        pdf.subtitulo(_sanitize("POST: " + post["nombre"], 100))
        pdf.set_font("Courier", "", 7.5)
        texto = post["texto"][:4000]
        pdf.multi_cell(0, 3.5, _sanitize(texto, 4000))
        if len(post["texto"]) > 4000:
            pdf.parrafo(f"... (truncado, {len(post['texto']) - 4000} caracteres mas)")
        pdf.ln(3)
        if pdf.get_y() > 250:
            pdf.add_page()

def _seccion_seo_redes(pdf, data):
    pdf.add_page()
    pdf.titulo_seccion("8. SEO Y REDES SOCIALES")
    
    seo = data.get("seo", {})
    if seo:
        pdf.subtitulo("Titulo largo")
        pdf.parrafo(seo.get("largo", {}).get("titulo", "?"))
        pdf.subtitulo("Titulos shorts")
        for s in seo.get("shorts", []):
            pdf.bullet(f"Short {s.get('num')}: {s.get('titulo', '?')}")
    
    pdf.ln(3)
    redes = data.get("redes", {})
    if redes:
        pdf.subtitulo("Copys de redes sociales (24 bloques)")
        for s in redes.get("shorts", []):
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(0, 5, _sanitize("Short " + str(s.get("id", "?"))), 0, 1)
            for red in ("youtube", "tiktok", "instagram", "x", "threads", "blogger"):
                bloque = s.get(red, {})
                if bloque:
                    pdf.set_font("Helvetica", "B", 8)
                    pdf.cell(0, 4, _sanitize(f"  {red.upper()}:"), 0, 1)
                    for k, v in bloque.items():
                        if isinstance(v, str) and v:
                            pdf.set_font("Courier", "", 7)
                            pdf.multi_cell(0, 3.5, _sanitize(f"    {k}: {v[:200]}", 300))
            if pdf.get_y() > 250:
                pdf.add_page()

def _seccion_assets(pdf, data):
    pdf.add_page()
    pdf.titulo_seccion("9. ASSETS GENERADOS")
    
    pdf.subtitulo("Ficheros multimedia")
    for f in data.get("assets", []):
        pdf.bullet(_sanitize(f"{f['nombre']}: {f['tamano']} ({f['tipo']})", 200))
    
    pdf.ln(4)
    pdf.subtitulo("Verificacion")
    pdf.parrafo("Alucinaciones detectadas: " + str(data.get("alucinaciones", 0)))
    pdf.parrafo("Ficheros sin commitear: " + str(data.get("sin_commitear", 0)))

def _seccion_aviso_legal(pdf):
    pdf.add_page()
    pdf.titulo_seccion("AVISO LEGAL", color=(80, 80, 80))
    pdf.parrafo("Este informe es material de SUPERVISION INTERNA del creador de Somos El Encuadre.")
    pdf.parrafo("No constituye acusacion de delito. No es opinion sobre la linea editorial.")
    pdf.parrafo("Los medios citados estan enlazados en las publicaciones correspondientes.")
    pdf.parrafo("El derecho de cita (Art. 32 LPI) ampara el uso de fragmentos con fines analiticos.")
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 8, "El mecanismo, expuesto.", 0, 1, "C")

def _leer_todo():
    data = {}
    
    # Recoleccion
    rec = _safe_load(OUT / f"recoleccion_{FECHA}.json", {})
    limpia = _safe_load(OUT / f"recoleccion_{FECHA}_limpia.json", {})
    filtrado = _safe_load(OUT / f"filtrado_{FECHA}.json", {})
    
    data["n_medios"] = sum(len(v) for sec in ("prensa","tv","radio","agencias") for v in (rec.get(sec) or {}).values()) if rec else 0
    data["n_recoleccion"] = sum(len(v) for sec in ("prensa","agencias") for v in (rec.get(sec) or {}).values()) if rec else 0
    
    # Aceptadas vs rechazadas
    items_limpios = []
    for sec in ("prensa","agencias"):
        for medio, ns in (limpia.get(sec) or {}).items():
            for n in ns:
                if isinstance(n, dict): items_limpios.append(n)
    data["n_limpias"] = len(items_limpios)
    data["aceptadas"] = items_limpios
    
    # Rechazadas del filtrado
    rechazadas = []
    if isinstance(filtrado, dict):
        for sec in ("prensa","agencias","tv","radio"):
            for med, ns in (filtrado.get(sec) or {}).items():
                for n in ns:
                    if isinstance(n, dict) and n.get("_motivo"):
                        rechazadas.append({"titular": n.get("titular", ""), "razon": n.get("_motivo", "?")})
    data["rechazadas"] = rechazadas
    
    # Analisis fase1
    af = _safe_load(OUT / f"analisis_fase1_{FECHA}.json", {})
    data["top16"] = af.get("top16", [])
    data["analisis"] = af.get("analisis", {})
    data["top3"] = af.get("top3", {})
    data["n_analisis"] = len(data["analisis"])
    
    # Dossier
    dossier = _safe_load(OUT / f"dossier_{FECHA}.json", {})
    data["dossier"] = dossier.get("dossier", {})
    data["hooks"] = dossier.get("guiones", {}).get("hooks_totales", [])
    data["citas"] = dossier.get("citas", [])
    data["n_hooks"] = len(data["hooks"])
    data["n_citas"] = len(data["citas"])
    
    # Tecnicas del enriquecido
    enr = _safe_load(OUT / f"dossier_{FECHA}_enriquecido.json", {})
    tecnicas = {}
    desglose = enr.get("dossier", {}).get("desglose_medios", "")
    for line in desglose.split("\n"):
        m = re.match(r"\*\*([^*]+)\*\*: '([^']*)' -> \*\*Framing:\*\* ([^|]+) \| \*\*Técnica:\*\* ([^|]+) \| \*\*Omite:\*\* (.+)", line)
        if m:
            tecnicas[m.group(1).strip()] = {
                "titular": m.group(2).strip(),
                "framing": m.group(3).strip(),
                "tecnica": m.group(4).strip(),
                "omite": m.group(5).strip(),
            }
    data["tecnicas"] = tecnicas
    
    # Produccion
    prod = _safe_load(OUT / f"produccion_{FECHA}.json", {})
    data["escenas"] = prod.get("escenas", [])
    data["texto_voz_largo"] = prod.get("texto_voz_largo", "")
    data["palabras"] = prod.get("palabras_totales", "?")
    
    # SEO
    data["seo"] = _safe_load(OUT / f"seo_{FECHA}.json", {})
    
    # Redes
    data["redes"] = _safe_load(OUT / f"redes_{FECHA}.json", {})
    data["n_redes"] = len(data["redes"].get("shorts", [])) if data["redes"] else 0
    
    # Posts web
    posts = []
    for p in sorted(COLA.glob(f"{FECHA}-*.md")):
        posts.append({"nombre": p.name, "texto": p.read_text()})
    data["posts"] = posts
    data["n_posts"] = len(posts)
    
    # Assets
    assets = []
    for f in [
        OUT / f"video_largo_{FECHA}.mp4",
        OUT / f"voz_largo_{FECHA}.mp3",
        ROOT / "web" / "docs" / "podcast" / f"{FECHA}.mp3",
    ]:
        if f.exists():
            assets.append({"nombre": f.name, "tamano": f"{f.stat().st_size // 1024 // 1024}MB", "tipo": "video" if f.suffix == ".mp4" else "audio"})
    for i in range(1, 5):
        f = OUT / f"short_{i}_{FECHA}.mp4"
        if f.exists():
            assets.append({"nombre": f.name, "tamano": f"{f.stat().st_size // 1024 // 1024}MB", "tipo": "short"})
    data["assets"] = assets
    
    return data

def generar_informe(fecha=None):
    fecha = fecha or FECHA
    print(f"Generando informe PDF para {fecha}...")
    print("=" * 60)
    
    data = _leer_todo()
    
    pdf = InformePDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    _portada(pdf)
    _resumen_ejecutivo(pdf, data)
    _seccion_recoleccion(pdf, data)
    _seccion_analisis(pdf, data)
    _seccion_dossier(pdf, data)
    _seccion_guion(pdf, data)
    _seccion_texto_alvaro(pdf, data)
    _seccion_posts(pdf, data)
    _seccion_seo_redes(pdf, data)
    _seccion_assets(pdf, data)
    _seccion_aviso_legal(pdf)
    
    # Guardar 2 sitios
    salida_local = OUT / f"informe_{fecha}.pdf"
    pdf.output(str(salida_local))
    print(f"✅ Local: {salida_local} ({salida_local.stat().st_size // 1024}KB)")
    
    sdcard_dir = pathlib.Path.home() / "storage" / "shared" / "Download" / "ElEncuadre"
    try:
        sdcard_dir.mkdir(parents=True, exist_ok=True)
        salida_sdcard = sdcard_dir / f"informe_{fecha}.pdf"
        salida_sdcard.write_bytes(salida_local.read_bytes())
        print(f"✅ Móvil: {salida_sdcard}")
    except Exception as e:
        print(f"⚠️ No se pudo copiar a /sdcard: {e}")
    
    # Notificación
    try:
        subprocess.run(["termux-notification",
            "--title", f"📄 Informe {fecha} listo",
            "--content", "Toca para abrir en /sdcard/Download/ElEncuadre/",
            "--action", f"termux-open {sdcard_dir}/informe_{fecha}.pdf",
            "--priority", "high"],
            check=False, timeout=10)
        print("✅ Notificación enviada")
    except Exception as e:
        print(f"⚠️ Notificación falló: {e}")
    
    print("=" * 60)
    print(f"✅ INFORME {fecha} OK")
    return True

if __name__ == "__main__":
    ok = generar_informe(sys.argv[1] if len(sys.argv) > 1 else None)
    sys.exit(0 if ok else 1)