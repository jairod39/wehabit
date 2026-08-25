"""
Pequeno servidor web que solo responde 'estoy vivo'. Ademas, este mismo
proceso se auto-visita por internet cada pocos minutos (no basta llamarse
a si mismo por dentro, tiene que salir y volver a entrar por la URL
publica para que Render lo cuente como actividad real y no lo duerma).

Esto es un respaldo propio, no un reemplazo de UptimeRobot: si algun dia
Render cambia como mide la inactividad, o si este auto-ping falla por lo
que sea, UptimeRobot sigue funcionando como plan B independiente. Dos
mecanismos distintos vigilando lo mismo es mas confiable que uno solo.
"""

import os
import time
import urllib.request
from threading import Thread

from flask import Flask

app = Flask("keep_alive")

# Render pone esta variable de entorno solo automaticamente en sus
# servicios (https://chambrebot.onrender.com). Si por lo que sea no
# estuviera disponible, usamos la URL fija como respaldo.
URL_PROPIA = os.environ.get("RENDER_EXTERNAL_URL", "https://chambrebot.onrender.com")
MINUTOS_ENTRE_PINGS = 10


@app.route("/")
def inicio():
    return "ChambreBot esta despierto."


def _correr_servidor():
    app.run(host="0.0.0.0", port=8080)


def _auto_ping():
    # Espera antes del primer ping para darle tiempo al servidor Flask
    # de arriba a terminar de arrancar antes de visitarse a si mismo.
    time.sleep(30)
    while True:
        try:
            with urllib.request.urlopen(URL_PROPIA, timeout=15) as respuesta:
                print(f"RASTRO: auto-ping OK ({respuesta.status})", flush=True)
        except Exception as error:
            print(f"RASTRO: auto-ping fallo: {error}", flush=True)
        time.sleep(MINUTOS_ENTRE_PINGS * 60)


def mantener_vivo():
    Thread(target=_correr_servidor, daemon=True).start()
    Thread(target=_auto_ping, daemon=True).start()
