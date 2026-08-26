"""
Conversacion para AGENDAR una visita/estadia: fechas, hora, extras, resumen
y confirmacion. Nunca cobra dinero - solo agenda y muestra el metodo
de pago del dueno como informacion para que el usuario lo tenga listo.

La direccion exacta y el link de ubicacion NUNCA se muestran antes de
confirmar la reserva (eso vive en explorar.py, en la vista previa).
Solo se revelan aqui, en el mensaje final de RESERVA_CREADA, para
proteger la privacidad del dueno hasta que la visita esta agendada.

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

# Rango 100+ para no colisionar con los estados de explorar.py (0-3).
# ConversationHandler usa un solo diccionario de estados para TODO el bot,
# asi que dos modulos que usen range() por separado terminan con los
# mismos numeros y uno sobreescribe al otro en el diccionario de main.py.
#
# Convencion: el nombre del estado es lo que el bot ESTA ESPERANDO recibir
# en ese momento (la respuesta a la ultima pregunta que hizo).
ESPERANDO_FECHA_INICIO, ESPERANDO_FECHA_FIN, ESPERANDO_HORA, ESPERANDO_EXTRAS, ESPERANDO_CONFIRMACION = range(100, 105)


async def iniciar_agendamiento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    propiedad_id = query.data.split(":", 1)[1]
    context.user_data["agendando_propiedad_id"] = propiedad_id
    context.user_data["extras_elegidos"] = set()

    await query.message.reply_text(textos.PEDIR_FECHA_INICIO)
    return ESPERANDO_FECHA_INICIO


async def recibir_fecha_inicio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    try:
        fecha = datetime.strptime(texto, "%Y-%m-%d").date()
    except ValueError:
        await update.message.reply_text(textos.FECHA_INVALIDA)
        return ESPERANDO_FECHA_INICIO

    context.user_data["fecha_inicio"] = fecha
    await update.message.reply_text(textos.PEDIR_FECHA_FIN)
    return ESPERANDO_FECHA_FIN


async def recibir_fecha_fin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    try:
        fecha_fin = datetime.strptime(texto, "%Y-%m-%d").date()
    except ValueError:
        await update.message.reply_text(textos.FECHA_INVALIDA)
        return ESPERANDO_FECHA_FIN

    fecha_inicio = context.user_data["fecha_inicio"]
    if fecha_fin < fecha_inicio:
        await update.message.reply_text(textos.FECHA_FIN_ANTES_DE_INICIO)
        return ESPERANDO_FECHA_FIN

    context.user_data["fecha_fin"] = fecha_fin
    await update.message.reply_text(textos.PEDIR_HORA_VISITA)
    return ESPERANDO_HORA


async def recibir_hora_visita(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    try:
        hora = datetime.strptime(texto, "%H:%M").time()
    except ValueError:
        await update.message.reply_text(textos.HORA_INVALIDA)
        return ESPERANDO_HORA

    context.user_data["hora_visita"] = hora.strftime("%H:%M")

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
    return ESPERANDO_EXTRAS


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
        return ESPERANDO_EXTRAS

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
    return ESPERANDO_EXTRAS


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
    hora_visita = context.user_data["hora_visita"]
    noches = (fecha_fin - fecha_inicio).days or 1
    extras_elegidos = list(context.user_data["extras_elegidos"])

    desglose = generar_desglose(propiedad, extras_elegidos, noches)
    resumen = (
        textos.CONFIRMAR_RESERVA
        + f"\n\nVisita: {fecha_inicio.isoformat()} a las {hora_visita}\n\n"
        + "\n".join(desglose)
    )

    await query.message.reply_text(resumen, reply_markup=teclados.teclado_confirmar())
    return ESPERANDO_CONFIRMACION


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
    hora_visita = context.user_data["hora_visita"]
    extras_elegidos = list(context.user_data["extras_elegidos"])
    noches = (fecha_fin - fecha_inicio).days or 1
    total = calcular_total(propiedad, extras_elegidos, noches)

    try:
        await llamar_con_limite(
            crear_reserva,
            propiedad_id=propiedad.id,
            inquilino_id=str(update.effective_user.id),
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            hora_visita=hora_visita,
            extras_elegidos=extras_elegidos,
            precio_total=total,
        )
    except ErrorDelMotor as error:
        await query.message.reply_text(error.mensaje)
        return ConversationHandler.END

    # Aqui, y SOLO aqui, se revela la direccion exacta y el mapa:
    # la visita ya quedo agendada, ya no es informacion publica suelta.
    ubicacion_texto = (
        f"\n\nDireccion: {propiedad.direccion_escrita}\n"
        f"Ubicacion (mapa): {propiedad.ubicacion}"
        if (propiedad.direccion_escrita or propiedad.ubicacion)
        else ""
    )
    mensaje = (
        textos.RESERVA_CREADA
        + (propiedad.metodo_pago or "El dueno te lo compartira directamente.")
        + ubicacion_texto
    )
    await query.edit_message_text(mensaje)
    return ConversationHandler.END
