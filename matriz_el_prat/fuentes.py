"""Conectores a fuentes públicas oficiales (comprobadas el 2026-10-24). Sin credenciales, sin datos personales.

Cada función devuelve una lista de dicts {titulo, url, fecha_publicacion, datos}. Si la fuente falla, lanza
FuenteError; el sub-agente lo registra como estado 'error' (nunca inventa datos).
"""
import datetime as dt, html as _html, json, re, urllib.parse, urllib.request
import xml.etree.ElementTree as ET

UA = "matriz_el_prat/1.0 (+https://github.com/canelonemf-byte/matriz-el-prat; auditoria ciudadana)"
KW_PRAT = re.compile(r"prat de llobregat", re.I)
KW_LOCAL = re.compile(r"haciendas locales|hisendes locals|r[eé]gimen local|r[eè]gim local|tributos locales|catastr|"
                      r"bienes inmuebles|b[eé]ns immobles|residuos|residus|vivienda|habitatge|aeropuerto|aeroport|AENA", re.I)

FUENTES = {
    "boe_sumario": {"url": "https://www.boe.es/datosabiertos/api/boe/sumario/{fecha}", "estado": "operativa",
                    "doc": "https://www.boe.es/datosabiertos/documentos/APIsumarioBOE.pdf"},
    "dogc_normativa": {"url": "https://analisi.transparenciacatalunya.cat/resource/n6hn-rmy7.json", "estado": "operativa",
                       "doc": "https://analisi.transparenciacatalunya.cat/d/n6hn-rmy7"},
    "bopb_rss": {"url": "https://bop.diba.cat/dades-obertes/butlleti-del-dia/administracio-local/feed", "estado": "operativa",
                 "nota": "solo el boletín del día; el histórico requiere el buscador (POST con token), no automatizado"},
    "placsp_atom": {"url": "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3.atom",
                    "estado": "operativa"},
    "elprat_dades_obertes": {"url": "https://seu-e.cat/ca/web/elpratdellobregat/dades-obertes", "estado": "operativa"},
}


class FuenteError(RuntimeError):
    pass


def _get(url, accept="*/*", timeout=40) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except Exception as e:  # noqa: BLE001
        raise FuenteError(f"{url}: {e}") from e


def boe_sumario(fecha: dt.date | None = None):
    fecha = fecha or dt.date.today()
    d = json.loads(_get(FUENTES["boe_sumario"]["url"].format(fecha=fecha.strftime("%Y%m%d")), "application/json"))
    if str(d.get("status", {}).get("code")) != "200":
        return []  # sin BOE ese día (domingo/festivo)
    out = []

    def walk(x, seccion=""):
        if isinstance(x, dict):
            if "titulo" in x and "identificador" in x:
                url = (x.get("url_html") or x.get("url_pdf", {}).get("texto", "") if isinstance(x.get("url_pdf"), dict) else x.get("url_html", ""))
                out.append({"titulo": x["titulo"], "url": url or f"https://www.boe.es/diario_boe/txt.php?id={x['identificador']}",
                            "fecha_publicacion": fecha.isoformat(), "datos": {"identificador": x["identificador"], "seccion": seccion}})
                return
            for k, v in x.items():
                walk(v, x.get("nombre", seccion) if k == "departamento" else seccion)
        elif isinstance(x, list):
            for v in x:
                walk(v, seccion)
    walk(d.get("data", {}))
    return out


def dogc_normativa(desde: dt.date | None = None, limit=200):
    desde = desde or dt.date.today() - dt.timedelta(days=7)
    q = urllib.parse.urlencode({"$where": f"data_de_publicaci_del_diari >= '{desde.isoformat()}T00:00:00'",
                                "$limit": limit, "$order": "data_de_publicaci_del_diari DESC"})
    rows = json.loads(_get(FUENTES["dogc_normativa"]["url"] + "?" + q, "application/json"))
    return [{"titulo": r.get("t_tol_de_la_norma_es") or r.get("t_tol_de_la_norma", ""),
             "url": (r.get("url_es_formato_html") or r.get("format_html") or {}).get("url", ""),
             "fecha_publicacion": r.get("data_de_publicaci_del_diari", "")[:10],
             "datos": {"rang": r.get("rang_de_norma", ""), "dogc": r.get("n_mero_de_diari", ""), "vigencia": r.get("vig_ncia_de_la_norma", "")}}
            for r in rows]


def bopb_rss():
    """RSS oficial del BOPB del día, sección Administració local (bop.diba.cat/dades-obertes)."""
    root = ET.fromstring(_get(FUENTES["bopb_rss"]["url"]))
    out = []
    for it in root.iter("item"):
        t, link, desc = _html.unescape(it.findtext("title", "")), it.findtext("link", ""), _html.unescape(it.findtext("description", ""))
        if "/anunci/" not in link:
            continue
        m = re.search(r"Data publicaci[oó]:</strong>\s*(\d\d)/(\d\d)/(\d{4})", desc)
        txt = re.sub(r"<[^>]+>", " ", desc)
        resumen = re.sub(r"\s+", " ", txt.split("Anunci en PDF")[0]).strip()
        out.append({"titulo": f"{t}: {resumen}"[:500], "url": link.replace("http://", "https://"),
                    "fecha_publicacion": f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else "",
                    "datos": {"emisor": t, "es_el_prat": bool(KW_PRAT.search(t))}})
    return out


def bopb_pdf_text(anuncio_id: int) -> str:
    """Descarga un anuncio del BOPB (PDF público) y devuelve su texto (requiere pdftotext de poppler)."""
    import subprocess, tempfile
    data = _get(f"https://bop.diba.cat/anuncio/ver-pdf/{anuncio_id}")
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        f.write(data); f.flush()
        return subprocess.run(["pdftotext", "-layout", f.name, "-"], capture_output=True, text=True, check=True).stdout


def placsp_atom():
    root = ET.fromstring(_get(FUENTES["placsp_atom"]["url"], timeout=90))
    ns = {"a": "http://www.w3.org/2005/Atom"}
    out = []
    for e in root.findall("a:entry", ns):
        raw = ET.tostring(e, encoding="unicode")
        link = e.find("a:link", ns)
        out.append({"titulo": (e.findtext("a:title", "", ns) or "").strip(), "url": link.get("href", "") if link is not None else "",
                    "fecha_publicacion": (e.findtext("a:updated", "", ns) or "")[:10],
                    "datos": {"organo_prat": bool(KW_PRAT.search(raw))}})
    return out


def elprat_dades_obertes():
    html = _get(FUENTES["elprat_dades_obertes"]["url"]).decode("utf-8", "replace")
    ids = sorted(set(re.findall(r"dadesobertes/dataset/([0-9a-f-]{36})", html)))
    temas = sorted(set(re.findall(r"showConjuntsDades/([a-z-]+)", html)))
    base = "https://seu-e.cat/ca/web/elpratdellobregat/dades-obertes/-/dadesobertes/dataset/"
    return [{"titulo": f"dataset {i}", "url": base + i, "fecha_publicacion": "", "datos": {"temas_portal": temas}} for i in ids]
