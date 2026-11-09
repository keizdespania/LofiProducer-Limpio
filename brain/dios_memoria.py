import json, sqlite3, time, datetime, pathlib
ROOT = pathlib.Path("/data/data/com.termux/files/home/LofiProducer")
DATA = ROOT / "data" / "agent"
DATA.mkdir(parents=True, exist_ok=True)

class Workspace:
    def __init__(self): self.path = DATA / "dios_workspace.json"
    def cargar(self):
        if not self.path.exists(): return {}
        try: return json.loads(self.path.read_text())
        except: return {}
    def guardar(self, d): self.path.write_text(json.dumps(d, indent=2, ensure_ascii=False))
    def anotar_tarea(self, prompt, resultado, tools):
        d = self.cargar()
        d["ultima_tarea"] = prompt[:120]
        d["ultimo_resultado"] = resultado[:200]
        d["ultimas_tools"] = tools[:5]
        d["timestamp"] = time.time()
        d.setdefault("historial", []).append({"t": prompt[:100], "r": resultado[:150], "ts": time.time()})
        d["historial"] = d["historial"][-10:]
        self.guardar(d)
    def compacto(self):
        d = self.cargar()
        if not d: return ""
        out = []
        if d.get("ultima_tarea"): out.append(f"Ultima: {d['ultima_tarea'][:80]}")
        if d.get("ultimas_tools"): out.append(f"Tools: {', '.join(d['ultimas_tools'][:3])}")
        return "\n".join(out)[:300]

class EpisodiosDB:
    def __init__(self):
        self.path = DATA / "dios_episodios.db"
        with sqlite3.connect(self.path) as c:
            c.execute("CREATE TABLE IF NOT EXISTS ep (id INTEGER PRIMARY KEY AUTOINCREMENT, prompt TEXT, resultado TEXT, tools TEXT, exito INTEGER, fecha TEXT)")
    def guardar(self, prompt, resultado, tools, exito=True):
        with sqlite3.connect(self.path) as c:
            c.execute("INSERT INTO ep (prompt, resultado, tools, exito, fecha) VALUES (?,?,?,?,?)",
                     (prompt[:400], resultado[:800], json.dumps(tools)[:200], 1 if exito else 0, datetime.datetime.now().isoformat()))
    def ultimas(self, n=3):
        with sqlite3.connect(self.path) as c:
            cur = c.execute("SELECT prompt, resultado, fecha FROM ep ORDER BY id DESC LIMIT ?", (n,))
            return [{"prompt": r[0], "resultado": r[1], "fecha": r[2]} for r in cur.fetchall()]
    def similares(self, prompt, umbral=0.5):
        pn = set(prompt.lower().split())
        with sqlite3.connect(self.path) as c:
            cur = c.execute("SELECT prompt, resultado FROM ep ORDER BY id DESC LIMIT 30")
            ms = []
            for p, r in cur.fetchall():
                pv = set((p or "").lower().split())
                if not pv or not pn: continue
                j = len(pn & pv) / len(pn | pv)
                if j >= umbral: ms.append((j, p, r))
            ms.sort(reverse=True)
            return [{"prompt": m[1], "resultado": m[2][:200]} for m in ms[:2]]

class CostesDB:
    def __init__(self):
        self.path = DATA / "dios_costes.db"
        with sqlite3.connect(self.path) as c:
            c.execute("CREATE TABLE IF NOT EXISTS costes (id INTEGER PRIMARY KEY AUTOINCREMENT, modelo TEXT, tin INTEGER, tout INTEGER, fecha TEXT)")
    def guardar(self, modelo, tin, tout):
        with sqlite3.connect(self.path) as c:
            c.execute("INSERT INTO costes (modelo, tin, tout, fecha) VALUES (?,?,?,?)",
                     (modelo, tin, tout, datetime.datetime.now().isoformat()))
    def resumen_hoy(self):
        hoy = datetime.date.today().isoformat()
        with sqlite3.connect(self.path) as c:
            r = c.execute("SELECT COUNT(*), SUM(tin), SUM(tout) FROM costes WHERE fecha LIKE ?", (hoy+"%",)).fetchone()
            return {"tareas": r[0] or 0, "tokens_in": r[1] or 0, "tokens_out": r[2] or 0}

class FallosDB:
    def __init__(self):
        self.path = DATA / "dios_fallos.db"
        with sqlite3.connect(self.path) as c:
            c.execute("CREATE TABLE IF NOT EXISTS fallos (id INTEGER PRIMARY KEY AUTOINCREMENT, prompt TEXT, tool TEXT, error TEXT, fecha TEXT)")
    def guardar(self, prompt, tool, error):
        with sqlite3.connect(self.path) as c:
            c.execute("INSERT INTO fallos (prompt, tool, error, fecha) VALUES (?,?,?,?)",
                     (prompt[:300], tool, error[:400], datetime.datetime.now().isoformat()))
    def similares(self, prompt, umbral=0.5):
        pn = set(prompt.lower().split())
        with sqlite3.connect(self.path) as c:
            cur = c.execute("SELECT prompt, tool, error FROM fallos ORDER BY id DESC LIMIT 20")
            ms = []
            for p, t, e in cur.fetchall():
                pv = set((p or "").lower().split())
                if not pv: continue
                j = len(pn & pv) / len(pn | pv)
                if j >= umbral: ms.append((j, t, e))
            ms.sort(reverse=True)
            return [{"tool": m[1], "error": m[2][:100]} for m in ms[:2]]

WORKSPACE = Workspace()
EPISODIOS = EpisodiosDB()
COSTES = CostesDB()
FALLOS = FallosDB()
