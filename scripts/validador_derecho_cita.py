"""validador_derecho_cita.py - Filtro legal para clips de terceros."""
import json, re
from pathlib import Path

def validar_clip(medio, tecnica, duracion_seg, tiene_fuente):
    """
    Retorna True si el clip es legal, False si el abogado lo rechaza.
    Reglas:
    - Duración máxima: 5 segundos.
    - Debe tener fuente clara (medio, programa, fecha).
    - Debe ser educativo (no sustituye el contenido original).
    """
    errores = []
    if duracion_seg > 5:
        errores.append("Duración excesiva (máx 5s para derecho de cita)")
    if not tiene_fuente:
        errores.append("Falta cita de la fuente (medio/programa/fecha)")
    if not tecnica or tecnica.lower() not in ["framing", "priming", "agenda", "omision"]:
        errores.append("La técnica no está justificada como educativa")
    
    if errores:
        print(f"⚖️ Abogado: RECHAZADO -> {', '.join(errores)}")
        return False
    print(f"⚖️ Abogado: APROBADO (clip de {duracion_seg}s de {medio})")
    return True
