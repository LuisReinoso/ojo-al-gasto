# Guía para periodistas: de una alerta a una nota

Esta guía explica cómo convertir una alerta de veeduria-ec en una nota verificada.

> Una alerta no es una nota. Una alerta es el punto de partida de la reportería.

## 1. Elija una alerta

1. Abra `informe.html` de su cantón.
2. Empiece por las alertas de nivel **alta**.
3. Elija una alerta con un monto importante para la comunidad.
4. Copie el código del proceso.

## 2. Verifique los datos

1. Ejecute `veeduria proceso <código>`.
2. Abra la "Ficha oficial" del resultado.
3. Compare el monto, la fecha y el proveedor con la ficha oficial.
4. Descargue los pliegos, el contrato y las actas desde el portal del SERCOP.
5. Ejecute `veeduria proveedor <RUC>` para ver todo lo que ganó ese proveedor en el país.

**AVISO:** si un dato de la herramienta no coincide con la ficha oficial, use la ficha oficial. Reporte la diferencia en el repositorio.

## 3. Busque el contexto

1. Lea la explicación y la base legal de la alerta en el informe.
2. Busque si la Contraloría ya examinó el tema: el informe técnico lista sus informes.
3. Compare con el resto del país: el informe da la tasa nacional de cada patrón.
4. Visite la obra si el proceso es una obra.

## 4. Pida la versión de la entidad

1. Ejecute `veeduria solicitud` con preguntas concretas.
2. Presente la solicitud y guarde la fe de recepción.
3. Espere el plazo legal: 10 días, prorrogables 5.
4. Publique la respuesta de la entidad o informe que no respondió.

Preguntas útiles:

- ¿Por qué se contrató por separado?
- ¿Por qué se usó un procedimiento sin concurso?
- ¿Por qué se presentó un solo oferente?
- ¿Qué recomendaciones de la Contraloría se cumplieron?

## 5. Escriba la nota

Escriba hechos verificables con su fuente:

| Escriba | No escriba |
|---|---|
| "El SERCOP registra dos procesos de USD 350.000 y USD 300.000, con objetos parecidos y el mismo proveedor, en un mes." | "Fraccionaron el contrato." |
| "La entidad no respondió la solicitud en el plazo legal." | "La entidad oculta información." |
| "El proceso tuvo un solo oferente. En el país esto ocurre en el 17 % de los casos." | "El proceso estaba amarrado." |
| "La Contraloría determinó que el personal técnico no correspondió al ofertado." | "El contratista estafó." |

**AVISO:** no atribuya delitos a personas. La calumnia tiene pena de cárcel (COIP, art. 182). Si tiene pruebas de un delito, preséntelas a la Fiscalía o a la Contraloría.

**AVISO:** no publique la cédula ni datos privados de personas naturales. Los archivos de la herramienta ya enmascaran el RUC. En las alertas, un proveedor persona natural aparece como "Persona natural"; su nombre está en la ficha oficial del SERCOP.

## 6. Antes de publicar

Revise esta lista:

- [ ] Cada cifra tiene su fuente y su fecha.
- [ ] Cada cifra coincide con la ficha oficial del SERCOP.
- [ ] La nota incluye la versión de la entidad o su silencio.
- [ ] La nota explica qué es normal: la tasa nacional o la ley.
- [ ] La nota no atribuye delitos a personas.
- [ ] La nota no expone datos privados.
- [ ] Un abogado revisó la nota si nombra a personas.

## Atajos

| Necesita | Comando |
|---|---|
| Ficha de un proceso | `veeduria proceso <código>` |
| Historial de un proveedor | `veeduria proveedor <nombre o RUC> --csv salida.csv` |
| Fecha límite de una solicitud | `veeduria plazo AAAA-MM-DD` |
| Solicitud LOTAIP | `veeduria solicitud <entidad.toml> --pedido "..."` |
| Datos para su propio análisis | `informes/<cantón>/procesos.csv` y `alertas.csv` |
