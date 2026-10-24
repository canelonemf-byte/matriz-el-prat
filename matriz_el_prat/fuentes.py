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
    "portal_transparencia": {"url": "https://seu-e.cat/ca/web/elpratdellobregat/govern-obert-i-transparencia", "estado": "operativa",
                             "nota": "112 ítems de publicidad activa; ver transparencia.py e inventario_obligaciones.yaml"},
    "seu_ckan": {"url": "https://dadesobertes.seu-e.cat/api/3/action/datastore_search", "estado": "operativa",
                 "nota": "datasets AOC filtrados por CODI_ENS 816910007 (Ajuntament del Prat)"},
    "catastro_estadisticas": {"url": "https://www.catastro.hacienda.gob.es/jaxi/tabla.do", "estado": "operativa",
                              "doc": "https://www.catastro.hacienda.gob.es/es-ES/estadisticas.html",
                              "nota": "estadística IBI (recibos, base liquidable, cuota) y catastro urbano por usos, por municipio"},
}

CODI_ENS = "816910007"
SEU_CKAN = {  # resource_id de dadesobertes.seu-e.cat (comprobados 2026-10-24)
    "tipus_impositius": "82ae0ea2-6fc6-4fd5-b944-4ef6d18717bc",
    "endeutament": "34db8dc5-ad5e-4bf0-83cc-537cd8671342",
    "pmp_proveidors": "eecca986-a51b-4b0e-a03b-6fc8bb71d387",
    "subvencions": "30798421-5952-4420-a769-d1121beb6534",
    "convenis": "8747a24f-aa98-4a7e-938a-df81cc16769a",
    "actes_ple": "b5d370d0-7916-48b6-8a69-3c7fa62a1467",
    "calendari_padrons": "59218973-d6a6-4cc1-bd3f-c9b9b851cb53",
}
CAMPOS_PERSONALES = {"BENEFICIARI", "NIF", "DNI", "NOM_BENEFICIARI"}


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


def seu_ckan(nombre: str, limit=5000) -> list[dict]:
    """Registros de un dataset AOC del Prat. Elimina campos con datos de personas físicas (p. ej. BENEFICIARI)."""
    q = urllib.parse.urlencode({"resource_id": SEU_CKAN[nombre], "filters": json.dumps({"CODI_ENS": CODI_ENS}), "limit": limit})
    d = json.loads(_get(f"{FUENTES['seu_ckan']['url']}?{q}", accept="application/json", timeout=60))
    if not d.get("success"):
        raise FuenteError(f"seu_ckan {nombre}: {d.get('error')}")
    return [{k: v for k, v in r.items() if k not in CAMPOS_PERSONALES} for r in d["result"]["records"]]


def _num(s):
    s = (s or "").strip()
    return None if s in ("", "..") else float(s.replace(".", "").replace(",", "."))


def catastro_tabla(path: str, file: str, municipio="Prat de Llobregat") -> list[list[str]]:
    """Consulta una tabla JAXI del Catastro seleccionando el municipio y todas las demás categorías."""
    base = FUENTES["catastro_estadisticas"]["url"]
    x = _get(f"{base}?path={path}&file={file}&type=pcaxis&L=0", timeout=90).decode("latin1")
    if 'name="cri1"' not in x:
        raise FuenteError(f"catastro {path}{file}: tabla no disponible")
    d = [("type", "pcaxis"), ("path", path), ("file", file), ("accion", "html")]
    for n, b in re.findall(r'(?s)<select[^>]*name="([^"]+)"[^>]*>(.*?)</select>', x):
        opts = re.findall(r'<option value="([^"]*)"[^>]*>\s*([^<]*?)\s*<', b)
        if n in ("rows", "columns"):
            d += [(n, v) for v, _ in opts]
        else:
            m = [v for v, t in opts if municipio in t]
            d += [(n, v) for v in (m[:1] if m else [v for v, _ in opts])]
    req = urllib.request.Request(base, data=urllib.parse.urlencode(d).encode(), headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            y = r.read().decode("latin1")
    except Exception as e:  # noqa: BLE001
        raise FuenteError(str(e)) from e
    y = re.sub(r"(?s)<script.*?</script>", "", y)
    out = []
    for row in re.findall(r"(?s)<tr[^>]*>(.*?)</tr>", y):
        c = [re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", "", v))).strip() for v in re.findall(r"(?s)<t[hd][^>]*>(.*?)</t[hd]>", row)]
        if any(c):
            out.append(c)
    return out


def _fila(tabla, municipio="Prat de Llobregat"):
    hdr = next(r for r in tabla if len(r) > 3 and r[0] == "")
    row = next(r for r in tabla if municipio in r[0])
    return {h: _num(v) for h, v in zip(hdr[1:], row[1:])}


def catastro_ibi_prat(anyo: int) -> dict:
    """Estadística tributaria del IBI (Catastro): recibos, base liquidable (miles €), cuota líquida (€) urbana y BICE."""
    return {"anyo": anyo,
            "urbana": _fila(catastro_tabla(f"/est{anyo}/ibi/", "U04008.px")),
            "bice": _fila(catastro_tabla(f"/est{anyo}/ibi/", "B04008.px")),
            "fuente": f"https://www.catastro.hacienda.gob.es/jaxi/tabla.do?path=/est{anyo}/ibi/&file=U04008.px&type=pcaxis&L=0"}


def catastro_urbano_usos(anyo: int) -> dict:
    """Bienes inmuebles urbanos y valor catastral (miles €) por uso (Catastro)."""
    return {"anyo": anyo,
            "inmuebles": _fila(catastro_tabla(f"/est{anyo}/catastro/urbano/", "URAO4208.px")),
            "valor_catastral_miles": _fila(catastro_tabla(f"/est{anyo}/catastro/urbano/", "URBO4208.px")),
            "variables": _fila(catastro_tabla(f"/est{anyo}/catastro/urbano/", "04108.px")),
            "fuente": f"https://www.catastro.hacienda.gob.es/jaxi/tabla.do?path=/est{anyo}/catastro/urbano/&file=URBO4208.px&type=pcaxis&L=0"}


def datos_fiscales_registros() -> list[dict]:
    """Registros para el almacén: estadísticas Catastro (último año disponible) y datasets AOC agregados."""
    out, hoy = [], dt.date.today()
    for y in (hoy.year, hoy.year - 1):
        try:
            d = catastro_ibi_prat(y); out.append({"titulo": f"Catastro: estadística IBI {y} El Prat (recibos, base, cuota)", "url": d["fuente"], "fecha_publicacion": f"{y}-01-01", "datos": d}); break
        except (FuenteError, StopIteration):
            continue
    for y in (hoy.year, hoy.year - 1):
        try:
            d = catastro_urbano_usos(y); out.append({"titulo": f"Catastro: inmuebles urbanos por uso {y} El Prat", "url": d["fuente"], "fecha_publicacion": f"{y}-01-01", "datos": d}); break
        except (FuenteError, StopIteration):
            continue
    for n in ("endeutament", "pmp_proveidors", "tipus_impositius", "calendari_padrons"):
        try:
            rs = seu_ckan(n)
        except FuenteError:
            continue
        out.append({"titulo": f"AOC dades obertes: {n} (Ajuntament del Prat)", "url": f"https://dadesobertes.seu-e.cat/dataset/?res={SEU_CKAN[n]}",
                    "fecha_publicacion": hoy.isoformat(), "datos": {"n": len(rs), "registros": rs[-40:]}})
    return out
