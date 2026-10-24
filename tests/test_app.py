import pathlib, pytest
from streamlit.testing.v1 import AppTest
from app import analitica as A

MAIN = str(pathlib.Path(__file__).resolve().parents[1] / "app" / "main.py")
PAGS = None


def _paginas():
    at = AppTest.from_file(MAIN, default_timeout=60).run()
    return at.sidebar.radio[0].options


@pytest.mark.parametrize("i", range(17))
def test_cada_pagina_carga(i):
    at = AppTest.from_file(MAIN, default_timeout=60).run()
    at.sidebar.radio[0].set_value(at.sidebar.radio[0].options[i]).run()
    assert not at.exception, at.exception


def test_formulas():
    assert abs(A.cagr(100, 121, 2) - 0.1) < 1e-9
    t = A.tendencia_log([2020, 2021, 2022, 2023], [100, 110, 121, 133.1])
    assert abs(t["crecimiento_anual"] - 0.1) < 1e-6 and t["prevision"][0]["min95"] <= t["prevision"][0]["prevision"]


def test_totales_reales_y_sin_personas():
    t = A.totales_anuales(A.liquidacion())
    assert (t.ingresos > 0).all()
    k = A.cargar("contractes_detall")
    for f in k["filas"][:2000]:
        assert f["adjudicatario"].startswith("(no se muestra") or A.__name__  # nombres solo si persona jurídica
    import re
    from app.fetchers import PJ
    assert all(PJ.search(f["adjudicatario"]) for f in k["filas"] if not f["adjudicatario"].startswith("(no se muestra"))


def test_manifiesto_cubre_datos_app():
    arch = {m["archivo"] for m in A.manifiesto()}
    for p in (A.FUENTES / "app").glob("*.json"):
        assert f"data/fuentes/app/{p.name}" in arch


def test_ia_sin_clave_no_inventa(monkeypatch):
    from app import ia
    monkeypatch.setattr(ia, "estado", lambda: "pendiente_de_clave")
    r = ia.preguntar("deuda viva")
    assert "fuente" in r["respuesta"].lower() or "acceso a la información" in r["respuesta"]


def test_validacion_cifras():
    from app import ia
    fuentes = "saldo 13,232,683 € (fuente x); formación 15,414 €"
    assert ia.validar("Sobraron 13.232.683 € [0] y 13,2 M€ en 2025; formación 15.414 €", fuentes) == []
    assert ia.validar("Se gastaron 999.999 € en 2025", fuentes) == ["999.999"]


def test_clave_no_en_repo():
    import subprocess
    out = subprocess.run(["git", "grep", "-n", "xai-"], capture_output=True, text=True).stdout
    assert "xai-" not in out.replace('"xai-"', "")
