"""Configuracion del outro KZ."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BRANDING_DIR = PROJECT_ROOT / "assets" / "branding"
OUTRO_DIR = PROJECT_ROOT / "assets" / "outro"

LOGO_PATH = BRANDING_DIR / "logo_kz.png"
PORTADA_PATH = BRANDING_DIR / "portada_referencia.jpg"
TEXTO_PNG = OUTRO_DIR / "texto_outro.png"
OUTRO_OUTPUT = OUTRO_DIR / "outro_kz.mp4"

ANCHO = 1920
ALTO = 1080
FPS = 30
DURACION = 6.0

BLUR_RADIUS = 30
BLUR_POWER = 3
OSCURECER = 0.55

# Logo
LOGO_ANCHO = 750
LOGO_Y_OFFSET = -120        # negativo = arriba del centro
LOGO_FADE_IN_START = 0.5
LOGO_FADE_IN_DUR = 1.0
LOGO_FADE_OUT_START = 5.0
LOGO_FADE_OUT_DUR = 0.7

# Texto (posiciones verticales absolutas)
TEXTO_1 = "THANKS FOR LISTENING"
TEXTO_2 = "Subscribe for more beats"
FUENTE = "Montserrat-ExtraBold.ttf"
TAM_TEXTO_1 = 58
TAM_TEXTO_2 = 36
Y_TEXTO_1 = 700
Y_TEXTO_2 = 790
TEXTO_FADE_IN_START = 1.2
TEXTO_FADE_IN_DUR = 0.9

VINETA = True
VINETA_ANGULO = "PI/4"

FADE_IN_DUR = 0.5
FADE_OUT_DUR = 0.8

AUDIO_OUTRO = None
