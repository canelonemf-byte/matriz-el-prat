"""Tests de ingesta BOE/DOGC con HTTP simulado (sin red).

Autor: Lázaro López Paz, El Prat de Llobregat, Barcelona, España, con asistencia de IA.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import datetime as dt
import json
from io import BytesIO
from unittest.mock import patch
import urllib.error

import pytest

from matriz_el_prat import agentes as A
from matriz_el_prat import fuentes as F


def _http_error(url: str, code: int, msg: str = "Error"):
    return urllib.error.HTTPError(url, code, msg, hdrs=None, fp=BytesIO(b""))


def _urlopen_raises(exc):
    def _fake(req, timeout=None):
        raise exc
    return _fake


def test_boe_sumario_http_404_es_sin_boe_ese_dia():
    fecha = dt.date(2026, 11, 15)  # domingo
    url = F.FUENTES["boe_sumario"]["url"].format(fecha="20261115")
    with patch.object(F.urllib.request, "urlopen", _urlopen_raises(_http_error(url, 404, "Not Found"))):
        assert F.boe_sumario(fecha) == []


def test_boe_sumario_http_500_sigue_siendo_error():
    fecha = dt.date(2026, 11, 16)
    url = F.FUENTES["boe_sumario"]["url"].format(fecha="20261116")
    with patch.object(F.urllib.request, "urlopen", _urlopen_raises(_http_error(url, 500, "Internal Server Error"))):
        with pytest.raises(F.FuenteError):
            F.boe_sumario(fecha)


def test_boe_sumario_json_status_no_200_devuelve_vacio():
    payload = json.dumps({"status": {"code": 404}}).encode()

    class _Resp:
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False
        def read(self):
            return payload

    with patch.object(F.urllib.request, "urlopen", lambda req, timeout=None: _Resp()):
        assert F.boe_sumario(dt.date(2026, 11, 15)) == []


def test_boe_ultimos_un_dia_con_error_no_detiene_los_demas(monkeypatch):
    fijo = dt.date(2026, 11, 18)

    class _Fecha(dt.date):
        @classmethod
        def today(cls):
            return fijo

    def fake_boe(fecha=None):
        fecha = fecha or fijo
        if fecha == fijo:  # hoy: error de red / 500
            raise F.FuenteError("https://www.boe.es/...: HTTP Error 500")
        if fecha == fijo - dt.timedelta(days=1):
            return [{"titulo": "sumario de ayer", "url": "https://boe.es/x", "fecha_publicacion": fecha.isoformat(), "datos": {}}]
        return []

    monkeypatch.setattr(A.dt, "date", _Fecha)
    monkeypatch.setattr(F, "boe_sumario", fake_boe)
    out = A._boe_ultimos(3)
    assert len(out) == 1 and out[0]["titulo"] == "sumario de ayer"


def test_ingesta_boe_falla_pero_dogc_sigue(monkeypatch):
    def boom(fecha=None):
        raise F.FuenteError("BOE caído")

    def dogc_ok(desde=None, limit=200):
        return [{"titulo": "norma DOGC", "url": "https://dogc.gencat.cat/x", "fecha_publicacion": "2026-11-17", "datos": {}}]

    monkeypatch.setattr(F, "boe_sumario", boom)
    monkeypatch.setattr(F, "dogc_normativa", dogc_ok)
    out = A._boe_y_dogc()
    assert [x["titulo"] for x in out] == ["norma DOGC"]


def test_ingesta_si_boe_y_dogc_fallan_propaga_error(monkeypatch):
    monkeypatch.setattr(A, "_boe_ultimos", lambda dias=3: (_ for _ in ()).throw(F.FuenteError("BOE")))
    monkeypatch.setattr(F, "dogc_normativa", lambda desde=None, limit=200: (_ for _ in ()).throw(F.FuenteError("DOGC")))
    with pytest.raises(F.FuenteError) as ei:
        A._boe_y_dogc()
    assert "BOE" in str(ei.value) and "DOGC" in str(ei.value)
