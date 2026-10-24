"""Fetchers de datos públicos oficiales para la app ciudadana (ejecutables por los agentes matriz_* de AGs-Core).

Uso: python -m app.fetchers [nombre ...]   -> escribe data/fuentes/app/<nombre>.json y actualiza MANIFIESTO.yaml
Reglas: solo fuentes oficiales, agregados, sin datos personales; si una fuente falla se registra el error y
se conserva el último fichero bueno (nunca se inventan cifras).
Autoría: Lázaro López Paz (El Prat de Llobregat) con asistencia de IA. MIT.
"""
from __future__ import annotations
import datetime as dt, hashlib, json, pathlib, re, sys, urllib.parse, urllib.request
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "fuentes" / "app"
MANIFIESTO = ROOT / "data" / "fuentes" / "MANIFIESTO.yaml"
SOCRATA = "https://analisi.transparenciacatalunya.cat/resource/{}.json"
UA = "matriz_el_prat-app/1.0 (+https://github.com/canelonemf-byte/matriz-el-prat)"
ENS9, ENS10 = "816910007", "0816910007"
ORGANOS = ["Ajuntament del Prat de Llobregat", "Prat Espais, SLU", "Aigües del Prat, S.A.", "El Prat Comunicació, SL"]
# Formas jurídicas de persona jurídica: solo estas se muestran por nombre (RGPD: nunca personas físicas)
PJ = re.compile(r"\b(S\.?\s?L\.?\s?U?\.?|S\.?\s?A\.?\s?U?\.?|S\.?C\.?C\.?L\.?|SCCL|S\.?\s?COOP|SCP|S\.?C\.?P\.?|FUNDACI[OÓ]|ASSOCIACI[OÓ]|ASOCIACI[OÓ]N|CONSORCI|AJUNTAMENT|DIPUTACI[OÓ]|UTE|U\.T\.E\.|S\.?L\.?L\.?|S\.?L\.?P\.?|SOCIEDAD|SOCIETAT|LIMITED|LTD|GMBH|SAS|SRL|B\.?V\.?|INC\.?|AIE|A\.I\.E\.)\b", re.I)


def soql(dataset: str, query: str, timeout: int = 240):
    url = SOCRATA.format(dataset) + "?" + urllib.parse.urlencode({"$query": query})
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return url, json.loads(r.read())


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def f_liquidacio():
    url, rows = soql("ytva-5kp3", f"SELECT any,codi_document,codi_estructura,desc_estructura,import,euros_habitant "
                                  f"WHERE codi_ens='{ENS10}' ORDER BY any LIMIT 5000")
    return {"dataset": "https://analisi.transparenciacatalunya.cat/d/ytva-5kp3",
            "descripcion": "Liquidación de presupuestos (derechos/obligaciones reconocidas). IN ingresos, DE gastos por capítulo, CF por política, IT ingresos tributarios",
            "filas": [{"any": int(r["any"]), "doc": r["codi_document"], "codigo": r["codi_estructura"],
                       "concepto": r["desc_estructura"], "importe": _num(r.get("import")),
                       "eur_hab": _num(r.get("euros_habitant"))} for r in rows]}, url


def f_pressupost():
    url, rows = soql("4g9s-gzp6", f"SELECT any_exercici,tipus_partida,tipus_classif,nivell,estructura,descripcio,import "
                                  f"WHERE codi_ens='{ENS9}' AND nivell in('1','2') ORDER BY any_exercici LIMIT 20000")
    return {"dataset": "https://analisi.transparenciacatalunya.cat/d/4g9s-gzp6",
            "descripcion": "Presupuesto inicial. tipus_partida D gasto / I ingreso; clasif E económica / F funcional (programas)",
            "filas": [{"any": int(r["any_exercici"]), "partida": r["tipus_partida"], "clasif": r["tipus_classif"],
                       "nivel": int(r["nivell"]), "codigo": r.get("estructura", ""), "concepto": r.get("descripcio", ""),
                       "importe": _num(r.get("import"))} for r in rows]}, url


def f_cost_serveis():
    url, rows = soql("7e8k-3vki", f"SELECT any,descripcio_servei,tipus_gestio,cost_efectiu WHERE codi_ens='{ENS9}' ORDER BY any LIMIT 5000")
    return {"dataset": "https://analisi.transparenciacatalunya.cat/d/7e8k-3vki",
            "descripcion": "Coste efectivo de los servicios (Ministerio de Hacienda vía Generalitat)",
            "filas": [{"any": int(r["any"]), "servicio": r["descripcio_servei"], "gestion": r.get("tipus_gestio", ""),
                       "coste": _num(r.get("cost_efectiu"))} for r in rows]}, url


def f_ens():
    url, rows = soql("7fnj-etev", f"SELECT * WHERE codiensmatriu='{ENS10}' OR codi10='{ENS10}' ORDER BY any LIMIT 5000")
    keep = ["ens", "codi10", "tipusens", "any", "pressupostdecofin", "datapressupostdecofin",
            "liquidaci_decofin", "dataliquidaci_decofin"]
    return {"dataset": "https://analisi.transparenciacatalunya.cat/d/7fnj-etev",
            "descripcion": "Entes del sector público local dependientes del Ajuntament y cumplimiento de envío de presupuesto/liquidación",
            "filas": [{k: r.get(k, "") for k in keep} for r in rows]}, url


def f_contractes():
    org = ",".join("'" + o.replace("'", "''") + "'" for o in ORGANOS)
    base = f"organisme_contractant in({org})"
    url, agg = soql("hb6v-jcbf", f"SELECT organisme_contractant,exercici,procediment_adjudicacio,tipus_contracte,count(*) as n,"
                                 f"sum(import_adjudicacio) as importe WHERE {base} GROUP BY organisme_contractant,exercici,"
                                 f"procediment_adjudicacio,tipus_contracte LIMIT 50000")
    _, top = soql("hb6v-jcbf", f"SELECT organisme_contractant,adjudicatari,count(*) as n,sum(import_adjudicacio) as importe "
                               f"WHERE {base} AND exercici>='2022' GROUP BY organisme_contractant,adjudicatari "
                               f"ORDER BY importe DESC LIMIT 400")
    tops, ocultos = [], {}
    for r in top:
        nom = (r.get("adjudicatari") or "").strip()
        if nom and PJ.search(nom):
            tops.append({"organo": r["organisme_contractant"], "adjudicatario": nom, "n": int(_num(r["n"])), "importe": _num(r.get("importe"))})
        else:
            o = ocultos.setdefault(r["organisme_contractant"], {"n": 0, "importe": 0.0})
            o["n"] += int(_num(r["n"])); o["importe"] += _num(r.get("importe"))
    return {"dataset": "https://analisi.transparenciacatalunya.cat/d/hb6v-jcbf",
            "descripcion": "Registro público de contratos de Catalunya (incluye menores). Importes de adjudicación",
            "nota_rgpd": "Solo se nombran adjudicatarios persona jurídica; personas físicas/no identificables se agregan sin nombre",
            "agregado": [{"organo": r["organisme_contractant"], "any": int(_num(r["exercici"])), "procedimiento": r.get("procediment_adjudicacio", ""),
                          "tipo": r.get("tipus_contracte", ""), "n": int(_num(r["n"])), "importe": _num(r.get("importe"))} for r in agg],
            "top_adjudicatarios_desde_2022": tops[:150], "no_nombrados_desde_2022": ocultos}, url


def f_contractes_detall():
    org = ",".join("'" + o.replace("'", "''") + "'" for o in ORGANOS)
    url, rows = soql("hb6v-jcbf", f"SELECT organisme_contractant,exercici,codi_expedient,descripcio_expedient,procediment_adjudicacio,"
                                  f"tipus_contracte,adjudicatari,import_adjudicacio,data_adjudicacio WHERE organisme_contractant in({org}) "
                                  f"AND exercici>='2024' LIMIT 20000")
    out = []
    for r in rows:
        nom = (r.get("adjudicatari") or "").strip()
        out.append({"organo": r["organisme_contractant"], "any": int(_num(r["exercici"])), "expediente": r.get("codi_expedient", ""),
                    "objeto": (r.get("descripcio_expedient") or "")[:200], "procedimiento": r.get("procediment_adjudicacio", ""),
                    "tipo": r.get("tipus_contracte", ""), "adjudicatario": nom if PJ.search(nom) else "(no se muestra: posible persona física)",
                    "importe": _num(r.get("import_adjudicacio")), "fecha": (r.get("data_adjudicacio") or "")[:10]})
    return {"dataset": "https://analisi.transparenciacatalunya.cat/d/hb6v-jcbf",
            "descripcion": "Contratos individuales 2024+ (para detección de anomalías). Adjudicatarios persona física no se muestran",
            "filas": out}, url


def f_ipc():
    url = "https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/IPC251852?nult=240"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.loads(r.read())
    anual = {}
    for x in d["Data"]:
        anual.setdefault(int(x["Anyo"]), []).append(float(x["Valor"]))
    return {"dataset": "https://www.ine.es/consul/serie.do?s=IPC251852",
            "descripcion": "IPC nacional, índice general (base 2021=100). Media anual de los meses disponibles",
            "anual": {str(k): {"media": sum(v) / len(v), "meses": len(v)} for k, v in sorted(anual.items())}}, url


FETCHERS = {"liquidacio": f_liquidacio, "pressupost": f_pressupost, "cost_serveis": f_cost_serveis,
            "ens": f_ens, "contractes": f_contractes,
            "contractes_detall": f_contractes_detall, "ipc": f_ipc}


def _manifest_upsert(archivo, url, sha):
    man = yaml.safe_load(MANIFIESTO.read_text(encoding="utf-8")) if MANIFIESTO.exists() else []
    man = [m for m in man if m.get("archivo") != archivo]
    man.append({"archivo": archivo, "url": url, "fecha_consulta": dt.date.today().isoformat(), "sha256": sha})
    MANIFIESTO.write_text(yaml.safe_dump(man, allow_unicode=True, sort_keys=False), encoding="utf-8")


def run(nombres=None) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    res = {}
    for n in nombres or FETCHERS:
        try:
            data, url = FETCHERS[n]()
            data["fecha_consulta"] = dt.date.today().isoformat(); data["url_consulta"] = url
            raw = json.dumps(data, ensure_ascii=False, indent=1).encode()
            p = OUT / f"{n}.json"; p.write_bytes(raw)
            sha = hashlib.sha256(raw).hexdigest()
            _manifest_upsert(str(p.relative_to(ROOT)), url, sha)
            res[n] = {"estado": "ok", "sha256": sha}
        except Exception as e:  # noqa: BLE001
            res[n] = {"estado": "error", "error": str(e)[:300]}
    return res


if __name__ == "__main__":
    print(json.dumps(run(sys.argv[1:] or None), indent=1, ensure_ascii=False))
