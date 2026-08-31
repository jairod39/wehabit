"""
Lista de paises del mundo, organizada por continente. Dato geografico
real y fijo (no cambia, no necesita IA ni consulta externa). Se separa
por continente para que el menu del bot no tenga que mostrar 190+
botones de una sola vez.
"""

PAISES_POR_CONTINENTE: dict[str, list[str]] = {
    "America": [
        "Colombia", "Mexico", "Argentina", "Peru", "Chile", "Ecuador",
        "Venezuela", "Bolivia", "Paraguay", "Uruguay", "Panama",
        "Costa Rica", "Guatemala", "Honduras", "El Salvador", "Nicaragua",
        "Republica Dominicana", "Cuba", "Puerto Rico", "Estados Unidos",
        "Canada", "Brasil", "Belice", "Jamaica", "Haiti", "Bahamas",
        "Trinidad y Tobago", "Guyana", "Surinam",
    ],
    "Europa": [
        "Espana", "Portugal", "Francia", "Italia", "Alemania",
        "Reino Unido", "Irlanda", "Paises Bajos", "Belgica", "Suiza",
        "Austria", "Suecia", "Noruega", "Dinamarca", "Finlandia",
        "Polonia", "Republica Checa", "Grecia", "Hungria", "Rumania",
        "Bulgaria", "Croacia", "Ucrania", "Rusia", "Islandia",
    ],
    "Asia": [
        "China", "Japon", "Corea del Sur", "India", "Emiratos Arabes Unidos",
        "Arabia Saudita", "Qatar", "Israel", "Turquia", "Tailandia",
        "Vietnam", "Filipinas", "Indonesia", "Malasia", "Singapur",
        "Pakistan", "Bangladesh", "Kazajistan", "Jordania", "Libano",
    ],
    "Africa": [
        "Sudafrica", "Egipto", "Marruecos", "Nigeria", "Kenia",
        "Ghana", "Tunez", "Argelia", "Etiopia", "Senegal",
    ],
    "Oceania": [
        "Australia", "Nueva Zelanda", "Fiyi", "Papua Nueva Guinea",
    ],
}
