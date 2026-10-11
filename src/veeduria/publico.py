"""Datos de la página pública: un resumen para cualquier persona, al estilo de una nota explicativa.

Habla de instituciones y de dinero público, no de personas: no muestra nombres de
proveedores personas naturales ni RUC. Las preguntas abiertas van dirigidas a la
entidad, que es quien debe responder.
"""

from __future__ import annotations

import re
from datetime import datetime

import pandas as pd

from . import reglas

SIGLAS = {
    "DMQ", "GAD", "GADDMQ", "EPMMOP", "EPMAPS", "EMASEO", "EMGIRS", "EPMSA", "EPMTPQ", "EPMHV", "EPMMQ", "AMT", "AMC",
    "UESERD", "BDE", "CBDMQ", "CDMI", "SIG", "IESS", "ECU", "LED", "PLMQ", "TIC", "EP", "SSU", "SAYN", "EMRAQ",
}
# Palabras tras las que viene un nombre propio (avenida, parroquia, liga…).
_INICIA_NOMBRE = {
    "AV", "AVENIDA", "PARROQUIA", "BARRIO", "SECTOR", "CALLE", "CALLES", "COMUNIDAD", "COMUNIDADES", "ESTADIO", "PARQUE",
    "PLAZA", "CIUDAD", "PROVINCIA", "CANTÓN", "CANTON", "LIGA", "INTERCAMBIADOR", "MIRADOR", "QUEBRADA", "QUEBRADAS", "BARRIOS",
}
# Palabras que cortan un nombre propio.
_CORTA_NOMBRE = {"TRAMO", "PARA", "EN", "CON", "UBICADO", "UBICADA", "DESDE", "HASTA", "Y", "INCLUYE", "FASE", "ENTRE", "HACIA"}
_CONECTORES = {"DE", "DEL", "LA", "LAS", "LOS", "EL"}
SIEMPRE_MAYUSCULA = {"QUITO", "ECUADOR", "PICHINCHA", "METROPOLITANO", "DISTRITO", "METRO"}

CATEGORIAS = {
    "works": "Obras",
    "services": "Servicios",
    "goods": "Bienes",
    "catalogo": "Compras por catálogo electrónico",
}


def pct(v: float, decimales: int = 1) -> str:
    return f"{100 * v:.{decimales}f}\u00a0%".replace(".", ",")


def frase(texto: str, largo: int = 110, propios: set[str] | None = None) -> str:
    """Pasa un objeto contractual en MAYÚSCULAS a minúsculas legibles, respetando siglas y nombres propios."""
    if not isinstance(texto, str) or not texto.strip():
        return ""
    propios = SIEMPRE_MAYUSCULA | {x.upper() for x in (propios or set())}
    t = re.sub(r"\s+", " ", texto.strip().strip("“”\"'"))
    salida = []
    en_nombre = False
    for i, p in enumerate(t.split(" ")):
        limpio = re.sub(r"[^\wÁÉÍÓÚÑÜ]", "", p.upper())
        capital = p[:1].upper() + p[1:].lower()
        if limpio in SIGLAS or re.search(r"\d", p) or len(limpio) == 1 and limpio not in ("Y", "O", "A", "E", "U"):
            salida.append(p.upper())
        elif limpio == "AV":
            salida.append("Av.")
        elif i == 0 or limpio in propios or (en_nombre and limpio not in _CONECTORES and limpio not in _CORTA_NOMBRE):
            salida.append(capital)
        else:
            salida.append(p.lower())
        if limpio in _INICIA_NOMBRE:
            en_nombre = True
        elif limpio in _CORTA_NOMBRE or re.search(r"[,():;\-]$", p) or p in ("-", "–"):
            en_nombre = False
    t = " ".join(salida)
    return t if len(t) <= largo else t[: largo - 1].rsplit(" ", 1)[0] + "…"


def nombre_corto(nombre: str) -> str:
    return nombre.split(" (")[0]


def categoria_publica(df: pd.DataFrame) -> pd.Series:
    return df["es_catalogo"].map({True: "catalogo"}).fillna(df["categoria"]).map(CATEGORIAS).fillna("Otros")


def anio_en_curso(anios: list[int]) -> int | None:
    hoy = datetime.now().year
    return hoy if hoy in anios else None


def resumen_anual(procesos: pd.DataFrame, anio: int, nombres: dict[str, str], top: int = 5, propios: set[str] | None = None) -> dict:
    d = procesos[procesos["anio"] == anio].copy()
    d["entidad_corta"] = d["ruc_entidad"].map(nombres).map(nombre_corto).fillna(d["buyer_name"])
    d["categoria_publica"] = categoria_publica(d)
    total = float(d["monto"].sum())

    mayores = d.nlargest(top, "monto")
    por_categoria = d.groupby("categoria_publica")["monto"].sum().sort_values(ascending=False)
    por_entidad = d.groupby("entidad_corta")["monto"].sum().sort_values(ascending=False)
    if len(por_entidad) > 6:
        por_entidad = pd.concat([por_entidad.head(6), pd.Series({"Otras entidades": por_entidad.iloc[6:].sum()})])
    return {
        "anio": anio,
        "procesos": len(d),
        "monto": total,
        "mayores": [
            {
                "objeto": frase(r.objeto, propios=propios),
                "entidad": r.entidad_corta,
                "monto": float(r.monto),
                "tipo": r.tipo,
                "codigo": r.codigo,
                "url": r.url_sercop,
            }
            for r in mayores.itertuples()
        ],
        "por_categoria": [(k, float(v), v / total if total else 0) for k, v in por_categoria.items() if v > 0],
        "por_entidad": [(k, float(v), v / total if total else 0) for k, v in por_entidad.items()],
        "sin_concurso": float(d.loc[d["tipo"].isin(reglas.DIRECTOS), "monto"].sum()),
    }


def preguntas_abiertas(ctx: dict, nombres: dict[str, str], propios: set[str] | None = None) -> list[dict]:
    """Preguntas a las instituciones, sin nombres de personas. Ordenadas por importancia."""
    p: list[dict] = []
    alertas: pd.DataFrame = ctx["alertas"]
    procesos: pd.DataFrame = ctx["procesos"]
    if not alertas.empty:
        frac = alertas[(alertas["regla"] == "Posible fraccionamiento") & (alertas["nivel"] == "alta")]
        ent = procesos.set_index("ocid")["ruc_entidad"]
        for _, g in frac.groupby("grupo"):
            entidad = nombre_corto(nombres.get(ent.get(g["ocid"].iloc[0]), g["buyer_name"].iloc[0]))
            limite = re.search(r"límite de (.+?) \(", g["explicacion"].iloc[0])
            p.append({
                "tema": "Contratación",
                "titulo": f"{entidad}: ¿por qué se contrataron por separado {len(g)} procesos parecidos con el mismo proveedor?",
                "texto": (
                    f"Suman {reglas.usd(g['monto'].sum())} en pocas semanas"
                    + (f"; cada uno quedó bajo el límite de {limite.group(1)}" if limite else "")
                    + (". Juntos superan el monto desde el que el Reglamento exige comisión técnica." if limite and "comisión técnica" in limite.group(1)
                       else ". Juntos habrían requerido un procedimiento más exigente.")
                    + " Puede haber una explicación válida."
                ),
                "procesos": [(r.codigo, r.url_sercop, frase(r.objeto, 80, propios), float(r.monto)) for r in g.itertuples()],
                "pedido": (
                    f"Copia de los informes de necesidad, estudios de mercado, pliegos, contratos y actas de entrega-recepción de los procesos "
                    f"{', '.join(g['codigo'])}, y la justificación técnica y legal para contratarlos por separado y no en un solo procedimiento."
                ),
            })
    ppto = ctx.get("ppto")
    if ppto:
        g = ppto["por_grupo"]
        obra = g[g.index.str.match(r"^75\b")]
        esperado = ppto["mes"] / 12
        if not obra.empty and obra["ejecucion"].iloc[0] < 0.5 * esperado:
            o = obra.iloc[0]
            p.append({
                "tema": "Presupuesto",
                "titulo": "¿Qué pasa con la obra pública?",
                "pedido": (
                    f"Listado de las obras financiadas con el grupo de gasto 75 (obras públicas) en {ppto['anio']}, con el monto codificado, "
                    "el monto devengado, el porcentaje de avance físico y la fecha prevista de terminación de cada una, y las causas de los retrasos."
                ),
                "texto": (
                    f"A {MESES[ppto['mes'] - 1]} de {ppto['anio']} se había ejecutado el {pct(o.ejecucion)} del presupuesto de obras públicas "
                    f"({reglas.usd(o.devengado)} de {reglas.usd(o.codificado)}). Un ritmo parejo daría cerca del {pct(esperado, 0)}."
                ),
                "procesos": [],
            })
    s = ctx.get("saip_destacado")
    if s is not None and s.recibidas and s.sin_responder and s.recibidas >= 10:
        p.append({
            "tema": "Transparencia",
            "titulo": "¿Por qué quedaron solicitudes de información sin respuesta?",
            "pedido": (
                f"Listado de las solicitudes de acceso a la información pública recibidas en {int(s.anio)} que no fueron respondidas, "
                "con su fecha de ingreso, el tema solicitado y el motivo de la falta de respuesta."
            ),
            "texto": f"Según el Portal Nacional de Transparencia, en {int(s.anio)} constan {int(s.sin_responder)} de {int(s.recibidas)} solicitudes "
                     "de acceso a la información sin respuesta. Para la ley, no responder es negar la información.",
            "procesos": [],
        })
    cal = ctx.get("calidad") or {}
    ilegibles = sum(c["ruc_ilegibles"] for c in cal.values())
    if ilegibles:
        p.append({
            "tema": "Datos abiertos",
            "titulo": "¿Por qué no se puede saber a quién se contrató?",
            "pedido": (
                "El conjunto de datos del numeral 8 del artículo 19 de la LOTAIP (procesos de contratación) del último mes publicado, "
                "con el RUC completo de cada contratista en formato de texto, en un archivo CSV."
            ),
            "texto": f"En los archivos de transparencia de la entidad, {ilegibles} números de RUC de contratistas están dañados "
                     "(una hoja de cálculo los convirtió a notación científica). La ley exige datos abiertos reutilizables.",
            "procesos": [],
        })
    return p


MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre")
