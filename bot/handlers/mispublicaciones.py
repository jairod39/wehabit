"""
Le permite a un dueno ver TODAS sus propiedades (activas e inactivas) y
prenderlas/apagarlas a conveniencia, sin tener que volver a escribir
nada. No es una ConversationHandler: son callbacks sueltos, porque no
hay ningun paso que pida texto libre.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from motor.propiedades import listar_propiedades_de_dueno, cambiar_estado_propiedad
from bot import textos
from bot.seguro import llamar_con_limite, ErrorDelMotor


def _teclado_lista(propiedades) -> InlineKeyboardMarkup:
    filas = []
    for p in propiedades:
        emoji = "🟢" if p.activa else "⚪"
        filas.append([InlineKeyboardButton(f"{emoji} {p.titulo}", callback_data=f"verpub:{p.id}")])
    filas.append([InlineKeyboardButton(textos.BOTON_VOLVER, callback_data="menu:volver")])
    return InlineKeyboardMarkup(filas)


def _teclado_detalle(propiedad) -> InlineKeyboardMarkup:
    texto_boton = "Desactivar" if propiedad.activa else "Activar"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(texto_boton, callback_data=f"togglepub:{propiedad.id}")],
        [InlineKeyboardButton(textos.BOTON_VOLVER, callback_data="menu:mispublicaciones")],
    ])


async def mostrar_mis_publicaciones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("RASTRO: mostrar_mis_publicaciones fue llamada", flush=True)
    query = update.callback_query
    await query.answer()

    dueno_id = str(update.effective_user.id)
    try:
        propiedades = await llamar_con_limite(listar_propiedades_de_dueno, dueno_id)
    except ErrorDelMotor as error:
        await query.message.reply_text(error.mensaje)
        return

    if not propiedades:
        await query.edit_message_text(
            textos.SIN_PUBLICACIONES_PROPIAS, reply_markup=_teclado_lista([])
        )
        return

    await query.edit_message_text(textos.MIS_PUBLICACIONES, reply_markup=_teclado_lista(propiedades))


async def ver_publicacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    id_propiedad = query.data.split(":", 1)[1]

    dueno_id = str(update.effective_user.id)
    try:
        propiedades = await llamar_con_limite(listar_propiedades_de_dueno, dueno_id)
    except ErrorDelMotor as error:
        await query.message.reply_text(error.mensaje)
        return

    propiedad = next((p for p in propiedades if p.id == id_propiedad), None)
    if propiedad is None:
        # No es tuya, o ya no existe. No decimos cual de las dos, por seguridad.
        await query.edit_message_text(textos.PUBLICACION_NO_ENCONTRADA)
        return

    estado_texto = "Activa (visible en busquedas)" if propiedad.activa else "Inactiva (oculta)"
    detalle = (
        f"{propiedad.titulo}\n\n"
        f"Estado: {estado_texto}\n"
        f"Precio: {propiedad.precio_base:,.0f}\n"
        f"Ciudad: {propiedad.ciudad}, {propiedad.pais}"
    )
    await query.edit_message_text(detalle, reply_markup=_teclado_detalle(propiedad))


async def alternar_publicacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("RASTRO: alternar_publicacion fue llamada", flush=True)
    query = update.callback_query
    await query.answer()
    id_propiedad = query.data.split(":", 1)[1]

    dueno_id = str(update.effective_user.id)
    try:
        propiedades = await llamar_con_limite(listar_propiedades_de_dueno, dueno_id)
    except ErrorDelMotor as error:
        await query.message.reply_text(error.mensaje)
        return

    propiedad = next((p for p in propiedades if p.id == id_propiedad), None)
    if propiedad is None:
        await query.edit_message_text(textos.PUBLICACION_NO_ENCONTRADA)
        return

    nuevo_estado = not propiedad.activa
    try:
        encontrada = await llamar_con_limite(cambiar_estado_propiedad, id_propiedad, nuevo_estado)
    except ErrorDelMotor as error:
        await query.message.reply_text(error.mensaje)
        return

    if not encontrada:
        await query.edit_message_text(textos.PUBLICACION_NO_ENCONTRADA)
        return

    propiedad.activa = nuevo_estado
    estado_texto = "Activa (visible en busquedas)" if propiedad.activa else "Inactiva (oculta)"
    detalle = (
        f"{propiedad.titulo}\n\n"
        f"Estado: {estado_texto}\n"
        f"Precio: {propiedad.precio_base:,.0f}\n"
        f"Ciudad: {propiedad.ciudad}, {propiedad.pais}"
    )
    await query.edit_message_text(detalle, reply_markup=_teclado_detalle(propiedad))
