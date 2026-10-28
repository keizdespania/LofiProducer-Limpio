"""Compresor de prompts sin dependencias externas (reemplaza tokenpruner)."""
import re

def comprimir(texto: str, max_chars: int = 3000) -> str:
    """Comprime texto: deduplica líneas, quita espacios extra, trunca."""
    if not texto:
        return texto
    # 1. Quitar espacios múltiples
    texto = re.sub(r'[ \t]+', ' ', texto)
    # 2. Quitar líneas en blanco repetidas
    texto = re.sub(r'\n{3,}', '\n\n', texto)
    # 3. Deduplicar líneas idénticas consecutivas
    lineas = texto.split('\n')
    unicas = []
    for l in lineas:
        if not unicas or unicas[-1].strip() != l.strip():
            unicas.append(l)
    texto = '\n'.join(unicas)
    # 4. Truncar si es enorme
    if len(texto) > max_chars:
        texto = texto[:max_chars] + "\n[...truncado]"
    return texto

def comprimir_mensajes(messages: list) -> list:
    """Comprime los contenidos user de una conversación."""
    if not messages:
        return messages
    result = []
    for m in messages:
        if m.get("role") == "user" and isinstance(m.get("content"), str):
            result.append({"role": m["role"], "content": comprimir(m["content"])})
        else:
            result.append(m)
    return result
