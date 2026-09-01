"""
Metricas reales, sacadas de interacciones de verdad (no un conteo
estatico): cada vez que alguien ve el detalle de una propiedad, queda
una fila en la pestana 'Vistas'. Con eso, mas las Propiedades y
Reservas que ya existian, se arma el resumen del panel.
"""

from datetime import datetime
from collections import Counter

from motor.sheets_client import (
    agregar_fila_con_creacion,
    leer_todas_las_filas,
    leer_todas_las_filas_seguro,
)

ENCABEZADOS_VISTAS = ["propiedad_id", "usuario_id", "fecha"]


def registrar_vista(propiedad_id: str, usuario_id: str) -> None:
    """Guarda que un usuario especifico vio el detalle de una propiedad.
    Guardar QUIEN vio (no solo cuantas veces) es la base para poder
    armar mas adelante el recorrido de un usuario: que vio, en que
    orden, y si termino agendando. Sin esto no hay perfil que armar,
    solo conteos sueltos.

    'mejor esfuerzo': si falla, no debe tumbar la experiencia del
    usuario viendo la propiedad (eso se maneja en quien la llama)."""
    agregar_fila_con_creacion(
        "Vistas",
        ENCABEZADOS_VISTAS,
        [propiedad_id, usuario_id, datetime.now().strftime("%Y-%m-%d %H:%M")],
    )


def recorrido_de_usuario(usuario_id: str) -> list[dict]:
    """
    Todas las vistas de un usuario especifico, en orden. Esta es la
    base de datos cruda para el futuro 'perfil de comprador': que vio,
    en que orden, cuando. Por ahora solo la expone, no la analiza.
    """
    filas = leer_todas_las_filas_seguro("Vistas")
    return [f for f in filas if str(f.get("usuario_id", "")) == str(usuario_id)]


def resumen_panel() -> dict:
    """
    Arma un resumen simple pero con datos reales:
    - conteo de propiedades por estado/tipo/pais
    - conteo de reservas por estado
    - top 5 propiedades mas vistas, con su titulo
    """
    filas_propiedades = leer_todas_las_filas("Propiedades")
    filas_reservas = leer_todas_las_filas_seguro("Reservas")
    filas_vistas = leer_todas_las_filas_seguro("Vistas")

    activas = sum(1 for f in filas_propiedades if str(f.get("activa", "")).strip().upper() == "TRUE")
    inactivas = len(filas_propiedades) - activas

    por_tipo = Counter(f.get("tipo", "sin tipo") for f in filas_propiedades)
    por_pais = Counter(f.get("pais", "sin pais") for f in filas_propiedades if f.get("pais"))

    por_estado_reserva = Counter(f.get("estado", "sin estado") for f in filas_reservas)

    conteo_vistas = Counter(f.get("propiedad_id") for f in filas_vistas if f.get("propiedad_id"))
    titulos_por_id = {f.get("id"): f.get("titulo", "") for f in filas_propiedades}
    top_vistas = [
        (titulos_por_id.get(pid, pid), cantidad)
        for pid, cantidad in conteo_vistas.most_common(5)
    ]

    return {
        "total_propiedades": len(filas_propiedades),
        "activas": activas,
        "inactivas": inactivas,
        "por_tipo": dict(por_tipo),
        "por_pais": dict(por_pais.most_common(10)),
        "total_reservas": len(filas_reservas),
        "por_estado_reserva": dict(por_estado_reserva),
        "top_vistas": top_vistas,
    }
