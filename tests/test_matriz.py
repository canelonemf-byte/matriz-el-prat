import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pytest
from matriz_el_prat import calculos as C, documentos as D, agentes as A
from matriz_el_prat.store import Store, redact


def test_tipos_of1_2026():
    assert C.TIPOS_PRAT_2026 == {"urbana_general": 0.6199, "urbana_diferenciado": 0.8350, "rustica": 0.4939, "bice": 1.3}


def test_cuota_ibi():
    r = C.cuota_ibi(100_000)
    assert r["cuota_integra"] == 619.9 and r["dentro_limites_trlrhl"]
    assert C.cuota_ibi(2_000_000, uso="C")["tipo_pct"] == 0.835
    assert C.cuota_ibi(None)["estado"] == C.PENDIENTE


def test_bice_ya_en_maximo():
    r = C.simular_cambio_tipo("bice", 1.30)
    assert any("máximo legal" in a for a in r["avisos"]) and r["variacion_recaudacion_eur"] == C.PENDIENTE
    assert not C.simular_cambio_tipo("bice", 1.5)["legal"]


def test_variacion_y_base_implicita():
    r = C.simular_cambio_tipo("urbana", 0.48, 1_000_000_000)
    assert r["variacion_recaudacion_eur"] == pytest.approx(-1_399_000)
    assert C.base_implicita(-2_700_000, 0.6199, 0.48) == pytest.approx(1_929_949_964.26)


def test_residuos_no_deficitaria():
    r = C.tasa_residuos_pxg(100, 40, 1_000_000, 1_000_000)
    assert r["cuota_bonificada"] == 60 and r["no_deficitaria"] is False
    assert C.tasa_residuos_pxg()["estado"] == C.PENDIENTE


def test_borradores_marcados():
    for doc in (D.mocion("t", "e", ["a"]), D.alegacion("o", "", ["m"], "p"), D.solicitud("a", ["h"], "s")):
        assert doc.startswith("# BORRADOR — NO PRESENTADO")
    assert "art. 66" in D.solicitud("a", ["h"], "s") and "art. 17.1" in D.alegacion("o", "", ["m"], "p")


def test_rgpd_redact():
    assert "12345678Z" not in redact("NIF 12345678Z y ***2631**")


def test_estructura_agentes(tmp_path):
    assert len(A.AGENTES) == 5 and len(A.SUBAGENTES) == 15
    s = Store(tmp_path / "t.sqlite")
    assert s.add("x", "y", "Ajuntament del Prat de Llobregat: ordenança fiscal", "https://e", "2026-10-23", True)
    assert not s.add("x", "y", "Ajuntament del Prat de Llobregat: ordenança fiscal", "https://e", "2026-10-23", True)
    r = A.SUBAGENTES[2](s).ejecutar()
    assert r["estado"] == "pendiente"
    det = next(x for x in A.SUBAGENTES if x.nombre == "sub_2_3_optimizador_ibi_y_tasas")(s).ejecutar()
    assert det["detecciones"]


def test_prioridad_beneficio():
    an = A.analizar_propuestas()
    assert all("beneficio" in a and "beneficiarios" in a for a in an)
    assert an[-1]["id"] == "PRAT-FIS-002"  # ya vigente: sin beneficio nuevo
    assert "Beneficio para la ciudadanía" in D.mocion("t", "e", ["a"])


def test_catalogo_verificado():
    c = A.catalogo()
    ids = {m["id"] for m in c["catalogo"]}
    assert ids == {"PRAT-FIS-001", "PRAT-FIS-002", "PRAT-ECO-001", "PRAT-URB-001", "PRAT-VIV-001", "PRAT-LEG-001"}
    for m in c["catalogo"]:
        assert m["agente"] in A.AGENTES and m["original"] and all(v["estado"] in ("verificado", "no_verificado", "incorrecto") for v in m["verificacion"])
