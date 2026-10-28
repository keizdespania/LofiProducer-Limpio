import secrets
import string


def generar_contrasena(longitud: int = 16) -> str:
    caracteres = string.ascii_letters + string.digits + string.punctuation
    # Evitamos ambigüedades eliminando algunos caracteres problemáticos (opcional)
    # pero mantenemos variación suficiente.
    caracteres = caracteres.replace('"', '').replace("'", '')
    return ''.join(secrets.choice(caracteres) for _ in range(longitud))


def main() -> None:
    pwd = generar_contrasena(16)
    print(pwd)


if __name__ == "__main__":
    main()
