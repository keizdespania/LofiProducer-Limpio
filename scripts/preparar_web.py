import shutil, datetime, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS, MKDOCS = ROOT / "docs", ROOT / "mkdocs.yml"
LANGS = ("en", "fr", "de", "pt")
ROOT_REP = {"](./analisis/)": "](analisis/index.md)", "](./contacto/)": "](contacto.md)", "](./)": "](index.md)"}

def backup():
    bak = Path.home() / f"web_bak_{datetime.datetime.now():%Y%m%d_%H%M%S}"
    bak.mkdir(parents=True, exist_ok=True)
    if MKDOCS.exists(): shutil.copy2(MKDOCS, bak / "mkdocs.yml")
    for s in ("analisis", "noticias", *LANGS):
        if (DOCS / s).exists(): shutil.copytree(DOCS / s, bak / "docs" / s)
    print(f"[BACKUP] {bak}")

def fix_rel(m, md: Path):
    rel = m.group(1)
    if not rel.endswith("/") or rel.startswith(("http://", "https://", "#")): return m.group(0)
    cand = (md.parent / rel.rstrip("/")).with_suffix(".md")
    if cand.exists(): return f"]({rel.rstrip('/')}.md)"
    idx = md.parent / rel / "index.md"
    return f"]({rel}index.md)" if idx.exists() else m.group(0)

def fix_links(md: Path):
    txt = md.read_text(encoding="utf-8", errors="ignore")
    pref = "../" * (len(md.relative_to(DOCS).parts) - 1)
    new = re.sub(r'(\]\()/(assets|media)/', rf'\1{pref}\2/', txt)
    new = re.sub(r'(src=["\'])/(assets|media)/', rf'\1{pref}\2/', new)
    if md.parent == DOCS:
        for k, v in ROOT_REP.items(): new = new.replace(k, v)
    elif md.relative_to(DOCS).parts[0] in LANGS:
        new = re.sub(r"\]\((\.\./[^\)\s#]+/)\)", lambda m: fix_rel(m, md), new)
    if new != txt:
        md.write_text(new, encoding="utf-8")
        return 1
    return 0

def main():
    backup()
    print("[LINKS]", sum(fix_links(m) for m in DOCS.rglob("*.md")))
    es_a = {p.relative_to(DOCS / "analisis") for p in (DOCS / "analisis").rglob("*.md") if p.name != "index.md"} if (DOCS / "analisis").exists() else set()
    for l in LANGS:
        ld = DOCS / l
        mds = list(ld.rglob("*.md")) if ld.exists() else []
        ha = {p.relative_to(ld / "analisis") for p in (ld / "analisis").rglob("*.md") if p.name != "index.md"} if (ld / "analisis").exists() else set()
        print(f"  [{l}] total={len(mds)} | faltan_analisis={len(es_a - ha)}")

if __name__ == "__main__": main()
