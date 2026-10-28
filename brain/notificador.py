"""Notificaciones push via Termux API."""
import subprocess, shutil

def notificar(titulo, mensaje):
    if not shutil.which("termux-notification"):
        return "AVISO: termux-api no instalado"
    try:
        subprocess.run(["termux-notification", "-t", titulo, "-c", mensaje], check=True, capture_output=True, timeout=10)
        return "OK: Notificacion enviada"
    except Exception as e:
        return "ERROR: " + str(e)
