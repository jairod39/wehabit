"""
Todo lo relacionado con citas de visita: agendarlas y consultarlas.
Importante: esto NUNCA cobra dinero, solo agenda. El metodo de pago se
muestra aparte, como informacion, no como un cobro automatico.

Las fechas de ESTADIA (checkin/checkout) no se manejan aqui: eso es un
acuerdo directo entre el dueno y el inquilino. Aqui solo agendamos la
CITA para conocer la propiedad.
"""

import uuid
from datetime import date

from motor.models import EstadoReserva
from motor.sheets_client import leer_todas_las_filas, agregar_fila


def crear_reserva(
    propiedad_id: str,
    inquilino_id: str,
    fecha_visita: date,
    hora_visita: str,
    extras_elegidos: list[str],
    precio_total: float,
    estado: EstadoReserva = EstadoReserva.PENDIENTE,
) -> str:
    """Guarda una cita de visita nueva y devuelve su id."""
    id_reserva = uuid.uuid4().hex[:8]
    agregar_fila(
        "Reservas",
        [
            id_reserva,
            propiedad_id,
            inquilino_id,
            fecha_visita.isoformat(),
            hora_visita,
            ",".join(extras_elegidos),
            precio_total,
            estado.value,
        ],
    )
    return id_reserva


def listar_reservas_de_inquilino(inquilino_id: str) -> list[dict]:
    """Todas las citas que ha agendado un inquilino especifico."""
    filas = leer_todas_las_filas("Reservas")
    return [f for f in filas if str(f.get("inquilino_id")) == str(inquilino_id)]


def listar_reservas_de_propiedad(propiedad_id: str) -> list[dict]:
    """Todas las citas de una propiedad especifica (util para el dueno)."""
    filas = leer_todas_las_filas("Reservas")
    return [f for f in filas if str(f.get("propiedad_id")) == str(propiedad_id)]


def horarios_ocupados(propiedad_id: str) -> set[tuple[str, str]]:
    """
    Pares (fecha_visita, hora_visita) ya agendados para esa propiedad,
    sin contar las citas canceladas. Sirve para no ofrecer un horario
    que ya esta tomado.
    """
    filas = listar_reservas_de_propiedad(propiedad_id)
    return {
        (f.get("fecha_visita", ""), f.get("hora_visita", ""))
        for f in filas
        if f.get("estado") != EstadoReserva.CANCELADA.value
    }
