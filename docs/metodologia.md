# Metodología

## Fuentes

| Fuente | Datos | Licencia |
|---|---|---|
| [SERCOP, datos abiertos OCDS](https://datosabiertos.compraspublicas.gob.ec/PLATAFORMA/datos-abiertos) | Todos los procesos del país, un archivo por mes | CC BY 3.0 Ecuador |
| [Portal Nacional de Transparencia](https://transparencia.dpe.gob.ec) | Publicación LOTAIP mensual, solicitudes, presupuesto, informes de Contraloría | Información pública (LOTAIP) |

## Procesamiento

1. La herramienta une las tablas de cada archivo mensual en una fila por proceso.
2. Si un proceso aparece en varios meses, la herramienta usa la versión más reciente.
3. Un proceso cuenta en el año de su publicación (inicio del periodo de ofertas). En catálogo electrónico se usa la fecha de la orden.
4. El monto es el presupuesto del proceso. Si no hay presupuesto, el monto es lo adjudicado.
5. Las entidades de un cantón se definen por RUC en `entidades/<cantón>.toml`.

## Comparación con el país

Cada tasa de la entidad se compara con la tasa nacional del mismo tipo de procedimiento y del mismo periodo. La herramienta calcula la probabilidad de que la diferencia sea casualidad (prueba binomial con corrección de Bonferroni). Una tasa se marca en rojo si cumple tres condiciones:

1. Es mayor que 1,5 veces la tasa nacional.
2. Tiene 5 casos o más.
3. Su probabilidad por azar es menor que 0,05 dividido entre el número de comparaciones.

## Alertas

| Alerta | Condición | Nivel |
|---|---|---|
| Posible fraccionamiento | 2 o más procesos de la misma entidad y el mismo proveedor, en 90 días, bajo el mismo régimen legal. Cada uno está bajo un límite y la suma lo supera | alta si los objetos se parecen; media si no |
| Proveedor único para servicios u obras | Régimen de bienes y servicios únicos para un servicio u obra, desde el 28-oct-2025 (RGLOSNCP, art. 139) | media |
| Un solo oferente | Procedimiento competitivo con un oferente | media |
| Contratación sin concurso | Régimen especial o contratación directa de USD 50.000 o más | media |
| Presupuesto al borde del límite | Presupuesto hasta 2 % bajo un límite | baja |
| Plazo de ofertas muy corto | Menos días que el 95 % de los procesos del mismo tipo en el país | baja |
| Adjudicado al precio máximo | Adjudicado por el 99,5 % del presupuesto o más | baja |
| Procedimiento bajo el umbral legal | Subasta, licitación o concurso de USD 10.000 o menos, desde el 7-oct-2025 | baja |

## Límites por fecha

| Publicación | Límites usados |
|---|---|
| Hasta el 25-jun-2025 | Menor cuantía y cotización, calculadas con el Presupuesto Inicial del Estado. Solo para menor cuantía, cotización y licitación |
| 26-jun a 27-oct-2025 | Ninguno: la transición de la reforma no tiene un límite verificado |
| Desde el 28-oct-2025 | Comisión técnica obligatoria desde USD 100.000 (RGLOSNCP, art. 88) |

Control: en todo el país ningún proceso de menor cuantía de bienes y servicios supera USD 72.126 en 2025. Esto confirma el límite calculado.

## Transparencia (LOTAIP)

- **Días hasta la publicación:** días entre el cierre del mes y la publicación. No hay una fecha límite verificada en la norma; la herramienta no califica atrasos.
- **Mes incompleto:** falta un numeral que la entidad publica en otros meses.
- **Solicitudes sin responder:** cifras anuales del portal. El año en curso es parcial.
- **Datos ilegibles:** RUC convertidos a notación científica por una hoja de cálculo.

## Privacidad

El RUC de una persona natural contiene su cédula. La herramienta lo enmascara en todos los archivos (LOPDP, art. 10). En las alertas, el informe técnico y la lista de proveedores, una persona natural aparece como "Persona natural". La razón: una alerta describe un patrón de la entidad, no una conducta del proveedor. `procesos.csv` conserva el nombre, igual que el dato oficial del SERCOP.

## Lo que la herramienta no ve

- Ínfimas cuantías y emergencias: no están en los datos abiertos del SERCOP.
- Calidad de las obras y precios unitarios: necesitan documentos y visitas.
- Vínculos entre proveedores y funcionarios: necesitan registros societarios.
