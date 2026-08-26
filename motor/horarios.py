"""
Convierte el texto libre que el dueno escribe con sus horarios de visita
(ej: "Viernes 15:00, Sabado 10:00, Sabado 15:00") en fechas concretas de
los proximos dias, saltando los horarios que ya estan ocupados.

Logica pura: no sabe nada de Telegram ni de Google Sheets. Recibe el
texto y el set de horarios ya ocupados, y devuelve fechas concretas.
"""

import unicodedata
from datetime import date, timedelta

DIAS_SEMANA = {
    "lunes": 0,
    "martes": 1,
    "miercoles": 2,
    "jueves": 3,
    "viernes": 4,
    "sabado": 5,
    "domingo": 6,
}

NOMBRES_DIA_CORTO = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]
NOMBRES_MES_CORTO = [
    "ene", "feb", "mar", "abr", "may", "jun",
    "jul", "ago", "sep", "oct", "nov", "dic",
]


def _sin_tildes(texto: str) -> str:
    forma = unicodedata.normalize("NFD", texto)
    return "".join(c for c in forma if unicodedata.category(c) != "Mn")


def parsear_horarios(texto: str) -> list[tuple[int, str]]:
    """
    "Viernes 15:00, Sabado 10:00" -> [(4, "15:00"), (5, "10:00")]
    Ignora silenciosamente cualquier parte que no se entienda (para no
    tumbar todo si el dueno escribio algo raro en una sola entrada).
    """
    resultado = []
    for parte in texto.split(","):
        parte = parte.strip()
        if not parte:
            continue
        pedazos = parte.split()
        if len(pedazos) != 2:
            continue
        dia_texto, hora_texto = pedazos
        dia_normalizado = _sin_tildes(dia_texto).lower()
        if dia_normalizado not in DIAS_SEMANA:
            continue
        if ":" not in hora_texto:
            continue
        resultado.append((DIAS_SEMANA[dia_normalizado], hora_texto))
    return resultado


def formatear_fecha_corta(fecha: date) -> str:
    return f"{NOMBRES_DIA_CORTO[fecha.weekday()]} {fecha.day} {NOMBRES_MES_CORTO[fecha.month - 1]}"


def proximos_horarios_disponibles(
    horarios_texto: str,
    ocupados: set[tuple[str, str]],
    hoy: date | None = None,
    semanas_adelante: int = 3,
) -> list[tuple[date, str]]:
    """
    Para cada horario que definio el dueno, busca la PRIMERA fecha libre
    (empezando manana) dentro de las proximas `semanas_adelante` semanas.
    Si esa combinacion fecha+hora ya esta ocupada, prueba la semana
    siguiente para ese mismo dia/hora.
    """
    hoy = hoy or date.today()
    slots_definidos = parsear_horarios(horarios_texto)
    disponibles = []

    for dia_semana, hora in slots_definidos:
        dias_hasta_ese_dia = (dia_semana - hoy.weekday()) % 7
        primera_fecha = hoy + timedelta(days=dias_hasta_ese_dia or 7)

        for semana in range(semanas_adelante):
            candidata = primera_fecha + timedelta(weeks=semana)
            if (candidata.isoformat(), hora) not in ocupados:
                disponibles.append((candidata, hora))
                break

    return disponibles
