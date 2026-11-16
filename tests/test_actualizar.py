import importlib.util, pathlib
spec = importlib.util.spec_from_file_location("act", pathlib.Path(__file__).resolve().parents[1] / "scripts" / "actualizar_todo.py")
act = importlib.util.module_from_spec(spec); spec.loader.exec_module(act)

def test_diff():
    assert act.diff({"a": 1, "b": {"c": 2}}, {"a": 1, "b": {"c": 3}}) == [{"campo": "b.c", "antes": 2, "ahora": 3}]

def test_metricas_e_iniciativas_con_datos():
    m = act.metricas()
    # Valores dependientes de los datos descargados: se comprueba coherencia, no una cifra fija
    assert m["contratos_a_revisar"] >= 1 and m["menores_repetidos"] >= 1
    assert m["contratos_a_revisar"] <= m["contratos_unicos_2024_mas"]
    ini = act.iniciativas_reglas(m)
    assert 1 <= len(ini) <= 3 and all(i["fuente"] for i in ini)
