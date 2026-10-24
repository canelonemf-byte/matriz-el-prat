"""Genera inventario_obligaciones.yaml y data/fuentes/ (datos agregados + manifiesto URL/sha256).
Uso: python scripts/generar_inventario.py   (solo fuentes públicas oficiales; sin datos personales)"""
import datetime as dt, hashlib, json, sys
from pathlib import Path
import yaml
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from matriz_el_prat import fuentes as F, transparencia as T, calculos as C

HOY = dt.date.today().isoformat()
OUT = ROOT / "data" / "fuentes"; OUT.mkdir(parents=True, exist_ok=True)
manifest = []

def guardar(nombre, obj, url):
    b = json.dumps(obj, ensure_ascii=False, indent=1, default=str).encode()
    (OUT / nombre).write_bytes(b)
    manifest.append({"archivo": f"data/fuentes/{nombre}", "url": url, "fecha_consulta": HOY, "sha256": hashlib.sha256(b).hexdigest()})

# 1) Portal de Transparència
portal = T.auditar()
guardar("portal_transparencia.json", portal, T.BASE)
P = {i["id"].split(".")[-1]: i for i in portal}

# 2) Datasets AOC (agregados, sin beneficiarios)
ck = {}
for n in F.SEU_CKAN:
    try:
        ck[n] = F.seu_ckan(n)
    except F.FuenteError as e:
        ck[n] = []; print("error", n, e)
agg = {
 "endeutament": sorted(({"any": r["ANY"], "deute_viu_eur": r["DEUTE_VIU"], "cens": r["CENS"]} for r in ck["endeutament"]), key=lambda r: r["any"]),
 "pmp": sorted(({"periode": r["DATA_ACTUALITZACIO"][:10], "pmp_dies": r["PERIODE_MIG_PAGAMENT"]} for r in ck["pmp_proveidors"]), key=lambda r: r["periode"]),
 "tipus_impositius": [r for r in ck["tipus_impositius"] if int(r["ANY"]) >= 2024],
 "subvencions_per_any": {}, "convenis_per_any": {}, "actes_ple": sorted(r["DATA_ACORD"][:10] for r in ck["actes_ple"]),
 "calendari_padrons": [{"resum": r["RESUM"], "data": r["DATA_PUB"][:10], "url": r["ENLLAÇ"]} for r in ck["calendari_padrons"]],
}
for r in ck["subvencions"]:
    y = str(r.get("DATA_DE_CONCESSIO", ""))[:4]; a = agg["subvencions_per_any"].setdefault(y, {"n": 0, "import_eur": 0.0})
    a["n"] += 1; a["import_eur"] = round(a["import_eur"] + float(r.get("IMPORT") or 0), 2)
for r in ck["convenis"]:
    y = str(r.get("ANY_SIGNATURA")); agg["convenis_per_any"][y] = agg["convenis_per_any"].get(y, 0) + 1
guardar("aoc_dades_obertes_agregado.json", agg, F.FUENTES["seu_ckan"]["url"])

# 3) Catastro
cat = {}
for y in (2026, 2025):
    try: cat["ibi"] = F.catastro_ibi_prat(y); break
    except Exception: pass
for y in (2026, 2025):
    try: cat["usos"] = F.catastro_urbano_usos(y); break
    except Exception: pass
guardar("catastro_estadisticas.json", cat, "https://www.catastro.hacienda.gob.es/es-ES/estadisticas.html")

def ult(lst): return lst[-1] if lst else None
def item(id_, nombre, base, estado, url, fecha=None, nota="", beneficio=""):
    return {"id": id_, "obligacion": nombre, "base_legal": base, "estado": estado, "url": url, "fecha": fecha, "nota": nota,
            "beneficio_ciudadano_si_se_corrige": beneficio}

def portal_item(key, nombre, base, beneficio="", override=None):
    p = P.get(key, {}); est, fecha, nota = p.get("estado", "no_encontrado"), p.get("actualizacion"), ""
    if p.get("contenido_dinamico"): nota = "contenido cargado desde dataset AOC"
    if est == "no_encontrado" and not nota: nota = "la página solo muestra el texto introductorio; confirmar en navegador antes de reclamar"
    if est == "desactualizado" and not nota: nota = f"última actualización {fecha}; frecuencia declarada: {p.get('frecuencia_declarada','')[:60]}"
    if override: est, fecha, nota = override
    return item(key, nombre, base, est, p.get("url", T.BASE), fecha, nota, beneficio)

sub_ult = max((y for y in agg["subvencions_per_any"] if y.isdigit()), default=None)
pmp_ult = ult(agg["pmp"]); deu_ult = ult(agg["endeutament"]); tip_ult = max((int(r["ANY"]) for r in agg["tipus_impositius"]), default=None)
CHECK = [
 portal_item("carrecs-electes", "Cargos electos", "Llei 19/2014 art. 9.1.b; Ley 19/2013 art. 6.1"),
 portal_item("cartipas-organitzacio-politica", "Cartipàs / organización política", "Llei 19/2014 art. 9.1"),
 portal_item("organigrama-de-l-ens", "Organigrama", "Llei 19/2014 art. 9.1.c; Ley 19/2013 art. 6.1", "saber quién es responsable de cada servicio"),
 portal_item("alts-carrecs-personal-directiu-i-carrecs-eventuals", "Retribuciones y declaraciones de altos cargos", "Llei 19/2014 arts. 9 y 11.1.b-c; Ley 19/2013 art. 8.1.f-g"),
 portal_item("retribucions-indemnitzacions-i-dietes-dels-empleats-publics", "Retribuciones de empleados públicos", "Llei 19/2014 art. 11.1.b", "control del gasto de personal"),
 portal_item("relacio-de-llocs-de-treball-rlt", "RLT", "Llei 19/2014 art. 9.1.d"),
 portal_item("estatuts", "ROM y estatutos de entes (enlace CIDO)", "Llei 19/2014 art. 10.1.a; Ley 19/2013 art. 7"),
 portal_item("ordenances-fiscals", "Ordenanzas fiscales vigentes (portal)", "Llei 19/2014 art. 10.1.a; Ley 19/2013 art. 7.c", "conocer impuestos y bonificaciones a las que se tiene derecho"),
 item("of1_ibi_2026", "OF 1 IBI 2026 (texto)", "TRLRHL art. 17.4", "publicado", "https://bop.diba.cat/anuncio/ver-pdf/3878031", "2025-12-23", "BOPB CVE 202510200458"),
 item("of_2027_aprobacion_inicial", "Ordenanzas fiscales 2027 (aprobación inicial Ple 22-10-2026)", "TRLRHL art. 17.1-2 (30 días de exposición)", "no_encontrado",
      "https://www.lavanguardia.com/elllobregat/sociedad/20261023/11666278/prat-congela-ibi-viviendas-comercios-2027-sube-70-grandes-propiedades.html", "2026-10-23",
      "solo prensa; el edicto BOPB y el texto se vigilan a diario (sub_1_2). Abre plazo de reclamaciones", "permite presentar reclamaciones en plazo"),
 item("of23_aparcamiento", "OF 23 tasa estacionamiento (Zona Taronja Mas Blau)", "TRLRHL art. 17.4", "no_encontrado", "https://cido.diba.cat/", None,
      "texto consolidado no localizado; tarifa 8 €/mes solo verificada en prensa", "trabajadores conocen la tarifa y sus derechos"),
 item("of_tasa_residuos", "OF tasa de residuos (descuento 40 % vigente según el Ajuntament)", "Ley 7/2022 art. 11.3; TRLRHL art. 17.4", "no_encontrado", "https://cido.diba.cat/", None,
      "texto no localizado automáticamente", "hogares conocen las bonificaciones"),
 portal_item("tipus-impositius", "Tipos impositivos", "Llei 19/2014 art. 11", "evitar confusión sobre lo que se paga",
      override=(("desactualizado" if tip_ult and tip_ult < 2026 else "publicado"), f"{tip_ult}", f"el dataset llega a {tip_ult}: IBI urbana 0,63; en 2026 rige 0,6199 (OF1)")),
 portal_item("calendari-i-padrons-fiscals", "Calendario y padrones fiscales", "TRLRHL art. 102.3 LGT", override=("publicado", ult(sorted(r["data"] for r in agg["calendari_padrons"])), "edicto anual en CIDO/BOPB")),
 portal_item("pressupost", "Presupuestos 2019-2026", "Llei 19/2014 art. 11.1.a; Ley 19/2013 art. 8.1.d"),
 portal_item("bases-d-execucio-del-pressupost-188", "Bases de ejecución del presupuesto", "Llei 19/2014 art. 11.1.a", "conocer las reglas de gasto"),
 portal_item("modificacio-de-pressupostos", "Modificaciones presupuestarias", "Llei 19/2014 art. 11.1.a"),
 portal_item("liquidacio-del-pressupost", "Liquidación del presupuesto", "Llei 19/2014 art. 11.1.c; Ley 19/2013 art. 8.1.e"),
 portal_item("compte-general", "Cuenta general", "Llei 19/2014 art. 11.1.c; Ley 19/2013 art. 8.1.e; TRLRHL art. 212", "conocer la situación patrimonial real"),
 portal_item("execucio-pressupostaria-trimestral", "Ejecución presupuestaria trimestral", "Llei 19/2014 art. 11.1.a; Ley 19/2013 art. 8.1.d", "seguir el gasto durante el año"),
 item("conprel_hacienda", "Ejecución y liquidación en Hacienda (CONPREL)", "LO 2/2012; Orden HAP/2105/2012", "no_verificado", F.FUENTES.get("conprel_hacienda", {}).get("url", "https://serviciostelematicosext.hacienda.gob.es/SGFAL/CONPREL"), None, "aplicación web sin API"),
 portal_item("endeutament", "Endeudamiento", "Llei 19/2014 art. 11.1.a", override=("publicado", f"{deu_ult['any']}" if deu_ult else None, f"deuda viva {deu_ult['any']}: {deu_ult['deute_viu_eur']:,.0f} €" if deu_ult else "")),
 portal_item("periode-mitja-de-pagament-a-proveidors", "Periodo medio de pago", "Ley 19/2013 art. 8.1.d; RD 635/2014",
      override=("publicado", pmp_ult["periode"] if pmp_ult else None, f"PMP {pmp_ult['pmp_dies']} días (máx. legal 30)" if pmp_ult else "")),
 portal_item("auditories-de-comptes", "Auditorías / control financiero", "Llei 19/2014 art. 11.1.c; Ley 19/2013 art. 8.1.e", "saber si el dinero se usa bien"),
 portal_item("pla-anual-de-control-financer", "Plan anual de control financiero", "RD 424/2017"),
 portal_item("inventari-general-del-patrimoni", "Inventario de patrimonio", "Llei 19/2014 art. 11.1.d"),
 portal_item("relacio-de-contractes-adjudicats-historics", "Contratos adjudicados", "Llei 19/2014 art. 13; Ley 19/2013 art. 8.1.a"),
 portal_item("relacio-de-contractes-menors-historic", "Contratos menores", "Llei 19/2014 art. 13.1; Ley 19/2013 art. 8.1.a"),
 portal_item("modificacions-de-contractes", "Modificaciones de contratos", "Llei 19/2014 art. 13.1.d; Ley 19/2013 art. 8.1.a", "control de sobrecostes"),
 item("placsp", "Perfil contratante (PLACSP)", "LCSP art. 63", "publicado", F.FUENTES["placsp_atom"]["url"], HOY, "ingesta diaria (sub_5_2)"),
 item("registre_contractes_gencat", "Plataforma de contractació pública de Catalunya", "LCSP art. 63; Llei 19/2014 art. 13", "publicado", "https://contractaciopublica.cat/ca/perfils-contractant/detall/4727047?categoria=0", HOY),
 portal_item("convenis-de-col-laboracio", "Convenios", "Llei 19/2014 art. 14; Ley 19/2013 art. 8.1.b",
      override=("publicado", max(agg["convenis_per_any"], default=None), f"convenios por año: {dict(sorted(agg['convenis_per_any'].items())[-4:])}")),
 portal_item("informacio-de-l-execucio-dels-convenis", "Ejecución de convenios", "Llei 19/2014 art. 14.2"),
 portal_item("subvencions-atorgades", "Subvenciones concedidas", "Llei 19/2014 art. 15; Ley 19/2013 art. 8.1.c",
      override=("publicado", sub_ult, f"dataset AOC/BDNS: {agg['subvencions_per_any'].get(sub_ult)} en {sub_ult}; la fecha de la página es antigua")),
 portal_item("convocatories-de-subvencions-i-ajuts", "Convocatorias de subvenciones", "Llei 19/2014 art. 15.1.a"),
 portal_item("actes-de-ple", "Actas del Pleno", "Llei 19/2014 art. 10.1; LBRL art. 70.1",
      override=("publicado", ult(agg["actes_ple"]), f"{len(agg['actes_ple'])} actas en dataset AOC")),
 item("videos_ple", "Vídeos de plenos", "LBRL art. 70.1 (publicidad sesiones)", "publicado", "https://www.elprat.cat/ajuntament/ple-municipal", HOY, "página accesible; no se auditan los vídeos uno a uno"),
 portal_item("convocatories-de-sessions-del-ple", "Convocatorias del Pleno", "LBRL art. 46.2.b; Llei 19/2014 art. 10", "saber cuándo y qué se vota"),
 item("mociones_aprobadas", "Mociones aprobadas (listado)", "Llei 19/2014 art. 10.1", "no_encontrado", T.BASE, None, "no existe listado propio; solo dentro de las actas", "seguir el cumplimiento de mociones"),
 portal_item("acords-de-junta-de-govern", "Acuerdos de Junta de Govern", "Llei 19/2014 art. 10.1.f"),
 portal_item("resolucions-de-les-sol-licituds-d-acces-a-la-informacio-publica", "Resoluciones de acceso a la información", "Llei 19/2014 art. 10.1.f", "ver qué información se pide y se deniega"),
 portal_item("memories-i-documents-dels-projectes-normatius-en-curs", "Proyectos normativos en curso", "Llei 19/2014 art. 10.1.c-d; Ley 19/2013 art. 7.b-d", "participar antes de aprobar normas"),
 portal_item("pla-anual-normatiu", "Plan anual normativo", "Ley 39/2015 art. 132"),
 portal_item("planejament-urbanistic", "POUM / planeamiento", "Llei 19/2014 art. 10.1.g"),
 portal_item("convenis-urbanistics", "Convenios urbanísticos", "TRLU art. 105"),
 portal_item("organismes-dependents-o-vinculats", "Entes dependientes (Prat Espais, Aigües del Prat, etc.)", "Llei 19/2014 art. 9.1.a"),
 item("prat_espais_cuentas_vpo", "Prat Espais SLU: cuentas anuales y adjudicación VPO", "Llei 19/2014 arts. 3.1.b y 11", "no_verificado", "https://www.pratespais.com/ca/informacio-juridica", None,
      "web accesible; cuentas y listas de adjudicación no localizadas automáticamente", "transparencia en la vivienda asequible"),
 portal_item("pla-de-mesures-antifrau", "Plan antifraude", "Orden HFP/1030/2021"),
 portal_item("registre-de-grups-d-interes", "Registro de grupos de interés", "Llei 19/2014 art. 45"),
 portal_item("agenda-institucional-dels-alts-carrecs", "Agenda de altos cargos", "Llei 19/2014 art. 55 (código conducta)"),
 portal_item("tauler-d-edictes-i-anuncis", "Tablón de edictos", "Ley 39/2015 art. 45"),
 item("bopb_edictos", "Edictos BOPB", "", "publicado", F.FUENTES["bopb_rss"]["url"], HOY, "ingesta diaria (sub_1_2)"),
 item("catastro_ibi", "Estadística IBI (Catastro)", "", "publicado", cat.get("ibi", {}).get("fuente"), str(cat.get("ibi", {}).get("anyo")), "recibos, base y cuota agregados"),
 item("idescat", "IDESCAT El Prat en xifres", "", "publicado", "https://www.idescat.cat/emex/?id=081691", HOY, "población 66.251 (2025)"),
 item("sindicatura", "Informes Sindicatura de Comptes / rendición cuenta general", "Llei 18/2010", "no_verificado", "http://expedients.sindicatura.cat/VerEnteLiferayCG.php?Codigo=081691000&l=ca_ES", None, "servidor no accesible desde el box"),
 item("antifrau", "Oficina Antifrau de Catalunya", "Llei 14/2008", "no_verificado", "https://www.antifrau.cat/", None, "servidor no accesible desde el box"),
 item("dades_obertes_aoc", "Dades obertes (AOC)", "Llei 19/2014 art. 17", "publicado", "https://seu-e.cat/ca/web/elpratdellobregat/dades-obertes", HOY),
]
from collections import Counter
inv = {"fecha_auditoria": HOY, "ente": "Ajuntament del Prat de Llobregat (CODI_ENS 816910007)",
       "metodo": "Portal de Transparència AOC (112 ítems, base legal declarada por el propio portal) + fuentes oficiales externas",
       "nota_rgpd": "Solo URL, fecha, hash y agregados. No se guardan datos de personas físicas (p. ej. beneficiarios).",
       "resumen_checklist": dict(Counter(i["estado"] for i in CHECK)),
       "resumen_portal": dict(Counter(i["estado"] for i in portal)),
       "checklist": CHECK,
       "portal_completo": [{k: i.get(k) for k in ("id", "titulo", "url", "base_legal", "frecuencia_declarada", "actualizacion", "estado")} for i in portal],
       "kpi": {"impacto_rebaja_ibi_0_48": C.impacto_rebaja_ibi(0.48), "padron": C.PADRON_IBI}}
(ROOT / "inventario_obligaciones.yaml").write_text(yaml.safe_dump(inv, allow_unicode=True, sort_keys=False, width=200), encoding="utf-8")
(OUT / "MANIFIESTO.yaml").write_text(yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False), encoding="utf-8")
print(inv["resumen_checklist"], inv["resumen_portal"])
