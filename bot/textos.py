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
BOTON_MIS_PUBLICACIONES = "Mis publicaciones"

MIS_PUBLICACIONES = "Estas son tus propiedades. Toca una para verla o cambiar su estado:"
SIN_PUBLICACIONES_PROPIAS = "Todavia no tienes ninguna propiedad publicada."
PUBLICACION_NO_ENCONTRADA = "No encontramos esa publicacion (puede que ya no exista)."

PUBLICAR_INTRO = (
    "Vamos a publicar tu propiedad. Te voy preguntando un dato a la vez, "
    "no necesitas tocar ninguna hoja de calculo.\n\n"
    "Que tipo de alojamiento es?"
)

PEDIR_TITULO = "Ponle un titulo corto (ej: 'Habitacion amoblada cerca al metro')"
ELEGIR_DESTACADO = "Marca todo lo que aplique (puedes elegir varios). Cuando termines, toca Listo:"
PEDIR_DESTACADO = "Escribe el detalle que quieras agregar (ej: 'con vista al mar')."

ELEGIR_METODO_PAGO = "Como prefieres que te paguen?"
PEDIR_METODO_PAGO_OTRO = "Escribe el metodo de pago que prefieres."

ELEGIR_EXTRAS_PUBLICAR = (
    "Marca lo que tu propiedad ofrece (puedes elegir varios). "
    "A cada uno le vas a poner un precio MENSUAL despues. Toca Listo cuando termines:"
)
PEDIR_EXTRA_NOMBRE_OTRO = "Como se llama ese extra?"
PEDIR_PRECIO_EXTRA = "Cuanto cuesta '{nombre}' al MES? (solo el numero)"

PEDIR_DESCRIPCION_PLANTILLA = (
    "Ya casi. Ahora escribe la descripcion siguiendo esta guia, para que "
    "siempre se lea igual de clara:\n\n"
    "1) Como es el ambiente (tranquilo, familiar, estudiantil...)\n"
    "2) Que hay cerca (transporte, comercio, universidades...)\n"
    "3) Algo que la haga especial\n\n"
    "Ejemplo: 'Ambiente tranquilo y familiar. A 5 minutos del metro y "
    "cerca a varios supermercados. Recien remodelada, con mucha luz natural.'"
)
PEDIR_DESCRIPCION = "Ahora describela: que tiene, como es, que la hace buena."
PEDIR_PRECIO = "Cual es el precio por noche? (solo el numero, sin simbolos)"
PRECIO_INVALIDO = "Eso no parece un numero. Escribe solo el precio, ej: 500000"
PEDIR_PAIS = "En que pais esta ubicada?"
PEDIR_CIUDAD = "En que ciudad?"
PEDIR_DIRECCION = (
    "Direccion (para mostrarla solo cuando alguien confirme una visita). "
    "Si prefieres no darla todavia, escribe: -"
)
PEDIR_METODO_PAGO = "Como prefieres que te paguen? (ej: Transferencia, efectivo). Si no aplica, escribe: -"
PEDIR_UBICACION = (
    "Toca el boton para compartir tu ubicacion exacta (queda guardada para "
    "mostrarla solo cuando alguien confirme una visita). Si prefieres no darla, escribe: -"
)
UBICACION_RECIBIDA = "Ubicacion guardada."
UBICACION_OMITIDA = "Sin problema, sin ubicacion por ahora."
UBICACION_INVALIDA = "Usa el boton para compartir tu ubicacion, o escribe - para saltar este paso."
PEDIR_HORARIOS_VISITA_DUENO = (
    "Que horarios ofreces para visitas? Formato: Dia HH:MM, separados por comas.\n"
    "Ejemplo: Viernes 15:00, Sabado 10:00, Sabado 15:00\n"
    "Si prefieres definirlos despues, escribe: -"
)
PEDIR_DISPONIBILIDAD = (
    "Algo que quieras decir sobre disponibilidad de estadia? (opcional, texto libre). "
    "Si no, escribe: -"
)
TEXTO_MUY_CORTO = "Eso quedo muy corto, dame un poco mas de detalle."

CONFIRMAR_PUBLICACION = "Revisa que todo este bien antes de publicar:"
PUBLICACION_CANCELADA = "Sin problema, no se publico nada. Puedes intentarlo de nuevo cuando quieras."
PUBLICACION_EXITOSA = (
    "Listo, tu propiedad ya esta publicada y visible en las busquedas. "
    "Si tienes mas habitaciones en el mismo predio, no tienes que "
    "volver a escribir todo, toca 'Publicar otra'."
)
PUBLICAR_OTRA_INTRO = (
    "Vamos con la siguiente. Uso el mismo pais, ciudad, direccion, "
    "ubicacion, metodo de pago y horarios de la anterior — solo te "
    "pregunto lo que suele cambiar entre habitaciones."
)

PUBLICAR_PROXIMAMENTE = (
    "Publicar tu propiedad directo desde el bot esta llegando pronto.\n"
    "Por ahora, escribenos y te ayudamos a cargarla manualmente."
)

ELEGIR_TIPO = "Que tipo de alojamiento buscas?"
ELEGIR_PAIS = "En que pais?"
ELEGIR_CONTINENTE = "Primero, en que continente esta?"
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

ELEGIR_HORARIO_VISITA = "Estos son los horarios disponibles para visitar. Elige uno:"

SIN_HORARIOS_DEFINIDOS = (
    "El dueno todavia no configuro horarios fijos para visitas.\n\n"
    "Escribe la fecha y hora que te gustaria (formato: AAAA-MM-DD HH:MM, "
    "ejemplo 2026-09-15 15:30). Quedara pendiente de confirmacion."
)

PEDIR_HORARIO_ALTERNATIVO = (
    "Escribe la fecha y hora que propones (formato: AAAA-MM-DD HH:MM, "
    "ejemplo 2026-09-15 15:30). Quedara pendiente de confirmacion."
)

HORARIO_ALTERNATIVO_INVALIDO = (
    "No entendi ese formato. Usa AAAA-MM-DD HH:MM, ejemplo 2026-09-15 15:30."
)

AVISO_HORARIO_SUJETO_A_CONFIRMACION = (
    "Ojo: este horario no estaba entre los que el dueno ya tenia definidos, "
    "asi que queda PENDIENTE hasta que el confirme contigo directamente."
)

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
