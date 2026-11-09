REDES = {
    "youtube": "youtube.com/@somoselencuadre.oficial",
    "tiktok": "tiktok.com/@somoselencuadre",
    "instagram": "instagram.com/somoselencuadre",
    "x": "x.com/SomosElEncuadre",
    "threads": "threads.net/@somoselencuadre",
    "telegram": "t.me/somoselencuadre",
    "web": "elencuadre.pages.dev",
}
F = {
    "x": "\n\n📺 {youtube}\n📄 {web}",
    "threads": "\n\n📺 {youtube}\n📸 {instagram}\n📩 {telegram}\n📄 {web}",
    "instagram": "\n\n📺 {youtube}\n🎵 {tiktok}\n📩 {telegram}\n🔗 Link en bio",
    "tiktok": "\n\n📩 {telegram}\n📄 {web}",
    "youtube_comunidad": "\n\n📱 {tiktok}\n📸 {instagram}\n🐦 {x}\n📩 {telegram}",
    "linkedin": "\n\n📺 {youtube}\n📄 {web}\n📩 {telegram}",
}
def footer(red):
    return F.get(red, "\n\n📄 {web}").format(**REDES)
