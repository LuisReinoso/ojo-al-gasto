"""Minimización de datos personales en lo que se publica (LOPDP art. 10).

El RUC de una persona natural es su número de cédula seguido de "001". La LOPDP
(art. 2, último inciso) hace públicos los nombres de comerciantes en su giro de
negocio, pero no su cédula; por eso en los informes públicos se enmascara el RUC
de personas naturales. Los RUC de sociedades y entidades públicas no son datos
personales (art. 2 lit. g) y se publican completos.

Nada se pierde para quien quiera verificar: cada proceso enlaza a su ficha en los
datos abiertos del SERCOP, y la herramienta puede guardar una copia completa
local con `--datos-completos`.
"""

from __future__ import annotations

import re

import pandas as pd

COLUMNAS_RUC = ("ruc_proveedor",)


def es_persona_natural(ruc: str) -> bool:
    """El tercer dígito del RUC indica el tipo: 0-5 persona natural, 6 entidad pública, 9 sociedad privada."""
    s = str(ruc).strip()
    return bool(re.fullmatch(r"\d{13}", s)) and int(s[2]) < 6


def enmascarar_ruc(ruc):
    """'1712345670001' -> '17********001' (solo la provincia, como hace la Contraloría).
    Deja intactos los RUC de sociedades y entidades públicas."""
    if ruc is None or (isinstance(ruc, float) and pd.isna(ruc)):
        return ruc
    partes = [p.strip() for p in str(ruc).split("|")]
    salida = [p[:2] + "*" * 8 + p[-3:] if es_persona_natural(p) else p for p in partes]
    return " | ".join(salida)


def enmascarar(df: pd.DataFrame) -> pd.DataFrame:
    """Copia del DataFrame con los RUC de personas naturales enmascarados."""
    if df is None or df.empty:
        return df
    out = df.copy()
    for col in COLUMNAS_RUC:
        if col in out:
            out[col] = out[col].map(enmascarar_ruc)
    return out


def _ruc_lista(ruc) -> list[str]:
    if ruc is None or (isinstance(ruc, float) and pd.isna(ruc)):
        return []
    return [p.strip() for p in str(ruc).split("|") if p.strip()]


def anonimizar_personas(df: pd.DataFrame) -> pd.DataFrame:
    """En tablas de alertas: reemplaza el nombre de un proveedor persona natural por una etiqueta.

    Las alertas señalan un patrón de la entidad, no una conducta del proveedor. Para no exponer
    a personas naturales junto a una alerta, se publica "Persona natural" y su RUC enmascarado.
    Las sociedades y entidades públicas conservan su nombre.
    """
    if df is None or df.empty or "proveedor" not in df or "ruc_proveedor" not in df:
        return df
    out = df.copy()

    def etiqueta(fila):
        rucs = _ruc_lista(fila["ruc_proveedor"])
        naturales = [r for r in rucs if es_persona_natural(r)]
        if not naturales:
            return fila["proveedor"]
        if len(rucs) == 1:
            return "Persona natural"
        return "Varios proveedores (incluye personas naturales)"

    out["proveedor"] = out.apply(etiqueta, axis=1)
    return out
