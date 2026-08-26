"""
Conversacion para EXPLORAR propiedades: elegir tipo, pais, ciudad,
ver la lista de resultados y el detalle de una propiedad especifica.
No maneja el agendamiento en si - eso vive en agendar.py.

Todas las consultas a Google Sheets pasan por llamar_con_limite, para
que si la red falla o se demora, el bot avise en vez de quedarse
trabado en silencio.
"""

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from motor.models import TipoPropiedad
from motor.propiedades import listar_propiedades, obtener_propiedad
from motor.precios import es_full
from bot import textos, teclados
from bot.seguro import llamar_con_limite, ErrorDelMotor

ELEGIR_TIPO, ELEGIR_PAIS, ELEGIR_CIUDAD, VER_LISTA = range(4)


async def iniciar_exploracion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("RASTRO: iniciar_exploracion fue llamada", flush=True)
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(textos.ELEGIR_TIPO, reply_markup=teclados.teclado_tipos())
    return ELEGIR_PAIS


async def recibir_tipo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tipo_texto = query.data.split(":", 1)[1]
    context.user_data["filtro_tipo"] = tipo_texto

    try:
        propiedades = await llamar_con_limite(listar_propiedades, tipo=TipoPropiedad(tipo_texto))
    except ErrorDelMotor as error:
        await query.message.reply_text(error.mensaje)
        return ConversationHandler.END

    paises = sorted({p.pais for p in propiedades if p.pais})

    if not paises:
        await query.edit_message_text(textos.SIN_RESULTADOS)
        return ConversationHandler.END

    await query.edit_message_text(
        textos.ELEGIR_PAIS,
        reply_markup=teclados.teclado_opciones(paises, "pais"),
    )
    return ELEGIR_CIUDAD


async def recibir_pais(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pais = query.data.split(":", 1)[1]
    context.user_data["filtro_pais"] = pais

    tipo_texto = context.user_data["filtro_tipo"]
    try:
        propiedades = await llamar_con_limite(
            listar_propiedades, tipo=TipoPropiedad(tipo_texto), pais=pais
        )
    except ErrorDelMotor as error:
        await query.message.reply_text(error.mensaje)
        return ConversationHandler.END

    ciudades = sorted({p.ciudad for p in propiedades if p.ciudad})

    await query.edit_message_text(
        textos.ELEGIR_CIUDAD,
        reply_markup=teclados.teclado_opciones(ciudades, "ciudad", volver_callback="volver:pais"),
    )
    return VER_LISTA


async def recibir_ciudad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ciudad = query.data.split(":", 1)[1]
    context.user_data["filtro_ciudad"] = ciudad

    tipo_texto = context.user_data["filtro_tipo"]
    pais = context.user_data["filtro_pais"]
    try:
        propiedades = await llamar_con_limite(
            listar_propiedades, tipo=TipoPropiedad(tipo_texto), pais=pais, ciudad=ciudad
        )
    except ErrorDelMotor as error:
        await query.message.reply_text(error.mensaje)
        return ConversationHandler.END

    if not propiedades:
        await query.edit_message_text(textos.SIN_RESULTADOS)
        return ConversationHandler.END

    await query.edit_message_text(
        textos.texto_resultados(len(propiedades)),
        reply_markup=teclados.teclado_lista_propiedades(propiedades),
    )
    return VER_LISTA


async def volver_a_menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Desde la pantalla de 'elegir tipo', vuelve al menu principal y
    termina la conversacion (asi /start o 'Buscar alojamiento' vuelven
    a funcionar como entry_point normalmente)."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(textos.BIENVENIDA, reply_markup=teclados.teclado_menu_principal())
    return ConversationHandler.END


async def volver_a_tipo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(textos.ELEGIR_TIPO, reply_markup=teclados.teclado_tipos())
    return ELEGIR_PAIS


async def volver_a_pais(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tipo_texto = context.user_data.get("filtro_tipo")

    try:
        propiedades = await llamar_con_limite(listar_propiedades, tipo=TipoPropiedad(tipo_texto))
    except ErrorDelMotor as error:
        await query.message.reply_text(error.mensaje)
        return ConversationHandler.END

    paises = sorted({p.pais for p in propiedades if p.pais})
    await query.edit_message_text(
        textos.ELEGIR_PAIS,
        reply_markup=teclados.teclado_opciones(paises, "pais", volver_callback="volver:tipo"),
    )
    return ELEGIR_CIUDAD


async def volver_a_ciudad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tipo_texto = context.user_data.get("filtro_tipo")
    pais = context.user_data.get("filtro_pais")

    try:
        propiedades = await llamar_con_limite(
            listar_propiedades, tipo=TipoPropiedad(tipo_texto), pais=pais
        )
    except ErrorDelMotor as error:
        await query.message.reply_text(error.mensaje)
        return ConversationHandler.END

    ciudades = sorted({p.ciudad for p in propiedades if p.ciudad})
    await query.edit_message_text(
        textos.ELEGIR_CIUDAD,
        reply_markup=teclados.teclado_opciones(ciudades, "ciudad", volver_callback="volver:pais"),
    )
    return VER_LISTA


async def volver_a_lista(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Vuelve a la lista de propiedades sin perder los filtros elegidos
    (tipo/pais/ciudad), en vez de reiniciar toda la busqueda desde cero."""
    query = update.callback_query
    await query.answer()
    tipo_texto = context.user_data.get("filtro_tipo")
    pais = context.user_data.get("filtro_pais")
    ciudad = context.user_data.get("filtro_ciudad")

    try:
        propiedades = await llamar_con_limite(
            listar_propiedades, tipo=TipoPropiedad(tipo_texto), pais=pais, ciudad=ciudad
        )
    except ErrorDelMotor as error:
        await query.message.reply_text(error.mensaje)
        return ConversationHandler.END

    if not propiedades:
        await query.edit_message_text(textos.SIN_RESULTADOS)
        return ConversationHandler.END

    await query.edit_message_text(
        textos.texto_resultados(len(propiedades)),
        reply_markup=teclados.teclado_lista_propiedades(propiedades),
    )
    return VER_LISTA


async def mostrar_detalle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    propiedad_id = query.data.split(":", 1)[1]

    try:
        propiedad = await llamar_con_limite(obtener_propiedad, propiedad_id)
    except ErrorDelMotor as error:
        await query.message.reply_text(error.mensaje)
        return ConversationHandler.END

    if propiedad is None:
        await query.edit_message_text(textos.SIN_RESULTADOS)
        return ConversationHandler.END

    etiqueta = f"\n\n{textos.ETIQUETA_FULL}" if es_full(propiedad) else ""
    codigo = (
        f"Codigo en la casa de arrendamiento: {propiedad.codigo_casa_arrendamiento}\n"
        if propiedad.codigo_casa_arrendamiento
        else ""
    )
    nota_agendamiento = (
        ""
        if propiedad.tipo == TipoPropiedad.HABITACION
        else f"\n\n{textos.NOTA_SIN_AGENDAMIENTO}"
    )
    detalle = (
        f"{propiedad.titulo}\n\n"
        f"{propiedad.descripcion}\n\n"
        f"Precio base por noche: {propiedad.precio_base:,.0f}\n"
        f"{codigo}"
        f"\n{textos.NOTA_UBICACION_PENDIENTE}"
        f"{nota_agendamiento}"
        f"{etiqueta}"
    )

    if propiedad.fotos:
        await query.message.reply_photo(propiedad.fotos[0], caption=detalle)
        await query.message.reply_text(
            "Que quieres hacer?",
            reply_markup=teclados.teclado_detalle_propiedad(propiedad),
        )
    else:
        await query.edit_message_text(
            detalle, reply_markup=teclados.teclado_detalle_propiedad(propiedad)
        )
    return VER_LISTA
