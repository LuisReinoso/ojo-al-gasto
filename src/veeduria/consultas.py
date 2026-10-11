"""Consultas rápidas para periodistas: la ficha de un proceso y el historial de un proveedor."""

from __future__ import annotations

import re

import pandas as pd

from . import reglas
from .privacidad import enmascarar_ruc


def _usd(v) -> str:
    return "—" if v is None or pd.isna(v) else reglas.usd(v)


def _pct(v: float) -> str:
    return f"{100 * v:.1f} %".replace(".", ",")


def _n(n: int, palabra: str = "proceso") -> str:
    return f"{n} {palabra}{'' if n == 1 else 's'}"


def _fecha(v) -> str:
    return "—" if v is None or pd.isna(v) else pd.Timestamp(v).strftime("%d/%m/%Y")


def buscar_proceso(nacional: pd.DataFrame, codigo: str) -> pd.DataFrame:
    """Busca por código (con o sin el sufijo del SERCOP) o por ocid."""
    c = codigo.strip().upper()
    c = re.sub(r"^OCDS-5WNO2W-", "", c)
    sin_sufijo = re.sub(r"-\d+$", "", c)
    m = nacional["codigo"].str.upper().isin({c, sin_sufijo}) | nacional["ocid"].str.upper().str.endswith(c)
    return nacional[m]


def ficha_proceso(nacional: pd.DataFrame, fila: pd.Series, completo: bool = False) -> str:
    base = reglas.linea_base(nacional)
    ruc = fila.ruc_proveedor if completo else enmascarar_ruc(fila.ruc_proveedor)
    lineas = [
        f"PROCESO {fila.codigo}",
        f"  Entidad:        {fila.buyer_name} (RUC {fila.ruc_entidad})",
        f"  Objeto:         {fila.objeto}",
        f"  Procedimiento:  {fila.tipo}",
        f"  Publicado:      {_fecha(fila.fecha_publicacion)}",
        f"  Presupuesto:    {_usd(fila.presupuesto)}",
        f"  Adjudicado:     {_usd(fila.monto_adjudicado)}",
        f"  Contrato:       {_usd(fila.monto_contrato)}",
        f"  Proveedor:      {fila.proveedor if isinstance(fila.proveedor, str) else '—'} (RUC {ruc if isinstance(ruc, str) and ruc else '—'})",
        f"  Oferentes:      {int(fila.num_oferentes) if pd.notna(fila.num_oferentes) else '—'}",
        f"  Ficha oficial:  {fila.url_sercop}",
    ]
    notas = []
    if fila.tipo in reglas.COMPETITIVOS and fila.num_oferentes == 1:
        tasa = base["tasa_un_oferente"].get(fila.tipo)
        notas.append(f"Tuvo un solo oferente. En el país, el {_pct(tasa)} de los procesos de este tipo tiene un solo oferente.")
    if fila.tipo in reglas.DIRECTOS:
        notas.append("No tuvo concurso de ofertas. Pida la resolución que justifica el procedimiento.")
    if pd.notna(fila.presupuesto) and pd.notna(fila.monto_adjudicado) and fila.presupuesto > 0:
        notas.append(f"Adjudicado por el {_pct(fila.monto_adjudicado / fila.presupuesto)} del presupuesto.")
    if notas:
        lineas += ["", "OBSERVACIONES"] + [f"  - {n}" for n in notas]
    lineas += [
        "",
        "SIGUIENTE PASO",
        "  1. Abra la ficha oficial y descargue los pliegos, el contrato y las actas.",
        f'  2. Pida lo que falte: veeduria solicitud <entidad.toml> --pedido "Contrato, planillas y actas de entrega-recepción del proceso {fila.codigo}" ...',
    ]
    return "\n".join(lineas)


def buscar_proveedor(nacional: pd.DataFrame, texto: str) -> pd.DataFrame:
    """Por RUC exacto o por parte del nombre (sin distinguir mayúsculas)."""
    t = texto.strip()
    if re.fullmatch(r"\d{13}", t):
        return nacional[nacional["ruc_proveedor"].fillna("").str.contains(t, regex=False)]
    return nacional[nacional["proveedor"].fillna("").str.contains(t, case=False, regex=False)]


def resumen_proveedor(d: pd.DataFrame, completo: bool = False, top: int = 10) -> str:
    if d.empty:
        return "No hay procesos adjudicados a ese proveedor en los años descargados."
    nombres = d.groupby(["proveedor", "ruc_proveedor"]).size().sort_values(ascending=False)
    total = d["monto_adjudicado"].sum()
    directos = d[d["tipo"].isin(reglas.DIRECTOS)]
    unicos = d[d["tipo"].isin(reglas.COMPETITIVOS) & (d["num_oferentes"] == 1)]
    lineas = ["PROVEEDOR"]
    for (nombre, ruc), n in nombres.head(5).items():
        lineas.append(f"  {nombre} (RUC {ruc if completo else enmascarar_ruc(ruc)}): {_n(int(n))}")
    if len(nombres) > 5:
        lineas.append(f"  … y {len(nombres) - 5} nombres más. Use el RUC para una búsqueda exacta.")
    lineas += [
        "",
        "RESUMEN",
        f"  Procesos ganados:        {len(d)}",
        f"  Monto adjudicado:        {_usd(total)}",
        f"  Entidades compradoras:   {d['buyer_name'].nunique()}",
        f"  Sin concurso de ofertas: {_n(len(directos))}, {_usd(directos['monto_adjudicado'].sum())}",
        f"  Con un solo oferente:    {_n(len(unicos))}, {_usd(unicos['monto_adjudicado'].sum())}",
        "",
        "POR ENTIDAD",
    ]
    por_ent = d.groupby("buyer_name").agg(procesos=("ocid", "size"), monto=("monto_adjudicado", "sum")).sort_values("monto", ascending=False)
    for nombre, f in por_ent.head(top).iterrows():
        lineas.append(f"  {_usd(f.monto):>18}  {_n(int(f.procesos)):>12}  {nombre}")
    lineas += ["", "PROCESOS MÁS GRANDES"]
    for f in d.nlargest(top, "monto_adjudicado").itertuples():
        lineas.append(f"  {_usd(f.monto_adjudicado):>18}  {_fecha(f.fecha_publicacion)}  {f.codigo}  {str(f.objeto)[:70]}")
    return "\n".join(lineas)


def tabla_proveedor(d: pd.DataFrame, completo: bool = False) -> pd.DataFrame:
    cols = ["fecha_publicacion", "codigo", "buyer_name", "tipo", "objeto", "proveedor", "ruc_proveedor",
            "presupuesto", "monto_adjudicado", "num_oferentes", "url_sercop"]
    out = d[cols].sort_values("fecha_publicacion")
    if not completo:
        out = out.assign(ruc_proveedor=out["ruc_proveedor"].map(enmascarar_ruc))
    return out
