#!/usr/bin/env python3
"""anecdotas_rotador.py - Rotador de 100 anécdotas. 20 categorías × 5.
Cuando se agotan (counter >= 100), regenera 100 nuevas con LLM.
"""
import json, sys
from pathlib import Path

ROOT = Path("/data/data/com.termux/files/home/LofiProducer")
CONFIG = ROOT / "config" / "anecdotas.json"
COUNTER = ROOT / "data" / "agent" / "anecdotas_counter.txt"

def _leer_counter():
    if COUNTER.exists():
        try: return int(COUNTER.read_text().strip())
        except: pass
    return 0

def _guardar_counter(n):
    COUNTER.parent.mkdir(parents=True, exist_ok=True)
    COUNTER.write_text(str(n))

def _regenerar_anecdotas():
    """Genera 100 nuevas anécdotas con LLM cuando se agotan."""
    print("[anecdotas] Regenerando 100 nuevas con LLM...", flush=True)
    try:
        sys.path.insert(0, str(ROOT / "brain"))
        from especialistas import pedir_a_especialista
        
        categorias = ["bar", "familia", "vecinos", "trabajo", "transporte",
                      "supermercado", "medico", "colegio", "redes", "telefono",
                      "cine_clasico", "historia", "cultura_pop", "deporte", "musica",
                      "literatura", "ciencia", "gastronomia", "viajes", "series"]
        
        prompt = f"""Genera 100 anécdotas cortas (2-4 frases) para monólogo de actualidad.
Cada una debe tener: lugar cotidiano, personaje con nombre, diálogo, observación irónica.
Distribuye 5 por categoría en: {', '.join(categorias)}.
NO menciones noticias concretas. Deben conectar con cualquier tema.
Devuelve SOLO JSON: {{"anecdotas": [{{"categoria": "...", "texto": "..."}}]}}"""
        
        resp = pedir_a_especialista("guionista_retencion_v2", prompt, contexto="", proveedor="auto")
        import re
        m = re.search(r'\{.*\}', resp, re.DOTALL)
        if not m: raise ValueError("Sin JSON en respuesta")
        data = json.loads(m.group(0))
        
        anecdotas = []
        for i, a in enumerate(data.get("anecdotas", [])[:100], 1):
            anecdotas.append({
                "id": i,
                "categoria": a.get("categoria", "generica"),
                "texto": a.get("texto", ""),
                "usada": False,
                "fecha_usada": None,
            })
        
        if len(anecdotas) < 50:
            raise ValueError(f"Solo {len(anecdotas)} anécdotas generadas")
        
        CONFIG.write_text(json.dumps({
            "version": 1,
            "generadas": "regeneradas",
            "total": len(anecdotas),
            "categorias": categorias,
            "anecdotas": anecdotas,
        }, indent=2, ensure_ascii=False))
        _guardar_counter(0)
        print(f"[anecdotas] ✅ {len(anecdotas)} nuevas generadas", flush=True)
        return anecdotas
    except Exception as e:
        print(f"[anecdotas] ❌ Regeneración falló: {e}", flush=True)
        return []

def coger_anecdota():
    """Coge la siguiente anécdota del rotador. Si agotado, regenera 100."""
    if not CONFIG.exists():
        raise FileNotFoundError(f"No existe {CONFIG}")
    
    data = json.loads(CONFIG.read_text())
    anecdotas = data.get("anecdotas", [])
    idx = _leer_counter()
    
    if idx >= len(anecdotas):
        # Agotadas, regenerar
        nuevas = _regenerar_anecdotas()
        if nuevas:
            anecdotas = nuevas
            idx = 0
        else:
            # Fallback: reset counter
            idx = 0
    
    anecdota = anecdotas[idx]
    anecdota["usada"] = True
    from datetime import datetime
    anecdota["fecha_usada"] = datetime.now().isoformat()
    
    # Guardar estado
    data["anecdotas"] = anecdotas
    CONFIG.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    _guardar_counter(idx + 1)
    
    return anecdota

if __name__ == "__main__":
    a = coger_anecdota()
    print(f"Anécdota #{a['id']} ({a['categoria']}):")
    print(f"  {a['texto'][:200]}...")
    print(f"Counter: {_leer_counter()}")
