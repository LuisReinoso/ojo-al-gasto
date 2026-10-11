"""Solicitudes de acceso a la información pública (LOTAIP) y cálculo de plazos.

El texto legal y los plazos salen de datos/normas.toml para poder corregirlos
sin tocar código si cambia la norma.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import date, timedelta
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre")


def feriados(cfg: dict, locales: list[str] | None = None) -> set[date]:
    salida = {date.fromisoformat(f) for fechas in cfg.get("feriados", {}).values() for f in fechas}
    salida.update(date.fromisoformat(f) for f in (locales or []))
    return salida


def sumar_dias_habiles(inicio: date, dias: int, no_laborables: set[date]) -> date:
    """El plazo empieza a correr el día hábil siguiente a la presentación."""
    d = inicio
    contados = 0
    while contados < dias:
        d += timedelta(days=1)
        if d.weekday() < 5 and d not in no_laborables:
            contados += 1
    return d


def calcular_plazos(presentacion: date, cfg: dict, feriados_locales: list[str] | None = None) -> dict:
    """La LOTAIP dice "plazo" (días calendario, lectura de la Defensoría); su Reglamento dice
    "término" (días hábiles). Se devuelven ambas fechas: la calendario es la exigible según la
    Defensoría y la hábil es la más tardía que una entidad podría alegar."""
    p = cfg["lotaip"]["plazos"]
    nl = feriados(cfg, feriados_locales)
    calendario = presentacion + timedelta(days=p["respuesta"])
    habiles = sumar_dias_habiles(presentacion, p["respuesta"], nl)
    anios_cubiertos = {int(a) for a in cfg.get("feriados", {})}
    return {
        "presentacion": presentacion,
        "calendario": calendario,
        "calendario_prorroga": calendario + timedelta(days=p["prorroga"]),
        "habiles": habiles,
        "habiles_prorroga": sumar_dias_habiles(habiles, p["prorroga"], nl),
        "feriados_conocidos": {presentacion.year, presentacion.year + (1 if presentacion.month == 12 else 0)} <= anios_cubiertos,
    }


def fecha_larga(d: date) -> str:
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def texto_plazos(p: dict, cfg: dict) -> str:
    pl = cfg["lotaip"]["plazos"]
    lineas = [
        f"Solicitud presentada el {fecha_larga(p['presentacion'])}. Plazo de respuesta ({pl['base_respuesta']}):",
        f"  • {pl['respuesta']} días calendario (lectura de la Defensoría del Pueblo): hasta el {fecha_larga(p['calendario'])}; "
        f"con prórroga notificada, hasta el {fecha_larga(p['calendario_prorroga'])}.",
        f"  • {pl['respuesta']} días hábiles (el Reglamento habla de 'término'): hasta el {fecha_larga(p['habiles'])}; "
        f"con prórroga, hasta el {fecha_larga(p['habiles_prorroga'])}.",
        "  • Para reclamar sin discusión espere a que pase también la fecha en días hábiles.",
        f"  • Sin respuesta: {cfg['lotaip']['si_no_responde']}",
    ]
    if not p["feriados_conocidos"]:
        lineas.append("  ! No hay calendario de feriados para ese año en datos/normas.toml: verifique las fechas en días hábiles.")
    return "\n".join(lineas)


def _slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60]


def generar(*, entidad: dict, autoridad: dict | None, pedido: str, nombre: str, cedula: str, correo: str,
            telefono: str, formato: str, cfg: dict, destino: Path, fecha: date) -> list[Path]:
    env = Environment(loader=PackageLoader("veeduria", "plantillas"), autoescape=select_autoescape(["html.j2"], default_for_string=False))
    plazos = calcular_plazos(fecha, cfg, entidad.get("feriados_locales"))
    ctx = {
        "e": entidad,
        "autoridad": autoridad or {},
        "pedido": pedido.strip(),
        "nombre": nombre.strip(),
        "cedula": cedula.strip(),
        "correo": correo.strip(),
        "telefono": telefono.strip(),
        "fecha": fecha_larga(fecha),
        "ciudad": entidad.get("canton", ""),
        "plazos": {k: fecha_larga(v) if isinstance(v, date) else v for k, v in plazos.items()},
        "l": cfg["lotaip"],
        "texto_plazos": texto_plazos(plazos, cfg),
    }
    destino.mkdir(parents=True, exist_ok=True)
    base = destino / f"{fecha.isoformat()}-{_slug(entidad.get('canton') or entidad['nombre'])}-{_slug(pedido)[:40]}"
    rutas = []
    if formato in ("md", "ambos"):
        ruta = base.with_suffix(".md")
        ruta.write_text(env.get_template("solicitud.md.j2").render(**ctx), encoding="utf-8")
        rutas.append(ruta)
    if formato in ("html", "ambos"):
        ruta = base.with_suffix(".html")
        ruta.write_text(env.get_template("solicitud.html.j2").render(**ctx), encoding="utf-8")
        rutas.append(ruta)
    return rutas
