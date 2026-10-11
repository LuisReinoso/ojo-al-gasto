from datetime import date

import pandas as pd
import pytest

from veeduria import reglas, solicitud
from veeduria.fuentes import transparencia as pnt

ANTES = reglas.Regimen.desde_config({
    "nombre": "PIE 2025", "desde": "2025-01-01", "hasta": "2025-06-25", "base_legal": "x",
    "bienes_servicios": [["menor cuantía de bienes y servicios", 72_000], ["cotización de bienes y servicios", 540_000]],
    "obras": [["menor cuantía de obras", 252_000], ["cotización de obras", 1_080_000]],
    "procedimientos": ["Menor Cuantía", "Cotización", "Licitación"],
})
DESPUES = reglas.Regimen.desde_config({
    "nombre": "reforma", "desde": "2025-10-28", "hasta": "2099-12-31", "base_legal": "y",
    "bienes_servicios": [["comisión técnica", 100_000]], "obras": [["comisión técnica", 100_000]],
})
U = [ANTES, DESPUES]


def proceso(ocid, fecha, monto, proveedor="1712345670001", categoria="services", tipo="Menor Cuantía", entidad="1760003410001", oferentes=3, adjudicado=None):
    f = pd.Timestamp(fecha)
    return {
        "ocid": ocid, "codigo": ocid, "buyer_name": "GAD", "ruc_entidad": entidad, "tipo_proceso": tipo,
        "objeto": "MANTENIMIENTO", "proveedor": "PROV", "ruc_proveedor": proveedor, "categoria": categoria,
        "presupuesto": monto, "monto": monto, "monto_adjudicado": adjudicado if adjudicado is not None else monto,
        "fecha": f, "fecha_publicacion": f, "inicio_ofertas": f, "fin_ofertas": f + pd.Timedelta(days=10),
        "num_oferentes": oferentes, "url_sercop": "",
    }


def tabla(*filas):
    return reglas.preparar(pd.DataFrame(filas))


def test_fraccionamiento_detecta_suma_sobre_limite_en_ventana():
    df = tabla(
        proceso("a", "2025-03-01", 60_000),
        proceso("b", "2025-03-20", 55_000),
        proceso("c", "2025-06-20", 60_000),  # fuera de la ventana de 90 días
    )
    al = reglas.posible_fraccionamiento(df, U)
    assert set(al["ocid"]) == {"a", "b"}
    assert "menor cuantía de bienes y servicios" in al["explicacion"].iloc[0]


def test_fraccionamiento_ignora_proveedores_distintos_y_sumas_bajo_limite():
    df = tabla(
        proceso("a", "2025-03-01", 60_000, proveedor="1"),
        proceso("b", "2025-03-02", 60_000, proveedor="2"),
        proceso("c", "2025-03-01", 30_000, proveedor="3"),
        proceso("d", "2025-03-05", 30_000, proveedor="3"),
    )
    assert reglas.posible_fraccionamiento(df, U).empty


def test_fraccionamiento_obras_usa_limite_de_obras():
    df = tabla(
        proceso("a", "2025-03-01", 200_000, categoria="works"),
        proceso("b", "2025-04-01", 100_000, categoria="works"),
    )
    al = reglas.posible_fraccionamiento(df, U)
    assert set(al["ocid"]) == {"a", "b"}
    assert "obras" in al["explicacion"].iloc[0]


def test_ventana_une_todos_los_procesos_encadenados():
    g = tabla(
        proceso("a", "2025-01-01", 40_000),
        proceso("b", "2025-02-01", 40_000),
        proceso("c", "2025-03-01", 40_000),
    ).sort_values("fecha_publicacion")
    marcados = reglas._ventanas_que_superan(g, 72_000, 90)
    assert list(marcados["ocid"]) == ["a", "b", "c"]


def test_un_solo_oferente_solo_en_competitivos():
    df = tabla(
        proceso("a", "2025-01-01", 10_000, oferentes=1),
        proceso("b", "2025-01-01", 10_000, oferentes=1, tipo="Contratacion directa"),
        proceso("c", "2025-01-01", 10_000, oferentes=4),
    )
    base = reglas.linea_base(df)
    assert list(reglas.un_solo_oferente(df, base)["ocid"]) == ["a"]


def test_junto_al_limite():
    df = tabla(proceso("a", "2025-01-01", 71_500), proceso("b", "2025-01-01", 60_000))
    assert list(reglas.junto_al_limite(df, U)["ocid"]) == ["a"]


@pytest.mark.parametrize("texto,esperado", [
    ("99406471.44", 99406471.44), ("12.059.316", 12059316.0), ("1.234,56", 1234.56),
    ("-13143270.7", -13143270.7), ("1234,5", 1234.5), ("1,234,567.89", 1234567.89), ("", None), ("N/A", None),
])
def test_numero(texto, esperado):
    assert pnt.numero(texto) == esperado


def test_notacion_cientifica():
    assert pnt.es_notacion_cientifica("1,76818E+12")
    assert pnt.es_notacion_cientifica("1.79E+12")
    assert not pnt.es_notacion_cientifica("1760003410001")


def test_dias_habiles_salta_fines_de_semana_y_feriados():
    # Viernes 30 de octubre de 2026 + 3 días hábiles, con feriados el 2 y 3 de noviembre.
    nl = {date(2026, 11, 2), date(2026, 11, 3)}
    assert solicitud.sumar_dias_habiles(date(2026, 10, 30), 3, nl) == date(2026, 11, 6)


def test_fraccionamiento_no_aplica_en_la_transicion_y_usa_regimen_nuevo():
    df = tabla(
        proceso("a", "2025-07-01", 60_000, tipo="Subasta Inversa Electrónica"),
        proceso("b", "2025-07-10", 60_000, tipo="Subasta Inversa Electrónica"),
        proceso("c", "2026-02-01", 90_000, tipo="Subasta Inversa Electrónica"),
        proceso("d", "2026-02-15", 30_000, tipo="Subasta Inversa Electrónica"),
    )
    al = reglas.posible_fraccionamiento(df, U)
    assert set(al["ocid"]) == {"c", "d"}
    assert al["base_legal"].iloc[0] == "y"


def test_no_mezcla_regimenes_en_una_ventana():
    df = tabla(proceso("a", "2025-06-20", 60_000), proceso("b", "2025-10-30", 60_000))
    assert reglas.posible_fraccionamiento(df, U).empty


def test_proveedor_unico_solo_servicios_y_obras_tras_reglamento():
    df = tabla(
        proceso("a", "2026-01-10", 50_000, tipo="Bienes y Servicios únicos", categoria="services"),
        proceso("b", "2026-01-10", 50_000, tipo="Bienes y Servicios únicos", categoria="goods"),
        proceso("c", "2025-05-10", 50_000, tipo="Bienes y Servicios únicos", categoria="services"),
    )
    al = reglas.proveedor_unico_no_permitido(df, pd.Timestamp("2025-10-28"))
    assert list(al["ocid"]) == ["a"]


def test_plazos_lotaip_calendario_y_habiles():
    cfg = {"lotaip": {"plazos": {"respuesta": 10, "prorroga": 5}}, "feriados": {"2026": ["2026-11-02", "2026-11-03"]}}
    p = solicitud.calcular_plazos(date(2026, 10, 26), cfg)
    assert p["calendario"] == date(2026, 11, 5)
    assert p["calendario_prorroga"] == date(2026, 11, 10)
    # 27-30 oct (4), 4-6 nov (3), 9-11 nov (3) = 10 días hábiles
    assert p["habiles"] == date(2026, 11, 11)
    assert p["habiles_prorroga"] == date(2026, 11, 18)


def test_regimen_anterior_ignora_subasta_inversa():
    df = tabla(
        proceso("a", "2025-03-01", 60_000, tipo="Subasta Inversa Electrónica"),
        proceso("b", "2025-03-05", 60_000, tipo="Subasta Inversa Electrónica"),
    )
    assert reglas.posible_fraccionamiento(df, U).empty


def test_similitud_define_nivel():
    assert reglas.similitud_objetos(["MANTENIMIENTO ALUMBRADO ORNAMENTAL PARQUES", "MANTENIMIENTO ILUMINACION ORNAMENTAL PUENTES"]) >= 0.2
    assert reglas.similitud_objetos(["EQUIPOS DETECCION GASES", "MONTACARGAS"]) == 0


def test_cola_binomial():
    assert reglas.cola_binomial(0, 10, 0.2) == pytest.approx(1.0)
    assert reglas.cola_binomial(10, 10, 0.5) == pytest.approx(0.5**10)
    assert reglas.cola_binomial(14, 24, 0.229) < 0.001
    assert reglas.cola_binomial(95, 1050, 0.17) == pytest.approx(1.0)  # n grande sin desbordar
    assert reglas.cola_binomial(300, 1050, 0.17) < 1e-6
