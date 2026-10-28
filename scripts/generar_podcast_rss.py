"""generar_podcast_rss.py - Genera el feed RSS para Spotify/Apple Podcasts."""
import pathlib, datetime, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "web" / "docs" / "podcast"
OUT.mkdir(parents=True, exist_ok=True)
fecha = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()

rss = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
<channel>
    <title>Somos El Encuadre</title>
    <link>https://elencuadre.pages.dev</link>
    <description>Analisis diario de manipulacion mediatica.</description>
    <language>es-es</language>
    <item>
        <title>Analisis {fecha}</title>
        <enclosure url="https://elencuadre.pages.dev/output/encuadre/voz_largo_{fecha}.mp3" type="audio/mpeg"/>
        <pubDate>{datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate>
    </item>
</channel>
</rss>'''
(OUT / "feed.xml").write_text(rss)
print(f"RSS generado en {OUT}/feed.xml")
