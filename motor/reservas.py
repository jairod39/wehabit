"""
Todo lo relacionado con reservas: agendar una visita/estadia y consultarlas.
Importante: esto NUNCA cobra dinero, solo agenda. El metodo de pago se
muestra aparte, como informacion, no como un cobro automatico.
"""

import uuid
from datetime import date

from motor.models import EstadoReserva
from motor.sheets_client import leer_todas_las_filas, agregar_fila


def crear_reserva(
    propiedad_id: str,
    inquilino_id: str,
    fecha_inicio: date,
    fecha_fin: date,
    extras_elegidos: list[str],
    precio_total: float,
) -> str:
    """Guarda una reserva nueva en estado PENDIENTE y devuelve su id."""
    id_reserva = uuid.uuid4().hex[:8]
    agregar_fila(
        "Reservas",
        [
            id_reserva,
            propiedad_id,
            inquilino_id,
            fecha_inicio.isoformat(),
            fecha_fin.isoformat(),
            ",".join(extras_elegidos),
            precio_total,
            EstadoReserva.PENDIENTE.value,
        ],
    )
    return id_reserva


def listar_reservas_de_inquilino(inquilino_id: str) -> list[dict]:
    """Todas las reservas que ha hecho un inquilino especifico."""
    filas = leer_todas_las_filas("Reservas")
    return [f for f in filas if str(f.get("inquilino_id")) == str(inquilino_id)]


def listar_reservas_de_propiedad(propiedad_id: str) -> list[dict]:
    """Todas las reservas de una propiedad especifica (util para el dueno)."""
    filas = leer_todas_las_filas("Reservas")
    return [f for f in filas if str(f.get("propiedad_id")) == str(propiedad_id)]
