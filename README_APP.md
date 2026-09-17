# Motor de decisión de póker — App

Backend FastAPI + frontend web mobile-friendly, corriendo sobre los
17 puntos del motor, todos conectados.

Dos formas de tenerla funcionando:

- **Local, en tu compu** (pasos acá abajo) — gratis, pero solo anda
  mientras la compu esté prendida y el servidor corriendo.
- **Online 24/7, gratis** (ver `GUIA_DESPLIEGUE.md`) — no depende de
  tu compu, accesible desde el celu en cualquier lado.

## 1. Instalar (una sola vez)

Necesitás Python 3.10 o más nuevo instalado. Después:

```bash
cd poker_app
pip install -r requirements.txt
```

## 2. Correr el servidor

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Dejalo corriendo. Vas a ver algo como:
```
Uvicorn running on http://0.0.0.0:8000
```

La app te va a pedir usuario y clave la primera vez (por defecto
`hero` / `cambiame` — para cambiarlos, definí las variables de
entorno `APP_USERNAME` y `APP_PASSWORD` antes de correr el comando de
arriba).

## 3. Usarlo desde la compu

Abrí `http://localhost:8000` en el navegador.

## 4. Usarlo desde el celular (mismo wifi que la compu)

1. En la compu, buscá tu IP local:
   - Mac/Linux: `ifconfig | grep "inet "` (algo tipo `192.168.1.XX`)
   - Windows: `ipconfig` (buscá "Dirección IPv4")
2. En el celu, conectado a la MISMA wifi, abrí en el navegador:
   `http://192.168.1.XX:8000` (con tu IP real)
3. Opcional: agregalo a la pantalla de inicio del celu (Safari:
   compartir → "Agregar a inicio"; Chrome Android: menú → "Agregar a
   pantalla de inicio") para que se sienta como una app.

## 5. Para que ande sin depender de tu compu

Ver `GUIA_DESPLIEGUE.md` — paso a paso, gratis, con Render.

## 6. Cómo usarla durante una partida

Ver `GUIA_DE_USO.md` — qué cargar y en qué orden en cada pantalla.

## Los 17 puntos del roadmap, todos conectados

Incluida la mezcla GTO/Explotador del Punto 11 y las tablas de
apertura por posición del Punto 4 — se activan cargando tu posición y
la cantidad de jugadores en la mesa en la pantalla de Decisión (son
campos opcionales; si no los cargás, la app sigue funcionando igual
con el resto de los puntos).

## Los datos quedan en tu compu (o en tu servicio de Render, si desplegaste ahí)

Todo se guarda como archivos JSON (manos jugadas y notas). Nada se
manda a ningún lado que no controles vos.
