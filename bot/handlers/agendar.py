"""
Conversacion para AGENDAR una CITA DE VISITA (no una estadia). El dueno
define en su ficha que horarios ofrece (ej "Viernes 15:00, Sabado 10:00")
y el bot los convierte en fechas concretas de las proximas semanas,
saltando los que ya estan ocupados.

Las fechas de ESTADIA (checkin/checkout) NO se manejan aqui: eso es un
acuerdo directo entre el dueno y el inquilino, fuera de este bot.

La direccion exacta y el link de ubicacion NUNCA se muestran antes de
confirmar la cita (eso vive en explorar.py, en la vista previa). Solo se
revelan aqui, en el mensaje final de RESERVA_CREADA, para proteger la
privacidad del dueno hasta que la visita esta agendada.

Todas las consultas y escrituras a Google Sheets pasan por
llamar_con_limite, para que si la red falla o se demora, el bot avise
en vez de quedarse trabado en silencio.
"""

from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from motor.propiedades import obtener_propiedad
from motor.precios import calcular_total, generar_desglose
from motor.reservas import crear_reserva, horarios_ocupados
from motor.horarios import proximos_horarios_disponibles
from motor.models import EstadoReserva
from bot import textos, teclados
from bot.seguro import llamar_con_limite, ErrorDelMotor

# Rango 100+ para no colisionar con los estados de explorar.py (0-3).
# ConversationHandler usa un solo diccionario de estados para TODO el bot,
# asi que dos modulos que usen range() por separado terminan con los
# mismos numeros y uno sobreescribe al otro en el diccionario de main.py.
#
# Convencion: el nombre del estado es lo que el bot ESTA ESPERANDO recibir
# en ese momento (la respuesta a la ultima pregunta que hizo).
ESPERANDO_HORARIO, ESPERANDO_FECHA_ALTERNATIVA, ESPERANDO_EXTRAS, ESPERANDO_CONFIRMACION = range(100, 104)


async def _obtener_propiedad_segura(context, mensaje_error_para: callable):
    """Trae la propiedad y avisa con un mensaje claro si ya no existe,
    en vez de seguir con un None y tronar en silencio mas adelante."""
    propiedad_id = context.user_data.get("agendando_propiedad_id")
    propiedad = await llamar_con_limite(obtener_propiedad, propiedad_id)
    if propiedad is None:
        await mensaje_error_para(
            "Esa propiedad ya no esta disponible (puede que la hayan "
            "desactivado). Vuelve a buscar, por favor."
        )
        return None
    return propiedad


async def iniciar_agendamiento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("RASTRO: iniciar_agendamiento fue llamada", flush=True)
    query = update.callback_query
    await query.answer()
    propiedad_id = query.data.split(":", 1)[1]
    context.user_data["agendando_propiedad_id"] = propiedad_id
    context.user_data["extras_elegidos"] = set()
    context.user_data["fuera_de_horario_definido"] = False

    try:
        propiedad = await _obtener_propiedad_segura(context, query.message.reply_text)
        if propiedad is None:
            return ConversationHandler.END
        ocupados = await llamar_con_limite(horarios_ocupados, propiedad_id)
    except ErrorDelMotor as error:
        await query.message.reply_text(error.mensaje)
        return ConversationHandler.END

    disponibles = proximos_horarios_disponibles(propiedad.horarios_visita, ocupados)

    if not disponibles:
        await query.message.reply_text(textos.SIN_HORARIOS_DEFINIDOS)
        return ESPERANDO_FECHA_ALTERNATIVA

    await query.message.reply_text(
        textos.ELEGIR_HORARIO_VISITA,
        reply_markup=teclados.teclado_horarios_visita(disponibles),
    )
    return ESPERANDO_HORARIO


async def recibir_horario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("RASTRO: recibir_horario fue llamada", flush=True)
    query = update.callback_query
    await query.answer()
    dato = query.data.split(":", 1)[1]

    if dato == "otro":
        await query.message.reply_text(textos.PEDIR_HORARIO_ALTERNATIVO)
        return ESPERANDO_FECHA_ALTERNATIVA

    fecha_texto, hora = dato.split("|")
    context.user_data["fecha_visita"] = datetime.strptime(fecha_texto, "%Y-%m-%d").date()
    context.user_data["hora_visita"] = hora

    return await _pasar_a_extras(update, context, via_callback=True)


async def recibir_fecha_alternativa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("RASTRO: recibir_fecha_alternativa fue llamada", flush=True)
    texto = update.message.text.strip()
    try:
        fecha_hora = datetime.strptime(texto, "%Y-%m-%d %H:%M")
    except ValueError:
        await update.message.reply_text(textos.HORARIO_ALTERNATIVO_INVALIDO)
        return ESPERANDO_FECHA_ALTERNATIVA

    context.user_data["fecha_visita"] = fecha_hora.date()
    context.user_data["hora_visita"] = fecha_hora.strftime("%H:%M")
    context.user_data["fuera_de_horario_definido"] = True

    return await _pasar_a_extras(update, context, via_callback=False)


async def _pasar_a_extras(update: Update, context: ContextTypes.DEFAULT_TYPE, via_callback: bool):
    responder = update.callback_query.message.reply_text if via_callback else update.message.reply_text
    try:
        propiedad = await _obtener_propiedad_segura(context, responder)
    except ErrorDelMotor as error:
        await responder(error.mensaje)
        return ConversationHandler.END
    if propiedad is None:
        return ConversationHandler.END

    await responder(
        textos.ELEGIR_EXTRAS,
        reply_markup=teclados.teclado_extras(propiedad, context.user_data["extras_elegidos"]),
    )
    return ESPERANDO_EXTRAS


async def alternar_extra(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("RASTRO: alternar_extra fue llamada", flush=True)
    query = update.callback_query
    extra_id = query.data.split(":", 1)[1]

    try:
        propiedad = await _obtener_propiedad_segura(context, query.message.reply_text)
    except ErrorDelMotor as error:
        await query.answer()
        await query.message.reply_text(error.mensaje)
        return ConversationHandler.END
    if propiedad is None:
        await query.answer()
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
    print("RASTRO: mostrar_resumen fue llamada", flush=True)
    query = update.callback_query
    try:
        propiedad = await _obtener_propiedad_segura(context, query.message.reply_text)
    except ErrorDelMotor as error:
        await query.message.reply_text(error.mensaje)
        return ConversationHandler.END
    if propiedad is None:
        return ConversationHandler.END

    fecha_visita = context.user_data["fecha_visita"]
    hora_visita = context.user_data["hora_visita"]
    extras_elegidos = list(context.user_data["extras_elegidos"])

    # noches=1 solo como referencia de precio, no es un total de estadia:
    # las fechas de estadia no se agendan aqui.
    desglose = generar_desglose(propiedad, extras_elegidos, 1)
    aviso_pendiente = (
        f"\n\n{textos.AVISO_HORARIO_SUJETO_A_CONFIRMACION}"
        if context.user_data.get("fuera_de_horario_definido")
        else ""
    )
    resumen = (
        textos.CONFIRMAR_RESERVA
        + f"\n\nVisita: {fecha_visita.isoformat()} a las {hora_visita}\n\n"
        + "\n".join(desglose)
        + aviso_pendiente
    )

    await query.message.reply_text(resumen, reply_markup=teclados.teclado_confirmar())
    return ESPERANDO_CONFIRMACION


async def confirmar_reserva(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("RASTRO: confirmar_reserva fue llamada", flush=True)
    query = update.callback_query
    await query.answer()
    decision = query.data.split(":", 1)[1]

    if decision == "no":
        await query.edit_message_text(textos.RESERVA_CANCELADA)
        return ConversationHandler.END

    try:
        propiedad = await _obtener_propiedad_segura(context, query.message.reply_text)
    except ErrorDelMotor as error:
        await query.message.reply_text(error.mensaje)
        return ConversationHandler.END
    if propiedad is None:
        return ConversationHandler.END

    fecha_visita = context.user_data["fecha_visita"]
    hora_visita = context.user_data["hora_visita"]
    extras_elegidos = list(context.user_data["extras_elegidos"])
    total = calcular_total(propiedad, extras_elegidos, 1)
    fuera_de_horario = context.user_data.get("fuera_de_horario_definido", False)

    try:
        await llamar_con_limite(
            crear_reserva,
            propiedad_id=propiedad.id,
            inquilino_id=str(update.effective_user.id),
            fecha_visita=fecha_visita,
            hora_visita=hora_visita,
            extras_elegidos=extras_elegidos,
            precio_total=total,
            estado=EstadoReserva.PENDIENTE,
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
    aviso_pendiente = (
        f"\n\n{textos.AVISO_HORARIO_SUJETO_A_CONFIRMACION}" if fuera_de_horario else ""
    )
    mensaje = (
        textos.RESERVA_CREADA
        + (propiedad.metodo_pago or "El dueno te lo compartira directamente.")
        + ubicacion_texto
        + aviso_pendiente
    )
    await query.edit_message_text(mensaje)
    return ConversationHandler.END
