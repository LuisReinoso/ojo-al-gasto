# Recorrido cognitivo (11-oct-2026)

Método: Cognitive Walkthrough (Wharton et al., 1994). Evaluación predictiva sobre capturas en un teléfono de 390 px. Valide con 5 usuarios reales.

## Usuarios

| Persona | Perfil | Llega desde |
|---|---|---|
| Ciudadana | Vive en Quito. Sin formación técnica. Usa el teléfono | Un enlace en WhatsApp |
| Periodista local | Conoce la LOTAIP. Poco tiempo. No usa la terminal | Un enlace o el índice |

## Tarea 1: entender en qué gasta Quito

| Paso | Q1 Objetivo claro | Q2 Acción visible | Q3 Acción comprensible | Q4 Retroalimentación | Problema |
|---|---|---|---|---|---|
| 1. Abrir el índice | ⚠️ | ⚠️ | ✅ | ✅ | La ciudad aparece en tercer lugar, debajo de dos guías |
| 2. Tocar "Quito" | ✅ | ⚠️ | ✅ | ✅ | El enlace es texto pequeño en una lista |
| 3. Leer la cifra principal | ✅ | ✅ | ⚠️ | ✅ | "566,7 millones" no tiene una referencia cercana |
| 4. Ver las compras más grandes | ✅ | ✅ | ✅ | ✅ | Ninguno |

Éxito estimado: 80 %.

## Tarea 2: hacer una pregunta a la entidad

| Paso | Q1 | Q2 | Q3 | Q4 | Problema |
|---|---|---|---|---|---|
| 1. Encontrar las preguntas | ⚠️ | ❌ | ✅ | ✅ | Están al final, tras unas 5 pantallas |
| 2. Elegir una pregunta | ✅ | ✅ | ✅ | ✅ | Ninguno |
| 3. Preparar la solicitud | ✅ | ❌ | ❌ | ❌ | No hay botón. El generador solo funciona en la terminal |
| 4. Presentar la solicitud | ⚠️ | ❌ | ❌ | ❌ | No hay enlace al portal ni explicación del plazo |

Éxito estimado: menos del 5 %. **Bloqueo crítico.**

## Tarea 3: periodista verifica un proceso desde una alerta

| Paso | Q1 | Q2 | Q3 | Q4 | Problema |
|---|---|---|---|---|---|
| 1. Abrir el informe técnico | ✅ | ⚠️ | ⚠️ | ✅ | Desde la página pública el enlace está al final |
| 2. Llegar a las alertas | ✅ | ⚠️ | ✅ | ✅ | No hay índice de secciones; hay que desplazarse mucho |
| 3. Leer la tabla de alertas | ✅ | ⚠️ | ✅ | ✅ | La tabla es ancha; en el teléfono hay que desplazar a los lados |
| 4. Abrir la ficha oficial | ✅ | ✅ | ✅ | ✅ | Ninguno |

Éxito estimado: 55 %.

## Correcciones por prioridad

| Prioridad | Corrección | Tarea |
|---|---|---|
| P0 | Texto sugerido que se puede copiar en cada pregunta, y pasos para presentarla por el canal oficial. El sitio no envía solicitudes ni pide datos personales | 2 |
| P0 | Mostrar las 3 preguntas principales justo después de la cifra principal | 2 |
| P0 | Enlace al Portal Nacional de Transparencia y plazos de respuesta | 2 |
| P1 | Identidad: nombre, logo y colores propios | 1, 2, 3 |
| P1 | Índice con la ciudad como tarjeta grande, primero | 1 |
| P1 | Botón "Compartir" (WhatsApp y otros) y vista previa del enlace | 1 |
| P1 | Barra de secciones en el informe técnico | 3 |
| P2 | En el teléfono, alertas como tarjetas en lugar de tablas anchas | 3 |
