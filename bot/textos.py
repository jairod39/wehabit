"""
Todos los textos que el usuario ve, en un solo lugar.
Cuando hagamos la version en ingles, este es el UNICO archivo que
hay que duplicar y traducir - la logica del bot no cambia nada.
"""

BIENVENIDA = (
    "Hola! Soy ChambreBot de WeHabit.\n\n"
    "Te ayudo a encontrar habitaciones y alojamientos verificados, "
    "y a agendar tu visita directo con el dueno.\n\n"
    "Que quieres hacer?"
)

BOTON_EXPLORAR = "Buscar alojamiento"
BOTON_PUBLICAR = "Publicar mi propiedad"

PUBLICAR_PROXIMAMENTE = (
    "Publicar tu propiedad directo desde el bot esta llegando pronto.\n"
    "Por ahora, escribenos y te ayudamos a cargarla manualmente."
)

ELEGIR_TIPO = "Que tipo de alojamiento buscas?"
ELEGIR_PAIS = "En que pais?"
ELEGIR_CIUDAD = "En que ciudad?"
SIN_RESULTADOS = "No encontramos alojamientos con esos filtros todavia."

ETIQUETA_FULL = "🔥 FULL - Todo incluido"

BOTON_AGENDAR = "Agendar visita"
BOTON_VOLVER = "Volver"

PEDIR_FECHA_INICIO = "Desde que fecha necesitas el alojamiento? (formato: AAAA-MM-DD)"
PEDIR_FECHA_FIN = "Hasta que fecha? (formato: AAAA-MM-DD)"
FECHA_INVALIDA = "Esa fecha no la entendi. Usa el formato AAAA-MM-DD, por ejemplo 2026-09-15."
FECHA_FIN_ANTES_DE_INICIO = "La fecha final no puede ser antes de la inicial. Intenta de nuevo."

PEDIR_HORA_VISITA = "A que hora quieres visitar? (formato: HH:MM, ejemplo 15:30)"
HORA_INVALIDA = "Esa hora no la entendi. Usa el formato HH:MM, por ejemplo 15:30 o 09:00."

NOTA_UBICACION_PENDIENTE = (
    "La direccion exacta y el mapa se comparten cuando confirmes tu visita, "
    "para proteger la privacidad del dueno."
)

NOTA_SIN_AGENDAMIENTO = (
    "Este alojamiento se maneja a traves de una casa de arrendamiento. "
    "Usa el codigo de arriba directamente en su sitio para mas informacion, "
    "no agendamos la visita por aqui."
)


def texto_resultados(cantidad: int) -> str:
    palabra = "opcion" if cantidad == 1 else "opciones"
    return f"Encontramos {cantidad} {palabra}:"

ELEGIR_EXTRAS = "Elige los adicionales que quieres (los que ya vienen incluidos no se pueden quitar):"
BOTON_LISTO_EXTRAS = "Listo, continuar"

CONFIRMAR_RESERVA = "Revisa el resumen antes de confirmar:"
BOTON_CONFIRMAR = "Confirmar agendamiento"
BOTON_CANCELAR = "Cancelar"

RESERVA_CREADA = (
    "Tu visita quedo agendada.\n\n"
    "El dueno va a confirmar contigo los detalles. "
    "Este es su metodo de pago, solo para que lo tengas listo "
    "cuando decidas confirmar en persona (nosotros no cobramos nada aqui):\n\n"
)

RESERVA_CANCELADA = "Sin problema, cancelamos el agendamiento."
