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
        reply_markup=teclados.teclado_opciones(ciudades, "ciudad"),
    )
    return VER_LISTA


async def recibir_ciudad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ciudad = query.data.split(":", 1)[1]

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
        f"Encontramos {len(propiedades)} opciones:",
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
    detalle = (
        f"{propiedad.titulo}\n\n"
        f"{propiedad.descripcion}\n\n"
        f"Precio base por noche: {propiedad.precio_base}\n"
        f"Direccion: {propiedad.direccion_escrita}\n"
        f"Ubicacion (Waze): {propiedad.ubicacion}"
        f"{etiqueta}"
    )

    if propiedad.fotos:
        await query.message.reply_photo(propiedad.fotos[0], caption=detalle)
        await query.message.reply_text(
            "Que quieres hacer?",
            reply_markup=teclados.teclado_detalle_propiedad(propiedad.id),
        )
    else:
        await query.edit_message_text(
            detalle, reply_markup=teclados.teclado_detalle_propiedad(propiedad.id)
        )
    return VER_LISTA
