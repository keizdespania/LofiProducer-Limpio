#!/usr/bin/env python3
"""hack_acestep.py — Extrae params de ACE-Step desde AST (sin ejecutar modelo)."""
import ast, json, sys
from pathlib import Path

SRC = Path.home() / "LofiProducer/kaggle_src/acestep_src/acestep/inference.py"
OUT = Path.home() / "LofiProducer/data/agent/acestep_params.json"

def _default_of(node):
    """Resuelve default real, incluyendo field(default=...) y field(default_factory=...)."""
    if node is None:
        return "REQUIRED"
    # field(default=X) o field(default_factory=X)
    if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "field":
        for kw in node.keywords:
            if kw.arg in ("default", "default_factory"):
                return f"field({kw.arg}={ast.unparse(kw.value)})"
        return "field()"
    return ast.unparse(node)

def extract_class(tree, name):
    params = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == name:
            # Herencia: captura nombres de bases
            bases = [ast.unparse(b) for b in node.bases]
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    field = item.target.id
                    typ = ast.unparse(item.annotation) if item.annotation else "?"
                    params[field] = {"type": typ, "default": _default_of(item.value)}
            return {"bases": bases, "fields": params}
    return {"bases": [], "fields": {}}

def main():
    if not SRC.exists():
        print(f"ERROR: no existe {SRC}")
        sys.exit(1)
    tree = ast.parse(SRC.read_text())
    gp = extract_class(tree, "GenerationParams")
    gc = extract_class(tree, "GenerationConfig")
    out = {
        "source": str(SRC),
        "GenerationParams": gp,
        "GenerationConfig": gc,
        "_total_params": len(gp["fields"]) + len(gc["fields"]),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"OK {OUT}")
    print(f"  GenerationParams: {len(gp['fields'])} (bases: {gp['bases']})")
    print(f"  GenerationConfig: {len(gc['fields'])} (bases: {gc['bases']})")
    print(f"  TOTAL: {out['_total_params']}")

if __name__ == "__main__":
    main()
