"""Línea de comandos de veeduria-ec.

    veeduria auditar entidades/quito.toml --anios 2025 2026
    veeduria entidades "ibarra"
    veeduria solicitud entidades/quito.toml --pedido "..." --nombre "..." --cedula "..." --correo "..."
    veeduria plazo 2026-10-12
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from datetime import date, datetime
from importlib import resources
from pathlib import Path

from . import consultas, informe, lotaip, procedencia, reglas, solicitud
from .fuentes import sercop, transparencia


def cargar_entidad(ruta: Path) -> dict:
    with open(ruta, "rb") as f:
        e = tomllib.load(f)
    if not e.get("rucs"):
        sys.exit(f"{ruta}: falta la lista [[rucs]] de entidades.")
    return e


def cargar_configuracion() -> dict:
    with resources.files("veeduria").joinpath("datos/normas.toml").open("rb") as f:
        return tomllib.load(f)


def cmd_auditar(a: argparse.Namespace) -> None:
    e = cargar_entidad(a.entidad)
    cfg = cargar_configuracion()
    anios = a.anios or [datetime.now().year - 1, datetime.now().year]
    cache = a.datos
    destino = a.salida or Path("informes") / a.entidad.stem
    rucs = [r["ruc"] for r in e["rucs"]]

    print(f"1/4 Descargando compras públicas del SERCOP ({', '.join(map(str, anios))})…")
    nacional = sercop.cargar(anios, cache, refrescar=a.refrescar)
    nacional = reglas.preparar(nacional)
    nacional = nacional[nacional["anio"].isin(anios)]
    procesos = nacional[nacional["ruc_entidad"].isin(rucs)].copy()
    print(f"    {len(procesos):,} procesos de {e['nombre']} (de {len(nacional):,} en el país)")

    print("2/4 Aplicando reglas de alerta…")
    alertas, base = reglas.todas(procesos, nacional, cfg)
    ctx = {
        "e": e,
        "anios": anios,
        "procesos": procesos,
        "alertas": alertas,
        "r": reglas.resumen(procesos, {x["ruc"]: x["nombre"] for x in e["rucs"]}),
        "tasas": reglas.tasas_comparadas(procesos, base),
        "proveedores": reglas.concentracion(procesos),
        "regimenes": [reglas.Regimen.desde_config(r) for r in cfg["contratacion"]["regimenes"]],
        "base_procesos": len(nacional),
        "dia_limite": cfg["lotaip"]["dia_limite_publicacion"],
        "cumplimiento": None, "saip": None, "ppto": None, "contraloria": None, "calidad": None, "cruce": None,
        "archivo_entidad": a.entidad.name,
        "cfg": cfg,
        "datos_completos": a.datos_completos,
    }

    id_pnt = e.get("id_transparencia")
    if id_pnt and not a.sin_transparencia:
        print("3/4 Revisando transparencia (Portal Nacional de Transparencia)…")
        try:
            ctx["cumplimiento"] = lotaip.cumplimiento_mensual(id_pnt, anios, cache, cfg["lotaip"]["dia_limite_publicacion"])
            ctx["saip"] = lotaip.solicitudes(id_pnt, anios, cache)
            ctx["ppto"] = lotaip.presupuesto(id_pnt, cache)
            ctx["contraloria"] = lotaip.auditorias_contraloria(id_pnt, cache)
            ctx["calidad"] = lotaip.calidad_contratacion(id_pnt, cache)
            if ctx["calidad"] and "Numeral 8" in ctx["calidad"]:
                ctx["cruce"] = lotaip.cruce_lotaip_sercop(ctx["calidad"]["Numeral 8"]["datos"], procesos, anios)
        except Exception as exc:  # el portal se cae con frecuencia; el informe de compras sigue siendo útil
            print(f"    Aviso: el Portal de Transparencia falló ({exc}). Se genera el informe sin esa sección.")
    else:
        print("3/4 Transparencia: omitido (sin id_transparencia en el archivo de la entidad).")

    print("4/4 Escribiendo informe…")
    ctx["procedencia"] = procedencia.registrar(cache, anios, id_pnt if not a.sin_transparencia else None)
    ruta, hallazgos = informe.escribir(destino, ctx)
    informe.escribir_indice(destino.parent)
    print(f"\nListo: {ruta.resolve()}")
    print(f"Página pública: {(ruta.parent / 'publico.html').resolve()}")
    if a.datos_completos:
        print(f"Copia sin enmascarar (no publicar): {(Path('privado') / destino.name).resolve()}")
    for h in hallazgos:
        print("  •", h.replace("<b>", "").replace("</b>", ""))


def cmd_entidades(a: argparse.Namespace) -> None:
    print("Portal Nacional de Transparencia:")
    try:
        for x in transparencia.buscar_entidades(a.texto):
            print(f"  id_transparencia = {x['id']:<6} RUC {x['ruc']}  {x['nombre']}  [{x['canton']}]")
    except Exception as exc:
        print(f"  (no disponible: {exc})")
    zips = sorted((a.datos / "sercop").glob("ocds_*.zip"))
    if not zips:
        print("\nSERCOP: aún no hay datos descargados. Ejecute primero 'veeduria descargar'.")
        return
    print(f"\nCompradores en datos del SERCOP ({zips[0].stem[5:]} a {zips[-1].stem[5:]}):")
    vistos: dict[str, tuple[str, int]] = {}
    for z in zips:
        t = sercop._leer_zip(z)["releases"]
        m = t[t["buyer_name"].str.contains(a.texto, case=False, na=False)]
        for ruc, g in m.groupby(m["buyer_id"].str.extract(r"(\d{13})", expand=False)):
            nombre, n = vistos.get(ruc, (g["buyer_name"].iloc[0], 0))
            vistos[ruc] = (nombre, n + g["ocid"].nunique())
    for ruc, (nombre, n) in sorted(vistos.items(), key=lambda kv: -kv[1][1]):
        print(f'[[rucs]]\nruc = "{ruc}"\nnombre = "{nombre}"  # {n} procesos\n')


def _nacional(a: argparse.Namespace):
    anios = a.anios or [datetime.now().year - 1, datetime.now().year]
    return reglas.preparar(sercop.cargar(anios, a.datos, avisar=lambda _m: None))


def cmd_proceso(a: argparse.Namespace) -> None:
    nacional = _nacional(a)
    encontrados = consultas.buscar_proceso(nacional, a.codigo)
    if encontrados.empty:
        sys.exit(f"No se encontró el proceso {a.codigo} en los años descargados. Pruebe con --anios.")
    for _, fila in encontrados.iterrows():
        print(consultas.ficha_proceso(nacional, fila, completo=a.completo))
        print()


def cmd_proveedor(a: argparse.Namespace) -> None:
    d = consultas.buscar_proveedor(_nacional(a), a.texto)
    print(consultas.resumen_proveedor(d, completo=a.completo))
    if a.csv and not d.empty:
        consultas.tabla_proveedor(d, completo=a.completo).to_csv(a.csv, index=False, encoding="utf-8-sig")
        print(f"\nTabla completa: {a.csv.resolve()}")


def cmd_descargar(a: argparse.Namespace) -> None:
    anios = a.anios or [datetime.now().year - 1, datetime.now().year]
    df = sercop.cargar(anios, a.datos, refrescar=a.refrescar)
    print(f"{len(df):,} procesos en caché en {a.datos.resolve()}")


def cmd_solicitud(a: argparse.Namespace) -> None:
    e = cargar_entidad(a.entidad)
    cfg = cargar_configuracion()
    autoridad = None
    if e.get("id_transparencia"):
        try:
            autoridad = transparencia.entidad(e["id_transparencia"])
        except Exception:
            autoridad = None
    rutas = solicitud.generar(
        entidad=e,
        autoridad=autoridad,
        pedido=a.pedido,
        nombre=a.nombre,
        cedula=a.cedula,
        correo=a.correo,
        telefono=a.telefono,
        formato=a.formato,
        cfg=cfg,
        destino=a.salida,
        fecha=a.fecha or date.today(),
    )
    for r in rutas:
        print(f"Generado: {r.resolve()}")


def cmd_plazo(a: argparse.Namespace) -> None:
    cfg = cargar_configuracion()
    locales = cargar_entidad(a.entidad).get("feriados_locales") if a.entidad else None
    p = solicitud.calcular_plazos(a.fecha, cfg, locales)
    print(solicitud.texto_plazos(p, cfg))


def _fecha(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="veeduria", description="Veeduría ciudadana automatizada de GADs del Ecuador.")
    ap.add_argument("--datos", type=Path, default=Path("datos"), help="carpeta de caché de descargas (por defecto ./datos)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("auditar", help="genera el informe de auditoría de una entidad")
    p.add_argument("entidad", type=Path, help="archivo .toml de la entidad (ver entidades/quito.toml)")
    p.add_argument("--anios", type=int, nargs="+", help="años a auditar (por defecto el anterior y el actual)")
    p.add_argument("--salida", type=Path, help="carpeta del informe (por defecto informes/<entidad>)")
    p.add_argument("--refrescar", action="store_true", help="vuelve a descargar los meses del año en curso")
    p.add_argument("--sin-transparencia", action="store_true", help="no consulta el Portal Nacional de Transparencia")
    p.add_argument("--datos-completos", action="store_true",
                   help="guarda además en ./privado una copia sin enmascarar los RUC de personas naturales (no la publique)")
    p.set_defaults(func=cmd_auditar)

    p = sub.add_parser("entidades", help="busca RUC e id de transparencia para armar el archivo de una entidad")
    p.add_argument("texto")
    p.set_defaults(func=cmd_entidades)

    p = sub.add_parser("proceso", help="ficha de un proceso de contratación (por código)")
    p.add_argument("codigo", help="código del proceso, p. ej. LICO-EPMMOP-2026-001")
    p.add_argument("--anios", type=int, nargs="+")
    p.add_argument("--completo", action="store_true", help="muestra el RUC completo de personas naturales (no lo publique)")
    p.set_defaults(func=cmd_proceso)

    p = sub.add_parser("proveedor", help="todo lo que un proveedor ganó en el país (por nombre o RUC)")
    p.add_argument("texto", help="RUC de 13 dígitos o parte del nombre")
    p.add_argument("--anios", type=int, nargs="+")
    p.add_argument("--csv", type=Path, help="guarda la lista de procesos en un CSV")
    p.add_argument("--completo", action="store_true", help="muestra el RUC completo de personas naturales (no lo publique)")
    p.set_defaults(func=cmd_proveedor)

    p = sub.add_parser("descargar", help="descarga los datos del SERCOP sin auditar")
    p.add_argument("--anios", type=int, nargs="+")
    p.add_argument("--refrescar", action="store_true")
    p.set_defaults(func=cmd_descargar)

    p = sub.add_parser("solicitud", help="redacta una solicitud de acceso a la información (LOTAIP)")
    p.add_argument("entidad", type=Path)
    p.add_argument("--pedido", required=True, help="qué información pide, con el mayor detalle posible")
    p.add_argument("--nombre", required=True)
    p.add_argument("--cedula", required=True)
    p.add_argument("--correo", required=True, help="correo para recibir la respuesta")
    p.add_argument("--telefono", default="")
    p.add_argument("--fecha", type=_fecha, help="fecha de presentación AAAA-MM-DD (por defecto hoy)")
    p.add_argument("--formato", choices=["md", "html", "ambos"], default="ambos")
    p.add_argument("--salida", type=Path, default=Path("solicitudes"))
    p.set_defaults(func=cmd_solicitud)

    p = sub.add_parser("plazo", help="calcula hasta cuándo debe responder la entidad una solicitud")
    p.add_argument("fecha", type=_fecha, help="fecha de presentación AAAA-MM-DD")
    p.add_argument("--entidad", type=Path, help="archivo .toml de la entidad, para sumar sus feriados locales")
    p.set_defaults(func=cmd_plazo)

    a = ap.parse_args(argv)
    a.func(a)


if __name__ == "__main__":
    main()
