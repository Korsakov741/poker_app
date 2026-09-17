# Cómo poner la app online, gratis, paso a paso

No hace falta terminal ni saber programar — todo se hace haciendo
clic. Al final vas a tener tu app en:

```
https://erencastro741.onrender.com
```

## Paso 0 — Qué vas a necesitar

Dos cuentas gratis: una en **GitHub** (donde "guardás" el código) y
una en **Render** (donde corre la app). Nada de esto pide tarjeta.

## Paso 1 — Crear cuenta en GitHub

1. Andá a **github.com**
2. "Sign up", poné tu mail, elegí usuario y clave.

## Paso 2 — Instalar GitHub Desktop

GitHub por la web NO deja subir una carpeta con subcarpetas adentro
(solo archivos sueltos, uno por uno) — por eso usamos este programa
en cambio. Sigue siendo solo clicks, nada de código.

1. Andá a **desktop.github.com** y descargalo (hay para Windows y Mac)
2. Instalalo y abrilo
3. Te va a pedir iniciar sesión — usá la cuenta de GitHub del Paso 1

## Paso 3 — Subir la carpeta `poker_app`

1. En GitHub Desktop: **File** → **Add Local Repository**
2. Elegí la carpeta `poker_app` que bajaste del chat (la que tiene
   adentro `backend`, `frontend`, `poker_engine`, `requirements.txt`,
   `render.yaml`)
3. Te va a avisar que esa carpeta todavía no es un repositorio —
   tocá **"create a repository"** (o "Crear repositorio")
4. Dejá el nombre como está y tocá **"Create Repository"**
5. Arriba a la derecha, vas a ver un botón que dice **"Publish
   repository"** — tocalo
6. Dejalo en **"Public"** (destildá "Keep this code private" si
   aparece marcado — no hay nada sensible en el código, tu clave de
   acceso a la app la ponés después directo en Render, no acá)
7. **"Publish Repository"**

Listo, tu código ya está en GitHub.

## Paso 4 — Crear cuenta en Render

1. Andá a **render.com**
2. **"Get Started"** → **"Sign up with GitHub"** (así queda conectado
   directo, sin pasos extra)

## Paso 5 — Crear el servicio

1. En Render: **"New +"** → **"Blueprint"**
2. Elegí el repositorio que publicaste en el Paso 3 (se va a llamar
   `poker_app`, o como haya quedado)
3. Render lee el archivo `render.yaml` solo y completa casi todo
   automáticamente — el nombre del servicio ya viene configurado
   como **`erencastro741`**, no hace falta que lo escribas
4. Te va a pedir dos datos — **acá elegís tu usuario y clave para
   entrar a la app**:
   - `APP_USERNAME`: el usuario que quieras (ej. `hero`)
   - `APP_PASSWORD`: una clave que quieras (guardala, la vas a usar
     cada vez que abras la app)
5. **"Apply"** / **"Create"**

## Paso 6 — Esperar

Tarda unos minutos en instalar todo. Cuando termina, tu app va a
estar en:

```
https://erencastro741.onrender.com
```

## Paso 7 — Usarla desde el celu

1. Abrí esa URL en el navegador del celu (cualquier wifi o datos, ya
   no depende de tu compu)
2. Te va a aparecer un cartel pidiendo usuario y clave — poné lo que
   elegiste en el Paso 5
3. Listo, ya está funcionando

**Un detalle:** si la app estuvo 15 minutos sin uso, se "duerme" y
tarda 30-60 segundos en despertar la próxima vez que la abrís. Nada
que hacer, solo esperar esa vez.

## Si más adelante querés el dominio real `erencastro741.com` (sin el ".onrender.com")

Eso es un paso aparte y distinto: hay que **comprar** ese dominio en
un sitio como Namecheap o GoDaddy (ronda $10-15 por año, no es
gratis) y después conectarlo desde el panel de Render (Settings →
Custom Domains) — eso de conectarlo sí es gratis. Si llegás a
comprarlo y querés ayuda para conectarlo, contame y seguimos con eso.
