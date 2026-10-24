"""Ciclo automático semanal de matriz_el_prat (ejecutable por el autopilot de AGs-Core).

1) Refresca todas las fuentes oficiales (app.fetchers)  2) ejecuta los tests  3) instantánea de métricas y diff contra
la anterior (reports/cambios_YYYY-MM-DD.json)  4) análisis de anomalías  5) reports/iniciativas_YYYY-MM-DD.md con 1-3
iniciativas BORRADOR basadas en datos (IA vía LiteLLM/Gemini si hay clave; si no, reglas). Nunca inventa cifras: todas
salen de los datos descargados. No envía ni presenta nada al Ajuntament.
Uso: python scripts/actualizar_todo.py [--sin-descarga] [--sin-tests]
Autoría: Lázaro López Paz (El Prat de Llobregat) con asistencia de IA. MIT.
"""
from __future__ import annotations
import datetime as dt, json, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app import analitica as A, fetchers, ia  # noqa: E402

REP = ROOT / "reports"; SNAP = REP / "snapshots"


def metricas() -> dict:
    t = A.totales_anuales(A.liquidacion()); u = t.iloc[-1]
    aoc = A.cargar_raiz("aoc_dades_obertes_agregado.json") or {}
    det = A.contratos_detalle(); f = A.formacion(A.personal())
    inv = A.inventario()
    return {"liquidacion_ultimo_anio": int(u["any"]), "ingresos": round(float(u.ingresos)), "gastos": round(float(u.gastos)),
            "saldo": round(float(u.saldo)), "sobrantes_5_anios": round(float(t.tail(5).saldo.sum())),
            "deuda_viva": aoc.get("endeutament", [{}])[-1].get("deute_viu_eur"), "pmp_dias": aoc.get("pmp", [{}])[-1].get("pmp_dies"),
            "contratos_unicos_2024_mas": int(len(det)), "contratos_a_revisar": int(len(A.anomalias_contratos(det))),
            "menores_repetidos": int(len(A.fraccionamiento(det))),
            "formacion_ultimo": {str(k): float(v) for k, v in f.tail(2).items()},
            "transparencia": inv["resumen_checklist"], "alertas": len(A.alertas())}


def diff(a: dict, b: dict, p="") -> list:
    out = []
    for k in sorted(set(a) | set(b)):
        x, y = a.get(k), b.get(k)
        if isinstance(x, dict) and isinstance(y, dict):
            out += diff(x, y, p + k + ".")
        elif x != y:
            out.append({"campo": p + k, "antes": x, "ahora": y})
    return out


def iniciativas_reglas(m: dict) -> list[dict]:
    ini = []
    f = m["formacion_ultimo"]
    if len(f) == 2:
        (a0, v0), (a1, v1) = sorted(f.items())
        if v1 < 0.5 * v0:
            ini.append({"titulo": "Recuperar el presupuesto de formación del personal",
                        "dato": f"Concepto 160200: {v0:,.0f} € ({a0}) → {v1:,.0f} € ({a1}), presupuesto inicial".replace(",", "."),
                        "propuesta": f"Pedir en el Pleno o por instancia que la formación vuelva al menos al nivel de {a0} mediante modificación presupuestaria, priorizando atención ciudadana y digitalización de trámites.",
                        "base_legal": "TREBEP art. 14.g; TRLRHL arts. 177-182 (modificaciones de crédito)",
                        "impacto": f"Coste: {v0 - v1:,.0f} € (diferencia entre ambos años)".replace(",", "."),
                        "fuente": "https://analisi.transparenciacatalunya.cat/d/4g9s-gzp6"})
    if m["sobrantes_5_anios"] > 0:
        ini.append({"titulo": "Destinar parte del superávit a inversiones financieramente sostenibles con beneficio directo para los vecinos",
                    "dato": f"Sobrante (derechos − obligaciones) {m['liquidacion_ultimo_anio']}: {m['saldo']:,.0f} €; suma últimos 5 años: {m['sobrantes_5_anios']:,.0f} €".replace(",", "."),
                    "propuesta": "Solicitar que el Ajuntament publique el remanente de tesorería y un plan de inversiones financieramente sostenibles (eficiencia energética, accesibilidad, digitalización de servicios), con indicadores de tiempo de servicio.",
                    "base_legal": "LOEPSF art. 32 y DA 6ª; TRLRHL DA 16ª",
                    "impacto": "No calculable hasta conocer el remanente de tesorería (pendiente)",
                    "fuente": "https://analisi.transparenciacatalunya.cat/d/ytva-5kp3"})
    t = m["transparencia"]; gaps = t.get("solo_enlace", 0) + t.get("sin_documentos", 0) + t.get("no_encontrado", 0)
    if gaps:
        ini.append({"titulo": "Publicar en el portal la ejecución trimestral del presupuesto y la ejecución de convenios",
                    "dato": f"{gaps} obligaciones de transparencia sin documento propio (solo_enlace/sin_documentos/no_encontrado) a fecha de la revisión",
                    "propuesta": "Preparar BORRADOR de solicitud de acceso a la información y de queja ante la GAIP si no se responde en plazo.",
                    "base_legal": "Llei 19/2014 arts. 11, 14 y 18; Ley 19/2013 art. 8",
                    "impacto": "Sin coste económico relevante; mejora el control ciudadano",
                    "fuente": "inventario_obligaciones.yaml"})
    return ini[:3]


def redactar(ini: list[dict], m: dict, cambios: list) -> str:
    hoy = dt.date.today().isoformat()
    txt = [f"# Iniciativas ciudadanas — {hoy} (BORRADOR)", "",
           "Generado automáticamente a partir de datos oficiales descargados. No se ha presentado nada ante el Ajuntament: "
           "cualquier presentación la decide y la hace Lázaro López Paz. Autoría: Lázaro López Paz, El Prat de Llobregat, con asistencia de IA. CC BY 4.0.", ""]
    modo = ia.estado()
    if modo != "pendiente_de_clave":
        r = ia.preguntar("Resume en 5 líneas, en castellano sencillo, la situación económica del Ayuntamiento y los cambios de esta semana: "
                         + json.dumps(cambios[:20], ensure_ascii=False))
        txt += ["## Resumen (IA, solo con cifras de las fuentes)", r["respuesta"], ""]
    else:
        txt += ["## Resumen", "IA generativa pendiente de clave (GEMINI_API_KEY / LiteLLM). Iniciativas generadas por reglas.", ""]
    txt += ["## Cambios desde la última ejecución", *(f"- `{c['campo']}`: {c['antes']} → {c['ahora']}" for c in cambios), "" if cambios else "- Sin cambios", ""]
    for i, x in enumerate(ini, 1):
        txt += [f"## {i}. {x['titulo']}", f"- **Dato:** {x['dato']}", f"- **Propuesta:** {x['propuesta']}", f"- **Base legal:** {x['base_legal']}",
                f"- **Impacto estimado:** {x['impacto']}", f"- **Fuente:** {x['fuente']}", "- **Estado:** propuesta (pendiente de decisión del usuario)", ""]
    return "\n".join(txt)


def registrar(ini: list[dict]):
    reg = ROOT / "docs" / "INICIATIVAS.md"; s = reg.read_text(encoding="utf-8")
    hoy = dt.date.today().isoformat()
    for x in ini:
        if x["titulo"] not in s:
            s += f"| IA-{hoy}-{abs(hash(x['titulo'])) % 1000:03d} | {x['titulo']} | IA (reglas) | propuesta | {x['fuente']} | {x['impacto']} | {hoy} |\n"
    reg.write_text(s, encoding="utf-8")


def main(argv):
    REP.mkdir(exist_ok=True); SNAP.mkdir(parents=True, exist_ok=True)
    hoy = dt.date.today().isoformat(); res = {"fecha": hoy}
    if "--sin-descarga" not in argv:
        res["fuentes"] = fetchers.run()
    if "--sin-tests" not in argv:
        t = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT, capture_output=True, text=True)
        res["tests"] = t.stdout.strip().splitlines()[-1] if t.stdout else t.stderr[-300:]
    m = metricas()
    prev = sorted(p for p in SNAP.glob("*.json") if p.stem != hoy)
    cambios = diff(json.loads(prev[-1].read_text()), m) if prev else []
    (SNAP / f"{hoy}.json").write_text(json.dumps(m, ensure_ascii=False, indent=1))
    (REP / f"cambios_{hoy}.json").write_text(json.dumps({"anterior": prev[-1].stem if prev else "", "cambios": cambios}, ensure_ascii=False, indent=1))
    det = A.contratos_detalle()
    an = A.anomalias_contratos(det)
    (REP / f"anomalias_{hoy}.json").write_text(an[["organo", "any", "expediente", "objeto", "adjudicatario", "importe", "motivo"]].head(100).to_json(orient="records", force_ascii=False, indent=1))
    ini = iniciativas_reglas(m)
    (REP / f"iniciativas_{hoy}.md").write_text(redactar(ini, m, cambios), encoding="utf-8")
    registrar(ini)
    res.update({"metricas": m, "cambios": len(cambios), "iniciativas": [x["titulo"] for x in ini]})
    print(json.dumps(res, ensure_ascii=False, indent=1, default=str))
    return 0 if "failed" not in str(res.get("tests", "")) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
