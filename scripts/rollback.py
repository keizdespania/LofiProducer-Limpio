#!/usr/bin/env python3
"""Snapshot pre-pipeline + rollback a cualquier tag."""
import subprocess, sys, pathlib, datetime, os
ROOT = pathlib.Path(__file__).resolve().parent.parent

def snapshot(motivo="pre-pipeline"):
    tag = f"snap-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}-{motivo}"
    subprocess.run(["git", "add", "-A"], cwd=str(ROOT), check=False)
    subprocess.run(["git", "commit", "-m", f"snapshot: {motivo}", "--no-verify"], cwd=str(ROOT), check=False)
    r = subprocess.run(["git", "tag", tag], cwd=str(ROOT), capture_output=True, text=True)
    if r.returncode == 0:
        subprocess.run(["git", "push", "origin", tag], cwd=str(ROOT), capture_output=True, check=False)
        print(f"OK snapshot: {tag}")
        return tag
    return None

def listar():
    r = subprocess.run(["git", "tag", "-l", "snap-*"], cwd=str(ROOT), capture_output=True, text=True)
    tags = sorted(r.stdout.strip().splitlines(), reverse=True)
    if not tags: print("(sin snapshots)"); return
    for t in tags[:15]:
        info = subprocess.run(["git", "log", "-1", "--format=%ci %s", t], cwd=str(ROOT), capture_output=True, text=True)
        print(f"  {t}  {info.stdout.strip()[:100]}")

def rollback(tag):
    if not tag or not tag.startswith("snap-"):
        print("ERROR: tag debe empezar con 'snap-'"); return False
    # Snapshot del estado actual antes de rollback (por si acaso)
    snapshot("pre-rollback")
    r = subprocess.run(["git", "reset", "--hard", tag], cwd=str(ROOT), capture_output=True, text=True)
    if r.returncode == 0:
        subprocess.run(["git", "push", "origin", "main", "--force-with-lease"], cwd=str(ROOT), check=False)
        print(f"OK rollback a {tag}")
        return True
    print(f"ERROR: {r.stderr[:200]}")
    return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: rollback.py {snapshot|listar|rollback <tag>}")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "snapshot": snapshot(sys.argv[2] if len(sys.argv) > 2 else "manual")
    elif cmd == "listar": listar()
    elif cmd == "rollback": sys.exit(0 if rollback(sys.argv[2] if len(sys.argv) > 2 else "") else 1)
