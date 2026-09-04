"""
Conversacion para que un dueno PUBLIQUE su propiedad hablando con el bot,
sin tocar el Google Sheet a mano y CASI SIN escribir texto libre.

Orden del flujo (pensado para minimizar friccion):
tipo -> continente -> pais -> ciudad -> destacados (varios, con menu) ->
precio -> direccion -> ubicacion -> metodo de pago (menu) ->
extras con precio mensual (menu) -> horarios de visita (solo habitacion) ->
disponibilidad -> descripcion (al final, con plantilla-guia) -> confirmar.

La descripcion va AL FINAL a proposito: para cuando el dueno la escribe,
ya definio todo lo demas con menus, asi que la descripcion solo tiene
que aportar lo que un menu no puede captar (el "sentir" del lugar), no
repetir datos que ya quedaron estructurados.

Es una ConversationHandler SEPARADA de la de explorar/agendar (no
comparte el mismo diccionario de estados).
"""

from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler

from motor.models import TipoPropiedad
from motor.propiedades import crear_propiedad, listar_ciudades_de_pais, agregar_extra_a_propiedad
from bot import textos, teclados
from bot.seguro import llamar_con_limite, ErrorDelMotor

(
    ESPERANDO_TIPO,
    ESPERANDO_CONTINENTE,
    ESPERANDO_PAIS,
    ESPERANDO_CIUDAD,
    ESPERANDO_CIUDAD_OTRA,
    ESPERANDO_DESTACADOS,
    ESPERANDO_DESTACADO_OTRO,
    ESPERANDO_PRECIO,
    ESPERANDO_DIRECCION,
    ESPERANDO_UBICACION,
    ESPERANDO_METODO_PAGO,
    ESPERANDO_METODO_PAGO_OTRO,
    ESPERANDO_EXTRAS,
    ESPERANDO_EXTRA_NOMBRE_OTRO,
    ESPERANDO_EXTRA_PRECIO,
    ESPERANDO_HORARIOS_VISITA,
    ESPERANDO_DISPONIBILIDAD,
    ESPERANDO_DESCRIPCION,
    ESPERANDO_CONFIRMACION,
) = range(200, 219)

SALTAR = {"-", "ninguna", "ninguno", "no", "skip"}


def _quiso_saltar(texto: str) -> bool:
    return texto.strip().lower() in SALTAR


async def iniciar_publicacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("RASTRO: iniciar_publicacion fue llamada", flush=True)
    query = update.callback_query
    await query.answer()
    context.user_data["nueva_propiedad"] = {}
    await query.edit_message_text(
        textos.PUBLICAR_INTRO, reply_markup=teclados.teclado_tipos_publicar()
    )
    return ESPERANDO_TIPO


async def recibir_tipo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tipo_texto = query.data.split(":", 1)[1]
    context.user_data["nueva_propiedad"]["tipo"] = tipo_texto
    await query.message.reply_text(
        textos.ELEGIR_CONTINENTE, reply_markup=teclados.teclado_continentes()
    )
    return ESPERANDO_CONTINENTE


async def recibir_continente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    continente = query.data.split(":", 1)[1]
    context.user_data["continente_actual"] = continente
    await query.message.reply_text(
        textos.ELEGIR_PAIS, reply_markup=teclados.teclado_paises_de_continente(continente)
    )
    return ESPERANDO_PAIS


async def volver_a_continentes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_reply_markup(reply_markup=teclados.teclado_continentes())
    return ESPERANDO_CONTINENTE


async def paginar_paises(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pagina = int(query.data.split(":", 1)[1])
    continente = context.user_data.get("continente_actual", "America")
    await query.edit_message_reply_markup(
        reply_markup=teclados.teclado_paises_de_continente(continente, pagina)
    )
    return ESPERANDO_PAIS


async def _mostrar_ciudades(mensaje_para_editar, context, pais: str, pagina: int = 0):
    try:
        ciudades = await llamar_con_limite(listar_ciudades_de_pais, pais)
    except ErrorDelMotor as error:
        await mensaje_para_editar.reply_text(error.mensaje)
        return ConversationHandler.END

    await mensaje_para_editar.reply_text(
        textos.ELEGIR_CIUDAD, reply_markup=teclados.teclado_ciudades_publicar(ciudades, pagina)
    )
    return ESPERANDO_CIUDAD


async def recibir_pais(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pais = query.data.split(":", 1)[1]
    context.user_data["nueva_propiedad"]["pais"] = pais
    return await _mostrar_ciudades(query.message, context, pais)


async def paginar_ciudades(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pagina = int(query.data.split(":", 1)[1])
    pais = context.user_data["nueva_propiedad"]["pais"]
    try:
        ciudades = await llamar_con_limite(listar_ciudades_de_pais, pais)
    except ErrorDelMotor as error:
        await query.message.reply_text(error.mensaje)
        return ConversationHandler.END
    await query.edit_message_reply_markup(
        reply_markup=teclados.teclado_ciudades_publicar(ciudades, pagina)
    )
    return ESPERANDO_CIUDAD


def _iniciar_destacados(context) -> None:
    context.user_data["nueva_propiedad"]["destacados_idx"] = set()
    context.user_data["nueva_propiedad"]["destacados_custom"] = []


async def recibir_ciudad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ciudad = query.data.split(":", 1)[1]
    context.user_data["nueva_propiedad"]["ciudad"] = ciudad
    _iniciar_destacados(context)
    await query.message.reply_text(
        textos.ELEGIR_DESTACADO, reply_markup=teclados.teclado_destacados_multi(set())
    )
    return ESPERANDO_DESTACADOS


async def pedir_ciudad_otra(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(textos.PEDIR_CIUDAD)
    return ESPERANDO_CIUDAD_OTRA


async def recibir_ciudad_otra(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    if len(texto) < 3:
        await update.message.reply_text(textos.TEXTO_MUY_CORTO)
        return ESPERANDO_CIUDAD_OTRA
    context.user_data["nueva_propiedad"]["ciudad"] = texto
    _iniciar_destacados(context)
    await update.message.reply_text(
        textos.ELEGIR_DESTACADO, reply_markup=teclados.teclado_destacados_multi(set())
    )
    return ESPERANDO_DESTACADOS


async def recibir_destacado_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    dato = query.data.split(":", 1)[1]
    datos = context.user_data["nueva_propiedad"]

    if dato == "otro":
        await query.message.reply_text(textos.PEDIR_DESTACADO)
        return ESPERANDO_DESTACADO_OTRO

    if dato == "listo":
        etiquetas = [
            teclados.DESTACADOS_PREDEFINIDOS[i]
            for i in range(len(teclados.DESTACADOS_PREDEFINIDOS))
            if str(i) in datos["destacados_idx"]
        ]
        etiquetas += datos["destacados_custom"]
        if not etiquetas:
            await query.answer("Marca al menos uno antes de continuar", show_alert=True)
            return ESPERANDO_DESTACADOS

        tipo_legible = datos["tipo"].capitalize()
        datos["titulo"] = f"{tipo_legible} en {datos['ciudad']} - {' y '.join(etiquetas[:2])}"
        datos["destacados"] = ", ".join(etiquetas)
        await query.message.reply_text(textos.PEDIR_PRECIO)
        return ESPERANDO_PRECIO

    seleccionados = datos["destacados_idx"]
    if dato in seleccionados:
        seleccionados.remove(dato)
    else:
        seleccionados.add(dato)
    await query.edit_message_reply_markup(
        reply_markup=teclados.teclado_destacados_multi(seleccionados)
    )
    return ESPERANDO_DESTACADOS


async def recibir_destacado_otro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    if len(texto) < 3:
        await update.message.reply_text(textos.TEXTO_MUY_CORTO)
        return ESPERANDO_DESTACADO_OTRO

    datos = context.user_data["nueva_propiedad"]
    datos["destacados_custom"].append(texto)
    await update.message.reply_text(
        textos.ELEGIR_DESTACADO,
        reply_markup=teclados.teclado_destacados_multi(datos["destacados_idx"]),
    )
    return ESPERANDO_DESTACADOS


async def recibir_precio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip().replace(",", "").replace(".", "")
    if not texto.isdigit():
        await update.message.reply_text(textos.PRECIO_INVALIDO)
        return ESPERANDO_PRECIO
    context.user_data["nueva_propiedad"]["precio_base"] = float(texto)
    await update.message.reply_text(textos.PEDIR_DIRECCION)
    return ESPERANDO_DIRECCION


async def recibir_direccion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    context.user_data["nueva_propiedad"]["direccion_escrita"] = "" if _quiso_saltar(texto) else texto
    await update.message.reply_text(
        textos.PEDIR_UBICACION, reply_markup=teclados.teclado_compartir_ubicacion()
    )
    return ESPERANDO_UBICACION


async def recibir_ubicacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.location:
        lat = update.message.location.latitude
        lon = update.message.location.longitude
        context.user_data["nueva_propiedad"]["ubicacion"] = (
            f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
        )
        await update.message.reply_text(textos.UBICACION_RECIBIDA, reply_markup=ReplyKeyboardRemove())
    else:
        texto = (update.message.text or "").strip()
        if not _quiso_saltar(texto):
            await update.message.reply_text(textos.UBICACION_INVALIDA)
            return ESPERANDO_UBICACION
        context.user_data["nueva_propiedad"]["ubicacion"] = ""
        await update.message.reply_text(textos.UBICACION_OMITIDA, reply_markup=ReplyKeyboardRemove())

    await update.message.reply_text(
        textos.ELEGIR_METODO_PAGO, reply_markup=teclados.teclado_metodos_pago()
    )
    return ESPERANDO_METODO_PAGO


def _iniciar_extras(context) -> None:
    context.user_data["nueva_propiedad"]["extras_idx"] = set()
    context.user_data["nueva_propiedad"]["extras_custom"] = []


async def _pasar_a_extras(mensaje, context):
    _iniciar_extras(context)
    await mensaje.reply_text(
        textos.ELEGIR_EXTRAS_PUBLICAR, reply_markup=teclados.teclado_extras_publicar_multi(set())
    )
    return ESPERANDO_EXTRAS


async def recibir_metodo_pago_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    dato = query.data.split(":", 1)[1]

    if dato == "otro":
        await query.message.reply_text(textos.PEDIR_METODO_PAGO_OTRO)
        return ESPERANDO_METODO_PAGO_OTRO

    context.user_data["nueva_propiedad"]["metodo_pago"] = teclados.METODOS_PAGO_PREDEFINIDOS[int(dato)]
    return await _pasar_a_extras(query.message, context)


async def recibir_metodo_pago_otro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    context.user_data["nueva_propiedad"]["metodo_pago"] = "" if _quiso_saltar(texto) else texto
    return await _pasar_a_extras(update.message, context)


async def _empezar_a_pedir_precios_extras(mensaje, context):
    """Arranca (o continua) la cola de 'pedir precio de cada extra
    marcado, uno por uno'. Si ya no queda ninguno, sigue con horarios."""
    datos = context.user_data["nueva_propiedad"]
    pendientes = datos["extras_pendientes"]

    if not pendientes:
        return await _pasar_a_horarios(mensaje, context)

    nombre = pendientes[0]
    await mensaje.reply_text(textos.PEDIR_PRECIO_EXTRA.format(nombre=nombre))
    return ESPERANDO_EXTRA_PRECIO


async def _pasar_a_horarios(mensaje, context):
    datos = context.user_data["nueva_propiedad"]
    if datos["tipo"] == TipoPropiedad.HABITACION.value:
        await mensaje.reply_text(textos.PEDIR_HORARIOS_VISITA_DUENO)
        return ESPERANDO_HORARIOS_VISITA

    datos["horarios_visita"] = ""
    await mensaje.reply_text(textos.PEDIR_DISPONIBILIDAD)
    return ESPERANDO_DISPONIBILIDAD


async def recibir_extra_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    dato = query.data.split(":", 1)[1]
    datos = context.user_data["nueva_propiedad"]

    if dato == "otro":
        await query.message.reply_text(textos.PEDIR_EXTRA_NOMBRE_OTRO)
        return ESPERANDO_EXTRA_NOMBRE_OTRO

    if dato == "listo":
        nombres = [
            teclados.EXTRAS_PUBLICAR_PREDEFINIDOS[i]
            for i in range(len(teclados.EXTRAS_PUBLICAR_PREDEFINIDOS))
            if str(i) in datos["extras_idx"]
        ]
        nombres += datos["extras_custom"]
        datos["extras_pendientes"] = nombres
        datos["extras_con_precio"] = []
        return await _empezar_a_pedir_precios_extras(query.message, context)

    seleccionados = datos["extras_idx"]
    if dato in seleccionados:
        seleccionados.remove(dato)
    else:
        seleccionados.add(dato)
    await query.edit_message_reply_markup(
        reply_markup=teclados.teclado_extras_publicar_multi(seleccionados)
    )
    return ESPERANDO_EXTRAS


async def recibir_extra_nombre_otro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    if len(texto) < 2:
        await update.message.reply_text(textos.TEXTO_MUY_CORTO)
        return ESPERANDO_EXTRA_NOMBRE_OTRO

    datos = context.user_data["nueva_propiedad"]
    datos["extras_custom"].append(texto)
    await update.message.reply_text(
        textos.ELEGIR_EXTRAS_PUBLICAR,
        reply_markup=teclados.teclado_extras_publicar_multi(datos["extras_idx"]),
    )
    return ESPERANDO_EXTRAS


async def recibir_extra_precio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip().replace(",", "").replace(".", "")
    if not texto.isdigit():
        await update.message.reply_text(textos.PRECIO_INVALIDO)
        return ESPERANDO_EXTRA_PRECIO

    datos = context.user_data["nueva_propiedad"]
    nombre = datos["extras_pendientes"].pop(0)
    datos["extras_con_precio"].append((nombre, float(texto)))
    return await _empezar_a_pedir_precios_extras(update.message, context)


async def recibir_horarios_visita(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    context.user_data["nueva_propiedad"]["horarios_visita"] = "" if _quiso_saltar(texto) else texto
    await update.message.reply_text(textos.PEDIR_DISPONIBILIDAD)
    return ESPERANDO_DISPONIBILIDAD


async def recibir_disponibilidad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    context.user_data["nueva_propiedad"]["disponibilidad"] = "" if _quiso_saltar(texto) else texto
    await update.message.reply_text(textos.PEDIR_DESCRIPCION_PLANTILLA)
    return ESPERANDO_DESCRIPCION


async def recibir_descripcion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    if len(texto) < 15:
        await update.message.reply_text(textos.TEXTO_MUY_CORTO)
        return ESPERANDO_DESCRIPCION
    datos = context.user_data["nueva_propiedad"]
    datos["descripcion"] = texto

    extras_texto = (
        "\n".join(f"  - {n}: +{p:,.0f}/mes" for n, p in datos.get("extras_con_precio", []))
        or "  (ninguno)"
    )
    resumen = (
        f"{textos.CONFIRMAR_PUBLICACION}\n\n"
        f"Titulo (generado automaticamente): {datos['titulo']}\n"
        f"Descripcion: {datos['descripcion']}\n"
        f"Precio base por noche: {datos['precio_base']:,.0f}\n"
        f"Pais: {datos['pais']}\n"
        f"Ciudad: {datos['ciudad']}\n"
        f"Direccion: {datos['direccion_escrita'] or '(sin especificar)'}\n"
        f"Ubicacion en mapa: {'Compartida' if datos.get('ubicacion') else '(sin especificar)'}\n"
        f"Metodo de pago: {datos['metodo_pago'] or '(sin especificar)'}\n"
        f"Extras:\n{extras_texto}\n"
        f"Horarios de visita: {datos['horarios_visita'] or '(sin especificar)'}\n"
        f"Disponibilidad: {datos['disponibilidad'] or '(sin especificar)'}"
    )
    await update.message.reply_text(resumen, reply_markup=teclados.teclado_confirmar_publicacion())
    return ESPERANDO_CONFIRMACION


async def confirmar_publicacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("RASTRO: confirmar_publicacion fue llamada", flush=True)
    query = update.callback_query
    await query.answer()
    decision = query.data.split(":", 1)[1]

    if decision == "no":
        await query.edit_message_text(textos.PUBLICACION_CANCELADA)
        return ConversationHandler.END

    datos = context.user_data["nueva_propiedad"]
    try:
        id_nuevo = await llamar_con_limite(
            crear_propiedad,
            tipo=TipoPropiedad(datos["tipo"]),
            titulo=datos["titulo"],
            descripcion=datos["descripcion"],
            dueno_id=str(update.effective_user.id),
            precio_base=datos["precio_base"],
            pais=datos["pais"],
            ciudad=datos["ciudad"],
            direccion_escrita=datos["direccion_escrita"],
            ubicacion=datos.get("ubicacion", ""),
            metodo_pago=datos["metodo_pago"],
            horarios_visita=datos["horarios_visita"],
            disponibilidad=datos["disponibilidad"],
            destacados=datos.get("destacados", ""),
        )
        for nombre, precio in datos.get("extras_con_precio", []):
            await llamar_con_limite(agregar_extra_a_propiedad, id_nuevo, nombre, precio)
    except ErrorDelMotor as error:
        await query.message.reply_text(error.mensaje)
        return ConversationHandler.END

    print(f"RASTRO: propiedad publicada con id={id_nuevo}", flush=True)
    await query.edit_message_text(textos.PUBLICACION_EXITOSA)
    return ConversationHandler.END
