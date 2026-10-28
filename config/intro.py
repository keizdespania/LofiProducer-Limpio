"""
Configuracion de la intro KZ.

Ajusta estos valores sin tocar el codigo de la fase.
"""

from pathlib import Path

# --- Rutas ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BRANDING_DIR = PROJECT_ROOT / "assets" / "branding"
INTRO_DIR = PROJECT_ROOT / "assets" / "intro"

LOGO_PATH = BRANDING_DIR / "logo_kz.png"
PORTADA_PATH = BRANDING_DIR / "portada_referencia.jpg"
INTRO_OUTPUT = INTRO_DIR / "intro_kz.mp4"

# --- Video ---
ANCHO = 1920
ALTO = 1080
FPS = 30
DURACION = 5.0

# --- Blur de fondo ---
BLUR_RADIUS = 25
BLUR_POWER = 3
OSCURECER = 0.35           # 0.35 = sutil, deja ver la portada

# --- Logo ---
# Logo es 1679x937 (ratio 1.79). A 1100px ancho queda 1100x614.
# Deja 410px a cada lado y 233px arriba/abajo.
LOGO_ANCHO = 1100
LOGO_FADE_IN_START = 0.5
LOGO_FADE_IN_DUR = 1.5
LOGO_FADE_OUT_START = 4.2
LOGO_FADE_OUT_DUR = 0.6

# --- Vineta (opcional) ---
VINETA = True
VINETA_ANGULO = "PI/4"

# --- Transiciones globales ---
FADE_IN_DUR = 0.7
FADE_OUT_DUR = 0.5

# --- Audio (opcional) ---
# None = silencio. Ruta a .mp3/.wav para pad de intro.
AUDIO_INTRO = None	
