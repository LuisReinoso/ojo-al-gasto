"""Reglas de alerta sobre la contratación pública.

Cada regla devuelve alertas, NO acusaciones: señala un patrón que la ley o la
buena práctica piden revisar. Siempre que es posible se compara con la línea
base nacional (todas las entidades del país en el mismo periodo y tipo de
procedimiento), para no confundir lo normal con lo sospechoso.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from itertools import combinations
from math import exp, lgamma, log

import pandas as pd

# Tipos de procedimiento en los que la ley espera competencia entre oferentes.
COMPETITIVOS = (
    "Subasta Inversa Electrónica",
    "Licitación",
    "Cotización",
    "Menor Cuantía",
    "Concurso publico",
    "Lista corta",
    "Licitación de Seguros",
    "Comunicación Social – Proceso de Selección",
)

# Procedimientos sin concurso de ofertas (contratación directa o régimen especial).
DIRECTOS = (
    "Contratacion directa",
    "Bienes y Servicios únicos",
    "Contratos entre Entidades Públicas o sus subsidiarias",
    "Comunicación Social – Contratación Directa",
    "Obra artística, científica o literaria",
    "Repuestos o Accesorios",
    "Asesoría y Patrocinio Jurídico",
    "Asesoría y Patrocinio Jurídico – Cons. puntuales y específicas",
    "Contratación Directa por Terminación Unilateral",
    "Transporte de correo interno o internacional",
    "Contrataciones con empresas públicas internacionales",
)


@dataclass(frozen=True)
class Regimen:
    """Límites de procedimiento vigentes entre dos fechas de publicación (LOSNCP y su Reglamento)."""

    nombre: str
    desde: pd.Timestamp
    hasta: pd.Timestamp
    base_legal: str
    bienes_servicios: tuple[tuple[str, float], ...]
    obras: tuple[tuple[str, float], ...]
    # Procedimientos a los que se aplican estos límites; vacío = todos los no directos.
    procedimientos: tuple[str, ...] = ()

    def limites(self, categoria: str) -> tuple[tuple[str, float], ...]:
        return self.obras if categoria == "works" else self.bienes_servicios

    @classmethod
    def desde_config(cls, c: dict) -> "Regimen":
        return cls(
            nombre=c["nombre"],
            desde=pd.Timestamp(c["desde"]),
            hasta=pd.Timestamp(c["hasta"]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1),
            base_legal=c["base_legal"],
            bienes_servicios=tuple((n, float(v)) for n, v in c["bienes_servicios"]),
            obras=tuple((n, float(v)) for n, v in c["obras"]),
            procedimientos=tuple(c.get("procedimientos", ())),
        )


def asignar_regimen(df: pd.DataFrame, regimenes: list[Regimen]) -> pd.Series:
    """Índice del régimen vigente en la fecha de publicación de cada proceso (-1 si ninguno)."""
    idx = pd.Series(-1, index=df.index)
    for i, r in enumerate(regimenes):
        idx[df["fecha_publicacion"].between(r.desde, r.hasta)] = i
    return idx


def usd(v: float) -> str:
    """Monto en formato local: USD 1.234.567."""
    return "USD " + f"{v:,.0f}".replace(",", ".")


def tipo_base(tipo_proceso: pd.Series) -> pd.Series:
    """'Catálogo electrónico - Mejor oferta en el convenio X...' -> 'Catálogo electrónico - Mejor oferta'."""
    return tipo_proceso.fillna("").str.split(" en el convenio").str[0].str.strip()


def preparar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["tipo"] = tipo_base(df["tipo_proceso"])
    df["anio"] = df["fecha_publicacion"].dt.year
    df["dias_ofertas"] = (df["fin_ofertas"] - df["inicio_ofertas"]).dt.total_seconds() / 86400
    df["es_catalogo"] = df["tipo"].str.startswith("Catálogo electrónico")
    return df


def _alerta(filas: pd.DataFrame, regla: str, nivel: str, explicacion, base_legal: str) -> pd.DataFrame:
    if filas.empty:
        return pd.DataFrame()
    out = filas[["ocid", "codigo", "buyer_name", "tipo", "objeto", "proveedor", "ruc_proveedor", "monto", "monto_adjudicado", "fecha_publicacion", "url_sercop"]].copy()
    out.insert(0, "regla", regla)
    out.insert(1, "nivel", nivel)
    out["explicacion"] = [explicacion(r) for r in filas.itertuples()] if callable(explicacion) else explicacion
    out["base_legal"] = base_legal
    return out


def linea_base(nacional: pd.DataFrame) -> pd.DataFrame:
    """Tasas nacionales por tipo de procedimiento, usadas como comparación."""
    comp = nacional[nacional["tipo"].isin(COMPETITIVOS) & nacional["num_oferentes"].notna()]
    g = comp.groupby("tipo").agg(
        procesos=("ocid", "size"),
        tasa_un_oferente=("num_oferentes", lambda s: (s == 1).mean()),
        mediana_oferentes=("num_oferentes", "median"),
        p05_dias_ofertas=("dias_ofertas", lambda s: s.quantile(0.05)),
    )
    con_presupuesto = comp[comp["presupuesto"].gt(0) & comp["monto_adjudicado"].gt(0) & _precio_libre(comp)]
    sin_ahorro = (con_presupuesto["monto_adjudicado"] / con_presupuesto["presupuesto"] >= 0.995).groupby(con_presupuesto["tipo"]).mean()
    g["tasa_sin_ahorro"] = sin_ahorro
    return g


def un_solo_oferente(df: pd.DataFrame, base: pd.DataFrame) -> pd.DataFrame:
    filas = df[df["tipo"].isin(COMPETITIVOS) & (df["num_oferentes"] == 1)]

    def texto(r):
        nac = base["tasa_un_oferente"].get(r.tipo)
        ref = f" A nivel nacional el {nac:.0%} de los procesos de este tipo tuvo un solo oferente." if pd.notna(nac) else ""
        return f"Procedimiento competitivo con un único oferente: no hubo competencia de precios.{ref}"

    return _alerta(
        filas, "Un solo oferente", "media", texto,
        "No es ilegal, pero reduce la garantía de mejor precio. LOSNCP art. 47 (subasta con un solo oferente pasa a negociación); RGLOSNCP art. 426.1 (criterios de riesgo del SERCOP).",
    )


def _precio_libre(df: pd.DataFrame) -> pd.Series:
    """Procesos en los que el oferente fija el precio. En menor cuantía de obras (régimen anterior)
    el precio era el presupuesto y se adjudicaba por sorteo: en los datos, el 100 % se adjudica al máximo."""
    return ~((df["tipo"] == "Menor Cuantía") & (df["categoria"] == "works"))


def sin_ahorro(df: pd.DataFrame, base: pd.DataFrame) -> pd.DataFrame:
    d = df[df["tipo"].isin(COMPETITIVOS) & df["presupuesto"].gt(0) & df["monto_adjudicado"].gt(0) & _precio_libre(df)]
    filas = d[d["monto_adjudicado"] / d["presupuesto"] >= 0.995]

    def texto(r):
        nac = base["tasa_sin_ahorro"].get(r.tipo)
        ref = f" Nacionalmente ocurre en el {nac:.0%} de este tipo de procesos." if pd.notna(nac) else ""
        return f"Se adjudicó por el {r.monto_adjudicado / r.monto:.1%} del presupuesto referencial: la competencia no bajó el precio.{ref}"

    return _alerta(filas, "Adjudicado al precio máximo", "baja", texto, "LOSNCP art. 21 y RGLOSNCP art. 426.1 (precios inusuales como criterio de alerta).")


def contratacion_directa(df: pd.DataFrame, monto_minimo: float = 50_000) -> pd.DataFrame:
    filas = df[df["tipo"].isin(DIRECTOS) & df["monto"].ge(monto_minimo)]
    return _alerta(
        filas, "Contratación sin concurso", "media",
        lambda r: f"Proceso por '{r.tipo}' por {usd(r.monto)}: no hubo concurso de ofertas. Revise la resolución que justifica el régimen especial o la contratación directa.",
        "LOSNCP art. 38 (régimen especial, lista taxativa) y Reglamento; la entidad debe motivar la causal.",
    )


def plazo_corto(df: pd.DataFrame, base: pd.DataFrame) -> pd.DataFrame:
    d = df[df["tipo"].isin(COMPETITIVOS) & df["dias_ofertas"].notna()].copy()
    d["p05"] = d["tipo"].map(base["p05_dias_ofertas"])
    filas = d[d["dias_ofertas"] < d["p05"]]
    return _alerta(
        filas, "Plazo de ofertas muy corto", "baja",
        lambda r: f"Hubo {r.dias_ofertas:.1f} días para presentar ofertas; el 95% de los procesos de este tipo en el país dio más tiempo. Plazos cortos limitan la participación.",
        "Comparación estadística, no un plazo legal. RGLOSNCP art. 426.1 (patrones de riesgo).",
    )


def _ventanas_que_superan(g: pd.DataFrame, limite: float, ventana_dias: int) -> pd.DataFrame | None:
    """Une todos los procesos que forman parte de alguna ventana de `ventana_dias` días con
    dos o más procesos cuya suma supera `limite`. `g` debe venir ordenado por fecha."""
    if len(g) < 2:
        return None
    fechas = g["fecha_publicacion"].tolist()
    montos = g["monto"].tolist()
    marcados: set[int] = set()
    for i in range(len(g)):
        j = i
        suma = 0.0
        while j < len(g) and (fechas[j] - fechas[i]).days <= ventana_dias:
            suma += montos[j]
            j += 1
        if j - i >= 2 and suma > limite:
            marcados.update(range(i, j))
    return g.iloc[sorted(marcados)] if marcados else None


_VACIAS = set(
    "DE LA LAS LOS EL DEL Y PARA EN POR CON A AL O U E SU SUS QUE SE UN UNA DMQ QUITO DISTRITO METROPOLITANO GAD EP EMPRESA PUBLICA "
    "ADQUISICION CONTRATACION SERVICIO SERVICIOS INCLUYE VARIOS 2024 2025 2026".split()
)


def _palabras(texto) -> set[str]:
    t = unicodedata.normalize("NFKD", str(texto).upper())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return {w for w in re.findall(r"[A-Z]{3,}", t) if w not in _VACIAS}


def similitud_objetos(objetos: list[str]) -> float:
    """Mayor similitud (Jaccard de palabras significativas) entre pares de objetos contractuales."""
    conjuntos = [_palabras(o) for o in objetos]
    mejor = 0.0
    for a, b in combinations(conjuntos, 2):
        if a and b:
            mejor = max(mejor, len(a & b) / len(a | b))
    return mejor


def posible_fraccionamiento(df: pd.DataFrame, regimenes: list[Regimen], ventana_dias: int = 90, similitud_alta: float = 0.2) -> pd.DataFrame:
    """Procesos de la misma entidad con el mismo proveedor que, cada uno por debajo de un límite,
    juntos lo superan dentro de una ventana corta. Es el patrón típico de subdivisión de contratos."""
    d = df[~df["es_catalogo"] & df["monto"].gt(0) & df["ruc_proveedor"].fillna("").ne("") & ~df["tipo"].isin(DIRECTOS)].copy()
    d["regimen"] = asignar_regimen(d, regimenes)
    d["clase"] = d["categoria"].eq("works").map({True: "works", False: "otros"})
    d = d[d["regimen"] >= 0].sort_values("fecha_publicacion")
    grupos = []
    for (_, _, clase, reg), g in d.groupby(["ruc_entidad", "ruc_proveedor", "clase", "regimen"]):
        if len(g) < 2:
            continue
        regimen = regimenes[int(reg)]
        if regimen.procedimientos:
            g = g[g["tipo"].isin(regimen.procedimientos)]
        # Se prueba primero el límite más bajo: es el que se eludiría con menos esfuerzo.
        for nombre, limite in regimen.limites(clase):
            marcados = _ventanas_que_superan(g[g["monto"] < limite], limite, ventana_dias)
            if marcados is not None:
                grupos.append((nombre, limite, regimen, marcados))
                break
    if not grupos:
        return pd.DataFrame()
    partes = []
    for nombre, limite, regimen, v in grupos:
        sim = similitud_objetos(v["objeto"].tolist())
        parecido = sim >= similitud_alta
        efecto = (
            "Juntos superan el monto desde el que el Reglamento exige comisión técnica."
            if "comisión técnica" in nombre
            else "Juntos habrían requerido un procedimiento más exigente."
        )
        a = _alerta(
            v, "Posible fraccionamiento" if parecido else "Mismo proveedor, suma sobre un límite", "alta" if parecido else "baja",
            f"{len(v)} procesos al mismo proveedor en menos de {ventana_dias} días, cada uno bajo el límite de {nombre} "
            f"({usd(limite)}), que suman {usd(v['monto'].sum())}. {efecto} "
            + ("Los objetos se parecen: pregunte por qué se contrataron por separado." if parecido
               else "Los objetos parecen distintos; probablemente es coincidencia."),
            regimen.base_legal,
        )
        a["similitud_objetos"] = round(sim, 2)
        a["grupo"] = v["ocid"].iloc[0]
        partes.append(a)
    return pd.concat(partes, ignore_index=True)


def junto_al_limite(df: pd.DataFrame, regimenes: list[Regimen], margen: float = 0.02) -> pd.DataFrame:
    """Presupuestos fijados justo debajo del límite de un procedimiento más exigente."""
    d = df[~df["es_catalogo"] & df["presupuesto"].gt(0)].copy()
    d["regimen"] = asignar_regimen(d, regimenes)
    d = d[d["regimen"] >= 0]
    marcas = {}
    for r in d.itertuples():
        regimen = regimenes[int(r.regimen)]
        if regimen.procedimientos and r.tipo not in regimen.procedimientos:
            continue
        for nombre, limite in regimen.limites(r.categoria):
            if limite * (1 - margen) <= r.presupuesto < limite:
                marcas[r.Index] = (nombre, limite, regimen.base_legal)
    if not marcas:
        return pd.DataFrame()
    filas = d.loc[list(marcas)]
    out = _alerta(
        filas, "Presupuesto al borde del límite", "baja",
        lambda r: f"Presupuesto de {usd(r.monto)}, a menos del {margen:.0%} del límite de {marcas[r.Index][0]} ({usd(marcas[r.Index][1])}). "
        "Pasar el límite obligaría a un procedimiento con más controles.",
        "",
    )
    out["base_legal"] = [marcas[i][2] for i in filas.index]
    return out


def proveedor_unico_no_permitido(df: pd.DataFrame, desde: pd.Timestamp) -> pd.DataFrame:
    """Régimen de proveedor único usado para servicios u obras, que el Reglamento vigente excluye."""
    filas = df[(df["tipo"] == "Bienes y Servicios únicos") & df["categoria"].isin(["services", "works"]) & (df["fecha_publicacion"] >= desde)]
    return _alerta(
        filas, "Proveedor único para servicios u obras", "media",
        lambda r: f"Contratado por el régimen de bienes y servicios únicos, clasificado por el SERCOP como {'obra' if r.categoria == 'works' else 'servicio'}. "
        "Si esta categoría del SERCOP corresponde al art. 139 del Reglamento, ese artículo no permite el proveedor único para servicios, obras ni consultorías. "
        "Pida el informe técnico motivado: puede ser un repuesto o la mejora de una tecnología mal clasificados.",
        "RGLOSNCP (DE 193, 2025) art. 139: proveedor único solo para repuestos, mejora de tecnologías existentes o patentes; no aplica a servicios, obras o consultorías.",
    )


def bajo_umbral_infima(df: pd.DataFrame, umbral: float, desde: pd.Timestamp) -> pd.DataFrame:
    """Subasta, licitación o concurso con presupuesto que no supera el umbral de ínfima cuantía."""
    filas = df[df["tipo"].isin(["Subasta Inversa Electrónica", "Licitación", "Concurso publico"]) & df["presupuesto"].le(umbral)
               & df["presupuesto"].gt(0) & (df["fecha_publicacion"] >= desde)]
    return _alerta(
        filas, "Procedimiento bajo el umbral legal", "baja",
        lambda r: f"{r.tipo} con presupuesto de {usd(r.monto)}: la ley reserva este procedimiento para montos mayores a {usd(umbral)}.",
        "LOSNCP reformada (2025) arts. 42, 47, 48 y 50.",
    )


def concentracion(df: pd.DataFrame, top: int = 15) -> pd.DataFrame:
    """Proveedores que concentran el dinero adjudicado (sin catálogo electrónico)."""
    d = df[~df["es_catalogo"] & df["monto_adjudicado"].gt(0) & df["proveedor"].notna()]
    total = d["monto_adjudicado"].sum()
    g = d.groupby(["ruc_proveedor", "proveedor"]).agg(
        procesos=("ocid", "size"),
        monto=("monto_adjudicado", "sum"),
        entidades=("buyer_name", "nunique"),
        directos=("tipo", lambda s: s.isin(DIRECTOS).sum()),
        un_oferente=("num_oferentes", lambda s: (s == 1).sum()),
    ).reset_index()
    g["participacion"] = g["monto"] / total if total else 0
    return g.sort_values("monto", ascending=False).head(top)


def resumen(df: pd.DataFrame, nombres: dict[str, str] | None = None) -> dict:
    """Cifras generales. `nombres` (RUC -> nombre) unifica entidades que el SERCOP escribe de varias formas."""
    d = df.copy()
    if nombres:
        d["buyer_name"] = d["ruc_entidad"].map(nombres).fillna(d["buyer_name"])
    por_tipo = d.groupby("tipo").agg(procesos=("ocid", "size"), monto=("monto", "sum")).sort_values("monto", ascending=False)
    por_entidad = d.groupby("buyer_name").agg(procesos=("ocid", "size"), monto=("monto", "sum")).sort_values("monto", ascending=False)
    por_categoria = d.groupby("categoria").agg(procesos=("ocid", "size"), monto=("monto", "sum"))
    return {
        "procesos": len(d),
        "monto": float(d["monto"].sum()),
        "adjudicado": float(d["monto_adjudicado"].sum()),
        "por_tipo": por_tipo,
        "por_entidad": por_entidad,
        "por_categoria": por_categoria,
        "mayores": d.nlargest(10, "monto"),
        "directo_monto": float(d.loc[d["tipo"].isin(DIRECTOS), "monto"].sum()),
        "catalogo_monto": float(d.loc[d["es_catalogo"], "monto"].sum()),
    }


def cola_binomial(k: int, n: int, p: float) -> float:
    """Probabilidad de ver k o más casos en n procesos si la tasa real fuera p (la nacional)."""
    if n <= 0 or pd.isna(p):
        return float("nan")
    if k <= 0:
        return 1.0
    if p <= 0:
        return 0.0
    if p >= 1:
        return 1.0
    # En escala logarítmica para que no desborde con n grandes.
    def log_pmf(i: int) -> float:
        return lgamma(n + 1) - lgamma(i + 1) - lgamma(n - i + 1) + i * log(p) + (n - i) * log(1 - p)

    return float(min(1.0, sum(exp(log_pmf(i)) for i in range(k, n + 1))))


def tasas_comparadas(df: pd.DataFrame, base: pd.DataFrame) -> pd.DataFrame:
    """Tasa de oferente único de la entidad frente a la nacional, por tipo de procedimiento."""
    comp = df[df["tipo"].isin(COMPETITIVOS) & df["num_oferentes"].notna()]
    g = comp.groupby("tipo").agg(procesos=("ocid", "size"), un_oferente=("num_oferentes", lambda s: int((s == 1).sum())))
    g["tasa_entidad"] = g["un_oferente"] / g["procesos"]
    g["tasa_nacional"] = base["tasa_un_oferente"].reindex(g.index)
    g["esperados"] = g["procesos"] * g["tasa_nacional"]
    g["p_valor"] = [cola_binomial(int(k), int(n), p) for k, n, p in zip(g["un_oferente"], g["procesos"], g["tasa_nacional"])]
    return g.sort_values("procesos", ascending=False)


def todas(df: pd.DataFrame, nacional: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    c = cfg["contratacion"]
    regimenes = [Regimen.desde_config(r) for r in c["regimenes"]]
    base = linea_base(nacional)
    partes = [
        posible_fraccionamiento(df, regimenes),
        un_solo_oferente(df, base),
        proveedor_unico_no_permitido(df, pd.Timestamp(c["proveedor_unico_desde"])),
        contratacion_directa(df),
        junto_al_limite(df, regimenes),
        plazo_corto(df, base),
        sin_ahorro(df, base),
        bajo_umbral_infima(df, c["umbral_infima"], pd.Timestamp(c["umbral_infima_desde"])),
    ]
    partes = [p for p in partes if not p.empty]
    alertas = pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()
    return alertas, base
