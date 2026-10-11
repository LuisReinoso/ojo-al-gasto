import pandas as pd

from veeduria import privacidad, publico


def test_enmascara_solo_personas_naturales():
    assert privacidad.enmascarar_ruc("1712345670001") == "17********001"
    assert privacidad.enmascarar_ruc("1792508215001") == "1792508215001"  # sociedad privada (tercer dígito 9)
    assert privacidad.enmascarar_ruc("1768154690001") == "1768154690001"  # entidad pública (tercer dígito 6)
    assert privacidad.enmascarar_ruc("1712345670001 | 1792508215001") == "17********001 | 1792508215001"
    assert pd.isna(privacidad.enmascarar_ruc(float("nan")))


def test_enmascarar_dataframe_no_toca_el_original():
    df = pd.DataFrame({"ruc_proveedor": ["0401234560001", "1790000000001"], "x": [1, 2]})
    out = privacidad.enmascarar(df)
    assert list(out["ruc_proveedor"]) == ["04********001", "1790000000001"]
    assert df["ruc_proveedor"].iloc[0] == "0401234560001"


def test_frase_respeta_siglas_y_nombres_propios():
    t = publico.frase("REHABILITACIÓN DE LA AV. GALO PLAZA LASSO (TRAMO: INTERCAMBIADOR CARCELÉN) EN QUITO EPMMOP", 200)
    assert t == "Rehabilitación de la Av. Galo Plaza Lasso (tramo: intercambiador Carcelén) en Quito EPMMOP"


def test_consultas_proceso_y_proveedor_enmascaran():
    from test_reglas import proceso, tabla
    from veeduria import consultas

    nac = tabla(
        proceso("ocds-5wno2w-SIE-X-2025-1-99", "2025-03-01", 50_000, tipo="Subasta Inversa Electrónica", oferentes=1),
        proceso("ocds-5wno2w-SIE-X-2025-2-99", "2025-03-05", 30_000, tipo="Subasta Inversa Electrónica", oferentes=3),
    )
    nac["codigo"] = ["SIE-X-2025-1", "SIE-X-2025-2"]
    nac["monto_contrato"] = nac["monto"]
    encontrados = consultas.buscar_proceso(nac, "SIE-X-2025-1-99")
    assert list(encontrados["codigo"]) == ["SIE-X-2025-1"]
    ficha = consultas.ficha_proceso(nac, encontrados.iloc[0])
    assert "17********001" in ficha and "1712345670001" not in ficha and "un solo oferente" in ficha
    resumen = consultas.resumen_proveedor(consultas.buscar_proveedor(nac, "1712345670001"))
    assert "2 procesos" in resumen and "1712345670001" not in resumen
    assert "1712345670001" in consultas.resumen_proveedor(consultas.buscar_proveedor(nac, "prov"), completo=True)


def test_anonimizar_personas_solo_naturales():
    df = pd.DataFrame({
        "proveedor": ["ANA PEREZ", "EMPRESA S.A.", "ANA PEREZ | EMPRESA S.A.", None],
        "ruc_proveedor": ["1712345670001", "1792508215001", "1712345670001 | 1792508215001", None],
    })
    out = privacidad.anonimizar_personas(df)
    assert list(out["proveedor"][:3]) == ["Persona natural", "EMPRESA S.A.", "Varios proveedores (incluye personas naturales)"]
    assert df["proveedor"].iloc[0] == "ANA PEREZ"
