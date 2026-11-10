#!/usr/bin/env python3
"""Genera redes_{fecha}_cruzadas.json con textos + links cruzados entre largo/shorts/posts."""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
BASE_URL = "https://elencuadre.pages.dev"

def _load(fecha):
    data = {"redes": {}, "prod": {}, "seo": {}, "yt": {}}
    for key, fname in [
        ("redes", f"redes_{fecha}.json"),
        ("prod", f"produccion_{fecha}.json"),
        ("seo", f"seo_{fecha}.json"),
    ]:
        p = OUT / fname
        if p.exists():
            try: data[key] = json.loads(p.read_text())
            except: pass
    p_yt = ROOT / "data" / "agent" / f"youtube_urls_{fecha}.json"
    if p_yt.exists():
        try: data["yt"] = json.loads(p_yt.read_text())
        except: pass
    return data

def _primer_comentario_short(hook, link_largo, link_post, fecha):
    """Genera primer_comentario YouTube para un short (cross-traffic)."""
    txt = f"🔥 {(hook or '').strip()[:180]}\n\n"
    if link_largo: txt += f"🎬 El análisis completo del día: {link_largo}\n"
    if link_post and link_post != link_largo:
        txt += f"📊 Post completo: {link_post}\n"
    txt += "\n💬 ¿Has visto esto en los medios que lees?\n\n"
    txt += "#ElEncuadre #Shorts #AnálisisMediático #Framing #Prensa"
    return txt


def _link_yt(video_id):
    return f"https://youtu.be/{video_id}" if video_id else None

def _build(fecha):
    d = _load(fecha)
    redes = d["redes"]
    prod = d["prod"]
    seo = d["seo"]
    yt = d["yt"]
    dossier = prod.get("dossier", {})
    titular = dossier.get("titular_brutal", "El Encuadre del día")[:80]

    # Links base
    yt_largo = _link_yt((yt.get("largo") or {}).get("video_id"))
    yt_shorts = [_link_yt(s.get("video_id")) for s in (yt.get("shorts") or [])]
    post_largo = f"{BASE_URL}/analisis/{fecha}-largo/"
    post_dossier = f"{BASE_URL}/analisis/{fecha}-dossier-v2/"
    post_mediano = f"{BASE_URL}/analisis/{fecha}-mediano-medio_crudo/"
    web_home = BASE_URL

    # ═══ LARGO ═══
    seo_largo = seo.get("largo", {})
    tit_largo = seo_largo.get("titulo", titular)
    largo = {
        "num": 0,
        "tipo": "largo",
        "titulo": tit_largo,
        "video_id": (yt.get("largo") or {}).get("video_id"),
        "link_yt": yt_largo,
        "link_post": post_largo,
        "link_dossier": post_dossier,
        "redes": {
            "x": {
                "texto": f"📺 {titular}\n\nDescubre cómo los medios construyen el relato del día.\n\n🎬 {yt_largo or '(YT largo)'}\n📄 Análisis completo: {post_largo}\n\n#ElEncuadre #AnálisisMediático",
            },
            "threads": {
                "texto": f"📺 VÍDEO COMPLETO: {titular}\n\nHoy analizamos las técnicas que han usado los medios para venderte el relato. Sin filtros.\n\n▶ {yt_largo or '(YT largo)'}\n📄 {post_largo}",
            },
            "instagram": {
                "texto": f"📺 {titular}\n\nAnálisis técnico completo. Link en bio.\n\n#ElEncuadre #MediosLibres #AnálisisMediático #Framing",
            },
            "youtube_comunidad": {
                "texto": f"📢 NUEVO VÍDEO: {titular}\n\nAnalizamos las técnicas mediáticas del día. ¿Quién controla tu relato?\n\n▶ {yt_largo or ''}",
            },
        },
    }

    # ═══ SHORTS ═══
    shorts = []
    raw_shorts = redes.get("shorts", [])
    prod_shorts = prod.get("shorts_finales", [])
    seo_shorts = seo.get("shorts", [])
    for i, s in enumerate(raw_shorts):
        num = s.get("id", i+1)
        p_s = prod_shorts[i] if i < len(prod_shorts) else {}
        seo_s = seo_shorts[i] if i < len(seo_shorts) else {}
        yt_s_link = yt_shorts[i] if i < len(yt_shorts) else None
        tipo = p_s.get("tipo", "")
        hook = p_s.get("hook", "")[:120]
        tit_s = seo_s.get("titulo", hook or f"Short {num}")

        redes_s = {}
        for red in ["youtube", "tiktok", "instagram", "x", "threads"]:
            r = s.get(red, {})
            if not r: continue
            texto = r.get("texto") or r.get("descripcion") or ""
            # Añadir link cruzado al largo o al post si existe
            if yt_largo and red in ("x", "threads"):
                texto = texto.rstrip() + f"\n\n🔗 Vídeo completo: {yt_largo}"
            elif post_largo and red in ("tiktok", "instagram"):
                texto = texto.rstrip() + f"\n\n📄 Análisis completo en elencuadre.pages.dev"
            redes_s[red] = {
                "texto": texto,
                "hashtags": r.get("hashtags", ""),
                "titulo": r.get("titulo", tit_s) if red == "youtube" else None,
                "tags": r.get("tags", []) if red == "youtube" else [],
                "primer_comentario": _primer_comentario_short(tit_s, yt_largo, post_largo, fecha) if red == "youtube" else None,
            }
            if red == "youtube":
                redes_s[red]["primer_comentario"] = r.get("primer_comentario", "")

        shorts.append({
            "num": num,
            "tipo": tipo,
            "titulo": tit_s,
            "hook": hook,
            "video_id": (yt.get("shorts") or [{}]*4)[i].get("video_id") if i < len(yt.get("shorts") or []) else None,
            "link_yt": yt_s_link,
            "link_largo": yt_largo,
            "link_post": post_largo,
            "redes": redes_s,
        })

    # ═══ POSTS (los 3 del blog) ═══
    posts = []
    post_defs = [
        ("largo", "Análisis Largo", post_largo, seo_largo.get("titulo", titular)),
        ("dossier", "Dossier Ejecutivo", post_dossier, dossier.get("titular_brutal", "Dossier del día")),
        ("mediano", "Análisis Mediano", post_mediano, seo.get("mediano", {}).get("titulo", "Análisis mediano")),
    ]
    for slug, tipo_post, url, titulo_post in post_defs:
        # Linkear al short más relacionado (por tipo o primero)
        short_link = yt_shorts[0] if yt_shorts else None
        posts.append({
            "slug": slug,
            "tipo": tipo_post,
            "titulo": titulo_post[:120],
            "url": url,
            "link_short": short_link,
            "link_yt_largo": yt_largo,
            "redes": {
                "x": {"texto": f"📄 {titulo_post[:100]}\n\nAnálisis técnico completo en el blog.\n\n{url}\n\n🎬 {yt_largo or ''}\n\n#ElEncuadre #AnálisisMediático"},
                "threads": {"texto": f"Nuevo artículo: {titulo_post[:80]}\n\nDesmontamos las técnicas mediáticas del día. Sin filtros.\n\n📄 {url}"},
                "instagram": {"texto": f"📰 {titulo_post[:80]}\n\nLink en bio para análisis completo.\n\n#ElEncuadre #Medios #Análisis"},
                "linkedin": {"texto": f"Interesante análisis técnico sobre framing mediático:\n\n{titulo_post[:100]}\n\n{url}"},
            },
        })

    return {
        "fecha": fecha,
        "largo": largo,
        "shorts": shorts,
        "posts": posts,
        "links_globales": {
            "yt_largo": yt_largo,
            "yt_shorts": yt_shorts,
            "web": web_home,
            "post_largo": post_largo,
            "post_dossier": post_dossier,
            "post_mediano": post_mediano,
        },
    }

if __name__ == "__main__":
    fecha = sys.argv[1] if len(sys.argv) > 1 else None
    if not fecha:
        import datetime
        fecha = datetime.date.today().isoformat()
    result = _build(fecha)
    out = OUT / f"redes_{fecha}_cruzadas.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"OK {out.name}: largo+{len(result['shorts'])} shorts+{len(result['posts'])} posts")
