# Ejemplo: leer con OCR un informe escaneado de la Contraloría

Informe: examen especial **DNA5-GAD-0022-2026**, contratos de las fiestas de Quito 2024, Secretaría de Cultura.
Descarga: <https://www.contraloria.gob.ec/WFDescarga.aspx?id=92775&tipo=inf>

## Problema

El PDF tiene 34 páginas. Un computador solo puede leer 143 palabras. El resto son imágenes escaneadas.

## Procedimiento

```bash
pdftoppm -r 150 -png informe.pdf p                     # 1. Una imagen por página
for f in p-*.png; do tesseract "$f" - -l spa; done > informe.txt   # 2. OCR
```

3. Pida al asistente: "Lee informe.txt. Haz una tabla con cada hallazgo, el monto, la norma incumplida y la página."
4. Compare cada cifra y cada código con el PDF original.

## Resultado

La Contraloría examinó 7 procesos y 1 convenio por **USD 3.012.978,02** (pág. 3).

| # | Hallazgo | Hecho principal | Pág. |
|---|---|---|---|
| 1 | Personal técnico de los procesos COTS-MDMQ-2024-3911 y -3912 no correspondió al ofertado | En la mayoría de eventos trabajó personal distinto al ofertado | 4-7 |
| 2 | En el proceso COTS-MDMQ-2024-3908 no se cumplió el rider técnico | El contrato exigía 2 ambulancias y 14 brigadas; el certificado registra 1 ambulancia y 1 brigada. No hubo multa | 8-10 |
| 3 | Convenio SECU-AJ-008-2024 (Quito Fest 2024) sin proyecto priorizado | Convenio de USD 825.000 sin proyecto específico ni precios unitarios | 10-15 |
| 4 | Proceso COTS-MDMQ-2024-3910 con inconsistencias en la fase preparatoria | Los términos de referencia exigían la obra de una fundación determinada (USD 43.000). Hubo una sola oferta | 15-23 |

Cada hallazgo tiene una recomendación obligatoria (LOCGE, art. 92).
Pregunta para una solicitud: **¿qué hizo la Secretaría de Cultura para cumplir las cuatro recomendaciones?**

## Lecciones

1. **El OCR se equivoca.** Leyó el total de la tabla como 3 012 976,02. La imagen y la suma de las filas dan 3 012 978,02. Compare siempre con el original.
2. **La Contraloría protege datos personales.** Escribe los RUC como "060XXXXXXXX001" y nombra a los funcionarios por su cargo. veeduria-ec usa el mismo criterio.
3. **No republique datos privados.** Una página cita el nombre, la dirección y el teléfono de un particular. No copie esos datos.
4. **Cite y enlace.** El informe dice "Se prohíbe su uso no autorizado". Los resultados de auditoría son públicos (LOTAIP, art. 19 núm. 7). Resuma, cite la página y enlace el original. No distribuya el PDF como propio.
