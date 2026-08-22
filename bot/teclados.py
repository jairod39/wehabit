"""
Construye los botones (InlineKeyboardMarkup) que usa el bot.
Separado de la logica de conversacion para que cada archivo tenga
una sola responsabilidad.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from motor.models import Propiedad, TipoPropiedad
from motor.precios import es_full
from bot import textos


def teclado_menu_principal() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(textos.BOTON_EXPLORAR, callback_data="menu:explorar")],
        [InlineKeyboardButton(textos.BOTON_PUBLICAR, callback_data="menu:publicar")],
    ])


def teclado_volver_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(textos.BOTON_VOLVER, callback_data="menu:volver")],
    ])


def teclado_tipos() -> InlineKeyboardMarkup:
    filas = [
        [InlineKeyboardButton(tipo.value.capitalize(), callback_data=f"tipo:{tipo.value}")]
        for tipo in TipoPropiedad
    ]
    return InlineKeyboardMarkup(filas)


def teclado_opciones(opciones: list[str], prefijo: str) -> InlineKeyboardMarkup:
    """Teclado generico para elegir entre una lista de textos (paises, ciudades)."""
    filas = [[InlineKeyboardButton(op, callback_data=f"{prefijo}:{op}")] for op in opciones]
    return InlineKeyboardMarkup(filas)


def teclado_lista_propiedades(propiedades: list[Propiedad]) -> InlineKeyboardMarkup:
    filas = []
    for propiedad in propiedades:
        etiqueta = f"🔥 {propiedad.titulo}" if es_full(propiedad) else propiedad.titulo
        filas.append([InlineKeyboardButton(etiqueta, callback_data=f"ver:{propiedad.id}")])
    return InlineKeyboardMarkup(filas)


def teclado_detalle_propiedad(propiedad_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(textos.BOTON_AGENDAR, callback_data=f"agendar:{propiedad_id}")],
        [InlineKeyboardButton(textos.BOTON_VOLVER, callback_data="menu:explorar")],
    ])


def teclado_extras(propiedad: Propiedad, seleccionados: set[str]) -> InlineKeyboardMarkup:
    filas = []
    for extra in propiedad.extras_disponibles:
        if extra.incluido_por_defecto:
            texto = f"✅ {extra.nombre} (incluido)"
            filas.append([InlineKeyboardButton(texto, callback_data="extra:nada")])
            continue
        marca = "✅" if extra.id in seleccionados else "⬜"
        texto = f"{marca} {extra.nombre} (+{extra.precio_extra})"
        filas.append([InlineKeyboardButton(texto, callback_data=f"extra:{extra.id}")])
    filas.append([InlineKeyboardButton(textos.BOTON_LISTO_EXTRAS, callback_data="extra:listo")])
    return InlineKeyboardMarkup(filas)


def teclado_confirmar() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(textos.BOTON_CONFIRMAR, callback_data="confirmar:si")],
        [InlineKeyboardButton(textos.BOTON_CANCELAR, callback_data="confirmar:no")],
    ])
