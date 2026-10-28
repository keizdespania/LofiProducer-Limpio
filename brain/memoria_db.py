"""Cajon 111.A - Memoria persistente del Dios en SQLite."""
from __future__ import annotations
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "agent" / "memoria.db"


def _conectar() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            prompt TEXT NOT NULL,
            resumen TEXT NOT NULL,
            steps INTEGER NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hechos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            hecho TEXT NOT NULL UNIQUE
        )
    """)
    conn.commit()
    return conn


def guardar_conversacion(prompt: str, resumen: str, steps: int) -> None:
    conn = _conectar()
    ts = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO conversaciones (ts, prompt, resumen, steps) VALUES (?, ?, ?, ?)",
        (ts, prompt, resumen, steps),
    )
    conn.commit()
    conn.close()


def recordar_hecho(hecho: str) -> str:
    conn = _conectar()
    ts = datetime.now(timezone.utc).isoformat()
    try:
        conn.execute("INSERT INTO hechos (ts, hecho) VALUES (?, ?)", (ts, hecho))
        conn.commit()
        msg = f"OK. Hecho memorizado: {hecho}"
    except sqlite3.IntegrityError:
        msg = f"Ese hecho ya estaba en mi memoria."
    conn.close()
    return msg


def consultar_hechos(limite: int = 20) -> str:
    conn = _conectar()
    cursor = conn.execute("SELECT ts, hecho FROM hechos ORDER BY id DESC LIMIT ?", (limite,))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return "No tengo hechos memorizados todavía."
    
    lineas = ["Hechos que recuerdo:"]
    for ts, hecho in reversed(rows):
        lineas.append(f"- {hecho}")
    return "\n".join(lineas)


def obtener_contexto_reciente(limite: int = 3) -> str:
    conn = _conectar()
    cursor = conn.execute("SELECT prompt, resumen FROM conversaciones ORDER BY id DESC LIMIT ?", (limite,))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return ""
    
    lineas = ["Ultimas interacciones:"]
    for prompt, resumen in reversed(rows):
        lineas.append(f"Pregunta: {prompt[:100]}...")
        lineas.append(f"Respuesta: {resumen[:100]}...")
    return "\n".join(lineas)

if __name__ == "__main__":
    print("── Test de memoria ──")
    guardar_conversacion("Test de prueba", "Resumen de prueba", 2)
    print(recordar_hecho("El usuario se llama KeiZ"))
    print(consultar_hechos())
