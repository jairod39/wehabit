"""
Todo lo relacionado con buscar y crear propiedades (habitaciones,
apartamentos, etc). Este archivo no sabe que existe Google Sheets:
solo le pide filas "crudas" a sheets_client y las convierte en
objetos Propiedad, con sus extras ya cargados adentro.
"""

import uuid

from motor.models import Propiedad, Extra, TipoPropiedad
from motor.sheets_client import leer_todas_las_filas, agregar_fila, actualizar_celda_por_id


def _texto_a_booleano(valor) -> bool:
    return str(valor).strip().upper() in ("TRUE", "SI", "1", "VERDADERO")


def _cargar_extras_por_propiedad() -> dict[str, list[Extra]]:
    """Lee toda la pestana 'Extras' UNA sola vez y los agrupa por propiedad_id."""
    filas = leer_todas_las_filas("Extras")
    extras_por_propiedad: dict[str, list[Extra]] = {}
    for fila in filas:
        propiedad_id = str(fila.get("propiedad_id", ""))
        if not propiedad_id:
            continue
        extra = Extra(
            id=str(fila["id"]),
            nombre=fila["nombre"],
            precio_extra=float(fila.get("precio_extra") or 0),
            incluido_por_defecto=_texto_a_booleano(fila.get("incluido_por_defecto")),
        )
        extras_por_propiedad.setdefault(propiedad_id, []).append(extra)
    return extras_por_propiedad


def _fila_a_propiedad(fila: dict, extras: list[Extra]) -> Propiedad:
    fotos_texto = str(fila.get("fotos", ""))
    return Propiedad(
        id=str(fila["id"]),
        tipo=TipoPropiedad(fila["tipo"]),
        titulo=fila["titulo"],
        descripcion=fila["descripcion"],
        dueno_id=str(fila["dueno_id"]),
        precio_base=float(fila["precio_base"]),
        pais=fila["pais"],
        ciudad=fila["ciudad"],
        ubicacion=fila.get("ubicacion", ""),
        direccion_escrita=fila.get("direccion_escrita", ""),
        metodo_pago=fila.get("metodo_pago", ""),
        codigo_casa_arrendamiento=fila.get("codigo_casa_arrendamiento", ""),
        horarios_visita=fila.get("horarios_visita", ""),
        disponibilidad=fila.get("disponibilidad", ""),
        fotos=[f.strip() for f in fotos_texto.split(",") if f.strip()],
        activa=_texto_a_booleano(fila.get("activa", "")),
        extras_disponibles=extras,
    )


def listar_propiedades(
    tipo: TipoPropiedad | None = None,
    pais: str | None = None,
    ciudad: str | None = None,
) -> list[Propiedad]:
    """Devuelve las propiedades activas, filtradas opcionalmente por tipo, pais y/o ciudad.

    IMPORTANTE: si una fila del Sheet tiene un dato mal puesto (precio en
    blanco, un tipo mal escrito, etc), esa fila se ignora y se reporta en
    los logs, pero NO tumba la busqueda completa. Antes, un solo error en
    cualquier parte del Sheet rompia TODAS las busquedas silenciosamente.
    """
    filas = leer_todas_las_filas("Propiedades")
    extras_por_propiedad = _cargar_extras_por_propiedad()

    propiedades = []
    for fila in filas:
        id_fila = fila.get("id")
        if not id_fila:
            continue
        try:
            propiedad = _fila_a_propiedad(fila, extras_por_propiedad.get(str(id_fila), []))
        except (ValueError, KeyError) as error:
            print(
                f"RASTRO: fila 'id={id_fila}' de Propiedades tiene un dato invalido "
                f"y se ignoro ({error}). Revisa esa fila en el Sheet.",
                flush=True,
            )
            continue
        propiedades.append(propiedad)

    propiedades = [p for p in propiedades if p.activa]

    if tipo is not None:
        propiedades = [p for p in propiedades if p.tipo == tipo]
    if pais is not None:
        propiedades = [p for p in propiedades if p.pais.lower() == pais.lower()]
    if ciudad is not None:
        propiedades = [p for p in propiedades if p.ciudad.lower() == ciudad.lower()]

    return propiedades


def obtener_propiedad(id_propiedad: str) -> Propiedad | None:
    """Busca una propiedad especifica por su id. Devuelve None si no existe."""
    for propiedad in listar_propiedades():
        if propiedad.id == id_propiedad:
            return propiedad
    return None


def crear_propiedad(
    tipo: TipoPropiedad,
    titulo: str,
    descripcion: str,
    dueno_id: str,
    precio_base: float,
    pais: str,
    ciudad: str,
    direccion_escrita: str = "",
    metodo_pago: str = "",
    horarios_visita: str = "",
    disponibilidad: str = "",
) -> str:
    """
    Escribe una propiedad nueva en la pestana 'Propiedades' y devuelve
    su id. El id es tecnico por ahora (invisible para el usuario, igual
    que los demas); mas adelante, cuando se generen QRs para compartir,
    se reemplaza por un identificador mas amigable.
    """
    id_nuevo = f"u{uuid.uuid4().hex[:8]}"
    agregar_fila(
        "Propiedades",
        [
            id_nuevo,
            tipo.value,
            titulo,
            descripcion,
            dueno_id,
            precio_base,
            pais,
            ciudad,
            "",  # ubicacion (link de mapa) - se agrega mas adelante
            direccion_escrita,
            metodo_pago,
            "",  # codigo_casa_arrendamiento - no aplica a publicaciones directas
            horarios_visita,
            disponibilidad,
            "",  # fotos - se agrega mas adelante
            "TRUE",
        ],
    )
    return id_nuevo


def listar_propiedades_de_dueno(dueno_id: str) -> list[Propiedad]:
    """
    Todas las propiedades de un dueno especifico, ACTIVAS E INACTIVAS
    (a diferencia de listar_propiedades, que solo trae las activas).
    Sirve para que el dueno vea y controle todo lo suyo, incluido lo
    que tiene apagado por ahora.
    """
    filas = leer_todas_las_filas("Propiedades")
    extras_por_propiedad = _cargar_extras_por_propiedad()

    propiedades = []
    for fila in filas:
        if str(fila.get("dueno_id", "")) != str(dueno_id):
            continue
        id_fila = fila.get("id")
        if not id_fila:
            continue
        try:
            propiedad = _fila_a_propiedad(fila, extras_por_propiedad.get(str(id_fila), []))
        except (ValueError, KeyError) as error:
            print(
                f"RASTRO: fila 'id={id_fila}' de Propiedades tiene un dato invalido "
                f"y se ignoro ({error}).",
                flush=True,
            )
            continue
        propiedades.append(propiedad)

    return propiedades


def cambiar_estado_propiedad(id_propiedad: str, activa: bool) -> bool:
    """Activa o desactiva una propiedad sin tocar ningun otro dato suyo.
    Devuelve False si no encontro la propiedad."""
    return actualizar_celda_por_id(
        "Propiedades", id_propiedad, "id", "activa", "TRUE" if activa else "FALSE"
    )
