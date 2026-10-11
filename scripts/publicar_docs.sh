#!/usr/bin/env bash
# Convierte la documentación (docs/*.md y README.md) a HTML dentro de informes/guia/,
# para leerla en el navegador junto a los informes. Requiere pandoc.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p informes/guia
python3 scripts/encabezado_docs.py
convertir() {  # $1 = archivo .md, $2 = salida .html
  sed -E 's#\]\(docs/(ux/)?([a-z0-9-]+)\.md\)#](\2.html)#g; s/\]\(([a-z0-9-]+)\.md\)/](\1.html)/g; s#\]\(\.\./README\.md\)#](README.html)#g' "$1" |
    pandoc -f gfm -t html5 -s --metadata title="Ojo al Gasto" -H scripts/estilo-docs.html -B scripts/encabezado-docs.html -A scripts/pie-docs.html -V document-css=false -o "$2"
}
for f in docs/*.md docs/ux/*.md; do convertir "$f" "informes/guia/$(basename "${f%.md}").html"; done
convertir README.md informes/guia/README.html
echo "Documentación en informes/guia/"
