import json


class MatrizElPratAgentes:
    def __init__(self, db_path="base_datos_master_mejoras_el_prat.json"):
        with open(db_path, "r", encoding="utf-8") as f:
            self.db = json.load(f)["registro_maestro_mejoras_el_prat"]

    def verificar_declaracion_independencia(self):
        return {
            "autor": self.db["autor"],
            "municipio": self.db["municipio"],
            "caracter": self.db["caracter_del_proyecto"],
            "vinculacion": self.db["vinculacion_institucional"],
            "finalidad": self.db["finalidad"],
        }

    def simular_balance_presupuestario(self):
        """Calcula el balance ordinario a partir del catálogo.

        Las partidas con fuera_presupuesto_ordinario=True (p. ej. VPO plurianual)
        se excluyen del superávit ordinario y se listan aparte.
        """
        ingresos = 0.0
        gastos = 0.0
        fuera = []

        for item in self.db.get("catalogo_mejoras", []):
            impacto = float(item.get("impacto_presupuestario_eur") or 0)
            if item.get("fuera_presupuesto_ordinario"):
                fuera.append(
                    {
                        "id": item.get("id", ""),
                        "titulo": item.get("titulo", ""),
                        "impacto_presupuestario_eur": impacto,
                        "nota": "Inversión plurianual fuera del presupuesto ordinario",
                    }
                )
                continue
            if impacto >= 0:
                ingresos += impacto
            else:
                gastos += impacto

        superavit = ingresos + gastos
        colchon = float(self.db.get("colchon_de_seguridad_anual_eur") or 0)

        return {
            "ingresos_ordinarios_eur": ingresos,
            "desembolso_ordinario_eur": gastos,
            "superavit_neto_ordinario_eur": superavit,
            "cumple_regla_de_oro": superavit >= colchon,
            "inversiones_fuera_presupuesto_ordinario": fuera,
        }

    def calcular_ahorro_ibi_familiar(self, valor_catastral_eur: float):
        cuota_actual = valor_catastral_eur * 0.0062
        cuota_propuesta = valor_catastral_eur * 0.0048
        ahorro = cuota_actual - cuota_propuesta
        return {
            "valor_catastral_eur": valor_catastral_eur,
            "cuota_actual_ibi_eur": round(cuota_actual, 2),
            "cuota_propuesta_ibi_eur": round(cuota_propuesta, 2),
            "ahorro_anual_familiar_eur": round(ahorro, 2),
        }


if __name__ == "__main__":
    sistema = MatrizElPratAgentes()
    print("=== VERIFICACIÓN DE INDEPENDENCIA ===")
    print(json.dumps(sistema.verificar_declaracion_independencia(), indent=2, ensure_ascii=False))
    print("\n=== BALANCE PRESUPUESTARIO ===")
    print(json.dumps(sistema.simular_balance_presupuestario(), indent=2, ensure_ascii=False))
