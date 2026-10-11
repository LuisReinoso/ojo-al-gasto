"""Análisis de cumplimiento de la LOTAIP y de los datos que la entidad publica.

Usa el Portal Nacional de Transparencia (ver fuentes/transparencia.py).
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .fuentes import transparencia as pnt


def cumplimiento_mensual(id_entidad: int, anios: list[int], cache: Path, dia_limite: int, avisar=print) -> pd.DataFrame:
    """Por mes: numerales publicados, faltantes respecto de los que la entidad publica otros meses,
    y días transcurridos entre el cierre del mes y la publicación.

    `dia_limite` es el día del mes siguiente hasta el que se permite publicar. Con 0 no se juzga
    puntualidad (no hay una fecha límite verificada en la norma).
    """
    df = pnt.cumplimiento_activa(id_entidad, anios, cache, avisar=avisar)
    if df.empty:
        return df
    todos = sorted(set().union(*df["numerales"]))
    df["faltantes"] = df["numerales"].apply(lambda n: [x for x in todos if x not in n])
    inicio_siguiente = pd.to_datetime(pd.DataFrame({"year": df["anio"], "month": df["mes"], "day": 1})) + pd.offsets.MonthBegin(1)
    # Día 1 del mes siguiente = 1 día después del cierre.
    df["dias_tras_cierre"] = (df["ultima_publicacion"].dt.normalize() - inicio_siguiente).dt.days + 1
    if dia_limite > 0:
        df["fecha_limite"] = inicio_siguiente + pd.to_timedelta(dia_limite - 1, unit="D")
        df["dias_atraso"] = (df["ultima_publicacion"].dt.normalize() - df["fecha_limite"]).dt.days.clip(lower=0)
        df["estado"] = df["dias_atraso"].gt(0).map({True: "tarde", False: "a tiempo"})
    else:
        df["dias_atraso"] = float("nan")
        df["estado"] = "publicado"
    df.loc[df["faltantes"].str.len() > 0, "estado"] = "incompleto"
    df.loc[df["numerales_publicados"] == 0, "estado"] = "no publicado"
    # El mes inmediatamente anterior aún está en su periodo normal de publicación.
    hoy = pd.Timestamp.today()
    en_curso = (inicio_siguiente.dt.year == hoy.year) & (inicio_siguiente.dt.month == hoy.month)
    df.loc[en_curso & df["estado"].isin(["no publicado", "incompleto"]), "estado"] = "pendiente"
    return df


def solicitudes(id_entidad: int, anios: list[int], cache: Path) -> pd.DataFrame:
    filas = []
    for anio in anios:
        d = pnt.estadisticas_saip(id_entidad, anio, cache)
        filas.append(
            {
                "anio": anio,
                "recibidas": d.get("total_saip"),
                "respondidas": d.get("responded_saip"),
                "sin_responder": d.get("not_responded_saip"),
                "porcentaje_sin_responder": d.get("percentage_sin_responder"),
            }
        )
    return pd.DataFrame(filas).astype({"anio": int, "recibidas": "Int64", "respondidas": "Int64", "sin_responder": "Int64"})


def _col(df: pd.DataFrame, patron: str) -> str | None:
    for c in df.columns:
        if re.search(patron, c, re.I):
            return c
    return None


def presupuesto(id_entidad: int, cache: Path) -> dict | None:
    """Ejecución presupuestaria (numeral 6) del último mes publicado."""
    periodo = pnt.ultimo_mes_con_numeral(id_entidad, "Numeral 6", cache)
    if not periodo:
        return None
    df = pnt.descargar_numeral(id_entidad, *periodo, "Numeral 6", cache)
    if df is None or df.empty:
        return None
    cols = {k: _col(df, p) for k, p in {
        "grupo": r"^categor", "codificado": r"^codificado", "devengado": r"^devengado", "comprometido": r"^comprometido", "pagado": r"^pagado",
    }.items()}
    if not all(cols.values()):
        return None
    d = pd.DataFrame({k: df[c] for k, c in cols.items()})
    for k in ("codificado", "devengado", "comprometido", "pagado"):
        d[k] = d[k].map(pnt.numero)
    d["grupo"] = d["grupo"].str.strip()
    g = d.groupby("grupo")[["codificado", "comprometido", "devengado", "pagado"]].sum()
    g = g[g["codificado"] > 0]
    g["ejecucion"] = g["devengado"] / g["codificado"]
    total = g[["codificado", "comprometido", "devengado", "pagado"]].sum()
    return {
        "anio": periodo[0],
        "mes": periodo[1],
        "por_grupo": g.sort_values("codificado", ascending=False),
        "codificado": float(total["codificado"]),
        "devengado": float(total["devengado"]),
        "ejecucion": float(total["devengado"] / total["codificado"]) if total["codificado"] else None,
        "url": df.attrs.get("url"),
        "valores_ilegibles": int(df[cols["codificado"]].map(pnt.numero).isna().sum()),
    }


def auditorias_contraloria(id_entidad: int, cache: Path) -> pd.DataFrame | None:
    """Informes de la Contraloría que la entidad reporta (numeral 7)."""
    periodo = pnt.ultimo_mes_con_numeral(id_entidad, "Numeral 7", cache)
    if not periodo:
        return None
    df = pnt.descargar_numeral(id_entidad, *periodo, "Numeral 7", cache)
    if df is None or df.empty:
        return None
    m = {k: _col(df, p) for k, p in {
        "informe": r"numero del informe", "tipo": r"tipo de examen", "examen": r"nombre del examen",
        "periodo": r"per[ií]odo", "area": r"area|área", "enlace": r"descargar el informe", "seguimiento": r"seguimiento",
    }.items()}
    out = pd.DataFrame({k: (df[c].str.strip() if c else "") for k, c in m.items()})
    out.attrs["url"] = df.attrs.get("url")
    out.attrs["periodo"] = periodo
    return out


def calidad_contratacion(id_entidad: int, cache: Path) -> dict | None:
    """Revisa los procesos de contratación publicados en LOTAIP (numeral 8) e incumplimientos (numeral 9)."""
    salida: dict = {}
    for numeral in ("Numeral 8", "Numeral 9"):
        periodo = pnt.ultimo_mes_con_numeral(id_entidad, numeral, cache)
        if not periodo:
            continue
        df = pnt.descargar_numeral(id_entidad, *periodo, numeral, cache)
        if df is None or df.empty:
            continue
        col_ruc = _col(df, r"identificaci|ruc")
        ilegibles = int(df[col_ruc].map(pnt.es_notacion_cientifica).sum()) if col_ruc else 0
        salida[numeral] = {
            "periodo": periodo,
            "filas": len(df),
            "columna_ruc": col_ruc,
            "ruc_ilegibles": ilegibles,
            "url": df.attrs.get("url"),
            "datos": df,
        }
    return salida or None


# Prefijos de códigos que el SERCOP no incluye en la descarga OCDS: órdenes de catálogo (CE), ínfimas
# cuantías (NIC, IC), arrendamiento de inmuebles (ARBI) y otros documentos sin proceso.
_FUERA_DE_OCDS = ("CE-", "NIC", "IC-", "ARBI", "FI-", "ORDEN", "GADDMQ", "CATE", "PE-")


def cruce_lotaip_sercop(lotaip8: pd.DataFrame, procesos: pd.DataFrame, anios: list[int]) -> dict:
    """Compara los códigos de proceso que la entidad declara en LOTAIP con los publicados en SERCOP.

    `procesos` deben ser los de TODAS las entidades auditadas: un proceso del municipio puede haberlo
    publicado una de sus empresas.
    """
    col = _col(lotaip8, r"codigo del proceso")
    if not col:
        return {}
    cod_l = {c for c in lotaip8[col].str.strip().str.upper() if c}
    cod_s = set(procesos["codigo"].dropna().str.strip().str.upper())
    fuera = {c for c in cod_l if c.startswith(_FUERA_DE_OCDS) or re.match(r"^\d{13}-", c)}
    anio_ok = {c for c in cod_l - cod_s - fuera if any(f"-{a}-" in c for a in anios)}
    return {
        "en_lotaip": len(cod_l),
        "encontrados_en_sercop": len(cod_l & cod_s),
        "fuera_de_ocds": len(fuera - cod_s),
        "no_encontrados": sorted(anio_ok),
    }
