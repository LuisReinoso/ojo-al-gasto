# Marco legal de la veeduría ciudadana automatizada de GADs municipales (Ecuador)

> **Fecha de corte:** 11 de octubre de 2026. **Primer objetivo:** Municipio del Distrito Metropolitano de Quito (MDMQ).
>
> **Convención:** todo dato sin marca fue leído en el texto fuente enlazado. `[NO VERIFICADO]` = no confirmado en una fuente abierta. `[INFERIDO]` = interpretación propia, no está literal en la norma. `[VERIFICADO CON DATOS]` = contrastado con los datos abiertos del SERCOP.
>
> **Sobre las fuentes:** casi todos los textos consolidados son compilaciones de Lexis, Ediciones Legales o Andina Ediciones publicadas en sitios `gob.ec`, no el facsímil del Registro Oficial (RO). Para cada norma se indica la última reforma que declara la compilación; las reformas posteriores están `[NO VERIFICADO]`. Este documento no es asesoría legal.

## 0. Lo que condiciona el diseño de la herramienta

1. **La contratación pública cambió de régimen en 2025.** La Ley Orgánica Reformatoria de la LOSNCP (RO Cuarto Suplemento 140, 7-oct-2025) eliminó la menor cuantía y la cotización y fijó en USD 10.000 el umbral entre ínfima cuantía y subasta, licitación o concurso. Antes, la Ley Orgánica de Integridad Pública (RO S. 68, 26-jun-2025) ya había reformado la LOSNCP; la Corte Constitucional la declaró inconstitucional por la forma (RO Edición Constitucional 96, 3-oct-2025). `[VERIFICADO CON DATOS]` En los datos del SERCOP la menor cuantía, la cotización, la contratación directa y la lista corta dejan de publicarse el 31-jul-2025, y desde el 26-jun-2025 aparecen licitaciones desde USD 10.096 (antes empezaban en USD 562.000). La herramienta aplica a cada proceso los límites vigentes en su fecha de publicación (`src/veeduria/datos/normas.toml`).
2. **El Estado ya define los patrones de riesgo.** La LOSNCP (art. 21) obliga al SERCOP a tener alertas tempranas automatizadas para "precios inusuales, concentración reiterada de adjudicaciones en un mismo proveedor, modificaciones frecuentes de plazos o condiciones contractuales". El RGLOSNCP (art. 426.1) añade la subdivisión de contratos y las vinculaciones. Una veeduría ciudadana puede replicar esos mismos criterios.
3. **Regla anti-fraccionamiento cuantificada:** según el RGLOSNCP (art. 270), la suma anual de ínfimas cuantías de los mismos bienes o servicios no puede superar USD 10.000. Las ínfimas cuantías no están en la descarga OCDS, así que esta regla queda pendiente de una fuente de datos.
4. **El plazo LOTAIP admite dos lecturas.** Son 10 días, prorrogables 5 (art. 34). La Defensoría del Pueblo dice "días calendario"; el Reglamento usa "término", que son días hábiles. La herramienta calcula ambos.
5. **Datos de funcionarios y proveedores:** según la LOPDP (art. 2, último inciso), son públicos el nombre, el cargo, el contacto profesional, la remuneración y la declaración patrimonial de los servidores públicos, y los datos de representantes y socios de personas jurídicas.
6. **Nueva obligación trimestral de los GAD** (COOTAD art. 198.4, reforma de febrero de 2026): publicar el indicador de gasto de inversión hasta el día 15 del mes siguiente a cada trimestre.

## 1. Constitución de la República (2008)

RO 449, 20-oct-2008. Compilación Lexis con última modificación 30-may-2024. URL: https://arconel.gob.ec/wp-content/uploads/downloads/2024/08/CONSTITUCION_DE_LA_REPUBLICA_DEL_ECUADOR.pdf

| Art. | Contenido |
|---|---|
| 18 núm. 2 | Derecho a acceder libremente a la información de entidades públicas y de privados que manejen fondos del Estado. Solo hay reserva en los casos que fije la ley. |
| 61 núm. 2 y 5 | Derecho a participar en los asuntos de interés público y a fiscalizar los actos del poder público. |
| 83 núm. 8 y 17 | Deber de administrar honradamente el patrimonio público y de denunciar y combatir la corrupción. |
| 91 | Acción de acceso a la información pública, cuando la información se niega de forma expresa o tácita, o es incompleta o no fidedigna. La reserva debe haberse declarado antes de la petición. |
| 95, 96 | Participación protagónica y control popular; reconocimiento de toda forma de organización social. |
| 100 | En todos los niveles de gobierno habrá instancias de participación: presupuestos participativos, rendición de cuentas, veedurías, observatorios, audiencias públicas. |
| 101 | Las sesiones de los GAD son públicas, con silla vacía. |
| 204 | El pueblo es el mandante y primer fiscalizador del poder público. Función de Transparencia y Control Social. |
| 208 | Atribuciones del CPCCS, entre ellas coadyuvar a las veedurías e investigar denuncias de corrupción. |
| 225, 227, 297 | Los GAD y sus empresas son sector público; principio de transparencia; quien maneja recursos públicos rinde cuentas. |

## 2. LOTAIP y su Reglamento

**Ley:** RO Segundo Suplemento 245, 7-feb-2023. Única modificación encontrada: la Corte Constitucional declaró inconstitucional la Disposición Transitoria Novena (RO S. 367, 29-may-2024), de modo que la información del art. 19 debe estar disponible sin requisito previo. URL: https://www.bce.fin.ec/images/transparencia2024/juridico/leyorganicadetransparencia.pdf

| Art. | Contenido |
|---|---|
| 4 núm. 1 | Datos abiertos: libre uso, reutilización y redistribución. |
| 4 núm. 3 | Denegación: falta de respuesta en el plazo legal, rechazo expreso o respuesta inexacta. |
| 8 | Obligados: sector público, incluidas sus empresas públicas, y entidades asociativas de GAD. |
| 11 | Informe anual a la Defensoría hasta el último día laborable de enero, con el detalle de solicitudes y tiempos de respuesta. |
| 12-13 | La Defensoría del Pueblo es el órgano rector. |
| 19 | Transparencia activa, actualizada mensualmente y en datos abiertos: 24 numerales (lista abajo). |
| 24 | Los GAD publican además las actas del concejo y sus comisiones, los planes de desarrollo y de uso del suelo y los trámites de sus servicios. |
| 31 | Calidad: datos abiertos reutilizables (núm. 3), sin acreditar interés (núm. 4), en el formato pedido (núm. 5). |
| 32 | Solicitud física o electrónica con identificación, contacto, descripción precisa y formato deseado. |
| 34 | Plazo de 10 días, prorrogable 5 por causas justificadas que se informen al solicitante. |
| 35 | No hay obligación de crear información, pero recopilar información dispersa no cuenta como crear. |
| 37 | Si un documento mezcla información pública y reservada, se entrega una versión pública. |
| 38 | Responder solo con un enlace web es insuficiente. |
| 39 | El titular de la entidad responde administrativa, civil o penalmente, incluso por no publicar o no actualizar. |
| 40-41 | Gestión oficiosa ante la Defensoría dentro de 30 días desde que venció el plazo de respuesta. |
| 44 | Reconoce el derecho a la vigilancia social y la veeduría ciudadana sobre esta ley. |
| DR Sexta | El silencio administrativo positivo no se aplica a las solicitudes LOTAIP (reforma al art. 207 del COA). |

**Art. 19, lista mínima:** 1 estructura orgánica; 2 directorio y distributivo de personal; 3 remuneraciones; 4 licencias y comisiones de servicio; 5 servicios; 6 presupuesto y su ejecución; 7 resultados de auditorías; 8 procesos de contratación; 9 contratistas incumplidos; 10 planes y programas; 11 contratos de crédito; 12 rendición de cuentas; 13 viáticos; 14 responsable de acceso a la información; 15 contratos colectivos; 16 índice de información reservada; 17 agenda de audiencias; 18 convenios; 19 donativos; 20 registro de activos de información; 21 políticas públicas; 22 formularios; 23 cuotas de acción afirmativa; 24 otra información relevante.

**Reglamento:** Decreto Ejecutivo 124, Suplemento RO 484, 24-ene-2024. URL: https://isspol.org.ec/wp-content/uploads/2026/04/REGLAMENTO-GENERAL-DE-LA-LEY-ORGANICA-DE-TRANSPARENCIA-Y-ACCESO-A-LA-INFORMACION-PUBLICA.pdf. Art. 11: transparencia activa en datos abiertos con formatos de la Defensoría. Art. 12: portal nacional. Art. 13: no se pueden exigir requisitos adicionales; la prórroga se motiva y comunica antes del vencimiento ("término"). Art. 15: gratuidad. Art. 26: queja ante la Defensoría por formulario web.

**Guía de la Defensoría DEPE-DPE-035-2023:** lee el plazo como "diez días calendario". URL: https://www.enamiep.gob.ec/wp-content/uploads/2024/03/DEPE-DPE-035-2023.pdf

**Fecha límite mensual de publicación:** `[NO VERIFICADO]`. Por eso la herramienta no califica de "tardía" una publicación mensual: muestra cuántos días después del cierre del mes se publicó.

## 3. Ley Orgánica de Participación Ciudadana (LOPC)

Suplemento RO 175, 20-abr-2010; última reforma 7-feb-2023. URL: https://www.tce.gob.ec/wp-content/uploads/2023/08/Ley-Organica-Participacion-Ciudadana.pdf

| Art. | Contenido |
|---|---|
| 67-71 | Presupuesto participativo, obligatorio en todos los niveles de gobierno, con seguimiento de la ejecución durante todo el año. |
| 77 | Silla vacía en los GAD. |
| 78-79 | Veedurías y observatorios. |
| 84-86 | Veedurías ciudadanas: monitorean cualquier actividad del Estado; reglamentadas por el CPCCS; sin conflicto de interés; se notifica su inicio a la entidad observada. |
| 87 | Las instituciones deben garantizar el acceso a la información que necesite la veeduría. |
| 88-95 | Rendición de cuentas anual. El nivel técnico rinde cuentas sobre presupuesto ejecutado y contratación de obras y servicios (art. 93). |

## 4. Reglamento General de Veedurías Ciudadanas (CPCCS)

Resolución PLE-CPCCS-388-22-11-2016 (RO 918, 9-ene-2017), reformada en 2017 y 2018. La Resolución CPCCS-PLE-SG-014-O-2026-0112 (abril de 2026) cita su texto, lo que indica que sigue vigente. URL: https://www.cpccs.gob.ec/wp-content/uploads/2020/02/reglamento-general-de-veedurias-ciudadanas.pdf

- **Integrantes:** mínimo 3 (art. 10). Ecuatorianos en goce de derechos de participación o extranjeros con situación regular (art. 12).
- **No pueden ser veedores** (art. 13): contratistas o proveedores del objeto observado, o quien tenga conflicto de intereses; parientes hasta el 4.º grado de consanguinidad o 2.º de afinidad del contratista o de los servidores involucrados; servidores cuyas funciones se relacionen con el objeto; quien ya esté en otra veeduría en curso; autoridades de elección popular y sus parientes hasta el 2.º grado; dirigentes de partidos o movimientos políticos; entre otros.
- **Atribuciones** (art. 14): vigilar planificación, presupuesto y gasto; fiscalizar adquisiciones y obras; pedir información conforme a la LOTAIP.
- **Prohibiciones** (art. 16): usar la información con otros fines, vincular la veeduría a partidos o intereses particulares, recibir dádivas, retrasar o impedir los contratos observados.
- **Trámite:** solicitud al CPCCS (arts. 29-30), verificación en 3 días término (art. 31), inducción de al menos 6 horas (art. 32), notificación a la entidad en 2 días término (art. 36), informe final en 15 días término desde que termina (art. 39). No puede haber dos veedurías con el mismo objeto (art. 28). Si la entidad niega la información, la veeduría presenta un reporte de novedad al CPCCS (art. 27).

## 5. Contratación pública

### 5.1 LOSNCP

RO S. 395, 4-ago-2008; reforma integral RO Cuarto Suplemento 140, 7-oct-2025. URL: https://portal.compraspublicas.gob.ec/sercop/wp-content/uploads/2025/12/LOSNCP.pdf

| Art. | Contenido |
|---|---|
| 16 | Observatorios ciudadanos permanentes de contratación pública. |
| 21 | Portal obligatorio, en datos abiertos; alertas tempranas automatizadas del SERCOP (precios inusuales, concentración en un proveedor, modificaciones frecuentes). |
| 22 | El PAC se publica hasta el 15 de enero. |
| 38 | Régimen especial: lista taxativa (medicamentos, seguridad, comunicación social, asesoría jurídica, repuestos, contratos entre entidades públicas, etc.). `[VERIFICADO]` en el texto. |
| 42, 47, 48 | Concurso de consultoría, subasta inversa y licitación: presupuesto mayor a USD 10.000. |
| 49 | Quien ganó una licitación de obra no puede ganar otra en la misma entidad hasta la recepción provisional de la anterior. |
| 50 | Ínfima cuantía hasta USD 10.000; no puede usarse para contratación constante y recurrente ni para subdividir contratos. |
| 58-60 | Emergencias: resolución motivada, máximo 60 días, publicación inmediata, informe de cierre. |
| 75-76 | Inhabilidades: entre otros, alcaldes y concejales de la jurisdicción y sus parientes, funcionarios que intervinieron en el proceso, proveedores suspendidos en el RUP. |
| 101 | Complementarios hasta el 8 % del contrato; en obras, el conjunto de complementarios, órdenes de trabajo y diferencias de cantidades hasta el 15 %. |
| 111 | Registro público de incumplimientos: suspensión de 5 años para contratistas incumplidos. |
| DG Tercera | Prohibido subdividir el objeto o el proyecto para eludir procedimientos. |

### 5.2 Reglamento General (RGLOSNCP)

Decreto Ejecutivo 193, Noveno Suplemento RO 153, 28-oct-2025; reformas hasta DE 461 (RO Tercer Suplemento 337, 30-jul-2026). URL: https://www.tce.gob.ec/wp-content/uploads/2026/08/Reglamento-General-a-la-Ley-Orga%CC%81nica-del-Sistema-Nacional-de-Contratacio%CC%81n-Pu%CC%81blica.pdf

| Art. | Contenido |
|---|---|
| 22 | 35 tipos de información relevante de publicación obligatoria: presupuesto referencial, pliegos, actas, adjudicación, contrato, complementarios, multas, comprobantes de pago, actas de recepción, etc. |
| 64 | Cada proceso del PAC lleva un código CPC de 9 dígitos. |
| 88 | Comisión técnica obligatoria cuando el presupuesto referencial es de USD 100.000 o más. |
| 139 | Proveedor único: solo repuestos con proveedor único, desarrollo o mejora de tecnologías existentes y patentes exclusivas, con informe técnico motivado. "Lo previsto en este artículo no aplicará para el caso de servicios, obras o consultorías." `[VERIFICADO]` en el texto. |
| 269-273 | Ínfima cuantía: aviso público, procurar 3 proformas, reporte en 5 días término; suma anual por objeto de hasta USD 10.000, con excepciones tasadas (art. 271). |
| 303-309 | Emergencias: publicación de la declaratoria en 3 días término, ampliaciones, informe de cierre con RUC de los contratistas. |
| 426.1 | Criterios de control del SERCOP: subdivisión de contratos, vinculaciones, precios inusuales, concentración en un proveedor. |

### 5.3 Umbrales en USD

| Periodo de publicación | Régimen | Límites que usa la herramienta |
|---|---|---|
| 2024 | LOSNCP anterior, PIE 2024 = USD 33.296.819.775,31 (tabla oficial SERCOP) | Menor cuantía bienes y servicios 66.593,64; cotización bienes y servicios 499.452,30; menor cuantía obras 233.077,74; cotización obras 998.904,59 |
| 1-ene-2025 a 25-jun-2025 | LOSNCP anterior, PIE 2025 = USD 36.063.017.083,08 | Menor cuantía bienes y servicios 72.126,03; cotización bienes y servicios 540.945,26; menor cuantía obras 252.441,12; cotización obras 1.081.890,51 |
| 26-jun-2025 a 27-oct-2025 | Transición (Ley de Integridad Pública, declaratoria de inconstitucionalidad, reforma de octubre) | Ninguno: no hay umbral verificado |
| Desde 28-oct-2025 | LOSNCP reformada + RGLOSNCP (DE 193) | Ínfima cuantía hasta 10.000; comisión técnica desde 100.000 |

`[VERIFICADO CON DATOS]` Los montos máximos observados en todo el país en 2025 coinciden con los límites del PIE 2025: ningún proceso de menor cuantía de bienes y servicios supera USD 72.126, ni de cotización de bienes y servicios USD 540.824, ni de menor cuantía de obras USD 252.440. Fuentes de las tablas: 2024 https://portal.compraspublicas.gob.ec/sercop/wp-content/uploads/2024/01/montos_contratacion_2024.pdf ; 2025 https://registrodelapropiedad.quito.gob.ec/wp-content/uploads/2025/01/Montos-de-contratacion-2025.pdf

## 6. COOTAD

RO S. 303, 19-oct-2010; compilación reformada al 30-oct-2025 (https://legalcloud.ec/wp-content/uploads/2025/10/COOTAD-30102025-Digital.pdf) y reforma de RO Sexto Suplemento 229, 23-feb-2026.

| Art. | Contenido |
|---|---|
| 57, 87 | El concejo aprueba el presupuesto y la liquidación y fiscaliza al alcalde. |
| 198.1, 198.4 (2026) | Al menos 70 % de los egresos no financieros a inversión (65 % en 2026, 68 % en 2027); indicador trimestral publicado hasta el día 15 del mes siguiente. Su aplicación al DMQ es `[INFERIDO]`. |
| 233-248 | Calendario presupuestario: anteproyecto hasta el 20 de octubre; proyecto definitivo hasta el 31 de octubre; aprobación hasta el 10 de diciembre. |
| 238, 241 | La asamblea local prioriza la inversión y emite resolución de conformidad sobre el anteproyecto. |
| 249 | Al menos 10 % de los ingresos no tributarios para grupos de atención prioritaria. |
| 265, 266 | Liquidación hasta el 31 de enero; rendición de cuentas anual sobre ejecución presupuestaria. |
| 302, 311, 312 | Participación y control social, silla vacía y responsabilidad por incumplirlos. |

## 7. Código Orgánico de Planificación y Finanzas Públicas

Segundo RO Suplemento 306, 22-oct-2010; última reforma 28-ago-2025. URL: https://www.tce.gob.ec/wp-content/uploads/2025/09/Codigo-Organico-de-Planificacion-y-Finanzas-Publicas.pdf. Art. 115: no hay contrato sin certificación presupuestaria. Art. 119: el ejecutivo del GAD presenta al concejo un informe semestral de ejecución dentro de 90 días. Arts. 174-175: libre acceso ciudadano a la información presupuestaria.

## 8. Contraloría General del Estado

LOCGE, Suplemento RO 595, 12-jun-2002. Art. 94: acción popular para denunciar irregularidades en la administración pública. Art. 45 núm. 14: incumplir la LOTAIP genera responsabilidad administrativa culposa. Reglamento de Denuncias (Acuerdo 045-CG-2018, https://www.contraloria.gob.ec/WFDescarga.aspx?id=605&tipo=nor): requisitos de identificación y relato de hechos, no se admiten denuncias anónimas y se protege la identidad del denunciante. Los informes de auditoría se publican por obligación del art. 19 núm. 7 de la LOTAIP.

## 9. Protección de datos personales (LOPDP)

Quinto Suplemento RO 459, 26-may-2021. URL: https://www.sot.gob.ec/wp-content/uploads/2024/11/21.-Ley-Organica-de-Proteccion-de-datos.pdf

- Art. 2 lit. g: la ley no se aplica a datos de personas jurídicas (razón social, RUC de sociedad, contratos).
- Art. 2, último inciso: son públicos el nombre, cargo y contacto profesional de servidores públicos, su remuneración y declaración patrimonial, y los datos de representantes y socios de personas jurídicas.
- Art. 10 lit. e: minimización.

Consecuencia para la herramienta `[INFERIDO]`: se publican nombres de proveedores, RUC y montos tal como los publica el SERCOP. No se publican cédulas, domicilios ni parentescos de personas naturales.

## 10. Normativa del Distrito Metropolitano de Quito

Código Municipal, Ordenanza Metropolitana 072-2024 (RO Edición Especial 1606, 30-may-2024), copia con modificaciones al 1-ago-2024: https://www.quito-turismo.gob.ec/descargas/2024/CODIGO_MUNICIPAL_01-08-2024.pdf. Las reformas posteriores están `[NO VERIFICADO]`.

| Ubicación | Contenido |
|---|---|
| arts. 320-329 | Publicidad de toda actividad municipal en formatos abiertos; transparencia proactiva (art. 324). |
| art. 362 | Solicitudes de acceso al MDMQ: plazo de 10 días, prorrogable 5. |
| art. 436-438 | Observatorios y veedurías sobre contratos y obras del municipio y sus empresas; las veedurías las califica el CPCCS. |
| art. 440 y ss. | Rendición de cuentas anual y presupuesto participativo. |
| arts. 67.79-67.94 | Silla vacía en el Concejo Metropolitano. |

## 11. Reglas automatizables y su estado en la herramienta

| Regla | Norma | Estado |
|---|---|---|
| Posible fraccionamiento (procesos al mismo proveedor que juntos superan un límite) | LOSNCP DG Tercera y art. 50; RGLOSNCP 270, 426.1 | Implementada, con límites por régimen |
| Presupuesto al borde de un límite | Límites de la tabla 5.3 | Implementada |
| Un solo oferente, comparado con la tasa nacional | LOSNCP 47; RGLOSNCP 426.1 | Implementada |
| Proveedor único usado para servicios u obras | RGLOSNCP 139 | Implementada (desde 28-oct-2025) |
| Subasta, licitación o concurso por USD 10.000 o menos | LOSNCP 42, 47, 48, 50 | Implementada (desde 7-oct-2025) |
| Contratación sin concurso por USD 50.000 o más | LOSNCP 38 | Implementada |
| Concentración de adjudicaciones en un proveedor | LOSNCP 21; RGLOSNCP 426.1 | Implementada (tabla de proveedores) |
| Adjudicación al precio máximo; plazos de oferta atípicos | LOSNCP 21; RGLOSNCP 426.1 | Implementada (comparación estadística) |
| Solicitudes LOTAIP sin responder | LOTAIP 4 núm. 3, 34 | Implementada (estadística del portal y generador de solicitudes con plazos) |
| Numerales de transparencia faltantes y días hasta la publicación | LOTAIP 19, 24 | Implementada |
| Datos publicados ilegibles (RUC en notación científica) | LOTAIP 4 núm. 1, 19, 31 núm. 3 | Implementada |
| Ejecución presupuestaria | LOTAIP 19 núm. 6; COPFP 119 | Implementada (informativa) |
| Informes de Contraloría | LOTAIP 19 núm. 7 | Implementada (listado) |
| Fraccionamiento de ínfimas cuantías (suma anual por CPC > USD 10.000) | RGLOSNCP 270, 271 | Pendiente: falta fuente abierta de ínfimas |
| Emergencias: plazos de publicación, duración, informe de cierre | LOSNCP 58-60; RGLOSNCP 303-309 | Pendiente: las emergencias no están en OCDS |
| Complementarios sobre el 8 % o el 15 % | LOSNCP 101 | Pendiente: requiere documentos del contrato |
| Inhabilidades y vínculos | LOSNCP 75-76 | Pendiente: requiere registros societarios |
| Contratista incumplido que vuelve a ganar | LOSNCP 111 | Pendiente: en Quito los RUC del numeral 9 son ilegibles |

## 12. Pendientes de verificación

1. Cifra exacta y RO del PIE 2026 (la Asamblea aprobó USD 46.255 millones el 29-nov-2025). Hoy no se usa en ninguna regla.
2. Umbrales vigentes entre el 26-jun-2025 y el 27-oct-2025.
3. Reformas a la LOSNCP posteriores al 7-oct-2025 y al RGLOSNCP posteriores al 30-jul-2026.
4. Fecha límite mensual de publicación LOTAIP fijada por la Defensoría.
5. Reformas al Código Municipal de Quito posteriores al 1-ago-2024 (por ejemplo, Ordenanza 095-2025).
6. Correspondencia exacta entre la categoría "Bienes y Servicios únicos" del SERCOP y el art. 139 del RGLOSNCP `[INFERIDO]`.
