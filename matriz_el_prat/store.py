"""Almacén SQLite persistente (retención permanente, sin reseteo). Cada registro guarda url de origen y fecha."""
import hashlib, json, os, re, sqlite3, threading, time
from pathlib import Path

DB_PATH = Path(os.getenv("MATRIZ_DB", Path(__file__).resolve().parents[1] / "data" / "matriz_el_prat.sqlite"))
_LOCK = threading.Lock()
# RGPD: se enmascaran NIF/DNI/NIE y correos antes de guardar (no se recogen datos personales).
_PII = [re.compile(r"\b\d{8}[A-Za-z]\b"), re.compile(r"\b[XYZxyz]\d{7}[A-Za-z]\b"),
        re.compile(r"\*{2,}\d+\*{2,}"), re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")]


def redact(text: str) -> str:
    for p in _PII:
        text = p.sub("[dato_personal_omitido]", text)
    return text


class Store:
    def __init__(self, path=None):
        self.path = Path(path or DB_PATH)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path, check_same_thread=False)
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS registros(id TEXT PRIMARY KEY, fuente TEXT, subagente TEXT, titulo TEXT,
          url TEXT, fecha_publicacion TEXT, fecha_ingesta TEXT, relevante INTEGER, datos TEXT);
        CREATE TABLE IF NOT EXISTS ejecuciones(ts TEXT, subagente TEXT, fuente TEXT, estado TEXT, nuevos INTEGER, detalle TEXT);
        CREATE TABLE IF NOT EXISTS retroalimentacion(ts TEXT, propuesta_id TEXT, tipo TEXT, valor TEXT);""")

    def add(self, fuente, subagente, titulo, url, fecha_publicacion="", relevante=False, datos=None) -> bool:
        rid = hashlib.sha256(f"{fuente}|{url}|{titulo}".encode()).hexdigest()[:24]
        with _LOCK:
            cur = self.db.execute("INSERT OR IGNORE INTO registros VALUES(?,?,?,?,?,?,?,?,?)",
                (rid, fuente, subagente, redact(titulo)[:500], url, fecha_publicacion,
                 time.strftime("%Y-%m-%dT%H:%M:%S%z"), int(relevante), json.dumps(datos or {}, ensure_ascii=False)))
            self.db.commit()
        return cur.rowcount == 1

    def log_run(self, subagente, fuente, estado, nuevos=0, detalle=""):
        with _LOCK:
            self.db.execute("INSERT INTO ejecuciones VALUES(?,?,?,?,?,?)",
                (time.strftime("%Y-%m-%dT%H:%M:%S%z"), subagente, fuente, estado, nuevos, detalle[:500]))
            self.db.commit()

    def feedback(self, propuesta_id, tipo, valor):
        with _LOCK:
            self.db.execute("INSERT INTO retroalimentacion VALUES(?,?,?,?)",
                (time.strftime("%Y-%m-%dT%H:%M:%S%z"), propuesta_id, tipo, str(valor)))
            self.db.commit()

    def query(self, sql, args=()):
        return [dict(zip([c[0] for c in cur.description], r)) for cur in [self.db.execute(sql, args)] for r in cur.fetchall()]

    def counts(self):
        return {r["fuente"]: r["n"] for r in self.query("SELECT fuente, COUNT(*) n FROM registros GROUP BY fuente")}
