"""
Conversacion para que un dueno PUBLIQUE su propiedad hablando con el bot,
sin tocar el Google Sheet a mano y CASI SIN escribir texto libre.

Filosofia: todo lo que se pueda estandarizar con un menu, se pide con
un menu (tipo, pais, ciudad, detalle destacado). Solo se deja texto
libre donde de verdad no hay forma de estandarizarlo (descripcion,
precio como numero, direccion, metodo de pago).

- PAIS: lista fija (dato geografico real, no cambia).
- CIUDAD: se arma con las ciudades que YA existen en nuestros datos
  para ese pais. Si la ciudad no esta, se agrega la primera vez y
  desde ahi queda disponible en el menu para todos los que publiquen
  despues en ese mismo pais. Asi el "menu" crece solo con datos reales,
  sin depender de una base de datos externa de todas las ciudades del
  mundo (eso no existe como algo manejable en botones).
- TITULO: no se pide como texto libre, se arma solo a partir de
  tipo + ciudad + detalle destacado (elegido de un menu tambien).

Es una ConversationHandler SEPARADA de la de explorar/agendar (no
comparte el mismo diccionario de estados).
"""

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from motor.models import TipoPropiedad
from motor.propiedades import crear_propiedad, listar_ciudades_de_pais
from bot import textos, teclados
from bot.seguro import llamar_con_limite, ErrorDelMotor

(
    ESPERANDO_TIPO,
    ESPERANDO_PAIS,
    ESPERANDO_CIUDAD,
    ESPERANDO_CIUDAD_OTRA,
    ESPERANDO_DESTACADO,
    ESPERANDO_DESTACADO_OTRO,
    ESPERANDO_DESCRIPCION,
    ESPERANDO_PRECIO,
    ESPERANDO_DIRECCION,
    ESPERANDO_METODO_PAGO,
    ESPERANDO_HORARIOS_VISITA,
    ESPERANDO_DISPONIBILIDAD,
    ESPERANDO_CONFIRMACION,
) = range(200, 213)

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
        textos.ELEGIR_PAIS, reply_markup=teclados.teclado_paises_publicar()
    )
    return ESPERANDO_PAIS


async def paginar_paises(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pagina = int(query.data.split(":", 1)[1])
    await query.edit_message_reply_markup(reply_markup=teclados.teclado_paises_publicar(pagina))
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


async def recibir_ciudad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ciudad = query.data.split(":", 1)[1]
    context.user_data["nueva_propiedad"]["ciudad"] = ciudad
    await query.message.reply_text(
        textos.ELEGIR_DESTACADO, reply_markup=teclados.teclado_destacados()
    )
    return ESPERANDO_DESTACADO


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
    # Esta ciudad queda grabada al publicar (va en la fila de la
    # propiedad), asi que la proxima persona que publique en este mismo
    # pais ya la va a ver en el menu, sin tener que escribirla de nuevo.
    context.user_data["nueva_propiedad"]["ciudad"] = texto
    await update.message.reply_text(
        textos.ELEGIR_DESTACADO, reply_markup=teclados.teclado_destacados()
    )
    return ESPERANDO_DESTACADO


def _construir_titulo(context: ContextTypes.DEFAULT_TYPE, detalle: str) -> None:
    """Construye el titulo SIEMPRE con la misma estructura (Tipo en
    Ciudad - detalle), sin importar si el detalle vino del menu o fue
    escrito a mano."""
    datos = context.user_data["nueva_propiedad"]
    tipo_legible = datos["tipo"].capitalize()
    datos["titulo"] = f"{tipo_legible} en {datos['ciudad']} - {detalle}"
    datos["destacado"] = detalle


async def recibir_destacado_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    dato = query.data.split(":", 1)[1]

    if dato == "otro":
        await query.message.reply_text(textos.PEDIR_DESTACADO)
        return ESPERANDO_DESTACADO_OTRO

    detalle = teclados.DESTACADOS_PREDEFINIDOS[int(dato)]
    _construir_titulo(context, detalle)
    await query.message.reply_text(textos.PEDIR_DESCRIPCION)
    return ESPERANDO_DESCRIPCION


async def recibir_destacado_otro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    if len(texto) < 3:
        await update.message.reply_text(textos.TEXTO_MUY_CORTO)
        return ESPERANDO_DESTACADO_OTRO

    _construir_titulo(context, texto)
    await update.message.reply_text(textos.PEDIR_DESCRIPCION)
    return ESPERANDO_DESCRIPCION


async def recibir_descripcion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    if len(texto) < 5:
        await update.message.reply_text(textos.TEXTO_MUY_CORTO)
        return ESPERANDO_DESCRIPCION
    context.user_data["nueva_propiedad"]["descripcion"] = texto
    await update.message.reply_text(textos.PEDIR_PRECIO)
    return ESPERANDO_PRECIO


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
    await update.message.reply_text(textos.PEDIR_METODO_PAGO)
    return ESPERANDO_METODO_PAGO


async def recibir_metodo_pago(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    context.user_data["nueva_propiedad"]["metodo_pago"] = "" if _quiso_saltar(texto) else texto

    if context.user_data["nueva_propiedad"]["tipo"] == TipoPropiedad.HABITACION.value:
        await update.message.reply_text(textos.PEDIR_HORARIOS_VISITA_DUENO)
        return ESPERANDO_HORARIOS_VISITA

    context.user_data["nueva_propiedad"]["horarios_visita"] = ""
    await update.message.reply_text(textos.PEDIR_DISPONIBILIDAD)
    return ESPERANDO_DISPONIBILIDAD


async def recibir_horarios_visita(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    context.user_data["nueva_propiedad"]["horarios_visita"] = "" if _quiso_saltar(texto) else texto
    await update.message.reply_text(textos.PEDIR_DISPONIBILIDAD)
    return ESPERANDO_DISPONIBILIDAD


async def recibir_disponibilidad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    context.user_data["nueva_propiedad"]["disponibilidad"] = "" if _quiso_saltar(texto) else texto

    datos = context.user_data["nueva_propiedad"]
    resumen = (
        f"{textos.CONFIRMAR_PUBLICACION}\n\n"
        f"Titulo (generado automaticamente): {datos['titulo']}\n"
        f"Descripcion: {datos['descripcion']}\n"
        f"Precio por noche: {datos['precio_base']:,.0f}\n"
        f"Pais: {datos['pais']}\n"
        f"Ciudad: {datos['ciudad']}\n"
        f"Direccion: {datos['direccion_escrita'] or '(sin especificar)'}\n"
        f"Metodo de pago: {datos['metodo_pago'] or '(sin especificar)'}\n"
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
            metodo_pago=datos["metodo_pago"],
            horarios_visita=datos["horarios_visita"],
            disponibilidad=datos["disponibilidad"],
        )
    except ErrorDelMotor as error:
        await query.message.reply_text(error.mensaje)
        return ConversationHandler.END

    print(f"RASTRO: propiedad publicada con id={id_nuevo}", flush=True)
    await query.edit_message_text(textos.PUBLICACION_EXITOSA)
    return ConversationHandler.END
