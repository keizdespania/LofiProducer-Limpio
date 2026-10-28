"""detector_evergreen.py - Recalienta posts antiguos."""
import pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
POSTS = ROOT / "web" / "docs" / "analisis"
print(f"✅ {len(list(POSTS.glob('*.md')))} posts detectados para revisión evergreen.")
