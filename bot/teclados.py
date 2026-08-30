"""
Construye los botones (InlineKeyboardMarkup) que usa el bot.
Separado de la logica de conversacion para que cada archivo tenga
una sola responsabilidad.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from motor.models import Propiedad, TipoPropiedad
from motor.precios import es_full
from bot import textos

# Lista fija de detalles destacados que el dueno puede elegir al publicar.
# Fija a proposito: asi el dato queda ESTANDARIZADO (una etiqueta real,
# no texto libre), lo que permite mas adelante armar un buscador preciso
# por esas mismas etiquetas, sin depender de IA ni de texto libre.
DESTACADOS_PREDEFINIDOS = [
    "Cerca al metro",
    "Con balcon",
    "Recien remodelada",
    "Amoblada",
    "Con parqueadero",
    "Wifi incluido",
    "Con bano privado",
    "Vista panoramica",
]


def teclado_menu_principal() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(textos.BOTON_EXPLORAR, callback_data="menu:explorar")],
        [InlineKeyboardButton(textos.BOTON_PUBLICAR, callback_data="menu:publicar")],
        [InlineKeyboardButton(textos.BOTON_MIS_PUBLICACIONES, callback_data="menu:mispublicaciones")],
    ])


def teclado_destacados() -> InlineKeyboardMarkup:
    filas = [
        [InlineKeyboardButton(t, callback_data=f"destacado:{i}")]
        for i, t in enumerate(DESTACADOS_PREDEFINIDOS)
    ]
    filas.append([InlineKeyboardButton("Otro (escribir el mio)", callback_data="destacado:otro")])
    return InlineKeyboardMarkup(filas)


def teclado_tipos_publicar() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(tipo.value.capitalize(), callback_data=f"publicar_tipo:{tipo.value}")]
        for tipo in TipoPropiedad
    ])


def teclado_confirmar_publicacion() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Si, publicar", callback_data="confirmar_publicar:si"),
            InlineKeyboardButton("No, cancelar", callback_data="confirmar_publicar:no"),
        ]
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
    filas.append([InlineKeyboardButton(textos.BOTON_VOLVER, callback_data="volver:menu")])
    return InlineKeyboardMarkup(filas)


def teclado_opciones(
    opciones: list[str], prefijo: str, volver_callback: str | None = None
) -> InlineKeyboardMarkup:
    """Teclado generico para elegir entre una lista de textos (paises, ciudades).
    Si se pasa volver_callback, agrega un boton 'Volver' al paso anterior."""
    filas = [[InlineKeyboardButton(op, callback_data=f"{prefijo}:{op}")] for op in opciones]
    if volver_callback:
        filas.append([InlineKeyboardButton(textos.BOTON_VOLVER, callback_data=volver_callback)])
    return InlineKeyboardMarkup(filas)


def teclado_lista_propiedades(propiedades: list[Propiedad]) -> InlineKeyboardMarkup:
    filas = []
    for propiedad in propiedades:
        etiqueta = f"🔥 {propiedad.titulo}" if es_full(propiedad) else propiedad.titulo
        filas.append([InlineKeyboardButton(etiqueta, callback_data=f"ver:{propiedad.id}")])
    filas.append([InlineKeyboardButton(textos.BOTON_VOLVER, callback_data="volver:ciudad")])
    return InlineKeyboardMarkup(filas)


def teclado_horarios_visita(slots: list[tuple]) -> InlineKeyboardMarkup:
    """slots es una lista de (fecha, hora). Cada boton codifica ambas
    en el callback_data, separadas por '|'."""
    from motor.horarios import formatear_fecha_corta

    filas = [
        [InlineKeyboardButton(
            f"{formatear_fecha_corta(fecha)} - {hora}",
            callback_data=f"horario:{fecha.isoformat()}|{hora}",
        )]
        for fecha, hora in slots
    ]
    filas.append([InlineKeyboardButton("Ninguno me sirve", callback_data="horario:otro")])
    return InlineKeyboardMarkup(filas)


def teclado_detalle_propiedad(propiedad: Propiedad) -> InlineKeyboardMarkup:
    filas = []
    # El agendamiento solo aplica a habitaciones, que se manejan directo con
    # el dueno. Apartamentos/casas van por casas de arrendamiento externas,
    # sobre las que no tenemos control ni acceso para agendar nada ahi.
    if propiedad.tipo == TipoPropiedad.HABITACION:
        filas.append([InlineKeyboardButton(textos.BOTON_AGENDAR, callback_data=f"agendar:{propiedad.id}")])
    filas.append([InlineKeyboardButton(textos.BOTON_VOLVER, callback_data="volver:lista")])
    return InlineKeyboardMarkup(filas)


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
