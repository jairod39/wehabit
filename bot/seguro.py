"""
Envoltorio para llamar funciones del motor con un limite de tiempo.
Sin esto, si Google Sheets se demora o la red falla, el bot se queda
trabado en silencio para siempre. Con esto, avisa y se resetea.
"""

import asyncio

TIEMPO_LIMITE_SEGUNDOS = 15


class ErrorDelMotor(Exception):
    """Se lanza cuando una consulta al motor falla o tarda demasiado."""
    def __init__(self, mensaje: str):
        super().__init__(mensaje)
        self.mensaje = mensaje


async def llamar_con_limite(funcion, *args, **kwargs):
    """Ejecuta una funcion del motor (sincrona) en un carril aparte,
    con un limite de tiempo. Si tarda mas de la cuenta o falla,
    lanza ErrorDelMotor con un mensaje entendible."""
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(funcion, *args, **kwargs),
            timeout=TIEMPO_LIMITE_SEGUNDOS,
        )
    except asyncio.TimeoutError:
        raise ErrorDelMotor(
            f"La hoja de datos tardo mas de {TIEMPO_LIMITE_SEGUNDOS} segundos en responder. "
            "Puede ser la red, intenta de nuevo con /start."
        )
    except Exception as error:
        raise ErrorDelMotor(f"Hubo un problema leyendo los datos: {error}")
