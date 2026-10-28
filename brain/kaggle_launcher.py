"""Lanzador de notebooks en Kaggle."""
import subprocess, pathlib, json

def lanzar_notebook(nombre, codigo_python):
    nb = {"cells": [{"cell_type": "code", "metadata": {}, "source": codigo_python.split("\n"), "outputs": [], "execution_count": None}],
          "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
          "nbformat": 4, "nbformat_minor": 5}
    root = pathlib.Path(__file__).resolve().parent.parent
    nb_path = root / "sandbox" / (nombre + ".ipynb")
    nb_path.parent.mkdir(parents=True, exist_ok=True)
    nb_path.write_text(json.dumps(nb, indent=2), encoding="utf-8")
    try:
        proc = subprocess.run(["python", "scripts/kaggle_orchestrator.py", str(nb_path)],
                             capture_output=True, text=True, cwd=str(root), timeout=300)
        return "OK: Lanzado.\n" + proc.stdout[-300:] if proc.returncode == 0 else "ERROR: " + proc.stderr[-300:]
    except Exception as e:
        return "ERROR: " + str(e)
