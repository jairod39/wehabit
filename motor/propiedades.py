"""
Todo lo relacionado con buscar y crear propiedades (habitaciones,
apartamentos, etc). Este archivo no sabe que existe Google Sheets:
solo le pide filas "crudas" a sheets_client y las convierte en
objetos Propiedad, con sus extras ya cargados adentro.
"""

from motor.models import Propiedad, Extra, TipoPropiedad
from motor.sheets_client import leer_todas_las_filas


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
        fotos=[f.strip() for f in fotos_texto.split(",") if f.strip()],
        activa=_texto_a_booleano(fila.get("activa", "")),
        extras_disponibles=extras,
    )


def listar_propiedades(
    tipo: TipoPropiedad | None = None,
    pais: str | None = None,
    ciudad: str | None = None,
) -> list[Propiedad]:
    """Devuelve las propiedades activas, filtradas opcionalmente por tipo, pais y/o ciudad."""
    filas = leer_todas_las_filas("Propiedades")
    extras_por_propiedad = _cargar_extras_por_propiedad()

    propiedades = [
        _fila_a_propiedad(f, extras_por_propiedad.get(str(f["id"]), []))
        for f in filas
        if f.get("id")
    ]
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
