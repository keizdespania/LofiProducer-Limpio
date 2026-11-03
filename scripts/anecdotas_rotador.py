#!/usr/bin/env python3
"""anecdotas_rotador.py - Rotador de 100 anécdotas. Auto-regenera si agotado."""
import json, sys
from pathlib import Path
from datetime import datetime

ROOT = Path('/data/data/com.termux/files/home/LofiProducer')
CONFIG = ROOT / 'config' / 'anecdotas.json'
COUNTER = ROOT / 'data' / 'agent' / 'anecdotas_counter.txt'

def coger_anecdota():
    """Coge la siguiente anécdota del banco. Regenera si agotado."""
    if not CONFIG.exists():
        return {"id": 0, "categoria": "fallback", "texto": "El otro día en el bar de Paco, alguien decía: 'Lo he leído en el periódico, así que es verdad'. Y yo pensé: 'Como el anuncio de la crema que quita arrugas'. Y el hombre se quedó pensando."}
    
    data = json.loads(CONFIG.read_text())
    anecdotas = data.get("anecdotas", [])
    
    # Leer counter
    counter = 0
    if COUNTER.exists():
        try: counter = int(COUNTER.read_text().strip())
        except: counter = 0
    
    # Si counter >= total, regenerar
    if counter >= len(anecdotas):
        print(f"   🔄 Banco agotado ({counter}/{len(anecdotas)}), regenerando 100 nuevas...", flush=True)
        try:
            from anecdotas_regenerar import regenerar
            nuevas = regenerar()
            if nuevas:
                anecdotas = nuevas
                data["anecdotas"] = nuevas
                data["generadas"] = datetime.now().isoformat()
                CONFIG.write_text(json.dumps(data, indent=2, ensure_ascii=False))
                counter = 0
        except Exception as e:
            print(f"   ⚠️ Regeneración falló: {e}, reiniciando counter", flush=True)
            counter = 0
    
    # Coger anécdota
    anecdota = anecdotas[counter % len(anecdotas)]
    anecdota["usada"] = True
    anecdota["fecha_usada"] = datetime.now().isoformat()
    
    # Actualizar JSON (marcar usada)
    anecdotas[counter % len(anecdotas)] = anecdota
    data["anecdotas"] = anecdotas
    CONFIG.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    
    # Incrementar counter
    COUNTER.parent.mkdir(parents=True, exist_ok=True)
    COUNTER.write_text(str(counter + 1))
    
    print(f"   📖 Anécdota #{counter + 1}/{len(anecdotas)} ({anecdota['categoria']})", flush=True)
    return anecdota

if __name__ == "__main__":
    a = coger_anecdota()
    print(f"=== ANÉCDOTA DEL DÍA ===")
    print(f"Categoría: {a['categoria']}")
    print(f"ID: {a['id']}")
    print(f"Texto: {a['texto']}")
