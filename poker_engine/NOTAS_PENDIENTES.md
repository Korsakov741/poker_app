# Notas pendientes — capa de captura de datos / UI (todavía no construida)

Estas notas son para cuando construyamos el flujo de captura real
(la parte de la app donde el usuario ingresa lo que pasa en la
mesa), no afectan el motor ya construido.

## Cantidad de jugadores en la mesa (seleccionable y ajustable)

Contexto: en póker no hay un número fijo universal de jugadores por
mesa. Lo habitual:
- **Full ring**: 9 o 10 jugadores.
- **6-max**: 6 jugadores (muy común online).
- **Heads-up**: 2 jugadores.
- **Torneos**: empiezan full ring (9-10 por mesa) y se van
  reduciendo a medida que eliminan jugadores — las mesas se
  "balancean" (mueven jugadores entre mesas para mantenerlas
  parejas) hasta llegar a la mesa final, que también se va
  reduciendo hasta terminar heads-up.

Lo que hay que tener en cuenta al programar la captura:
- La app tiene que dejar **elegir** cuántos jugadores hay en la mesa
  en un momento dado (no asumir 6-max ni 9-max por defecto).
- En torneos, esa cantidad **cambia mano a mano** a medida que
  eliminan gente — la captura tiene que permitir ajustarlo
  fácilmente entre manos, no solo una vez al empezar la sesión.
- Esto ya está soportado por el motor: ninguno de los puntos
  construidos hasta ahora asume una cantidad fija de jugadores (el
  Punto 1 toma una lista de rangos de rivales de cualquier largo, el
  Punto 17/ICM se probó con hasta 40 jugadores). El límite es solo de
  la futura interfaz de captura, no del motor.

(Agregar acá cualquier otra cosa que surja y convenga anotar para la
etapa de captura de datos / UI, en vez de resolverla apurados en el
momento.)
