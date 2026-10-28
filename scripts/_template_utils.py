"""Helper unificado para rellenar templates Kaggle."""
import re


def fill_template(code, replacements):
    for name, val in replacements.items():
        code = code.replace(f'__{name}__', str(val))
    remaining = re.findall(r'__[A-Z][A-Z0-9_]+__', code)
    if remaining:
        raise ValueError(f'Placeholders sin rellenar: {set(remaining)}')
    try:
        compile(code, '<kernel>', 'exec')
    except SyntaxError as e:
        raise ValueError(f'Kernel no compila: {e}')
    return code
