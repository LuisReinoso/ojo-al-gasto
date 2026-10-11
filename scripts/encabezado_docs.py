"""Genera el encabezado y el pie de las guías HTML desde la marca y la plantilla de la herramienta."""
import sys
from pathlib import Path

raiz = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(raiz / "src"))
from veeduria.informe import MARCA  # noqa: E402

plantilla = (raiz / "src/veeduria/plantillas/_marca.html.j2").read_text(encoding="utf-8")
encabezado = (
    plantilla.split("#}", 1)[1]
    .replace("{{ raiz }}", "../")
    .replace("{{ marca.nombre }}", MARCA["nombre"])
    .replace("{{ marca.lema }}", MARCA["lema"])
    .strip()
)
(raiz / "scripts/encabezado-docs.html").write_text(encabezado + "\n<main>\n", encoding="utf-8")
(raiz / "scripts/pie-docs.html").write_text(
    f'<footer class="pie">{MARCA["nombre"]} · herramienta libre (licencia MIT)</footer>\n</main>\n', encoding="utf-8"
)
