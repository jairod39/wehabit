"""
Modelos de datos del motor de WeHabit.

Filosofia: una Propiedad no sabe si "es" una habitacion o un apartamento.
Solo tiene un campo "tipo" (texto libre) y una lista de "extras" e
"items_calificables" que dependen de ese tipo. Asi, agregar un modulo
nuevo (vehiculos, por ejemplo) no requiere tocar este archivo: solo
se crean propiedades con tipo="vehiculo" y sus propios extras.
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum


class TipoPropiedad(str, Enum):
    """Tipos de propiedad soportados hoy. Agregar uno nuevo es una linea."""
    HABITACION = "habitacion"
    APARTAMENTO = "apartamento"
    CASA = "casa"
    VEHICULO = "vehiculo"


class EstadoReserva(str, Enum):
    PENDIENTE = "pendiente"
    CONFIRMADA = "confirmada"
    COMPLETADA = "completada"
    CANCELADA = "cancelada"


@dataclass
class Extra:
    """Un adicional que el dueno puede ofrecer: internet, comida, lavado, etc."""
    id: str
    nombre: str
    precio_extra: float = 0.0
    incluido_por_defecto: bool = False


@dataclass
class ItemCalificable:
    """Un aspecto que los inquilinos pueden calificar despues de una estadia."""
    id: str
    nombre: str


@dataclass
class Propiedad:
    """
    Una propiedad generica. El campo 'tipo' determina el modulo
    (habitacion, apartamento, vehiculo...) pero la estructura es la misma
    para todos.
    """
    id: str
    tipo: TipoPropiedad
    titulo: str
    descripcion: str
    dueno_id: str
    precio_base: float
    pais: str
    ciudad: str
    ubicacion: str = ""  # link de Waze generado desde la ubicacion compartida en Telegram
    direccion_escrita: str = ""  # direccion en texto, sirve sin necesidad de internet
    metodo_pago: str = ""  # texto informativo, el bot NUNCA cobra directamente
    codigo_casa_arrendamiento: str = ""  # codigo/referencia en la casa de arrendamiento, si aplica
    horarios_visita: str = ""  # horarios que el dueno ofrece para VISITAS, ej "Viernes 15:00, Sabado 10:00"
    disponibilidad: str = ""  # texto libre del dueno sobre disponibilidad de estadia (solo informativo)
    fecha_publicacion: str = ""  # cuando se creo, para medir crecimiento en el tiempo
    destacados: str = ""  # etiquetas elegidas de menu al publicar, separadas por coma
    fotos: list[str] = field(default_factory=list)
    extras_disponibles: list[Extra] = field(default_factory=list)
    items_calificables: list[ItemCalificable] = field(default_factory=list)
    activa: bool = True

    def calcular_precio(self, extras_elegidos: list[str], noches: int) -> float:
        """Suma el precio base + los extras que el usuario eligio, por noches."""
        total = self.precio_base
        for extra in self.extras_disponibles:
            if extra.id in extras_elegidos and not extra.incluido_por_defecto:
                total += extra.precio_extra
        return total * noches


@dataclass
class Reserva:
    """
    Una CITA DE VISITA para conocer la propiedad (no una reserva de
    estadia). Las fechas de estadia (checkin/checkout) son un acuerdo
    directo entre el dueno y el inquilino, no algo que agendamos aqui.
    """
    id: str
    propiedad_id: str
    inquilino_id: str
    fecha_visita: date
    hora_visita: str = ""  # ej "15:30"
    extras_elegidos: list[str] = field(default_factory=list)
    precio_total: float = 0.0
    estado: EstadoReserva = EstadoReserva.PENDIENTE


@dataclass
class Calificacion:
    """
    Calificacion de UN item especifico, hecha por un inquilino que tuvo
    una reserva COMPLETADA. El promedio general se calcula aparte,
    ponderando todos los items calificados de una propiedad.
    """
    id: str
    propiedad_id: str
    reserva_id: str
    inquilino_id: str
    item_id: str
    puntaje: int  # 1 a 5
    comentario: str = ""
