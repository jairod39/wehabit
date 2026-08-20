"""
Unico lugar del proyecto que lee el archivo .env.
Todo lo demas le pide las claves a este archivo, nunca lee el .env directo.
"""

import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "credenciales_google.json")
# Alternativa mas segura para hosting en la nube: pegar el contenido COMPLETO
# del archivo JSON de credenciales como un secreto de texto, en vez de subir
# el archivo. Si esta presente, tiene prioridad sobre GOOGLE_CREDENTIALS_PATH.
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")


def validar_configuracion() -> None:
    """Revisa que las claves necesarias existan antes de arrancar el bot."""
    faltantes = []
    if not TELEGRAM_BOT_TOKEN:
        faltantes.append("TELEGRAM_BOT_TOKEN")
    if not GOOGLE_SHEET_ID:
        faltantes.append("GOOGLE_SHEET_ID")

    if faltantes:
        raise RuntimeError(
            "Faltan estas claves en tu archivo .env: " + ", ".join(faltantes) +
            "\nRevisa .env.example para ver que necesitas."
        )
