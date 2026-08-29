"""
Unico archivo del proyecto que importa gspread y habla directo con
Google Sheets. Todo lo demas le pide datos a este archivo, nunca
a Google Sheets directamente. Asi, si el dia de manana cambiamos de
Google Sheets a otra base de datos, solo hay que reescribir ESTE archivo.
"""

import json

import gspread
from google.oauth2.service_account import Credentials

from motor.config import GOOGLE_SHEET_ID, GOOGLE_CREDENTIALS_PATH, GOOGLE_CREDENTIALS_JSON

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]

_cliente = None
_hoja = None


def _conectar():
    """Crea la conexion una sola vez y la reutiliza (no reconecta en cada llamada)."""
    global _cliente, _hoja
    if _hoja is None:
        if GOOGLE_CREDENTIALS_JSON:
            info = json.loads(GOOGLE_CREDENTIALS_JSON)
            credenciales = Credentials.from_service_account_info(info, scopes=SCOPES)
        else:
            credenciales = Credentials.from_service_account_file(
                GOOGLE_CREDENTIALS_PATH, scopes=SCOPES
            )
        _cliente = gspread.authorize(credenciales)
        _hoja = _cliente.open_by_key(GOOGLE_SHEET_ID)
    return _hoja


def obtener_pestana(nombre: str):
    """Devuelve una pestana (worksheet) por nombre: 'Propiedades', 'Extras', etc."""
    return _conectar().worksheet(nombre)


def leer_todas_las_filas(nombre_pestana: str) -> list[dict]:
    """Lee todas las filas de una pestana como una lista de diccionarios
    (usa la fila 1, los encabezados, como llaves)."""
    pestana = obtener_pestana(nombre_pestana)
    return pestana.get_all_records()


def agregar_fila(nombre_pestana: str, valores: list) -> None:
    """Agrega una fila nueva al final de una pestana."""
    pestana = obtener_pestana(nombre_pestana)
    pestana.append_row(valores, value_input_option="USER_ENTERED")


def actualizar_celda_por_id(
    nombre_pestana: str, id_valor: str, columna_id: str, columna_objetivo: str, valor_nuevo
) -> bool:
    """Busca la fila cuyo 'columna_id' coincide con id_valor, y le
    actualiza SOLO la celda de 'columna_objetivo'. Devuelve False si no
    encontro la fila (para que quien llama pueda avisar, no fallar en
    silencio)."""
    pestana = obtener_pestana(nombre_pestana)
    encabezados = pestana.row_values(1)
    if columna_id not in encabezados or columna_objetivo not in encabezados:
        return False
    col_id_idx = encabezados.index(columna_id) + 1
    col_objetivo_idx = encabezados.index(columna_objetivo) + 1

    valores_columna_id = pestana.col_values(col_id_idx)
    for fila_num, valor in enumerate(valores_columna_id[1:], start=2):
        if str(valor) == str(id_valor):
            pestana.update_cell(fila_num, col_objetivo_idx, valor_nuevo)
            return True
    return False
