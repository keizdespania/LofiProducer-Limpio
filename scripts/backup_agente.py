"""Cajon 105.C - Gestion de backups del agente con TTL de 48h."""
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKUP_DIR = ROOT / "data" / "agent" / "backups"
TTL_HORAS = 48


def hacer_backup(path_original: Path) -> str:
    """Copia un archivo a la carpeta de backups con timestamp."""
    if not path_original.exists():
        return "No existia, nada que respaldar."
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre = f"{timestamp}_{path_original.name}"
    destino = BACKUP_DIR / nombre
    
    shutil.copy2(path_original, destino)
    return str(destino)


def limpiar_backups_viejos() -> int:
    """Borra los backups de mas de 48 horas. Devuelve cuantos borro."""
    ahora = time.time()
    limite = ahora - (TTL_HORAS * 3600)
    borrados = 0
    
    for f in BACKUP_DIR.glob("*"):
        if f.is_file() and f.stat().st_mtime < limite:
            f.unlink()
            borrados += 1
            
    return borrados

if __name__ == "__main__":
    print(f"Limpiando backups de mas de {TTL_HORAS}h...")
    n = limpiar_backups_viejos()
    print(f"✅ {n} backups eliminados.")
