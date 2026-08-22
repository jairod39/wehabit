"""
Comando /start y el menu principal. Es la puerta de entrada al bot.
"""

import asyncio
import time

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from bot import textos, teclados
from motor.sheets_client import leer_todas_las_filas


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


async def menu_publicar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        textos.PUBLICAR_PROXIMAMENTE, reply_markup=teclados.teclado_volver_menu()
    )


async def menu_volver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Vuelve al menu principal desde una pantalla sin salida (ej. 'publicar')."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        textos.BIENVENIDA, reply_markup=teclados.teclado_menu_principal()
    )
