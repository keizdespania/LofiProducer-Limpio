"""Test completo de pykokoro: verifica, instala dependencias y genera audio."""
import subprocess, sys, pathlib, time

def check_install(pkg, import_name=None):
    import_name = import_name or pkg
    try:
        __import__(import_name)
        print(f"✅ {pkg} ya instalado")
        return True
    except ImportError:
        print(f"⚠️  {pkg} NO instalado. Instalando...")
        r = subprocess.run([sys.executable, "-m", "pip", "install", pkg],
                          capture_output=True, text=True, timeout=300)
        if r.returncode == 0:
            print(f"✅ {pkg} instalado correctamente")
            return True
        else:
            print(f"❌ Error instalando {pkg}: {r.stderr[-300:]}")
            return False

# 1. Verificar dependencias
print("═══ 1. Verificando dependencias ═══")
if not check_install("pykokoro"):
    sys.exit(1)
if not check_install("soundfile"):
    sys.exit(1)

# 2. Generar audio
print("\n═══ 2. Generando audio de prueba ═══")
from pykokoro import KokoroPipeline, PipelineConfig
import soundfile as sf

out_dir = pathlib.Path("output/audios")
out_dir.mkdir(parents=True, exist_ok=True)
out_file = out_dir / f"test_voz_{int(time.time())}.wav"

print("Cargando modelo (primera vez descarga ~170MB)...")
inicio = time.time()

try:
    pipe = KokoroPipeline(PipelineConfig(voice="af_heart", model_quality="q8"))
    print(f"Modelo cargado en {time.time() - inicio:.1f}s")
    
    texto = "Hola Arquitecto. Soy el Dios de la Construccion. Mi voz local funciona correctamente en Termux."
    print(f"Generando audio: '{texto[:50]}...'")
    
    t2 = time.time()
    res = pipe.run(texto)
    print(f"Audio generado en {time.time() - t2:.1f}s")
    
    sf.write(str(out_file), res.audio, res.sample_rate)
    size_kb = out_file.stat().st_size / 1024
    print(f"\n✅ AUDIO GUARDADO: {out_file} ({size_kb:.1f} KB)")
    print(f"   Duracion: {len(res.audio) / res.sample_rate:.1f}s")
    print(f"   Sample rate: {res.sample_rate} Hz")
    print(f"   Tiempo total: {time.time() - inicio:.1f}s")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
