"""Prueba de punta a punta del informe con datos sintéticos (sin red)."""

import pandas as pd

from veeduria import informe, reglas
from veeduria.cli import cargar_configuracion

from test_reglas import proceso, tabla


def test_informe_completo_con_lotaip(tmp_path):
    procesos = tabla(
        proceso("a", "2025-03-01", 60_000),
        proceso("b", "2025-03-20", 55_000),
        proceso("c", "2026-02-01", 80_000, tipo="Licitación", oferentes=1),
        proceso("d", "2026-02-02", 300_000, tipo="Bienes y Servicios únicos", categoria="services", oferentes=1),
    )
    cfg = cargar_configuracion()
    alertas, base = reglas.todas(procesos, procesos, cfg)
    cumplimiento = pd.DataFrame({
        "anio": [2025, 2025, 2025], "mes": [1, 2, 3], "numerales_publicados": [26, 25, 0],
        "numerales": [[], [], []], "ultima_publicacion": pd.to_datetime(["2025-02-15", "2025-03-15", None]),
        "dias_tras_cierre": [15, 15, None], "dias_atraso": [None] * 3, "faltantes": [[], ["Numeral 6"], ["x"]],
        "estado": ["publicado", "incompleto", "no publicado"],
    })
    saip = pd.DataFrame({"anio": [2025], "recibidas": [10], "respondidas": [7], "sin_responder": [3], "porcentaje_sin_responder": [30.0]})
    ctx = {
        "e": {"nombre": "GAD de prueba", "canton": "Prueba", "rucs": [{"ruc": "1760003410001", "nombre": "GAD"}]},
        "anios": [2025, 2026], "procesos": procesos, "alertas": alertas,
        "r": reglas.resumen(procesos), "tasas": reglas.tasas_comparadas(procesos, base),
        "proveedores": reglas.concentracion(procesos),
        "regimenes": [reglas.Regimen.desde_config(r) for r in cfg["contratacion"]["regimenes"]],
        "base_procesos": len(procesos), "dia_limite": 0, "cumplimiento": cumplimiento, "saip": saip,
        "ppto": None, "contraloria": None, "calidad": None, "cruce": None,
    }
    ruta, hallazgos = informe.escribir(tmp_path, ctx)
    html = ruta.read_text(encoding="utf-8")
    assert "Posible fraccionamiento" in html and "Proveedor único para servicios u obras" in html
    assert any("1 mes no publicado, 1 mes incompleto" in h for h in hallazgos)
    assert any("3 de 10 solicitudes" in h for h in hallazgos)
    assert (tmp_path / "alertas.csv").exists() and (tmp_path / "resumen.json").exists()
    publico = (tmp_path / "publico.html").read_text(encoding="utf-8")
    assert "¿En qué gasta Prueba?" in publico and "Lo que puede preguntar" in publico and "Cómo presentar su pregunta" in publico and "<dialog" not in publico
    # La página pública no muestra RUC de personas naturales ni nombres de proveedores.
    assert "1712345670001" not in publico and "PROV" not in publico
    for archivo in ("alertas.csv", "procesos.csv", "informe.html"):
        texto = (tmp_path / archivo).read_text(encoding="utf-8-sig")
        assert "1712345670001" not in texto, archivo
    alertas_csv = (tmp_path / "alertas.csv").read_text(encoding="utf-8-sig")
    assert "17********001" in alertas_csv and "Persona natural" in alertas_csv
    # Las alertas no nombran a personas naturales.
    assert ",PROV," not in alertas_csv and ">PROV<" not in (tmp_path / "informe.html").read_text(encoding="utf-8")
