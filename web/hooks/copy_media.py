"""on_pre_build: copia web/media -> web/docs/media para que MkDocs empaquete las imagenes."""
import shutil
from pathlib import Path

def on_pre_build(config, **kwargs):
    src = Path(__file__).resolve().parent.parent / "media"
    dst = Path(__file__).resolve().parent.parent / "docs" / "media"
    if not src.is_dir():
        return
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    print(f"[copy_media] {sum(1 for _ in dst.rglob('*') if _.is_file())} ficheros -> web/docs/media/")
