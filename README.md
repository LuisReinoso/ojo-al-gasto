# Ojo al Gasto (veeduria-ec)

Herramienta libre para auditar las compras públicas de los municipios del Ecuador. Está hecha para periodistas, veedurías y ciudadanos.

Usa solo datos oficiales y abiertos: el SERCOP y el Portal Nacional de Transparencia de la Defensoría del Pueblo.

> Una alerta no es una acusación. Una alerta le dice dónde mirar.

Ojo al Gasto es una herramienta de control social (Constitución, art. 95). No es una veeduría registrada en el CPCCS: sirve a quienes forman una.

## Qué obtiene

| Comando | Resultado |
|---|---|
| `veeduria auditar` | Una página pública ("¿En qué gasta su cantón?") con preguntas para la entidad y los pasos para presentarlas, un informe técnico con alertas y su base legal, y tablas CSV |
| `veeduria proceso` | La ficha de un proceso: entidad, monto, proveedor, oferentes y enlace oficial |
| `veeduria proveedor` | Todo lo que un proveedor ganó en el país, por entidad y por monto |
| `veeduria solicitud` | Una solicitud LOTAIP lista para firmar, con la fecha límite de respuesta |
| `veeduria plazo` | La fecha límite de respuesta de una solicitud |
| `veeduria entidades` | Los RUC de las entidades de un cantón, para preparar su archivo |

Ejemplos publicados: [Quito](informes/quito/publico.html) e [Ibarra](informes/ibarra/publico.html).

## Instalación

1. Instale Python 3.11 o superior.
2. Ejecute estos comandos:

```bash
git clone https://github.com/LuisReinoso/ojo-al-gasto.git
cd ojo-al-gasto
pip install .
```

## Uso

### Auditar un municipio

```bash
veeduria auditar entidades/quito.toml --anios 2025 2026
```

La primera vez descarga 22 archivos del SERCOP. Esto toma unos minutos. Abra `informes/quito/publico.html`.

### Auditar otro cantón

1. Ejecute `veeduria descargar --anios 2025 2026`.
2. Ejecute `veeduria entidades "nombre del cantón"`.
3. Copie `entidades/quito.toml` a un archivo nuevo.
4. Pegue el `id_transparencia` y los RUC del municipio y de sus empresas públicas.
5. No incluya hospitales ni direcciones distritales: son del Gobierno central.
6. Ejecute `veeduria auditar entidades/su-canton.toml`.

### Investigar un proceso o un proveedor

```bash
veeduria proceso COTS-EPMGDT-2025-002
veeduria proveedor "nombre o RUC" --csv proveedor.csv
```

### Pedir información

```bash
veeduria solicitud entidades/quito.toml --nombre "Ana Pérez" --cedula 1700000000 \
  --correo ana@example.com --pedido "Contrato y actas del proceso LICO-EPMMOP-2026-001"
```

La entidad tiene 10 días para responder, prorrogables 5 (LOTAIP, art. 34). El comando calcula la fecha en días calendario y en días hábiles.

## Archivos del informe

| Archivo | Contenido |
|---|---|
| `publico.html` | Resumen para el público. No nombra a personas naturales |
| `informe.html` | Informe técnico con todas las alertas y su base legal |
| `alertas.csv`, `procesos.csv`, `proveedores.csv` | Datos para análisis propio |
| `procedencia.json` | Archivos oficiales usados, con fecha y huella SHA-256 |

**AVISO:** el RUC de una persona natural contiene su cédula. Todos los archivos lo muestran enmascarado. En las alertas, el informe técnico y `proveedores.csv`, una persona natural aparece como "Persona natural": una alerta describe un patrón de la entidad, no una conducta del proveedor. `procesos.csv` conserva el nombre, igual que el dato oficial del SERCOP. La opción `--datos-completos` guarda una copia sin cambios en `./privado`. No publique esa copia.

## Límites

- El SERCOP no publica en datos abiertos las ínfimas cuantías ni las emergencias.
- La subasta inversa no trae presupuesto en datos abiertos. Se usa el monto adjudicado.
- Entre el 26 de junio y el 27 de octubre de 2025 cambió la ley de contratación. En ese periodo no se aplican reglas de límite.

## Proyectos relacionados

- [Observatorio de Contratación Pública](https://www.contratostransparentes.ec/) de la Fundación Ciudadanía y Desarrollo: índices y alertas de riesgo nacionales.
- [licita.ec](https://licita.ec): buscador y alertas de procesos del SERCOP.

Ojo al Gasto se centra en lo local: un cantón, preguntas a sus entidades y los pasos para presentarlas por LOTAIP.

## Documentación

- [Guía para periodistas](docs/periodistas.md): de una alerta a una nota publicable.
- [Hazlo tú](docs/hazlo-tu.md): cómo crear un proyecto así con IA, sin saber programar.
- [Ejemplo con OCR](docs/ejemplo-contraloria.md): leer un informe escaneado de la Contraloría.
- [Metodología](docs/metodologia.md) y [marco legal](docs/marco-legal.md).
- [Hallazgos de Quito 2025-2026](docs/auditoria-quito-2025-2026.md).
- [Reglas de redacción](docs/estilo.md).
- Revisiones de experiencia de uso: [recorrido cognitivo](docs/ux/recorrido-cognitivo.md) y [diseño y marca](docs/ux/revision-diseno.md).

## Contribuir

Reporte errores o proponga mejoras en [Issues](https://github.com/LuisReinoso/ojo-al-gasto/issues). Las reglas están en `src/veeduria/reglas.py`. Los umbrales y los textos legales están en `src/veeduria/datos/normas.toml`. Si cambia una norma, corrija ese archivo.

```bash
pip install -e ".[dev]"
pytest
```

## Licencia

Código: MIT. Datos del SERCOP: CC BY 3.0 Ecuador. Información del Portal de Transparencia: pública según la LOTAIP.
