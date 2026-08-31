"""
Punto de entrada del bot. Este es el UNICO archivo que se ejecuta
directamente (con "python -m bot.main"). Solo conecta piezas, no
tiene logica propia.
"""

from telegram.request import HTTPXRequest
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)

from motor.config import TELEGRAM_BOT_TOKEN, validar_configuracion
from bot.handlers import start, explorar, agendar, publicar, mispublicaciones
from bot.keep_alive import mantener_vivo


async def manejar_error(update, context):
    """Imprime en los logs CUALQUIER error que ocurra en cualquier parte
    del bot, con todo el detalle, para poder diagnosticar sin adivinar."""
    import traceback
    print("=" * 60, flush=True)
    print(f"RASTRO: ERROR CAPTURADO: {context.error}", flush=True)
    if context.error:
        traceback.print_exception(type(context.error), context.error, context.error.__traceback__)
    print("=" * 60, flush=True)


def construir_aplicacion() -> Application:
    validar_configuracion()
    solicitud = HTTPXRequest(
        connect_timeout=20.0,
        read_timeout=20.0,
        write_timeout=20.0,
        pool_timeout=20.0,
    )
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).request(solicitud).build()

    conversacion = ConversationHandler(
        entry_points=[
            CommandHandler("start", start.cmd_start),
            CallbackQueryHandler(explorar.iniciar_exploracion, pattern="^menu:explorar$"),
        ],
        states={
            explorar.ELEGIR_PAIS: [
                CallbackQueryHandler(explorar.recibir_tipo, pattern="^tipo:"),
                CallbackQueryHandler(explorar.volver_a_menu_principal, pattern="^volver:menu$"),
            ],
            explorar.ELEGIR_CIUDAD: [
                CallbackQueryHandler(explorar.recibir_pais, pattern="^pais:"),
                CallbackQueryHandler(explorar.volver_a_tipo, pattern="^volver:tipo$"),
            ],
            explorar.VER_LISTA: [
                CallbackQueryHandler(explorar.recibir_ciudad, pattern="^ciudad:"),
                CallbackQueryHandler(explorar.mostrar_detalle, pattern="^ver:"),
                CallbackQueryHandler(agendar.iniciar_agendamiento, pattern="^agendar:"),
                CallbackQueryHandler(explorar.iniciar_exploracion, pattern="^menu:explorar$"),
                CallbackQueryHandler(explorar.volver_a_pais, pattern="^volver:pais$"),
                CallbackQueryHandler(explorar.volver_a_ciudad, pattern="^volver:ciudad$"),
                CallbackQueryHandler(explorar.volver_a_lista, pattern="^volver:lista$"),
            ],
            agendar.ESPERANDO_HORARIO: [
                CallbackQueryHandler(agendar.recibir_horario, pattern="^horario:"),
            ],
            agendar.ESPERANDO_FECHA_ALTERNATIVA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, agendar.recibir_fecha_alternativa)
            ],
            agendar.ESPERANDO_EXTRAS: [
                CallbackQueryHandler(agendar.alternar_extra, pattern="^extra:"),
            ],
            agendar.ESPERANDO_CONFIRMACION: [
                CallbackQueryHandler(agendar.confirmar_reserva, pattern="^confirmar:"),
            ],
        },
        fallbacks=[CommandHandler("start", start.cmd_start)],
    )

    conversacion_publicar = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(publicar.iniciar_publicacion, pattern="^menu:publicar$"),
        ],
        states={
            publicar.ESPERANDO_TIPO: [
                CallbackQueryHandler(publicar.recibir_tipo, pattern="^publicar_tipo:")
            ],
            publicar.ESPERANDO_CONTINENTE: [
                CallbackQueryHandler(publicar.recibir_continente, pattern="^continente:")
            ],
            publicar.ESPERANDO_PAIS: [
                CallbackQueryHandler(publicar.paginar_paises, pattern="^paispub_pag:"),
                CallbackQueryHandler(publicar.volver_a_continentes, pattern="^continente_volver:"),
                CallbackQueryHandler(publicar.recibir_pais, pattern="^paispub:"),
            ],
            publicar.ESPERANDO_CIUDAD: [
                CallbackQueryHandler(publicar.paginar_ciudades, pattern="^ciudadpub_pag:"),
                CallbackQueryHandler(publicar.pedir_ciudad_otra, pattern="^ciudadpub_otra:"),
                CallbackQueryHandler(publicar.recibir_ciudad, pattern="^ciudadpub:"),
            ],
            publicar.ESPERANDO_CIUDAD_OTRA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, publicar.recibir_ciudad_otra)
            ],
            publicar.ESPERANDO_DESTACADO: [
                CallbackQueryHandler(publicar.recibir_destacado_menu, pattern="^destacado:")
            ],
            publicar.ESPERANDO_DESTACADO_OTRO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, publicar.recibir_destacado_otro)
            ],
            publicar.ESPERANDO_DESCRIPCION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, publicar.recibir_descripcion)
            ],
            publicar.ESPERANDO_PRECIO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, publicar.recibir_precio)
            ],
            publicar.ESPERANDO_DIRECCION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, publicar.recibir_direccion)
            ],
            publicar.ESPERANDO_METODO_PAGO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, publicar.recibir_metodo_pago)
            ],
            publicar.ESPERANDO_HORARIOS_VISITA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, publicar.recibir_horarios_visita)
            ],
            publicar.ESPERANDO_DISPONIBILIDAD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, publicar.recibir_disponibilidad)
            ],
            publicar.ESPERANDO_CONFIRMACION: [
                CallbackQueryHandler(publicar.confirmar_publicacion, pattern="^confirmar_publicar:")
            ],
        },
        fallbacks=[CommandHandler("start", start.cmd_start)],
    )

    app.add_handler(conversacion)
    app.add_handler(conversacion_publicar)
    app.add_handler(CommandHandler("probar", start.cmd_probar))
    app.add_handler(CallbackQueryHandler(start.menu_volver, pattern="^menu:volver$"))
    app.add_handler(
        CallbackQueryHandler(mispublicaciones.mostrar_mis_publicaciones, pattern="^menu:mispublicaciones$")
    )
    app.add_handler(CallbackQueryHandler(mispublicaciones.ver_publicacion, pattern="^verpub:"))
    app.add_handler(CallbackQueryHandler(mispublicaciones.alternar_publicacion, pattern="^togglepub:"))
    app.add_error_handler(manejar_error)

    return app


if __name__ == "__main__":
    mantener_vivo()
    aplicacion = construir_aplicacion()
    print("ChambreBot esta corriendo...")
    aplicacion.run_polling(drop_pending_updates=True)
