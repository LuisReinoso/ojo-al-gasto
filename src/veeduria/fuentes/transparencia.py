"""Portal Nacional de Transparencia (Defensoría del Pueblo) - LOTAIP.

Portal: https://transparencia.dpe.gob.ec
Las entidades publican cada mes sus obligaciones de transparencia activa
(numerales de la LOTAIP) como conjuntos de datos CSV, y el portal registra las
solicitudes de acceso a la información (SAIP) recibidas y respondidas.

Se usan solo los servicios públicos que consume la propia web del portal, sin
autenticación.
"""

from __future__ import annotations

import csv
import io
import json
import re
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

BACKEND = "https://transparencia.dpe.gob.ec/backend"
TRANSPARENCIA = f"{BACKEND}/v1/transparency"
USER_AGENT = "veeduria-ec/0.1 (herramienta ciudadana de datos abiertos)"


def _get(url: str, params: dict | None = None, intentos: int = 5, timeout: int = 120) -> requests.Response:
    espera = 3.0
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
    raise RuntimeError(f"El Portal de Transparencia no respondió: {url} {params}")


def _cache_json(ruta: Path, url: str, params: dict | None, vigente: bool) -> object:
    """Cachea respuestas JSON. Los periodos cerrados no cambian; el vigente se refresca."""
    if ruta.exists() and not vigente:
        return json.loads(ruta.read_text(encoding="utf-8"))
    datos = _get(url, params).json()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    return datos


def buscar_entidades(texto: str) -> list[dict]:
    """Busca entidades registradas en el portal por nombre."""
    r = _get(f"{BACKEND}/v1/admin/public/establishment/list", {"search": texto, "page": 1})
    salida = []
    for grupo in r.json().get("results", []):
        for e in grupo.get("data", []):
            salida.append(
                {
                    "id": e["id"],
                    "nombre": e["name"],
                    "ruc": e.get("identification"),
                    "canton": ", ".join(e.get("canton") or []),
                    "autoridad": f"{e.get('first_name_authority', '')} {e.get('last_name_authority', '')}".strip(),
                    "cargo": e.get("job_authority"),
                    "correo": e.get("email_authority"),
                }
            )
    return salida


def entidad(id_entidad: int) -> dict:
    return _get(f"{BACKEND}/v1/admin/public/establishment/{id_entidad}").json()


def estadisticas_saip(id_entidad: int, anio: int, cache: Path) -> dict:
    """Solicitudes de acceso a la información del año: ingresadas, respondidas, sin responder."""
    vigente = anio >= datetime.now().year
    ruta = cache / "transparencia" / str(id_entidad) / f"saip_{anio}.json"
    return _cache_json(ruta, f"{TRANSPARENCIA}/api/establishment/tp/calc", {"year": anio, "establishment_id": id_entidad}, vigente)


def publicaciones_mes(id_entidad: int, anio: int, mes: int, cache: Path) -> list[dict]:
    """Numerales de transparencia activa publicados por la entidad para un mes."""
    hoy = datetime.now()
    vigente = (anio, mes) >= ((hoy.year, hoy.month - 2) if hoy.month > 2 else (hoy.year - 1, hoy.month + 10))
    ruta = cache / "transparencia" / str(id_entidad) / f"activa_{anio}_{mes:02d}.json"
    datos = _cache_json(
        ruta, f"{TRANSPARENCIA}/transparency/active/public", {"month": mes, "year": anio, "establishment_id": id_entidad}, vigente
    )
    return datos if isinstance(datos, list) else []


def cumplimiento_activa(id_entidad: int, anios: list[int], cache: Path, avisar=print) -> pd.DataFrame:
    """Una fila por mes: cuántos numerales se publicaron y cuándo."""
    hoy = datetime.now()
    filas = []
    for anio in anios:
        for mes in range(1, 13):
            if (anio, mes) >= (hoy.year, hoy.month):
                break
            avisar(f"  Transparencia activa {anio}-{mes:02d}")
            pubs = publicaciones_mes(id_entidad, anio, mes, cache)
            fechas = [pd.Timestamp(p["published_at"]).tz_convert("America/Guayaquil").tz_localize(None) for p in pubs if p.get("published_at")]
            filas.append(
                {
                    "anio": anio,
                    "mes": mes,
                    "numerales_publicados": len(pubs),
                    "numerales": sorted(p["numeral"]["name"] for p in pubs),
                    "primera_publicacion": min(fechas) if fechas else pd.NaT,
                    "ultima_publicacion": max(fechas) if fechas else pd.NaT,
                }
            )
    return pd.DataFrame(filas)


def _leer_csv(texto: str) -> pd.DataFrame:
    muestra = texto[:2000]
    sep = ";" if muestra.count(";") > muestra.count(",") else ","
    filas = list(csv.reader(io.StringIO(texto), delimiter=sep))
    if not filas:
        return pd.DataFrame()
    cab = [c.strip() for c in filas[0]]
    ancho = len(cab)
    cuerpo = [(f + [""] * ancho)[:ancho] for f in filas[1:] if any(c.strip() for c in f)]
    return pd.DataFrame(cuerpo, columns=cab)


def _decodificar(raw: bytes) -> str:
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("cp1252", errors="replace")


def descargar_numeral(id_entidad: int, anio: int, mes: int, patron_numeral: str, cache: Path) -> pd.DataFrame | None:
    """Descarga el 'Conjunto de datos' de un numeral (p. ej. 'Numeral 6').

    `patron_numeral` se compara exactamente con el nombre del numeral en el portal.
    """
    for pub in publicaciones_mes(id_entidad, anio, mes, cache):
        if pub["numeral"]["name"].strip() != patron_numeral:
            continue
        archivos = [f for f in pub["files"] if re.search(r"conjunto", f.get("description", ""), re.I)]
        if not archivos:
            return None
        ruta = cache / "transparencia" / str(id_entidad) / f"{patron_numeral.replace(' ', '_')}_{anio}_{mes:02d}.csv"
        if not ruta.exists():
            raw = _get(TRANSPARENCIA + archivos[0]["url_download"]).content
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_text(_decodificar(raw), encoding="utf-8")
        df = _leer_csv(ruta.read_text(encoding="utf-8"))
        df.attrs["url"] = TRANSPARENCIA + archivos[0]["url_download"]
        return df
    return None


def ultimo_mes_con_numeral(id_entidad: int, patron_numeral: str, cache: Path, max_meses: int = 6) -> tuple[int, int] | None:
    """Último (año, mes) en que la entidad publicó el numeral indicado."""
    hoy = datetime.now()
    anio, mes = hoy.year, hoy.month
    for _ in range(max_meses):
        mes -= 1
        if mes == 0:
            anio, mes = anio - 1, 12
        if any(p["numeral"]["name"].strip() == patron_numeral for p in publicaciones_mes(id_entidad, anio, mes, cache)):
            return anio, mes
    return None


def numero(valor: str) -> float | None:
    """Convierte montos publicados con formatos mezclados ('12.059.316', '1,5', '99406471.44')."""
    if valor is None:
        return None
    s = str(valor).strip().replace("$", "").replace(" ", "")
    if not s or not re.search(r"\d", s):
        return None
    if re.fullmatch(r"-?\d{1,3}(\.\d{3})+", s):  # 12.059.316 -> separador de miles
        s = s.replace(".", "")
    elif re.fullmatch(r"-?\d{1,3}(\.\d{3})+,\d+", s):  # 1.234,56
        s = s.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"-?\d+,\d+", s):  # 1234,56
        s = s.replace(",", ".")
    else:
        s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def es_notacion_cientifica(valor: str) -> bool:
    """True si un identificador (RUC/cédula) quedó destruido como '1,76818E+12'."""
    return bool(re.fullmatch(r"\s*\d+([.,]\d+)?[eE]\+?\d+\s*", str(valor)))
