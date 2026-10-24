"""Auditoría de publicidad activa del Ajuntament del Prat (Ley 19/2013 arts. 6-8; Llei 19/2014 arts. 8-15).

Rastrea el Portal de Transparència (plataforma AOC, seu-e.cat). Cada página-ítem declara su base legal, su frecuencia
de actualización y la fecha de 'Actualització'. Estado:
  publicado       hay contenido o enlaces y la fecha cumple la frecuencia declarada
  desactualizado  la última actualización supera la frecuencia declarada (anual: >16 meses; trimestral: >5; mensual: >2)
  no_encontrado   la página no tiene contenido ni enlaces
Solo se guardan URL, fecha, hash y un resumen; nunca datos personales.
"""
import datetime as dt, hashlib, html as _html, re
from concurrent.futures import ThreadPoolExecutor
from . import fuentes as F

BASE = "https://seu-e.cat/ca/web/elpratdellobregat/govern-obert-i-transparencia"
SECCIONES = ["informacio-institucional-i-organitzativa", "contractes-convenis-i-subvencions", "gestio-economica",
             "accio-de-govern-i-normativa", "serveis-i-tramits"]


def _txt(x):
    t = re.sub(r"(?s)<script.*?</script>|<style.*?</style>", "", x)
    t = re.sub(r"<[^>]+>", "|", t)
    return re.sub(r"(\| ?)+", "|", _html.unescape(re.sub(r"\s+", " ", t)))


def hojas() -> list[str]:
    urls = set()
    for s in SECCIONES:
        try:
            x = F._get(f"{BASE}/{s}").decode("utf-8", "ignore")
        except F.FuenteError:
            continue
        urls |= set(re.findall(re.escape(BASE) + r"/[a-z0-9-]+/[a-z0-9-]+/[a-z0-9-]+(?=[\"?])", x))
    return sorted(urls)


def evaluar(url: str, x: str, hoy: dt.date | None = None) -> dict:
    hoy = hoy or dt.date.today()
    t = _txt(x)
    title = re.search(r"(?s)<title>\s*(.*?)\s*-", x)
    cat = re.search(r"19/2014 \(catalana\):\|(.*?)\|Llei", t)
    es = re.search(r"19/2013 \(espanyola\):\|(.*?)\|", t)
    fr = re.search(r"requerida:\|(.*?)\|", t)
    a = t.find("requerida:|"); a = t.find("|", a + 11) if a > 0 else -1
    b = t.find("|Indicadors de transparència|")
    body = t[a:b] if a > 0 and b > a else ""
    body = re.sub(r"Actualització: ?\d\d/\d\d/\d{4}|Font: [^|]*", "", body)
    ds = [dt.date(int(y), int(m), int(d)) for d, m, y in re.findall(r"Actualització: ?(\d\d)/(\d\d)/(\d{4})", t)]
    up = max(ds) if ds else None
    ra = x.find("requerida:"); rb = x.find("Indicadors de transpar", ra)
    links = sorted({h for h in re.findall(r'href="([^"#]+)"', x[ra:rb]) if h.startswith("http") and "indicadors-de-transparencia" not in h})
    freq = fr[1].strip() if fr else ""
    lim = 480
    for k, v in (("trimestral", 150), ("mensual", 60), ("semestral", 240)):
        if k in freq.lower():
            lim = v
    n = len(re.sub(r"[|\s-]", "", body))
    segs = [g for g in body.split("|") if len(g.strip()) > 3 and "{{" not in g]
    dinamico = "{{" in body or "Descarrega't aquestes dades" in body
    if (n < 15 or len(segs) <= 1) and not links and not dinamico:
        estado = "no_encontrado"  # solo el texto introductorio de la plantilla AOC
    elif up and (hoy - up).days > lim:
        estado = "desactualizado"
    else:
        estado = "publicado"
    return {"id": url.split("transparencia/")[1].replace("/", "."), "titulo": title[1].strip() if title else "",
            "url": url, "base_legal": {"llei_19_2014": cat[1].strip() if cat else None, "ley_19_2013": es[1].strip() if es else None},
            "frecuencia_declarada": freq, "actualizacion": up.isoformat() if up else None, "estado": estado,
            "enlaces": links[:10], "contenido_dinamico": dinamico, "sha256_pagina": hashlib.sha256(body.encode()).hexdigest(), "resumen": body.strip("| ")[:240]}


def auditar(urls=None, workers=8) -> list[dict]:
    urls = urls or hojas()
    def one(u):
        try:
            return evaluar(u, F._get(u, timeout=60).decode("utf-8", "ignore"))
        except F.FuenteError as e:
            return {"id": u.split("transparencia/")[1].replace("/", "."), "url": u, "estado": "error", "error": str(e)[:200]}
    with ThreadPoolExecutor(workers) as ex:
        return sorted(ex.map(one, urls), key=lambda r: r["id"])


def como_registros(items) -> list[dict]:
    return [{"titulo": f"[transparencia:{i['estado']}] {i.get('titulo') or i['id']}", "url": i["url"],
             "fecha_publicacion": i.get("actualizacion") or "", "datos": i} for i in items]
