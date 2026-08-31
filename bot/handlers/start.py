"""
Comando /start y el menu principal. Es la puerta de entrada al bot.
"""

import asyncio
import time

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from bot import textos, teclados
from bot.seguro import llamar_con_limite, ErrorDelMotor
from motor.sheets_client import leer_todas_las_filas
from motor.metricas import resumen_panel


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("RASTRO: cmd_start fue llamado", flush=True)
    await update.message.reply_text(
        textos.BIENVENIDA, reply_markup=teclados.teclado_menu_principal()
    )
    # IMPORTANTE: /start esta registrado como entry_point Y como fallback.
    # Si no se devuelve ConversationHandler.END explicitamente, un /start
    # enviado a mitad de una conversacion (ej. mientras el bot espera una
    # fecha) NO reinicia el estado interno, y el bot queda esperando la
    # respuesta anterior aunque en pantalla se vea el menu principal.
    return ConversationHandler.END


async def cmd_probar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando de diagnostico: prueba la conexion con Google Sheets sola,
    sin pasar por todo el flujo de busqueda, y reporta el resultado exacto."""
    await update.message.reply_text("Probando conexion con la hoja...")
    inicio = time.time()
    try:
        filas = await asyncio.to_thread(leer_todas_las_filas, "Propiedades")
        duracion = time.time() - inicio
        await update.message.reply_text(
            f"Conexion exitosa en {duracion:.1f} segundos.\nFilas encontradas: {len(filas)}"
        )
    except Exception as error:
        duracion = time.time() - inicio
        await update.message.reply_text(
            f"Error despues de {duracion:.1f} segundos:\n{type(error).__name__}: {error}"
        )


async def menu_volver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Vuelve al menu principal desde una pantalla sin salida."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        textos.BIENVENIDA, reply_markup=teclados.teclado_menu_principal()
    )


async def cmd_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Panel simple para el equipo: propiedades, reservas y las mas
    vistas, con datos reales sacados de las interacciones del bot."""
    try:
        resumen = await llamar_con_limite(resumen_panel)
    except ErrorDelMotor as error:
        await update.message.reply_text(error.mensaje)
        return

    por_tipo = "\n".join(f"  - {t}: {c}" for t, c in resumen["por_tipo"].items()) or "  (sin datos)"
    por_pais = "\n".join(f"  - {p}: {c}" for p, c in resumen["por_pais"].items()) or "  (sin datos)"
    por_estado_reserva = (
        "\n".join(f"  - {e}: {c}" for e, c in resumen["por_estado_reserva"].items())
        or "  (sin reservas todavia)"
    )
    top_vistas = (
        "\n".join(f"  {i+1}. {titulo} ({cantidad} vistas)" for i, (titulo, cantidad) in enumerate(resumen["top_vistas"]))
        or "  (todavia nadie ha visto ninguna propiedad)"
    )

    texto = (
        "📊 Panel WeHabit\n\n"
        f"Propiedades totales: {resumen['total_propiedades']} "
        f"({resumen['activas']} activas, {resumen['inactivas']} inactivas)\n\n"
        f"Por tipo:\n{por_tipo}\n\n"
        f"Por pais (top 10):\n{por_pais}\n\n"
        f"Reservas totales: {resumen['total_reservas']}\n"
        f"Por estado:\n{por_estado_reserva}\n\n"
        f"Mas vistas:\n{top_vistas}"
    )
    await update.message.reply_text(texto)
