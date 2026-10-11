"""Procedencia de los datos: qué archivos oficiales se usaron, cuándo se descargaron y su huella.

Con esto cualquier persona puede reproducir el informe y comprobar que partió de los
mismos datos: si la huella SHA-256 de su descarga coincide, los datos son idénticos.
"""

from __future__ import annotations

import hashlib
import sys
from datetime import datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def _sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def _version() -> str:
    try:
        return version("veeduria-ec")
    except PackageNotFoundError:
        return "desarrollo"


def registrar(cache: Path, anios: list[int], id_transparencia: int | None) -> dict:
    archivos = sorted(p for a in anios for p in (cache / "sercop").glob(f"ocds_{a}_*.zip"))
    if id_transparencia:
        archivos += sorted((cache / "transparencia" / str(id_transparencia)).glob("*"))
    return {
        "herramienta": f"veeduria-ec {_version()}",
        "comando": "veeduria " + " ".join(sys.argv[1:]) if sys.argv and sys.argv[0].endswith("veeduria") else None,
        "generado": datetime.now().isoformat(timespec="seconds"),
        "fuentes": {
            "SERCOP (OCDS, CC BY 3.0 EC)": "https://datosabiertos.compraspublicas.gob.ec/PLATAFORMA/datos-abiertos",
            "Portal Nacional de Transparencia (Defensoría del Pueblo)": "https://transparencia.dpe.gob.ec",
        },
        "archivos": [
            {
                "archivo": str(p.relative_to(cache)),
                "descargado": datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds"),
                "bytes": p.stat().st_size,
                "sha256": _sha256(p),
            }
            for p in archivos
            if p.is_file()
        ],
    }
