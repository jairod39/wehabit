"""
Conversacion para AGENDAR una visita/estadia: fechas, extras, resumen
y confirmacion. Nunca cobra dinero - solo agenda y muestra el metodo
de pago del dueno como informacion para que el usuario lo tenga listo.

Todas las consultas y escrituras a Google Sheets pasan por
llamar_con_limite, para que si la red falla o se demora, el bot avise
en vez de quedarse trabado en silencio.
"""

from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from motor.propiedades import obtener_propiedad
from motor.precios import calcular_total, generar_desglose
from motor.reservas import crear_reserva
from bot import textos, teclados
from bot.seguro import llamar_con_limite, ErrorDelMotor

PEDIR_INICIO, PEDIR_FIN, ELEGIR_EXTRAS, CONFIRMAR = range(4)


async def iniciar_agendamiento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    propiedad_id = query.data.split(":", 1)[1]
    context.user_data["agendando_propiedad_id"] = propiedad_id
    context.user_data["extras_elegidos"] = set()

    await query.message.reply_text(textos.PEDIR_FECHA_INICIO)
    return PEDIR_FIN


async def recibir_fecha_inicio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    try:
        fecha = datetime.strptime(texto, "%Y-%m-%d").date()
    except ValueError:
        await update.message.reply_text(textos.FECHA_INVALIDA)
        return PEDIR_FIN

    context.user_data["fecha_inicio"] = fecha
    await update.message.reply_text(textos.PEDIR_FECHA_FIN)
    return ELEGIR_EXTRAS


async def recibir_fecha_fin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    try:
        fecha_fin = datetime.strptime(texto, "%Y-%m-%d").date()
    except ValueError:
        await update.message.reply_text(textos.FECHA_INVALIDA)
        return ELEGIR_EXTRAS

    fecha_inicio = context.user_data["fecha_inicio"]
    if fecha_fin < fecha_inicio:
        await update.message.reply_text(textos.FECHA_FIN_ANTES_DE_INICIO)
        return ELEGIR_EXTRAS

    context.user_data["fecha_fin"] = fecha_fin

    try:
        propiedad = await llamar_con_limite(
            obtener_propiedad, context.user_data["agendando_propiedad_id"]
        )
    except ErrorDelMotor as error:
        await update.message.reply_text(error.mensaje)
        return ConversationHandler.END

    await update.message.reply_text(
        textos.ELEGIR_EXTRAS,
        reply_markup=teclados.teclado_extras(propiedad, context.user_data["extras_elegidos"]),
    )
    return CONFIRMAR


async def alternar_extra(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    extra_id = query.data.split(":", 1)[1]

    try:
        propiedad = await llamar_con_limite(
            obtener_propiedad, context.user_data["agendando_propiedad_id"]
        )
    except ErrorDelMotor as error:
        await query.answer()
        await query.message.reply_text(error.mensaje)
        return ConversationHandler.END

    if extra_id == "nada":
        await query.answer()
        return CONFIRMAR

    if extra_id == "listo":
        await query.answer()
        return await mostrar_resumen(update, context)

    seleccionados = context.user_data["extras_elegidos"]
    if extra_id in seleccionados:
        seleccionados.remove(extra_id)
    else:
        seleccionados.add(extra_id)

    await query.answer()
    await query.edit_message_reply_markup(
        reply_markup=teclados.teclado_extras(propiedad, seleccionados)
    )
    return CONFIRMAR


async def mostrar_resumen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        propiedad = await llamar_con_limite(
            obtener_propiedad, context.user_data["agendando_propiedad_id"]
        )
    except ErrorDelMotor as error:
        await query.message.reply_text(error.mensaje)
        return ConversationHandler.END

    fecha_inicio = context.user_data["fecha_inicio"]
    fecha_fin = context.user_data["fecha_fin"]
    noches = (fecha_fin - fecha_inicio).days or 1
    extras_elegidos = list(context.user_data["extras_elegidos"])

    desglose = generar_desglose(propiedad, extras_elegidos, noches)
    resumen = textos.CONFIRMAR_RESERVA + "\n\n" + "\n".join(desglose)

    await query.message.reply_text(resumen, reply_markup=teclados.teclado_confirmar())
    return CONFIRMAR


async def confirmar_reserva(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    decision = query.data.split(":", 1)[1]

    if decision == "no":
        await query.edit_message_text(textos.RESERVA_CANCELADA)
        return ConversationHandler.END

    try:
        propiedad = await llamar_con_limite(
            obtener_propiedad, context.user_data["agendando_propiedad_id"]
        )
    except ErrorDelMotor as error:
        await query.message.reply_text(error.mensaje)
        return ConversationHandler.END

    fecha_inicio = context.user_data["fecha_inicio"]
    fecha_fin = context.user_data["fecha_fin"]
    noches = (fecha_fin - fecha_inicio).days or 1
    extras_elegidos = list(context.user_data["extras_elegidos"])
    total = calcular_total(propiedad, extras_elegidos, noches)

    try:
        await llamar_con_limite(
            crear_reserva,
            propiedad_id=propiedad.id,
            inquilino_id=str(update.effective_user.id),
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            extras_elegidos=extras_elegidos,
            precio_total=total,
        )
    except ErrorDelMotor as error:
        await query.message.reply_text(error.mensaje)
        return ConversationHandler.END

    mensaje = textos.RESERVA_CREADA + (propiedad.metodo_pago or "El dueno te lo compartira directamente.")
    await query.edit_message_text(mensaje)
    return ConversationHandler.END
