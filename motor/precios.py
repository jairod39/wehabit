"""
Todo lo relacionado con calcular precios. Solo hace cuentas: no sabe
nada de Telegram ni de Google Sheets.
"""

from motor.models import Propiedad


def calcular_total(propiedad: Propiedad, extras_elegidos: list[str], noches: int) -> float:
    """Precio final: base + extras elegidos que no vengan incluidos, por noches."""
    return propiedad.calcular_precio(extras_elegidos, noches)


def generar_desglose(propiedad: Propiedad, extras_elegidos: list[str], noches: int) -> list[str]:
    """Lista de lineas de texto explicando de donde sale el precio final,
    para mostrarsela al usuario antes de agendar (transparencia total)."""
    lineas = [f"Precio base por noche: {propiedad.precio_base}"]
    for extra in propiedad.extras_disponibles:
        if extra.incluido_por_defecto:
            lineas.append(f"{extra.nombre}: incluido")
        elif extra.id in extras_elegidos:
            lineas.append(f"{extra.nombre}: +{extra.precio_extra} por noche")
    lineas.append(f"Noches: {noches}")
    lineas.append(f"Total: {calcular_total(propiedad, extras_elegidos, noches)}")
    return lineas


def es_full(propiedad: Propiedad) -> bool:
    """
    Una propiedad se considera 'Full' (todo incluido) cuando TODOS sus
    extras disponibles vienen marcados como incluidos por defecto.
    Esto se calcula solo, el dueno no tiene que marcar nada aparte.
    """
    if not propiedad.extras_disponibles:
        return False
    return all(extra.incluido_por_defecto for extra in propiedad.extras_disponibles)
