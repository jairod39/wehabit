# WeHabit — ChambreBot

Puente entre dueños de habitaciones (y a futuro apartamentos, casas, vehículos)
y personas que buscan alquilar, todo por Telegram. No procesa pagos: solo
muestra, agenda y conecta.

## Cómo está organizado (y por qué)

Cada archivo hace UNA sola cosa. Así, si algo falla o hay que cambiar algo,
sabemos exactamente dónde mirar sin tocar el resto.

```
wehabit/
├── .env                  → tus claves reales (nunca se sube a git)
├── .env.example           → plantilla de qué claves hacen falta
├── .gitignore              → le dice a git qué ignorar (las claves, entre otras cosas)
├── requirements.txt        → lista de librerías que hay que instalar
│
├── motor/                  → EL MOTOR: datos y lógica de negocio, sin Telegram
│   ├── config.py            → lee las claves del .env
│   ├── models.py             → qué es una Propiedad, un Extra, una Reserva, una Calificación
│   ├── sheets_client.py       → (próximo paso) conexión con Google Sheets
│   ├── propiedades.py          → (próximo paso) buscar y guardar propiedades
│   ├── precios.py               → (próximo paso) calcular precio con extras
│   ├── reservas.py               → (próximo paso) agendar y consultar reservas
│   └── calificaciones.py          → (próximo paso) guardar y promediar calificaciones
│
└── bot/                    → EL BOT: solo conversa con el usuario en Telegram
    ├── main.py               → (próximo paso) arranca el bot
    └── handlers/              → (próximo paso) una respuesta por archivo
        ├── start.py
        ├── explorar.py
        ├── agendar.py
        └── calificar.py
```

## Por qué está separado así

El `motor/` no sabe que existe Telegram. Si mañana agregamos WhatsApp, o el
portal web, se conectan al mismo motor sin tocarlo. Y el `bot/` no sabe cómo
se guardan los datos — solo le pregunta al motor y muestra la respuesta.

## Estado actual

✅ Estructura del proyecto
✅ Modelo genérico de datos (sirve para habitaciones, apartamentos, vehículos...)
✅ Manejo seguro de claves (.env)
⬜ Conexión con Google Sheets
⬜ Lógica de propiedades, precios, reservas, calificaciones
⬜ El bot de Telegram en sí
