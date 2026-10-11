# Hazlo tú: audite a su municipio con inteligencia artificial

Esta guía explica cómo crear un proyecto como veeduria-ec. No necesita saber programar. Necesita revisar cada resultado.

## Es posible

Este proyecto se hizo en una jornada de trabajo. Una persona puso las preguntas y revisó los resultados. Un asistente de IA escribió el código, buscó las leyes y cruzó los datos.

Es posible por tres razones:

1. El Estado publica los datos: el SERCOP publica cada proceso y la Defensoría publica la transparencia de cada entidad.
2. Un asistente de IA escribe y ejecuta código a partir de instrucciones en español.
3. Las herramientas complementarias son libres.

**AVISO:** la IA comete errores con mucha seguridad. Usted es responsable de lo que publica.

## Herramientas

| Herramienta | Para qué sirve | Costo |
|---|---|---|
| Claude Code (u otro asistente de programación con IA) | Escribe y ejecuta el código | Suscripción o créditos. Hay alternativas libres, menos capaces |
| Python 3.11 | Procesa los datos | Libre |
| Playwright | Abre páginas web de forma automática y toma capturas | Libre |
| Tesseract u otro OCR | Convierte documentos escaneados en texto | Libre |

## Método

### 1. Haga una pregunta concreta

Mal: "Quiero auditar al municipio".
Bien: "¿En qué gastó mi municipio en 2025 y hubo competencia?".

### 2. Encuentre los datos

Copie este pedido al asistente:

> Busca dónde descargar todas las compras públicas del Municipio de [cantón] en Ecuador. Prueba el enlace. Descarga una muestra. Dime qué columnas trae y qué datos faltan.

Use solo datos que la página muestra a cualquier visitante. No use contraseñas ni atajos.

### 3. Lea la ley

> Investiga el marco legal vigente en Ecuador para auditar compras de un municipio. Para cada norma dame el Registro Oficial, el enlace que abriste y los artículos. Marca con [NO VERIFICADO] todo lo que no leíste en una fuente abierta. No inventes números de artículo.

### 4. Compare con el país

Un patrón solo es raro si ocurre más que en el resto del país. Pida al asistente la tasa nacional de cada patrón.

### 5. Desconfíe de las cifras sorprendentes

Una cifra sorprendente es probablemente un error. Revise los casos uno por uno. Revise que las partes sumen el total.

### 6. Pida una verificación independiente

> Recalcula estas cifras desde los datos crudos en datos/. No leas el código en src/. Para cada cifra responde CONFIRMADA, REFUTADA o NO VERIFICABLE, con tu cifra y tu código.

### 7. Publique con cuidado

Lea la [guía para periodistas](periodistas.md).

## Errores de la IA en este proyecto

| Error | Causa | Cómo se detectó |
|---|---|---|
| El cruce LOTAIP-SERCOP dio 0 coincidencias | El SERCOP agrega un número al final del código | 0 era imposible. Se compararon dos códigos |
| Aplicó límites de "menor cuantía" a todo 2025 y 2026 | La ley eliminó ese procedimiento en 2025 | Los datos muestran que desaparece el 31-jul-2025 |
| Casi marca 457 procesos de "proveedor único" como ilegales | La categoría del SERCOP no equivale al artículo de la ley | Se leyó el artículo. La alerta cambió a "verifique" |
| Marcó como fraccionamiento compras distintas | La subasta inversa no tenía techo de monto | Revisión manual de cada caso |
| Escribió "la mayoría" de informes sin seguimiento | Eran 19 de 151 | Se contaron antes de publicar |
| El OCR leyó un total como 3 012 976,02 | Error de lectura en una tabla | La suma de las filas da 3 012 978,02 |
| Marcó "adjudicado al precio máximo" en la menor cuantía de obras | En ese procedimiento el precio era fijo por ley | Un revisor independiente lo advirtió. Los datos lo confirmaron: 1.789 de 1.789 procesos al precio máximo |
| Usó dos RUC reales de personas como ejemplo en las pruebas | Se copiaron de los datos | Auditoría antes del commit: se cambiaron por números inválidos |
| El texto de fraccionamiento citaba una prohibición en casos donde no cambiaba el procedimiento | El límite era el de la comisión técnica, no el de un procedimiento | Revisor independiente; el texto ahora distingue los dos casos |

## Ejemplo con OCR

Vea [ejemplo-contraloria.md](ejemplo-contraloria.md): un informe escaneado de 34 páginas, convertido en texto y resumido en 4 hallazgos.

## Lo que la IA no hace

- No decide qué es importante para su comunidad.
- No visita la obra.
- No da asesoría legal.
- No firma lo que usted publica.

## Empiece hoy

1. Instale Python y un asistente de IA.
2. Siga el [README](../README.md).
3. Ejecute `veeduria auditar` para su cantón.
4. Elija una alerta.
5. Presente una solicitud con `veeduria solicitud`.
