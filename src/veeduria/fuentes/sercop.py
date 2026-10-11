"""Descarga y normalización de la contratación pública del SERCOP (estándar OCDS).

Fuente: https://datosabiertos.compraspublicas.gob.ec/PLATAFORMA/datos-abiertos
Licencia de los datos: CC BY 3.0 Ecuador.

La descarga masiva entrega un ZIP por año y mes con varias tablas CSV
(releases, tender, awards, suppliers, contracts, planning). Aquí se cachean en
disco y se unen en una sola tabla de procesos, una fila por `ocid`.

Limitación conocida: la descarga OCDS NO incluye las ínfimas cuantías.
"""

from __future__ import annotations

import io
import time
import zipfile
from pathlib import Path

import pandas as pd
import requests

BASE = "https://datosabiertos.compraspublicas.gob.ec/PLATAFORMA"
USER_AGENT = "veeduria-ec/0.1 (herramienta ciudadana de datos abiertos)"
TABLAS = ("releases", "tender", "awards", "suppliers", "contracts", "planning")
MESES = (
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
)


def _get(url: str, params: dict | None = None, intentos: int = 6, timeout: int = 300) -> requests.Response:
    """GET con reintentos: el portal responde 429 si se le pide muy rápido."""
    espera = 5.0
    for intento in range(intentos):
        try:
            r = requests.get(url, params=params, timeout=timeout, headers={"User-Agent": USER_AGENT})
        except requests.RequestException:
            if intento == intentos - 1:
                raise
        else:
            if r.status_code == 200:
                return r
            if r.status_code not in (429, 500, 502, 503, 504):
                r.raise_for_status()
        time.sleep(espera)
        espera *= 2
    raise RuntimeError(f"El portal no respondió tras {intentos} intentos: {url} {params}")


def descargar_mes(anio: int, mes: int, cache: Path, refrescar: bool = False) -> Path:
    """Descarga (o reutiliza) el ZIP OCDS de un mes. Devuelve la ruta del ZIP."""
    destino = cache / "sercop" / f"ocds_{anio}_{mes:02d}.zip"
    if destino.exists() and not refrescar:
        return destino
    destino.parent.mkdir(parents=True, exist_ok=True)
    r = _get(f"{BASE}/download", {"type": "csv", "year": anio, "month": mes, "method": "all"})
    if not r.content.startswith(b"PK"):
        raise RuntimeError(f"Respuesta inesperada del SERCOP para {anio}-{mes:02d}: {r.content[:120]!r}")
    tmp = destino.with_suffix(".part")
    tmp.write_bytes(r.content)
    tmp.replace(destino)
    return destino


def _leer_zip(ruta: Path) -> dict[str, pd.DataFrame]:
    tablas: dict[str, pd.DataFrame] = {}
    with zipfile.ZipFile(ruta) as z:
        for nombre in z.namelist():
            clave = nombre.split("_", 1)[0]
            if clave in TABLAS:
                with z.open(nombre) as f:
                    tablas[clave] = pd.read_csv(io.TextIOWrapper(f, encoding="utf-8"), dtype=str, keep_default_na=False)
    return tablas


def _num(serie: pd.Series) -> pd.Series:
    return pd.to_numeric(serie.replace("", None), errors="coerce")


def _fecha(serie: pd.Series) -> pd.Series:
    # Las fechas vienen con zona horaria (-05:00 o Z); se normalizan a fecha local de Ecuador.
    f = pd.to_datetime(serie.replace("", None), errors="coerce", utc=True)
    return f.dt.tz_convert("America/Guayaquil").dt.tz_localize(None)


def construir_procesos(tablas: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Une las tablas OCDS de un mes en una fila por proceso (ocid)."""
    rel = tablas["releases"].sort_values("id").drop_duplicates("ocid", keep="last")
    base = rel[["ocid", "id", "buyer_id", "buyer_name", "date"]].rename(
        columns={"id": "release_id", "date": "fecha"}
    )

    t = tablas["tender"]
    t = t[t["release_id"].isin(base["release_id"])]
    t = t.drop_duplicates("ocid", keep="last")[
        [
            "ocid", "id", "title", "description", "status", "value_amount",
            "procurementMethod", "procurementMethodDetails", "mainProcurementCategory",
            "tenderPeriod_startDate", "tenderPeriod_endDate", "numberOfTenderers",
        ]
    ].rename(
        columns={
            "id": "codigo",
            "title": "titulo",
            "description": "objeto",
            "status": "estado",
            "value_amount": "presupuesto",
            "procurementMethod": "metodo",
            "procurementMethodDetails": "tipo_proceso",
            "mainProcurementCategory": "categoria",
            "tenderPeriod_startDate": "inicio_ofertas",
            "tenderPeriod_endDate": "fin_ofertas",
            "numberOfTenderers": "num_oferentes",
        }
    )

    a = tablas["awards"]
    a = a[a["release_id"].isin(base["release_id"])].copy()
    a["amount"] = _num(a["amount"])
    a_ok = a[a["status"].isin(["active", ""])]
    adj = a_ok.groupby("ocid", as_index=False).agg(monto_adjudicado=("amount", "sum"), estado_adjudicacion=("status", "first"))

    s = tablas["suppliers"]
    s = s[s["release_id"].isin(base["release_id"])].copy()
    s["ruc_proveedor"] = s["id"].str.extract(r"EC-RUC-(\d{10,13})", expand=False)
    prov = s.groupby("ocid", as_index=False).agg(
        proveedor=("name", lambda x: " | ".join(sorted(set(x)))),
        ruc_proveedor=("ruc_proveedor", lambda x: " | ".join(sorted(set(v for v in x if isinstance(v, str))))),
        num_proveedores=("name", "nunique"),
    )

    c = tablas["contracts"]
    c = c[c["release_id"].isin(base["release_id"])].copy()
    c["amount"] = _num(c["amount"])
    con = c.groupby("ocid", as_index=False).agg(monto_contrato=("amount", "sum"), fecha_firma=("dateSigned", "max"))

    p = tablas.get("planning", pd.DataFrame(columns=["ocid", "budget_id"]))
    par = p.drop_duplicates("ocid", keep="last")[["ocid", "budget_id"]].rename(columns={"budget_id": "partida"})

    df = (
        base.merge(t, on="ocid", how="left")
        .merge(adj, on="ocid", how="left")
        .merge(prov, on="ocid", how="left")
        .merge(con, on="ocid", how="left")
        .merge(par, on="ocid", how="left")
    )
    df["ruc_entidad"] = df["buyer_id"].str.extract(r"(\d{13})", expand=False)
    df["presupuesto"] = _num(df["presupuesto"])
    df["num_oferentes"] = _num(df["num_oferentes"])
    for col in ("fecha", "inicio_ofertas", "fin_ofertas", "fecha_firma"):
        df[col] = _fecha(df[col])
    # `fecha` es la de la última actualización del proceso. Para asignar el año se usa la
    # publicación (inicio del periodo de ofertas); en compras por catálogo no existe y se usa `fecha`.
    df["fecha_publicacion"] = df["inicio_ofertas"].fillna(df["fecha"])
    # Monto de referencia: el presupuesto del proceso; si no lo hay (catálogo, algunas subastas), lo adjudicado.
    df["monto"] = df["presupuesto"].fillna(df["monto_adjudicado"])
    # El SERCOP agrega al código el identificador interno de la entidad (SIE-MDMQ-2025-101-41357);
    # el código que usa la entidad en sus documentos y en LOTAIP es sin ese sufijo.
    df["codigo"] = df["codigo"].str.replace(r"-\d+$", "", regex=True)
    df["url_sercop"] = f"{BASE}/ocds/" + df["ocid"]
    return df.drop(columns=["release_id"])


def cargar(anios: list[int], cache: Path, refrescar: bool = False, avisar=print) -> pd.DataFrame:
    """Descarga y une todos los meses disponibles de los años pedidos.

    El resultado unido se guarda en caché (procesos_<años>.pkl) y se reutiliza mientras
    no cambie ninguno de los archivos mensuales.
    """
    hoy = pd.Timestamp.today()
    rutas = []
    for anio in anios:
        ultimo_mes = hoy.month if anio == hoy.year else 12
        for mes in range(1, ultimo_mes + 1):
            avisar(f"  SERCOP {anio}-{mes:02d} ({MESES[mes - 1]})")
            rutas.append((anio, mes, descargar_mes(anio, mes, cache, refrescar=refrescar and anio == hoy.year)))

    unido = cache / "sercop" / f"procesos_{'_'.join(map(str, sorted(anios)))}.pkl"
    if unido.exists() and unido.stat().st_mtime > max(r.stat().st_mtime for _, _, r in rutas):
        return pd.read_pickle(unido)

    partes = []
    for anio, mes, ruta in rutas:
        tablas = _leer_zip(ruta)
        if "releases" not in tablas or tablas["releases"].empty:
            continue
        procesos = construir_procesos(tablas)
        procesos["anio_archivo"] = anio
        procesos["mes_archivo"] = mes
        partes.append(procesos)
    if not partes:
        return pd.DataFrame()
    df = pd.concat(partes, ignore_index=True)
    # Un mismo proceso puede reaparecer en otro mes si se actualizó: queda la versión más reciente.
    df = df.sort_values(["anio_archivo", "mes_archivo"]).drop_duplicates("ocid", keep="last").reset_index(drop=True)
    df.to_pickle(unido)
    return df


def filtrar_entidades(df: pd.DataFrame, rucs: list[str]) -> pd.DataFrame:
    return df[df["ruc_entidad"].isin(rucs)].copy()
