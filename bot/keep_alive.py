"""
Pequeno servidor web que solo responde 'estoy vivo'. Un servicio externo
(UptimeRobot, gratis) le hace ping cada pocos minutos para que la
plataforma de hosting gratuita no apague el bot por inactividad.
"""

from threading import Thread

from flask import Flask

app = Flask("keep_alive")


@app.route("/")
def inicio():
    return "ChambreBot esta despierto."


def _correr():
    app.run(host="0.0.0.0", port=8080)


def mantener_vivo():
    hilo = Thread(target=_correr)
    hilo.start()
