"""Genera el informe HTML y los CSV de una auditoría."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
from jinja2 import Environment, PackageLoader, select_autoescape

from . import privacidad, publico

# Identidad pública del proyecto. Para cambiar el nombre, edite solo este valor.
MARCA = {
    "nombre": "Ojo al Gasto",
    "lema": "Control ciudadano de las compras municipales",
}
FAVICON = (
    "data:image/svg+xml,"
    "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E"
    "%3Cpath d='M1.8 12C4.8 6.2 19.2 6.2 22.2 12C19.2 17.8 4.8 17.8 1.8 12Z' fill='white' stroke='%231c5cab' stroke-width='2.2'/%3E"
    "%3Ccircle cx='12' cy='12' r='4.3' fill='%23eb6834'/%3E%3C/svg%3E"
)
CSS_MARCA = """
  .marca { display: flex; align-items: center; justify-content: space-between; gap: .8rem; flex-wrap: wrap;
           padding: .7rem 0 .9rem; border-bottom: 1px solid var(--linea, #e3e1dc); margin-bottom: 1.4rem; }
  .marca-enlace { display: inline-flex; align-items: center; gap: .45rem; text-decoration: none; color: inherit; white-space: nowrap; }
  .marca-logo { width: 34px; height: 34px; flex: none; }
  .marca-nombre { font-weight: 800; font-size: 1.15rem; letter-spacing: -.01em; }
  .marca-lema { color: var(--text-muted, #6f6e69); font-size: .82rem; }
"""

MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre")

DESCRIPCIONES = {
    "Posible fraccionamiento": "Varios procesos de la misma entidad con el mismo proveedor y objetos parecidos, en pocas semanas, cada uno bajo un límite legal y que juntos lo superan. La ley prohíbe dividir una compra para eludir el procedimiento que corresponde; puede haber una explicación válida. Pregunte por qué se contrataron por separado.",
    "Mismo proveedor, suma sobre un límite": "Procesos de la misma entidad con el mismo proveedor que juntos superan un límite, pero con objetos distintos. Probablemente es coincidencia. Se listan para que pueda descartarlo.",
    "Proveedor único para servicios u obras": "Contratos por el régimen de bienes y servicios únicos clasificados como servicio u obra. Si esa categoría corresponde al art. 139 del Reglamento de la LOSNCP (vigente desde el 28-oct-2025), ese artículo solo permite el proveedor único para repuestos, mejora de tecnologías existentes y patentes. Puede ser un error de clasificación: pida el informe técnico motivado.",
    "Un solo oferente": "Procedimientos pensados para que compitan varios proveedores, pero en los que se presentó uno solo. Puede deberse a un mercado pequeño, o a requisitos o plazos que alejaron a otros oferentes.",
    "Contratación sin concurso": "Contratos de USD 50.000 o más adjudicados por régimen especial o contratación directa, sin concurso de ofertas. Son legales cuando se cumple la causal; pida la resolución motivada.",
    "Presupuesto al borde del límite": "Presupuestos fijados apenas por debajo del monto que obligaría a un procedimiento con más controles (hasta junio de 2025, los límites de menor cuantía y cotización; desde octubre de 2025, los USD 100.000 desde los que es obligatoria una comisión técnica).",
    "Plazo de ofertas muy corto": "Procesos en los que se dio menos tiempo para presentar ofertas que en el 95% de procesos del mismo tipo en el país.",
    "Adjudicado al precio máximo": "Procesos adjudicados por el 99,5% o más del presupuesto referencial: la competencia no logró bajar el precio. No incluye la menor cuantía de obras, donde el precio era fijo por ley.",
    "Procedimiento bajo el umbral legal": "Subastas, licitaciones o concursos con presupuesto de USD 10.000 o menos, monto que la ley reformada reserva a la ínfima cuantía.",
}
ORDEN_REGLAS = list(DESCRIPCIONES)
ORDEN_REGLAS.append(ORDEN_REGLAS.pop(ORDEN_REGLAS.index("Mismo proveedor, suma sobre un límite")))


def _miles(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    return f"{v:,.0f}".replace(",", ".")


def _usd_m(v) -> str:
    if v is None or pd.isna(v):
        return "—"
    if abs(v) >= 1e6:
        return "USD " + f"{v / 1e6:,.1f}".replace(",", "_").replace(".", ",").replace("_", ".") + " M"
    return f"USD {_miles(v)}"


def _pct(v, decimales: int = 1) -> str:
    if v is None or pd.isna(v):
        return "—"
    return f"{100 * v:.{decimales}f}\u00a0%".replace(".", ",")


def _millones(v) -> str:
    """566717500 -> '566,7'; menos de 10 millones lleva dos decimales."""
    if v is None or pd.isna(v):
        return "—"
    m = v / 1e6
    return f"{m:,.{2 if abs(m) < 10 else 1}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def _prob(p: float) -> str:
    return "menor a 1 en 1.000" if p < 0.001 else f"{p:.3f}".replace(".", ",")


def _fecha(v) -> str:
    if v is None or pd.isna(v):
        return ""
    return pd.Timestamp(v).strftime("%d/%m/%Y")


def _corto(v, n: int) -> str:
    s = "" if v is None or (isinstance(v, float) and pd.isna(v)) else str(v)
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def entorno() -> Environment:
    env = Environment(loader=PackageLoader("veeduria", "plantillas"), autoescape=select_autoescape(["html", "j2"]))
    env.filters.update(miles=_miles, usd_m=_usd_m, pct=_pct, fecha=_fecha, corto=_corto, millones=_millones)
    env.globals["mes_nombre"] = lambda m: MESES[int(m) - 1]
    env.globals["prob"] = _prob
    env.globals["marca"] = MARCA
    env.globals["favicon"] = FAVICON
    env.globals["css_marca"] = CSS_MARCA
    return env


def hallazgos_principales(ctx: dict) -> list[str]:
    """Frases cortas con lo más relevante, ordenadas de mayor a menor gravedad."""
    h: list[str] = []
    r = ctx["r"]
    alertas: pd.DataFrame = ctx["alertas"]
    if not alertas.empty:
        frac = alertas[alertas["regla"] == "Posible fraccionamiento"]
        if not frac.empty:
            h.append(
                f"<b>{frac['grupo'].nunique()} grupos de procesos con posible fraccionamiento</b>: mismo proveedor, objetos parecidos y suma sobre un límite legal "
                f"({frac['ocid'].nunique()} procesos, USD {_miles(frac.drop_duplicates('ocid')['monto'].sum())}). Son la primera prioridad para preguntar."
            )
    tasas: pd.DataFrame = ctx["tasas"]
    # Corrección de Bonferroni: se comparan varios tipos de procedimiento a la vez.
    umbral_p = 0.05 / max(len(tasas), 1)
    altas = tasas[(tasas["un_oferente"] >= 5) & (tasas["tasa_entidad"] > 1.5 * tasas["tasa_nacional"]) & (tasas["p_valor"] < umbral_p)]
    for tipo, f in altas.iterrows():
        h.append(
            f"En <b>{tipo}</b>, el {_pct(f.tasa_entidad)} de los procesos tuvo un solo oferente, frente al {_pct(f.tasa_nacional)} del país "
            f"({int(f.un_oferente)} procesos; se esperarían unos {f.esperados:.0f}). Que ocurra por azar es improbable "
            f"(probabilidad {_prob(f.p_valor)})."
        )
    mejores = tasas[(tasas["procesos"] >= 30) & (tasas["tasa_entidad"] < 0.67 * tasas["tasa_nacional"])]
    if not mejores.empty:
        h.append(
            "En competencia está <b>mejor que el promedio del país</b>: tuvo menos procesos con un solo oferente en "
            + "; ".join(f"{t.replace('Concurso publico', 'Concurso público')} ({_pct(f.tasa_entidad)} frente a {_pct(f.tasa_nacional)})" for t, f in mejores.iterrows()) + "."
        )
    if r["monto"]:
        h.append(f"El <b>{_pct(r['directo_monto'] / r['monto'])}</b> del monto ({_usd_m(r['directo_monto'])}) se contrató por régimen especial o contratación directa, sin concurso de ofertas.")
    prov: pd.DataFrame = ctx["proveedores"]
    if not prov.empty:
        p = prov.iloc[0]
        h.append(f"El proveedor que más recibe es <b>{p.proveedor}</b>: {_usd_m(p.monto)} en {p.procesos} proceso{'s' if p.procesos != 1 else ''} ({_pct(p.participacion)} de lo adjudicado sin catálogo).")
    s = ctx.get("saip_destacado")
    if s is not None:
        if s.sin_responder and s.recibidas >= 10:
            h.append(f"En {int(s.anio)} la entidad dejó <b>sin responder {_miles(s.sin_responder)} de {_miles(s.recibidas)} solicitudes de acceso a la información</b> ({_pct(s.sin_responder / s.recibidas)}).")
    cum = ctx.get("cumplimiento")
    if cum is not None and not cum.empty:
        evaluados = cum[cum["estado"] != "pendiente"]
        conteo = evaluados["estado"].value_counts()
        nombres = {"no publicado": ("mes no publicado", "meses no publicados"), "incompleto": ("mes incompleto", "meses incompletos"),
                   "tarde": ("mes publicado tarde", "meses publicados tarde")}
        problemas = [f"{conteo[e]} {nombres[e][int(conteo[e] != 1)]}" for e in nombres if e in conteo]
        if problemas:
            h.append(f"En la transparencia LOTAIP, de {len(evaluados)} meses evaluados hubo <b>{', '.join(problemas)}</b>"
                     + (" (incompleto: falta algún numeral que la entidad sí publica otros meses)." if "incompleto" in conteo else "."))
        pub = cum[cum["numerales_publicados"] > 0]
        if not pub.empty:
            h.append(
                f"Publica la información de transparencia de cada mes, en promedio, <b>{pub['dias_tras_cierre'].mean():.0f} días después del cierre del mes</b> "
                f"(entre {pub['dias_tras_cierre'].min():.0f} y {pub['dias_tras_cierre'].max():.0f})."
            )
    cal = ctx.get("calidad") or {}
    ilegibles = sum(c["ruc_ilegibles"] for c in cal.values())
    if ilegibles:
        h.append(f"<b>{_miles(ilegibles)} RUC de contratistas</b> publicados en sus archivos LOTAIP son ilegibles (notación científica de Excel): no se puede saber a quién se contrató.")
    ppto = ctx.get("ppto")
    if ppto and ppto.get("ejecucion") is not None:
        mes = MESES[ppto["mes"] - 1]
        h.append(f"A {mes} de {ppto['anio']} había ejecutado (devengado) el <b>{_pct(ppto['ejecucion'])}</b> de su presupuesto codificado "
                 f"(un ritmo parejo daría cerca del {_pct(ppto['mes'] / 12)}).")
        g = ppto["por_grupo"]
        obra = g[g.index.str.match(r"^75\b")]
        if not obra.empty and obra["codificado"].iloc[0] > 0:
            o = obra.iloc[0]
            h.append(f"En <b>obras públicas</b> (grupo 75) había ejecutado solo el <b>{_pct(o.ejecucion)}</b>: "
                     f"{_usd_m(o.devengado)} de {_usd_m(o.codificado)} presupuestados.")
    return h


def _fecha_larga(v) -> str:
    v = pd.Timestamp(v)
    return f"{v.day} de {MESES[v.month - 1]} de {v.year}"


def _contexto_publico(ctx: dict, procedencia: dict) -> dict:
    e = ctx["e"]
    nombres = {x["ruc"]: x["nombre"] for x in e["rucs"]}
    propios = {e.get("canton", ""), e.get("provincia", "")} - {""}
    anios = ctx["anios"]
    curso = publico.anio_en_curso(anios)
    orden = sorted((a for a in anios if a != curso), reverse=True) + ([curso] if curso else [])
    procesos = ctx["procesos"]
    anuales = []
    for a in orden:
        r = publico.resumen_anual(procesos, a, nombres, propios=propios)
        if r["procesos"]:
            anuales.append(r)
    t = ctx["tasas"]
    t = t[t["procesos"] >= 30]
    competencia = [
        {"tipo": tipo.replace("Concurso publico", "Concurso público"), "procesos": int(f.procesos), "entidad": float(f.tasa_entidad), "pais": float(f.tasa_nacional)}
        for tipo, f in t.iterrows() if pd.notna(f.tasa_nacional)
    ]
    mejor = sum(c["entidad"] < c["pais"] for c in competencia)
    frase_comp = (
        f"En {mejor} de {len(competencia)} tipos de procedimiento, {e['canton']} tuvo menos procesos con un solo oferente que el promedio del país."
        if competencia else ""
    )
    fechas = [a["descargado"][:10] for a in procedencia["archivos"]]
    n_sercop = sum(a["archivo"].startswith("sercop/ocds_") for a in procedencia["archivos"])
    n_pnt = sum(a["archivo"].startswith("transparencia/") for a in procedencia["archivos"])
    return {
        **ctx,
        "anuales": anuales,
        "anio_curso": curso,
        "competencia": competencia,
        "tope_competencia": max([c["pais"] for c in competencia] + [c["entidad"] for c in competencia] + [0.01]),
        "frase_competencia": frase_comp,
        "preguntas": publico.preguntas_abiertas(ctx, nombres, propios),
        "fecha_datos": _fecha_larga(procesos.get("fecha", procesos["fecha_publicacion"]).max()) if not procesos.empty else "",
        "procedencia": {
            **procedencia,
            "desde": _fecha_larga(min(fechas)) if fechas else "",
            "hasta": _fecha_larga(max(fechas)) if fechas else "",
            "n_sercop": n_sercop,
            "n_pnt": n_pnt,
        },
        "archivo_entidad": ctx.get("archivo_entidad", "entidad.toml"),
        "solicitud_js": _datos_solicitud(ctx),
    }


def _datos_solicitud(ctx: dict) -> dict:
    """Plazos y portal oficial para los pasos de "Cómo presentar su pregunta"."""
    lot = (ctx.get("cfg") or {}).get("lotaip", {})
    return {
        "dias": lot.get("plazos", {}).get("respuesta", 10),
        "prorroga": lot.get("plazos", {}).get("prorroga", 5),
        "portal": lot.get("portal", "https://transparencia.dpe.gob.ec"),
    }


def escribir(destino: Path, ctx: dict) -> tuple[Path, list[str]]:
    """Escribe el informe técnico, la página pública y los CSV. Todo lo que se escribe aquí
    puede publicarse: los RUC de personas naturales van enmascarados (ver privacidad.py)."""
    destino.mkdir(parents=True, exist_ok=True)
    alertas_completas: pd.DataFrame = ctx["alertas"]
    if not alertas_completas.empty and "grupo" not in alertas_completas:
        alertas_completas["grupo"] = None
    alertas = privacidad.enmascarar(privacidad.anonimizar_personas(alertas_completas))
    procesos_pub = privacidad.enmascarar(ctx["procesos"])
    proveedores_pub = privacidad.enmascarar(privacidad.anonimizar_personas(ctx["proveedores"]))
    grupos = {regla: g for regla, g in alertas.groupby("regla")} if not alertas.empty else {}
    r = {**ctx["r"], "mayores": privacidad.enmascarar(privacidad.anonimizar_personas(ctx["r"]["mayores"]))}
    ctx = {
        **ctx,
        "r": r,
        "alertas": alertas,
        "proveedores": proveedores_pub,
        "grupos": grupos,
        "orden_reglas": ORDEN_REGLAS,
        "descripciones": DESCRIPCIONES,
        "conteo_alertas": alertas.groupby("regla")["ocid"].nunique().to_dict() if not alertas.empty else {},
        "limite_filas": 200,
        "umbral_p": 0.05 / max(len(ctx["tasas"]), 1),
        "generado": datetime.now().strftime("%d/%m/%Y %H:%M"),
    }
    saip = ctx.get("saip")
    if saip is not None and not saip.empty:
        cerrados = saip[saip["anio"] < datetime.now().year]
        ctx["saip_destacado"] = (cerrados if not cerrados.empty else saip).iloc[-1]
    ctx["hallazgos"] = hallazgos_principales(ctx)
    env = entorno()
    (destino / "informe.html").write_text(env.get_template("informe.html.j2").render(**ctx), encoding="utf-8")

    procedencia = ctx.get("procedencia") or {"archivos": []}
    (destino / "procedencia.json").write_text(json.dumps(procedencia, ensure_ascii=False, indent=2), encoding="utf-8")
    (destino / "publico.html").write_text(env.get_template("publico.html.j2").render(**_contexto_publico(ctx, procedencia)), encoding="utf-8")

    procesos_pub.to_csv(destino / "procesos.csv", index=False, encoding="utf-8-sig")
    if not alertas.empty:
        alertas.to_csv(destino / "alertas.csv", index=False, encoding="utf-8-sig")
    proveedores_pub.to_csv(destino / "proveedores.csv", index=False, encoding="utf-8-sig")
    if ctx.get("cumplimiento") is not None:
        ctx["cumplimiento"].to_csv(destino / "lotaip_cumplimiento.csv", index=False, encoding="utf-8-sig")
    if ctx.get("datos_completos"):
        # Copia sin enmascarar, solo para uso local (la carpeta privado/ no se sube al repositorio).
        privado = Path("privado") / destino.name
        privado.mkdir(parents=True, exist_ok=True)
        ctx["procesos"].to_csv(privado / "procesos.csv", index=False, encoding="utf-8-sig")
        alertas_completas.to_csv(privado / "alertas.csv", index=False, encoding="utf-8-sig")
        ctx["proveedores"].to_csv(privado / "proveedores.csv", index=False, encoding="utf-8-sig")
    resumen = {
        "entidad": ctx["e"]["nombre"],
        "canton": ctx["e"].get("canton", ""),
        "anios": ctx["anios"],
        "generado": ctx["generado"],
        "procesos": ctx["r"]["procesos"],
        "monto_usd": round(ctx["r"]["monto"], 2),
        "monto_sin_concurso_usd": round(ctx["r"]["directo_monto"], 2),
        "alertas_por_regla": ctx["conteo_alertas"],
        "hallazgos": ctx["hallazgos"],
    }
    (destino / "resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    return destino / "informe.html", ctx["hallazgos"]


def escribir_indice(raiz: Path) -> Path:
    """Genera la portada con una tarjeta por cada cantón auditado en `raiz`."""
    ciudades = []
    for r in sorted(raiz.glob("*/resumen.json")):
        d = json.loads(r.read_text(encoding="utf-8"))
        ciudades.append({
            "carpeta": r.parent.name,
            "canton": d.get("canton") or r.parent.name.capitalize(),
            "monto": d.get("monto_usd", 0),
            "procesos": d.get("procesos", 0),
            "anios": d.get("anios", []),
        })
    ciudades.sort(key=lambda c: -c["monto"])
    ruta = raiz / "index.html"
    ruta.write_text(entorno().get_template("indice.html.j2").render(ciudades=ciudades), encoding="utf-8")
    return ruta
