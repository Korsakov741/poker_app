# Cómo usar la app durante una partida

La app tiene 4 pestañas abajo: **Decisión**, **Jugadores**, **Manos**,
**Sesión**. Esta guía te dice qué hacer en cada una, en el momento
en que la necesitás.

Regla de oro de toda la app: **nunca te va a decir "hacé esto"**. Te
muestra rangos y opciones con sus razones — la decisión final siempre
es tuya.

---

## 1. Durante la mano, cuando dudás qué hacer → pestaña "Decisión"

Esta es la que más vas a usar, en vivo, en medio de una mano.

1. **"Mi mano"**: tocá cada espacio vacío, elegís el número/letra
   (2 al As) y después el palo. Repetí para tu segunda carta.
2. **"Board"**: si ya salieron cartas comunitarias, cargalas igual
   (tocar → número → palo). Arriba, tocá el botón de la calle en la
   que estás (*preflop / flop / turn / river*) — eso ajusta cuántos
   espacios de board aparecen.
3. **"Rival principal"**: ponele un apodo al jugador que te está
   haciendo dudar (ej. `villain_1`). **Usá siempre el mismo apodo
   para la misma persona real** — así la app va acumulando lo que
   aprende de él, mano tras mano.
4. Su rango probable, escrito simple: por ejemplo `22+, A9s+, KJo+`
   (el `+` significa "esa mano y mejores"). Si no tenés idea, dejalo
   vacío — la app asume "cualquier mano al azar".
5. **"La apuesta"**: tocá si hay algo que pagar o no. Si hay,
   completá cuánto es la apuesta y cuánto hay en el bote en ese
   momento.
6. **Opcional pero recomendado**: tu posición en la mesa y cuántos
   jugadores hay sentados — esto activa dos capas extra del motor
   (tablas de apertura + mezcla contra la teoría).
7. **Opcional**: tu propio rango representado (si querés que la app
   evalúe si un farol tuyo tendría sentido acá) y cartas muertas.
8. Tocá **"Calcular"**.
9. Mirá el resultado:
   - La barra de arriba es tu **equity real** contra el rango que
     cargaste.
   - Abajo, la lista de **acciones candidatas** — cada una con su
     valor y la razón atrás. Vienen ordenadas de mejor a peor, pero
     mostrás TODAS, no una sola.
10. Jugás la mano como vos decidas. Cuando termine esa acción puntual,
    bajá hasta **"¿Qué hiciste realmente?"**, elegí la acción real
    (puede ser distinta a la recomendada) y tocá **Registrar** — así
    alimenta la revisión de sesión más tarde.

---

## 2. Cuando termina una mano completa → pestaña "Manos"

Esto es lo que hace que la app "aprenda" de verdad sobre cada rival.
Cuanto más completes esto, mejor van a leer los puntos que dependen
de datos reales (perfiles, sizing-tells, imagen propia).

1. **ID de la mano**: cualquier texto que la identifique (ej.
   `mesa1-042`).
2. **Jugadores**: todos los que llegaron a esa mano, separados por
   coma, incluyéndote (`hero`).
3. **Board**: las cartas comunitarias que salieron (si la mano no
   llegó al flop, dejalo vacío).
4. **Acciones**: una fila por cada acción de la mano, en orden —
   quién actuó, en qué calle, qué hizo (retirarse/chequear/pagar/
   apostar/subir), y si apostó o subió, qué fracción del bote fue
   (ej. `0.7` para 70% del bote). Tocá "+ agregar acción" para sumar
   más filas.
5. **Ganador(es)**: quién se llevó el bote.
6. **¿Hubo showdown?**: si se mostraron las cartas, activalo y
   escribí qué mano tenía cada uno (formato: `jugador:carta1,carta2`,
   separando varios jugadores con `;`).
7. **Guardar mano**.

---

## 3. Para revisar a un rival → pestaña "Jugadores"

1. Tocá su nombre en la lista (van a aparecer todos los que ya
   cargaste en manos guardadas).
2. Vas a ver sus stats reales (VPIP, PFR, factor de agresión, etc.)
   y los dos ejes calculados por la app (tight↔loose,
   pasivo↔agresivo).
3. Podés agregarle una nota a mano en cualquier momento — por
   ejemplo, algo que notaste que los números todavía no reflejan.

---

## 4. Al final de la sesión → pestaña "Sesión"

1. Vas a ver un resumen: cuántas decisiones registraste, en qué % de
   ellas coincidiste con la mejor recomendación, y cuánto valor se
   calcula que se perdió en total.
2. Abajo, la lista de manos que más vale la pena repasar después —
   las que más se alejaron de la mejor opción disponible en el
   momento.

---

## Ejemplo rápido, de punta a punta

Estás en el flop, tenés As-Kd, el board es Ac-7h-2h, un rival
llamado `mesa3_juan` apuesta 70 en un bote de 100.

1. Pestaña Decisión → cargás As y Kd en "Mi mano".
2. Cargás Ac, 7h, 2h en "Board", tocás "flop".
3. Rival: `mesa3_juan`, rango: `77, 88, AKo, AKs, 99` (lo que
   pensás que puede tener).
4. "Sí, enfrento una apuesta" → apuesta 70, bote 100.
5. Calcular → ves tu equity real y las opciones (pagar, apostar por
   valor, apostar de farol, retirarse), cada una con su razón.
6. Decidís, jugás, y registrás qué hiciste realmente.
7. Cuando termina la mano, vas a "Manos" y cargás todo lo que pasó
   (para que la próxima vez que enfrentes a `mesa3_juan`, la app ya
   sepa algo real sobre él).
