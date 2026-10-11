# Revisión de diseño visual y marca (11-oct-2026)

Método: UI Design Review, 10 dimensiones. Base: capturas en un teléfono de 390 px del índice, la página pública de Quito y el informe técnico.

## Puntaje antes de los cambios: 58/100

| Dimensión | Puntaje | Observación |
|---|---|---|
| Jerarquía visual | 6 | La cifra principal destaca. Las preguntas, que son lo más útil, están al final |
| Tipografía | 7 | Legible, 16-17 px, interlineado 1,55. Sin personalidad en los títulos |
| Color | 7 | Paleta validada y modo oscuro. Sin color de marca |
| Espaciado | 7 | Aire suficiente |
| Consistencia | 5 | El índice, el informe y las guías usan estilos distintos |
| Imágenes y gráficos | 6 | Barras claras. Sin logo ni ícono; el navegador no tiene ícono de pestaña |
| Diseño y grilla | 6 | Una columna correcta en el teléfono. Tablas anchas en el informe |
| Componentes | 4 | No hay botones de acción. Los enlaces hacen todo el trabajo |
| Marca y personalidad | 1 | Sin nombre, logo ni identidad. "veeduria-ec" es un nombre técnico |
| Estándares actuales | 7 | Limpio y rápido. Sin botón de compartir ni vista previa para WhatsApp |

## Decisiones de marca

| Elemento | Decisión | Razón |
|---|---|---|
| Nombre | **Ojo al Gasto** | Expresión ecuatoriana. Dice qué hace. No se encontró otro proyecto de transparencia con ese nombre. "Lupa Pública" y "Lupa Ciudadana" ya existen |
| Lema | Control ciudadano de las compras municipales | Control social (Constitución, art. 95). No se usa "veeduría" porque las veedurías se registran en el CPCCS |
| Logo | Un ojo con una moneda como pupila | Se lee en 16 px. Funciona como ícono de pestaña |
| Color principal | Azul `#1c5cab`; en modo oscuro `#6da7ec` con texto oscuro | Confianza institucional. Contraste medido: 6,63:1 con blanco; 7,49:1 sobre fondo oscuro |
| Color de atención | Naranja `#eb6834` | Solo en el logo. Nunca en texto ni en bordes decorativos |
| Tipografía | Fuente del sistema; títulos en peso 800 | Rápida, sin descargas, sin rastreo de terceros |
| Tono | Serio, cercano, sin adjetivos | Coherente con docs/estilo.md |

El nombre está en un solo lugar (`src/veeduria/informe.py`, `MARCA`). Para cambiarlo, edite ese valor.

## Segunda revisión (11-oct-2026)

Las tarjetas con borde de color a la izquierda son un patrón típico de interfaces generadas con IA. Se reemplazaron por tarjetas con un borde fino uniforme y por cajas de fondo gris suave.

Se probó Pico CSS como base visual. El resultado se vio genérico y poco profesional, y se descartó. El diseño propio se mantiene.

## Cambios aplicados

1. Encabezado de marca común en todas las páginas, con logo e ícono de pestaña.
2. Página pública: las preguntas van justo después de la cifra principal.
3. Cada pregunta tiene un texto sugerido que se puede copiar, y una guía de 5 pasos para presentarla por el canal oficial. El sitio no envía solicitudes ni pide datos personales.
4. Botón "Compartir" y vista previa para WhatsApp (etiquetas Open Graph).
5. Índice: cada ciudad es una tarjeta grande, primero.
6. Informe técnico: barra de secciones.
