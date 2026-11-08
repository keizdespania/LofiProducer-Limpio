"""_figuras_helper.py - Inyección Top-1 de 3 figuras (hero + 2 inline)."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def cargar_imgs(fecha, tipo):
    p = ROOT / "web" / "media" / "imagenes" / f"web_urls_{fecha}.json"
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text()).get(tipo, [])[:3]
    except Exception:
        return []


def _fig(name, caption, eager=False):
    if not name:
        return ""
    load = 'loading="eager"' if eager else 'loading="lazy"'
    fp = ' fetchpriority="high"' if eager else ""
    cap = (
        '<figcaption style="font-size:0.85em;color:#888;text-align:center;'
        'margin-top:0.5em;font-style:italic;">' + caption + '</figcaption>'
    ) if caption else ""
    alt = re.sub(r'["<>]', "", caption or "Analisis")[:80]
    return (
        '<figure style="margin:1.5em 0;">'
        '<img src="../../media/imagenes/' + name + '" alt="' + alt + '" '
        'width="832" height="480" '
        'style="width:100%;border-radius:8px;aspect-ratio:16/9;object-fit:cover;" '
        + load + fp + ' decoding="async">' + cap + '</figure>'
    )


def _prev_h2(html, pos):
    matches = list(re.finditer(r"<h2[^>]*>(.*?)</h2>", html[:pos], re.DOTALL))
    if not matches:
        return ""
    return re.sub(r"<[^>]+>", "", matches[-1].group(1)).strip()[:80]


def _next_h2(html, pos):
    m = re.search(r"<h2[^>]*>(.*?)</h2>", html[pos:], re.DOTALL)
    if not m:
        return ""
    return re.sub(r"<[^>]+>", "", m.group(1)).strip()[:80]


def construir_hero_e_inline(html, imgs, tema):
    if not imgs:
        return "", html
    hero = _fig(imgs[0], tema[:60], eager=True)
    if len(imgs) < 2:
        return hero, html
    cierre = html.find("</h2>")
    if cierre < 0:
        return hero, html
    pos_a = cierre + 5
    cap_a = _prev_h2(html, pos_a) or "Contexto"
    fig_a = _fig(imgs[1], cap_a)
    html = html[:pos_a] + "\n" + fig_a + "\n" + html[pos_a:]
    if len(imgs) >= 3:
        last_h2 = html.rfind("<h2")
        if last_h2 > 0:
            cap_b = _next_h2(html, last_h2) or "Cierre"
            fig_b = _fig(imgs[2], cap_b)
            html = html[:last_h2] + fig_b + "\n" + html[last_h2:]
    return hero, html
